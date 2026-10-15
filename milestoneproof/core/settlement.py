"""
Milestone Scope Valuation & Criteria Completion Calculator for MilestoneProof.
Calculates objective, contract-grounded criteria completion metrics and proportional
valuation references. All contractual and payment decisions remain under the sole
discretion and authority of the human reviewer.
"""

from typing import List, Dict, Any
from milestoneproof.core.models import (
    StatementOfWork,
    CriterionVerification,
    FinancialSettlement
)


class SettlementCalculator:
    """Calculates weighted completion percentages and informative valuation references."""

    @classmethod
    def calculate(
        cls,
        sow: StatementOfWork,
        verifications: List[CriterionVerification]
    ) -> FinancialSettlement:
        """Compute the financial settlement for a milestone audit."""
        verif_map = {v.criterion_id: v for v in verifications}

        total_weight = 0.0
        earned_weight = 0.0
        deductions: List[Dict[str, Any]] = []

        must_criteria_missing = False

        for criterion in sow.criteria:
            weight = criterion.weight
            total_weight += weight

            verif = verif_map.get(criterion.id)
            status = verif.status if verif else "MISSING"

            criterion_value = (weight / max(1.0, sum(c.weight for c in sow.criteria))) * sow.milestone_payout

            if status == "VERIFIED":
                earned_weight += weight
            elif status == "PARTIAL":
                # Partial award: 50% credit, 50% retained escrow
                earned_weight += (weight * 0.5)
                retained_val = round(criterion_value * 0.5, 2)
                deductions.append({
                    "criterion_id": criterion.id,
                    "title": criterion.title,
                    "status": "PARTIAL",
                    "priority": criterion.priority,
                    "withheld_amount": retained_val,
                    "reason": verif.gap_description if verif and verif.gap_description else "Incomplete deliverable implementation"
                })
            else:  # MISSING or OUT_OF_SCOPE
                if criterion.priority == "MUST":
                    must_criteria_missing = True
                retained_val = round(criterion_value, 2)
                deductions.append({
                    "criterion_id": criterion.id,
                    "title": criterion.title,
                    "status": "MISSING",
                    "priority": criterion.priority,
                    "withheld_amount": retained_val,
                    "reason": verif.gap_description if verif and verif.gap_description else "Requirement not implemented"
                })

        raw_percentage = (earned_weight / total_weight * 100.0) if total_weight > 0 else 0.0

        # Safety rule: If a MUST requirement is completely missing, cap immediate payout at 60%
        final_percentage = raw_percentage
        if must_criteria_missing and final_percentage > 60.0:
            final_percentage = 60.0

        recommended_release = round(sow.milestone_payout * (final_percentage / 100.0), 2)
        retained_escrow = round(sow.milestone_payout - recommended_release, 2)

        return FinancialSettlement(
            milestone_amount=sow.milestone_payout,
            currency=sow.currency,
            verified_percentage=round(final_percentage, 1),
            recommended_release_amount=recommended_release,
            retained_escrow_amount=retained_escrow,
            deductions=deductions
        )
