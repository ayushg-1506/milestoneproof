"""
Unit and integration tests for LLMEngine and Open-Weight Model Integration.
Verifies external API compatibility, response normalization, transparent
evaluator attribution, and error/fallback behavior.
"""

import unittest
from unittest.mock import patch, MagicMock
from milestoneproof.core.models import AcceptanceCriterion, EvidenceCitation
from milestoneproof.core.llm_engine import LLMEngine


class TestModelIntegration(unittest.TestCase):

    def setUp(self):
        self.criterion = AcceptanceCriterion(
            id="AC-1",
            title="JWT Authentication Service",
            description="Generate access and refresh tokens securely.",
            priority="MUST",
            verification_type="AST_FUNCTION",
            expected_symbols=["create_access_token"],
            keywords=["jwt", "token"]
        )
        self.citations = [
            EvidenceCitation(
                file_path="src/auth.py",
                line_start=10,
                line_end=20,
                snippet="def create_access_token(user_id):\n    return jwt.encode({'sub': user_id}, 'secret')",
                symbol_name="create_access_token",
                symbol_type="function"
            )
        ]

    def test_provider_detection(self):
        """Verify correct provider identification from API base URL."""
        engine_groq = LLMEngine(api_base="https://api.groq.com/openai/v1", api_key="dummy_key")
        self.assertEqual(engine_groq.provider, "Groq")
        self.assertTrue(engine_groq.is_model_available)

        engine_openrouter = LLMEngine(api_base="https://openrouter.ai/api/v1", api_key="dummy_key")
        self.assertEqual(engine_openrouter.provider, "OpenRouter")
        self.assertTrue(engine_openrouter.is_model_available)

        engine_hf = LLMEngine(api_base="https://api-inference.huggingface.co/v1", api_key="dummy_key")
        self.assertEqual(engine_hf.provider, "HuggingFace")
        self.assertTrue(engine_hf.is_model_available)

        engine_unconfigured = LLMEngine(api_base=None, api_key=None, ollama_host=None)
        self.assertEqual(engine_unconfigured.provider, "Deterministic")
        self.assertFalse(engine_unconfigured.is_model_available)

    def test_deterministic_demo_mode_attribution(self):
        """Verify unconfigured engine clearly attributes evaluation to deterministic engine."""
        engine = LLMEngine(api_base=None, api_key=None, ollama_host=None)
        result = engine.evaluate_criterion(self.criterion, self.citations)

        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(result["evaluator"], "DETERMINISTIC_ENGINE")
        self.assertIn("Deterministic Rule Engine", result["evaluator_details"])

    def test_safe_parse_json_markdown_fence(self):
        """Verify JSON parsing safely strips markdown code fences."""
        engine = LLMEngine()
        raw = '```json\n{"status": "VERIFIED", "confidence": 0.95, "reasoning": "All good."}\n```'
        parsed = engine._safe_parse_json(raw)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed["status"], "VERIFIED")

    def test_format_model_result_normalizes_lists(self):
        """Verify that list outputs from models are safely normalized to strings."""
        engine = LLMEngine()
        model_output = {
            "status": "partial",
            "confidence": 0.88,
            "reasoning": ["Line 12 has token generation.", "Refresh token is missing."],
            "gap_description": ["No refresh token method found."],
            "remediation_steps": ["Add refresh_token function."]
        }
        res = engine._format_model_result(model_output, "llama-3.2 via Groq")
        self.assertEqual(res["status"], "PARTIAL")
        self.assertIsInstance(res["reasoning"], str)
        self.assertIn("Refresh token is missing.", res["reasoning"])
        self.assertIsInstance(res["gap_description"], str)
        self.assertIsInstance(res["remediation_steps"], str)
        self.assertEqual(res["evaluator"], "AI_MODEL")
        self.assertIn("Groq", res["evaluator_details"])

    @patch("requests.post")
    def test_external_api_success(self, mock_post):
        """Verify successful chat completions response produces AI_MODEL attribution."""
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{
                "message": {
                    "content": '{"status": "VERIFIED", "confidence": 0.96, "reasoning": "Token creation verified in src/auth.py.", "gap_description": null, "remediation_steps": null}'
                }
            }]
        }
        mock_post.return_value = mock_resp

        engine = LLMEngine(
            api_base="https://api.groq.com/openai/v1",
            api_key="gsk_test123",
            model_name="llama-3.1-8b-instant"
        )
        result = engine.evaluate_criterion(self.criterion, self.citations)

        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(result["evaluator"], "AI_MODEL")
        self.assertIn("llama-3.1-8b-instant via Groq", result["evaluator_details"])

    @patch("requests.post")
    def test_external_api_rate_limit_fallback(self, mock_post):
        """Verify 429 rate limit error gracefully engages fallback and tags attribution."""
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.text = "Rate limit reached for requests per minute"
        mock_post.return_value = mock_resp

        engine = LLMEngine(
            api_base="https://api.groq.com/openai/v1",
            api_key="gsk_test123",
            model_name="llama-3.1-8b-instant"
        )
        result = engine.evaluate_criterion(self.criterion, self.citations)

        # Output should be generated by fallback, NOT claimed as AI
        self.assertEqual(result["evaluator"], "DETERMINISTIC_FALLBACK")
        self.assertIn("Model inference unavailable", result["evaluator_details"])
        self.assertIn("HTTP 429", result["evaluator_details"])


if __name__ == "__main__":
    unittest.main()
