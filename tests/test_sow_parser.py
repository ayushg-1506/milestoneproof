"""
Unit tests for SOW Parser.
"""

import unittest
from milestoneproof.core.sow_parser import SOWParser


class TestSOWParser(unittest.TestCase):

    def test_parse_markdown_table(self):
        markdown_sow = """
# Milestone 2: Payment API Integration
- Project: FinTech SaaS
- Contractor: Sarah Jenkins
- Milestone Amount: $3,200 USD
- Due Date: 2026-11-01

## Criteria Table
| ID | Requirement | Priority | Verification |
| :--- | :--- | :---: | :--- |
| AC-1 | Stripe Payment Processing | MUST | AST_FUNCTION: `process_payment` |
| AC-2 | Webhook Signature Check | MUST | SECURITY_CHECK: HMAC verification |
| AC-3 | Unit Test Coverage | SHOULD | TEST_SUITE: pytest |
"""
        sow = SOWParser.parse_content(markdown_sow)
        self.assertEqual(sow.title, "Milestone 2: Payment API Integration")
        self.assertEqual(sow.project_name, "FinTech SaaS")
        self.assertEqual(sow.contractor_name, "Sarah Jenkins")
        self.assertEqual(sow.milestone_payout, 3200.0)
        self.assertEqual(sow.currency, "USD")
        self.assertEqual(len(sow.criteria), 3)

        ac1 = sow.criteria[0]
        self.assertEqual(ac1.id, "AC-1")
        self.assertEqual(ac1.priority, "MUST")
        self.assertEqual(ac1.weight, 1.5)

        ac3 = sow.criteria[2]
        self.assertEqual(ac3.id, "AC-3")
        self.assertEqual(ac3.priority, "SHOULD")
        self.assertEqual(ac3.weight, 1.0)

    def test_parse_markdown_bullets(self):
        markdown_sow = """
# Milestone 1: Frontend Onboarding
Fee: $1,500 USD

### AC-1: Landing Page Responsive Hero
Implement the primary hero component using Tailwind CSS.

### AC-2: Auth Modal Dialog (Optional)
Modal window with login/signup toggle.
"""
        sow = SOWParser.parse_content(markdown_sow)
        self.assertEqual(sow.milestone_payout, 1500.0)
        self.assertEqual(len(sow.criteria), 2)
        self.assertEqual(sow.criteria[0].id, "AC-1")
        self.assertEqual(sow.criteria[1].priority, "SHOULD")


if __name__ == "__main__":
    unittest.main()
