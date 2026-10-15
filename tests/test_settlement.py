"""
Unit tests for Financial Settlement Calculator.
"""

import unittest
from milestoneproof.core.models import (
    StatementOfWork,
    AcceptanceCriterion,
    CriterionVerification
)
from milestoneproof.core.settlement import SettlementCalculator


class TestSettlementCalculator(unittest.TestCase):

    def setUp(self):
        self.sow = StatementOfWork(
            title="Test Milestone",
            milestone_payout=2000.0,
            currency="USD",
            criteria=[
                AcceptanceCriterion(id="AC-1", title="Core API", description="Desc", priority="MUST", weight=1.5),
                AcceptanceCriterion(id="AC-2", title="Auth", description="Desc", priority="MUST", weight=1.5),
                AcceptanceCriterion(id="AC-3", title="Docs", description="Desc", priority="SHOULD", weight=1.0)
            ]
        )

    def test_full_verified_payout(self):
        verifications = [
            CriterionVerification(criterion_id="AC-1", title="Core API", priority="MUST", status="VERIFIED", reasoning="Good"),
            CriterionVerification(criterion_id="AC-2", title="Auth", priority="MUST", status="VERIFIED", reasoning="Good"),
            CriterionVerification(criterion_id="AC-3", title="Docs", priority="SHOULD", status="VERIFIED", reasoning="Good")
        ]
        settlement = SettlementCalculator.calculate(self.sow, verifications)

        self.assertEqual(settlement.verified_percentage, 100.0)
        self.assertEqual(settlement.recommended_release_amount, 2000.0)
        self.assertEqual(settlement.retained_escrow_amount, 0.0)
        self.assertEqual(len(settlement.deductions), 0)

    def test_partial_and_missing_deductions(self):
        verifications = [
            CriterionVerification(criterion_id="AC-1", title="Core API", priority="MUST", status="VERIFIED", reasoning="Good"),
            CriterionVerification(criterion_id="AC-2", title="Auth", priority="MUST", status="PARTIAL", gap_description="Missing 2FA", reasoning="Partial"),
            CriterionVerification(criterion_id="AC-3", title="Docs", priority="SHOULD", status="MISSING", gap_description="No docs", reasoning="Missing")
        ]
        settlement = SettlementCalculator.calculate(self.sow, verifications)

        # Total weight = 4.0. Earned = 1.5 + (1.5*0.5) + 0 = 2.25. (2.25 / 4.0) = 56.25%
        self.assertAlmostEqual(settlement.verified_percentage, 56.2, places=1)
        self.assertEqual(settlement.recommended_release_amount, 1125.0)
        self.assertEqual(settlement.retained_escrow_amount, 875.0)
        self.assertEqual(len(settlement.deductions), 2)

    def test_missing_must_criteria_cap(self):
        # Even if 2 criteria are verified, if a MUST is missing, payout is capped at 60%
        sow = StatementOfWork(
            title="Cap Test",
            milestone_payout=1000.0,
            criteria=[
                AcceptanceCriterion(id="AC-1", title="Must 1", description="D", priority="MUST", weight=1.0),
                AcceptanceCriterion(id="AC-2", title="Must 2 (Missing)", description="D", priority="MUST", weight=0.2),
                AcceptanceCriterion(id="AC-3", title="Should 1", description="D", priority="SHOULD", weight=1.0),
            ]
        )
        verifications = [
            CriterionVerification(criterion_id="AC-1", title="Must 1", priority="MUST", status="VERIFIED", reasoning="Good"),
            CriterionVerification(criterion_id="AC-2", title="Must 2", priority="MUST", status="MISSING", reasoning="Missing"),
            CriterionVerification(criterion_id="AC-3", title="Should 1", priority="SHOULD", status="VERIFIED", reasoning="Good"),
        ]
        settlement = SettlementCalculator.calculate(sow, verifications)
        self.assertLessEqual(settlement.verified_percentage, 60.0)


if __name__ == "__main__":
    unittest.main()
