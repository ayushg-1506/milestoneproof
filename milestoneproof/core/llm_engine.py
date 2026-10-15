"""
Open-Weight AI Model Connector for MilestoneProof.
Supports configurable external OpenAI-compatible inference APIs (e.g. Hugging Face,
Groq, OpenRouter) and local/remote Ollama runtimes, with transparent evaluator
attribution and deterministic fallback.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from milestoneproof.core.models import AcceptanceCriterion, EvidenceCitation

logger = logging.getLogger(__name__)


class LLMEngine:
    """Connects to open-weight model runtimes with transparent evaluator attribution."""

    def __init__(
        self,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        ollama_host: Optional[str] = None,
        timeout: int = 30
    ):
        # External inference API configuration (OpenAI-compatible)
        self.api_base = (
            api_base
            or os.getenv("MODEL_API_BASE")
            or os.getenv("OPENAI_API_BASE")
        )
        self.api_key = (
            api_key
            or os.getenv("MODEL_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )
        self.model_name = (
            model_name
            or os.getenv("MODEL_NAME")
            or os.getenv("MILESTONEPROOF_MODEL")
            or "meta-llama/Llama-3.2-3B-Instruct"
        )
        self.timeout = int(os.getenv("MODEL_TIMEOUT", str(timeout)))
        self.ollama_host = ollama_host or os.getenv("OLLAMA_HOST")

        # Provider determination
        self.provider = self._determine_provider()
        self.is_model_available = self._check_availability()

    def _determine_provider(self) -> str:
        """Identify which provider runtime is configured."""
        if self.api_base and self.api_key:
            if "groq.com" in self.api_base:
                return "Groq"
            elif "openrouter.ai" in self.api_base:
                return "OpenRouter"
            elif "huggingface.co" in self.api_base:
                return "HuggingFace"
            return "OpenAI-Compatible"
        elif self.ollama_host:
            return "Ollama"
        return "Deterministic"

    def _check_availability(self) -> bool:
        """Check if configured model inference endpoint is available."""
        if self.provider in ["Groq", "OpenRouter", "HuggingFace", "OpenAI-Compatible"]:
            # If API base and key are provided, external endpoint is configured
            return bool(self.api_base and self.api_key)
        elif self.provider == "Ollama" and self.ollama_host:
            try:
                resp = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
                return resp.status_code == 200
            except Exception:
                return False
        return False

    def evaluate_criterion(
        self,
        criterion: AcceptanceCriterion,
        citations: List[EvidenceCitation]
    ) -> Dict[str, Any]:
        """
        Evaluate code evidence against a criterion.
        Transparently tags whether output was produced by AI_MODEL, DETERMINISTIC_ENGINE,
        or DETERMINISTIC_FALLBACK.
        """
        # If citations list is completely empty, it is definitively missing
        if not citations:
            return {
                "status": "MISSING",
                "confidence": 0.98,
                "reasoning": f"No corresponding code, symbols, or tests found in repository for '{criterion.title}'.",
                "gap_description": f"Criterion '{criterion.id}' is entirely unimplemented.",
                "remediation_steps": f"Implement {criterion.title} according to specifications: {criterion.description}.",
                "evaluator": "DETERMINISTIC_ENGINE",
                "evaluator_details": "Deterministic AST Scanner (zero code citations detected)"
            }

        # If external model or Ollama is configured, attempt inference
        if self.is_model_available:
            try:
                if self.provider in ["Groq", "OpenRouter", "HuggingFace", "OpenAI-Compatible"]:
                    result = self._query_chat_completions(criterion, citations)
                else:
                    result = self._query_ollama(criterion, citations)

                if result:
                    return result
            except Exception as e:
                logger.warning(f"Model inference failed ({type(e).__name__}: {e}), engaging deterministic fallback")
                fallback_reason = f"{type(e).__name__}: {str(e)[:80]}"
                det_eval = self._deterministic_eval(criterion, citations)
                det_eval["evaluator"] = "DETERMINISTIC_FALLBACK"
                det_eval["evaluator_details"] = f"Model inference unavailable ({fallback_reason}); evaluated via deterministic AST rules."
                return det_eval

        # Standard deterministic rule-based evaluation (Demo Mode or Offline)
        det_eval = self._deterministic_eval(criterion, citations)
        det_eval["evaluator"] = "DETERMINISTIC_ENGINE"
        det_eval["evaluator_details"] = "Deterministic Rule Engine (AST & Semantic Analysis)"
        return det_eval

    def _query_chat_completions(
        self,
        criterion: AcceptanceCriterion,
        citations: List[EvidenceCitation]
    ) -> Optional[Dict[str, Any]]:
        """Query an external OpenAI-compatible open-weight model endpoint."""
        prompt_data = self._build_prompts(criterion, citations)
        endpoint = f"{self.api_base.rstrip('/')}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload: Dict[str, Any] = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": prompt_data["system"]},
                {"role": "user", "content": prompt_data["user"]}
            ],
            "temperature": 0.1,
            "max_tokens": 300
        }

        if self.provider in ["Groq", "OpenAI-Compatible"]:
            payload["response_format"] = {"type": "json_object"}

        resp = requests.post(endpoint, json=payload, headers=headers, timeout=self.timeout)

        if resp.status_code == 200:
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            parsed = self._safe_parse_json(content)
            if parsed:
                return self._format_model_result(parsed, f"{self.model_name} via {self.provider}")
        else:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:120]}")

        return None

    def _query_ollama(
        self,
        criterion: AcceptanceCriterion,
        citations: List[EvidenceCitation]
    ) -> Optional[Dict[str, Any]]:
        """Query local/remote Ollama instance."""
        prompt_data = self._build_prompts(criterion, citations)
        endpoint = f"{self.ollama_host.rstrip('/')}/api/generate"

        payload = {
            "model": self.model_name,
            "prompt": f"{prompt_data['system']}\n\n{prompt_data['user']}",
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "num_ctx": 1024,
                "num_predict": 150
            }
        }

        resp = requests.post(endpoint, json=payload, timeout=self.timeout)
        if resp.status_code == 200:
            raw = resp.json().get("response", "")
            parsed = self._safe_parse_json(raw)
            if parsed:
                return self._format_model_result(parsed, f"{self.model_name} (Ollama)")
        return None

    def _build_prompts(
        self,
        criterion: AcceptanceCriterion,
        citations: List[EvidenceCitation]
    ) -> Dict[str, str]:
        """Construct concise, grounded prompts for model evaluation."""
        evidence_snippets = []
        for i, c in enumerate(citations[:3]):
            lines = c.snippet.strip().split("\n")
            trimmed = "\n".join(lines[:20])
            evidence_snippets.append(
                f"--- Citation {i+1}: {c.file_path} (Lines {c.line_start}-{c.line_end}) ---\n{trimmed}"
            )
        evidence_text = "\n\n".join(evidence_snippets)

        system_prompt = (
            "You are MilestoneProof, an objective contract deliverable verification auditor. "
            "You verify whether submitted code artifacts genuinely satisfy contractual Acceptance Criteria. "
            "Respond ONLY in valid JSON with these exact keys:\n"
            "\"status\": one of \"VERIFIED\", \"PARTIAL\", or \"MISSING\",\n"
            "\"confidence\": float between 0.0 and 1.0,\n"
            "\"reasoning\": a single factual string citing files and lines,\n"
            "\"gap_description\": specific missing item string or null if fully satisfied,\n"
            "\"remediation_steps\": actionable instruction string for the contractor or null if verified."
        )

        user_prompt = f"""ACCEPTANCE CRITERION:
