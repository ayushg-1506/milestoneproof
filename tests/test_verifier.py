"""
End-to-end integration tests for MilestoneVerifier.
"""

import os
import unittest
from milestoneproof.core.verifier import MilestoneVerifier


class TestMilestoneVerifier(unittest.TestCase):

    def setUp(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sow_path = os.path.join(base_dir, "examples", "sample_sow_auth_payment.md")
        self.deliverable_path = os.path.join(base_dir, "examples", "sample_deliverable")

    def test_sample_audit_execution(self):
        report = MilestoneVerifier.audit_from_files(self.sow_path, self.deliverable_path)

        self.assertEqual(report.total_criteria, 5)
        self.assertGreater(report.verified_count, 0)
        self.assertGreater(report.missing_count, 0)

        # Check that AC-1 (JWT Auth) is verified
        ac1 = next((r for r in report.results if r.criterion_id == "AC-1"), None)
        self.assertIsNotNone(ac1)
        self.assertEqual(ac1.status, "VERIFIED")
        self.assertTrue(len(ac1.citations) > 0)
        self.assertEqual(ac1.citations[0].file_path, "src/auth_service.py")

        # Check that AC-3 (Stripe Webhook Signature) caught the gap (missing HMAC verification)
        ac3 = next((r for r in report.results if r.criterion_id == "AC-3"), None)
        self.assertIsNotNone(ac3)
        self.assertEqual(ac3.status, "PARTIAL")
        self.assertIsNotNone(ac3.gap_description)

        # Check that AC-4 (Rate Limiter) was correctly flagged MISSING
        ac4 = next((r for r in report.results if r.criterion_id == "AC-4"), None)
        self.assertIsNotNone(ac4)
        self.assertEqual(ac4.status, "MISSING")

        # Check settlement calculations
        self.assertEqual(report.settlement.milestone_amount, 2500.0)
        self.assertGreater(report.settlement.recommended_release_amount, 0)
        self.assertGreater(report.settlement.retained_escrow_amount, 0)
        self.assertEqual(
            round(report.settlement.recommended_release_amount + report.settlement.retained_escrow_amount, 2),
            2500.0
        )

        # Check contractor letter generated
        self.assertIn("Alex Rivera", report.contractor_letter)
        self.assertIn("AC-1", report.contractor_letter)


if __name__ == "__main__":
    unittest.main()
