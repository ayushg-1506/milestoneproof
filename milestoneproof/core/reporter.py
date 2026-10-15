"""
Audit Report & Contractor Letter Generator for MilestoneProof.
Formats verification evidence into formal Markdown audit reports and
diplomatic, constructive contractor review letters that prevent disputes.
"""

from datetime import datetime, timezone
from typing import List
from milestoneproof.core.models import (
    StatementOfWork,
    CriterionVerification,
    FinancialSettlement,
    AuditReport
)


class ReportGenerator:
    """Generates Markdown reports and client-contractor communication documents."""

    @classmethod
    def create_audit_report(
        cls,
        sow: StatementOfWork,
        verifications: List[CriterionVerification],
        settlement: FinancialSettlement
    ) -> AuditReport:
        """Create full AuditReport data model."""
        verified = sum(1 for v in verifications if v.status == "VERIFIED")
        partial = sum(1 for v in verifications if v.status == "PARTIAL")
        missing = sum(1 for v in verifications if v.status == "MISSING")

        letter = cls.generate_contractor_letter(sow, verifications, settlement)

        return AuditReport(
            sow_title=sow.title,
            contractor_name=sow.contractor_name,
            project_name=sow.project_name,
            scan_timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            total_criteria=len(sow.criteria),
            verified_count=verified,
            partial_count=partial,
            missing_count=missing,
            compliance_score=settlement.verified_percentage,
            results=verifications,
            settlement=settlement,
            contractor_letter=letter
        )

    @classmethod
    def generate_markdown_report(cls, report: AuditReport) -> str:
        """Generate comprehensive Markdown deliverable audit report."""
        lines = [
            f"# Milestone Deliverable Audit Report: {report.sow_title}",
            "",
            f"- **Project**: {report.project_name}",
            f"- **Subcontractor / Contractor**: {report.contractor_name}",
            f"- **Audit Timestamp**: {report.scan_timestamp}",
            f"- **Compliance Score**: {report.compliance_score:.1f}%",
            f"- **Verification Breakdown**: {report.verified_count} Verified | {report.partial_count} Partial | {report.missing_count} Missing",
            "",
            "## 1. Financial Settlement Summary",
            "",
            f"| Metric | Amount ({report.settlement.currency}) | Notes |",
            "| :--- | :---: | :--- |",
            f"| **Agreed Milestone Payout** | ${report.settlement.milestone_amount:,.2f} | Full contract value |",
            f"| **Verified Deliverable Payout** | **${report.settlement.recommended_release_amount:,.2f}** | Immediate release recommended ({report.settlement.verified_percentage:.1f}%) |",
            f"| **Retained Escrow Sum** | ${report.settlement.retained_escrow_amount:,.2f} | Held pending missing criteria |",
            "",
        ]

        if report.settlement.deductions:
            lines.extend([
                "### Itemized Escrow Retentions",
                "",
                "| Criterion | Priority | Status | Withheld | Reason / Gap |",
                "| :--- | :---: | :---: | :---: | :--- |"
            ])
            for d in report.settlement.deductions:
                lines.append(
                    f"| **{d['criterion_id']}**: {d['title']} | {d['priority']} | `{d['status']}` | ${d['withheld_amount']:,.2f} | {d['reason']} |"
                )
            lines.append("")

        lines.extend([
            "## 2. Requirement Verification Traceability Matrix",
            ""
        ])

        for res in report.results:
            badge = "✅ VERIFIED" if res.status == "VERIFIED" else ("⚠️ PARTIAL" if res.status == "PARTIAL" else "❌ MISSING")
            lines.extend([
                f"### {res.criterion_id}: {res.title} [{badge}]",
                f"- **Priority**: {res.priority} | **Confidence**: {res.confidence * 100:.0f}%",
                f"- **Audit Finding**: {res.reasoning}"
            ])

            if res.citations:
                lines.append("- **Empirical Evidence Cited**:")
                for cit in res.citations:
                    lines.append(f"  * `{cit.file_path}` (Lines {cit.line_start}-{cit.line_end})")
                    snippet_preview = "\n    > " + "\n    > ".join(cit.snippet.strip().splitlines()[:5])
                    lines.append(snippet_preview)

            if res.gap_description:
                lines.append(f"- **Identified Gap**: {res.gap_description}")
            if res.remediation_steps:
                lines.append(f"- **Remediation Checklist**: {res.remediation_steps}")

            lines.append("")

        lines.extend([
            "---",
            "",
            "## 3. Contractor Communication Draft",
            "",
            "```text",
            report.contractor_letter,
            "```",
            "",
            "*Report generated deterministically by MilestoneProof Edge-Native Deliverable Auditor.*"
        ])

        return "\n".join(lines)

    @classmethod
    def generate_contractor_letter(
        cls,
        sow: StatementOfWork,
        verifications: List[CriterionVerification],
        settlement: FinancialSettlement
    ) -> str:
        """Draft a constructive, diplomatic review letter for the contractor."""
        verified_items = [v for v in verifications if v.status == "VERIFIED"]
        pending_items = [v for v in verifications if v.status in ["PARTIAL", "MISSING"]]

        letter = [
            f"Hi {sow.contractor_name},",
            "",
            f"Thanks for submitting the deliverable artifacts for Milestone '{sow.title}' on {sow.project_name}.",
            "I've completed an automated code and deliverable review against our agreed Statement of Work.",
            ""
        ]

        if verified_items:
            letter.append(f"First, great progress on the core functionality! We have verified {len(verified_items)} of our acceptance criteria:")
            for v in verified_items:
                files_str = f" (in `{v.citations[0].file_path}`)" if v.citations else ""
                letter.append(f"  ✓ {v.criterion_id} - {v.title}{files_str}")
            letter.append("")

        if settlement.retained_escrow_amount == 0:
            letter.extend([
                f"All contractual acceptance criteria have been verified. I have released the full payment of ${settlement.recommended_release_amount:,.2f} {settlement.currency} immediately.",
                "",
                "Thank you for the fantastic work!",
                "Best regards,"
            ])
        else:
            letter.extend([
                f"To keep cash flow moving, I have approved an immediate release of ${settlement.recommended_release_amount:,.2f} {settlement.currency} ({settlement.verified_percentage:.1f}%).",
                f"We are temporarily holding ${settlement.retained_escrow_amount:,.2f} {settlement.currency} in escrow until the following {len(pending_items)} pending items are resolved:",
                ""
            ])

            for p in pending_items:
                status_label = "Partial completion" if p.status == "PARTIAL" else "Not yet detected"
                letter.append(f"  • [{p.criterion_id}] {p.title} ({status_label}):")
                if p.gap_description:
                    letter.append(f"    - Note: {p.gap_description}")
                if p.remediation_steps:
                    letter.append(f"    - Action needed: {p.remediation_steps}")

            letter.extend([
                "",
                "As soon as you push these updates or point me to the relevant branch, I will run the re-verification and release the remaining balance right away.",
                "",
                "Please let me know if you have any questions or need clarification on any requirement!",
                "",
                "Best regards,"
            ])

        return "\n".join(letter)