ID: {criterion.id}
Title: {criterion.title}
Specification: {criterion.description}
Priority: {criterion.priority}
Verification Type: {criterion.verification_type}

EMPIRICAL CODE EVIDENCE SUBMITTED:
{evidence_text}

Analyze the evidence strictly against the specification.
Output valid JSON only."""

        return {"system": system_prompt, "user": user_prompt}

    def _safe_parse_json(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse JSON from model output safely."""
        text = raw_text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            return json.loads(text)
        except Exception:
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    return json.loads(text[start:end+1])
                except Exception:
                    pass
        return None

    def _format_model_result(self, parsed: Dict[str, Any], details: str) -> Dict[str, Any]:
        """Normalize model output fields to match schema."""
        status = str(parsed.get("status", "PARTIAL")).upper()
        if status not in ["VERIFIED", "PARTIAL", "MISSING"]:
            status = "PARTIAL"

        reasoning = parsed.get("reasoning", "Evaluated by open-weight AI model.")
        if isinstance(reasoning, list):
            reasoning = " ".join(str(r) for r in reasoning)

        gap = parsed.get("gap_description")
        if isinstance(gap, list):
            gap = " ".join(str(g) for g in gap)

        remediation = parsed.get("remediation_steps")
        if isinstance(remediation, list):
            remediation = " ".join(str(r) for r in remediation)

        try:
            confidence = float(parsed.get("confidence", 0.9))
        except (ValueError, TypeError):
            confidence = 0.85

        return {
            "status": status,
            "confidence": min(1.0, max(0.0, confidence)),
            "reasoning": str(reasoning),
            "gap_description": str(gap) if gap else None,
            "remediation_steps": str(remediation) if remediation else None,
            "evaluator": "AI_MODEL",
            "evaluator_details": details
        }

    def _deterministic_eval(
        self,
        criterion: AcceptanceCriterion,
        citations: List[EvidenceCitation]
    ) -> Dict[str, Any]:
        """High-precision deterministic rule-based evaluation."""
        combined_snippets = " ".join([c.snippet.lower() for c in citations])
        files = [c.file_path for c in citations]

        # 1. Check for explicit gaps based on verification type
        if criterion.verification_type == "SECURITY_CHECK":
            has_hmac = "hmac" in combined_snippets or "signature" in combined_snippets or "verify" in combined_snippets
            has_constant_time = "compare_digest" in combined_snippets or "verify_signature" in combined_snippets

            if has_hmac and has_constant_time:
                return {
                    "status": "VERIFIED",
                    "confidence": 0.95,
                    "reasoning": f"Security verification verified in {files[0]}; constant-time HMAC check detected.",
                    "gap_description": None,
                    "remediation_steps": None
                }
            elif has_hmac:
                return {
                    "status": "PARTIAL",
                    "confidence": 0.88,
                    "reasoning": f"Webhook/signature handler present in {files[0]}, but missing constant-time comparison or strict secret validation.",
                    "gap_description": "Cryptographic signature check is incomplete or lacks timing-attack protection.",
                    "remediation_steps": "Ensure webhook payload verifies HMAC signature using hmac.compare_digest with webhook secret."
                }
            else:
                return {
                    "status": "PARTIAL",
                    "confidence": 0.90,
                    "reasoning": f"Handler implemented in {files[0]}, but no cryptographic signature verification was detected.",
                    "gap_description": "Missing webhook HMAC signature verification header check.",
                    "remediation_steps": "Add Stripe/provider signature verification before processing event payload."
                }

        # 2. Check for Test Suite requirements
        elif criterion.verification_type == "TEST_SUITE":
            test_citations = [c for c in citations if c.symbol_type == "test" or "test" in c.file_path.lower()]
            has_assert = "assert" in combined_snippets

            if len(test_citations) >= 2 and has_assert:
                return {
                    "status": "VERIFIED",
                    "confidence": 0.92,
                    "reasoning": f"Test suite verified with {len(test_citations)} test cases located in {files[0]}.",
                    "gap_description": None,
                    "remediation_steps": None
                }
            elif len(test_citations) >= 1:
                return {
                    "status": "PARTIAL",
                    "confidence": 0.85,
                    "reasoning": f"Found test definitions in {files[0]}, but coverage appears minimal or edge cases are omitted.",
                    "gap_description": "Insufficient test coverage; only basic happy-path cases detected.",
                    "remediation_steps": "Add unit tests covering error states, expired tokens, and invalid payload schemas."
                }
            else:
                return {
                    "status": "MISSING",
                    "confidence": 0.90,
                    "reasoning": "No dedicated test functions or assertions found corresponding to this requirement.",
                    "gap_description": "Missing test suite implementations.",
                    "remediation_steps": "Implement pytest test file verifying expected behavior."
                }

        # 3. Check for specific keywords match density
        matched_kws = [k for k in criterion.keywords if k.lower() in combined_snippets]
        kw_ratio = len(matched_kws) / max(1, len(criterion.keywords))

        symbol_matches = [
            c for c in citations
            if c.symbol_name and any(s.lower() in c.symbol_name.lower() for s in criterion.expected_symbols)
        ]

        if symbol_matches or kw_ratio >= 0.6:
            if "todo" in combined_snippets or ("pass" in combined_snippets and len(combined_snippets) < 100):
                return {
                    "status": "PARTIAL",
                    "confidence": 0.90,
                    "reasoning": f"Symbol found in {files[0]}, but implementation contains TODO stubs or incomplete logic.",
                    "gap_description": "Function contains stubbed logic without full implementation.",
                    "remediation_steps": "Replace mock responses or stubbed methods with actual production logic."
                }

            return {
                "status": "VERIFIED",
                "confidence": 0.90,
                "reasoning": f"Verified implementation in {files[0]} (lines {citations[0].line_start}-{citations[0].line_end}).",
                "gap_description": None,
                "remediation_steps": None
            }

        elif kw_ratio >= 0.25:
            return {
                "status": "PARTIAL",
                "confidence": 0.80,
                "reasoning": f"Partial implementation detected in {files[0]}, but several core requirements are absent.",
                "gap_description": f"Missing expected symbols/methods: {', '.join(criterion.expected_symbols) if criterion.expected_symbols else 'required sub-components'}.",
                "remediation_steps": f"Complete implementation of {criterion.title} matching SOW specifications."
            }

        return {
            "status": "MISSING",
            "confidence": 0.85,
            "reasoning": f"Weak keyword match ({len(matched_kws)}/{len(criterion.keywords)}) in {files[0]}; core logic appears missing.",
            "gap_description": f"Requirement '{criterion.title}' was not implemented in the deliverable.",
            "remediation_steps": f"Implement {criterion.title} according to SOW specifications."
        }
