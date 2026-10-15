"""
Unit tests for Report and Letter Generator.
"""

import unittest
from milestoneproof.core.models import (
    StatementOfWork,
    CriterionVerification,
    EvidenceCitation
)
from milestoneproof.core.settlement import SettlementCalculator
from milestoneproof.core.reporter import ReportGenerator


class TestReportGenerator(unittest.TestCase):

    def setUp(self):
        self.sow = StatementOfWork(
            title="Backend Auth Sprint",
            project_name="Agency Client A",
            contractor_name="David Chen",
            milestone_payout=1800.0,
            criteria=[]
        )
        self.verifications = [
            CriterionVerification(
                criterion_id="AC-1",
                title="JWT Authentication",
                priority="MUST",
                status="VERIFIED",
                confidence=0.95,
                citations=[
                    EvidenceCitation(
                        file_path="src/auth.py",
                        line_start=10,
                        line_end=25,
                        snippet="def create_token(): pass"
                    )
                ],
                reasoning="Fully verified in src/auth.py"
            ),
            CriterionVerification(
                criterion_id="AC-2",
                title="Rate Limiter",
                priority="MUST",
                status="MISSING",
                confidence=0.90,
                citations=[],
                reasoning="No rate limiter found",
                gap_description="Rate limiting middleware is missing.",
                remediation_steps="Add rate limiting middleware."
            )
        ]
        self.settlement = SettlementCalculator.calculate(self.sow, self.verifications)

    def test_report_generation(self):
        report = ReportGenerator.create_audit_report(self.sow, self.verifications, self.settlement)
        md = ReportGenerator.generate_markdown_report(report)

        self.assertIn("# Milestone Deliverable Audit Report", md)
        self.assertIn("David Chen", md)
        self.assertIn("Agency Client A", md)
        self.assertIn("AC-1: JWT Authentication", md)
        self.assertIn("AC-2: Rate Limiter", md)
        self.assertIn("src/auth.py", md)

    def test_contractor_letter(self):
        letter = ReportGenerator.generate_contractor_letter(self.sow, self.verifications, self.settlement)
        self.assertIn("Hi David Chen,", letter)
        self.assertIn("AC-1 - JWT Authentication", letter)
        self.assertIn("Rate Limiter", letter)
        self.assertIn("temporarily holding", letter)


if __name__ == "__main__":
    unittest.main()
