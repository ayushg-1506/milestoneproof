"""
Verification Orchestrator for MilestoneProof.
Coordinates AST parsing, open-weight model semantic evaluation, financial
settlement calculation, and final audit report synthesis.
"""

from typing import Optional, List
from milestoneproof.core.models import (
    StatementOfWork,
    CriterionVerification,
    AuditReport
)
from milestoneproof.core.sow_parser import SOWParser
from milestoneproof.core.ast_scanner import ASTScanner
from milestoneproof.core.llm_engine import LLMEngine
from milestoneproof.core.settlement import SettlementCalculator
from milestoneproof.core.reporter import ReportGenerator


class MilestoneVerifier:
    """End-to-end verifier for milestone deliverables."""

    def __init__(self, llm_engine: Optional[LLMEngine] = None):
        self.llm = llm_engine or LLMEngine()

    def audit_deliverable(
        self,
        sow: StatementOfWork,
        deliverable_path: str
    ) -> AuditReport:
        """Audit a local deliverable repository against an SOW specification."""
        # 1. Scan deliverable directory
        scanner = ASTScanner(deliverable_path)
        scanner.scan()

        # 2. Verify each acceptance criterion
        verifications: List[CriterionVerification] = []

        for criterion in sow.criteria:
            # Find evidence citations deterministically
            citations = scanner.find_evidence_for_criterion(
                keywords=criterion.keywords,
                expected_symbols=criterion.expected_symbols,
                verification_type=criterion.verification_type
            )

            # Evaluate with hybrid open-weight LLM / deterministic engine
            eval_result = self.llm.evaluate_criterion(criterion, citations)

            verifications.append(
                CriterionVerification(
                    criterion_id=criterion.id,
                    title=criterion.title,
                    priority=criterion.priority,
                    status=eval_result["status"],
                    confidence=eval_result["confidence"],
                    citations=citations,
                    reasoning=eval_result["reasoning"],
                    gap_description=eval_result.get("gap_description"),
                    remediation_steps=eval_result.get("remediation_steps")
                )
            )

        # 3. Calculate financial settlement
        settlement = SettlementCalculator.calculate(sow, verifications)

        # 4. Synthesize final audit report and contractor communication
        report = ReportGenerator.create_audit_report(sow, verifications, settlement)
        return report

    @classmethod
    def audit_from_files(
        cls,
        sow_path: str,
        deliverable_path: str,
        llm_engine: Optional[LLMEngine] = None
    ) -> AuditReport:
        """Convenience method to load SOW from file and audit deliverable."""
        sow = SOWParser.parse_file(sow_path)
        verifier = cls(llm_engine=llm_engine)
        return verifier.audit_deliverable(sow, deliverable_path)
