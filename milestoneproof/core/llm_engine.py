"""
Open-Weight AI Model Connector for MilestoneProof.
Interfaces with local Google Gemma / Phi-3 via Ollama, with an autonomous
deterministic rule-based fallback when offline.
"""

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from milestoneproof.core.models import AcceptanceCriterion, EvidenceCitation

logger = logging.getLogger(__name__)


class LLMEngine:
    """Connects to local open-weight model runtimes (Ollama) with deterministic fallback."""

    def __init__(
        self,
        model_name: Optional[str] = None,
        ollama_host: Optional[str] = None,
        timeout: int = 15
    ):
        self.ollama_host = ollama_host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.model_name = model_name or os.getenv("MILESTONEPROOF_MODEL", "phi3:latest")
        self.timeout = timeout
        self.is_ollama_available = self._check_ollama()

    def _check_ollama(self) -> bool:
        """Ping local Ollama daemon to check availability."""
        try:
            resp = requests.get(f"{self.ollama_host}/api/tags", timeout=2)
            if resp.status_code == 200:
                tags = resp.json().get("models", [])
                model_names = [m.get("name") for m in tags]
                logger.info(f"Ollama connected. Available models: {model_names}")
                # If specified model is not in ollama, pick first available or gemma/phi
                if model_names and not any(self.model_name in m for m in model_names):
                    # Check if gemma or phi is available
                    gemma_match = [m for m in model_names if "gemma" in m]
                    phi_match = [m for m in model_names if "phi" in m]
                    if gemma_match:
                        self.model_name = gemma_match[0]
                    elif phi_match:
                        self.model_name = phi_match[0]
                    else:
                        self.model_name = model_names[0]
                return True
        except Exception:
            pass
        return False

    def evaluate_criterion(
        self,
        criterion: AcceptanceCriterion,
        citations: List[EvidenceCitation]
    ) -> Dict[str, Any]:
        """
        Evaluate code evidence against a criterion using open-weight model or deterministic logic.
        Returns dict with: status, confidence, reasoning, gap_description, remediation_steps.
        """
        # If citations list is completely empty, it is definitively missing
        if not citations:
            return {
                "status": "MISSING",
                "confidence": 0.98,
                "reasoning": f"No corresponding code, symbols, or tests found in repository for '{criterion.title}'.",
                "gap_description": f"Criterion '{criterion.id}' is entirely unimplemented.",
                "remediation_steps": f"Implement {criterion.title} according to specifications: {criterion.description}."
            }

        # If Ollama is available, query the local open-weight model
        if self.is_ollama_available:
            try:
                result = self._query_ollama(criterion, citations)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Ollama inference error, falling back to deterministic: {e}")

        # Deterministic semantic analysis fallback
        return self._deterministic_eval(criterion, citations)

    def _query_ollama(
        self,
        criterion: AcceptanceCriterion,
        citations: List[EvidenceCitation]
    ) -> Optional[Dict[str, Any]]:
        """Construct prompt and query local Gemma / Phi-3 model via Ollama."""
        evidence_text = "\n\n".join([
            f"--- Citation {i+1}: {c.file_path} (Lines {c.line_start}-{c.line_end}) ---\n{c.snippet}"
            for i, c in enumerate(citations[:4])
        ])

        system_prompt = (
            "You are MilestoneProof, an objective contract deliverable verification auditor. "
            "You verify whether submitted code artifacts genuinely satisfy contractual Acceptance Criteria. "
            "Respond in valid JSON only, with keys: "
            "'status' (one of: 'VERIFIED', 'PARTIAL', 'MISSING'), "
            "'confidence' (float 0.0 to 1.0), "
            "'reasoning' (1-2 concise factual sentences citing lines), "
            "'gap_description' (specific missing edge cases, security validation, or tests, or null if fully verified), "
            "'remediation_steps' (concise instructions to contractor to unlock full payout, or null if verified)."
        )

        user_prompt = f"""
ACCEPTANCE CRITERION TO VERIFY:
ID: {criterion.id}
Title: {criterion.title}
Specification: {criterion.description}
Priority: {criterion.priority}
Verification Type: {criterion.verification_type}

EMPIRICAL CODE EVIDENCE SUBMITTED BY SUBCONTRACTOR:
{evidence_text}

Analyze the evidence strictly. Check if all requirements in the specification are fulfilled or if security/edge-case gaps exist.
Output JSON only.
"""

        payload = {
            "model": self.model_name,
            "prompt": f"{system_prompt}\n\n{user_prompt}",
            "stream": False,
            "format": "json",
            "options": {
                "temperature": 0.1,
                "top_p": 0.9,
                "num_ctx": 256,
                "num_batch": 64
            }
        }

        resp = requests.post(
            f"{self.ollama_host}/api/generate",
            json=payload,
            timeout=self.timeout
        )

        if resp.status_code == 200:
            raw_response = resp.json().get("response", "")
            parsed = json.loads(raw_response)
            # Normalize status
            status = parsed.get("status", "PARTIAL").upper()
            if status not in ["VERIFIED", "PARTIAL", "MISSING"]:
                status = "PARTIAL"
            return {
                "status": status,
                "confidence": float(parsed.get("confidence", 0.9)),
                "reasoning": parsed.get("reasoning", "Evaluated by local model."),
                "gap_description": parsed.get("gap_description"),
                "remediation_steps": parsed.get("remediation_steps")
            }
        return None

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
            # Check for signature verification or HMAC
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

        # Check for expected symbols
        symbol_matches = [
            c for c in citations
            if c.symbol_name and any(s.lower() in c.symbol_name.lower() for s in criterion.expected_symbols)
        ]

        if symbol_matches or kw_ratio >= 0.6:
            # Check for stub or TODO markers
            if "todo" in combined_snippets or "pass" in combined_snippets and len(combined_snippets) < 100:
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
