"""
Command Line Interface for MilestoneProof.
Enables terminal auditing, CI integration, and running the local dashboard server.
"""

import sys
import os
import argparse
from milestoneproof.core.verifier import MilestoneVerifier
from milestoneproof.core.reporter import ReportGenerator


def main():
    parser = argparse.ArgumentParser(
        prog="milestoneproof",
        description="Edge-Native SOW & Subcontractor Deliverable Verification Engine"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: audit
    audit_parser = subparsers.add_parser("audit", help="Audit a deliverable repository against an SOW")
    audit_parser.add_argument("--sow", required=True, help="Path to Statement of Work Markdown/JSON file")
    audit_parser.add_argument("--deliverable", required=True, help="Path to deliverable repository directory")
    audit_parser.add_argument("--output", help="Optional path to export Markdown audit report")
    audit_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON summary")

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Launch the local interactive web dashboard")
    serve_parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    serve_parser.add_argument("--port", type=int, default=5000, help="Port number (default: 5000)")
    serve_parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    # Command: demo
    subparsers.add_parser("demo", help="Run quick audit on built-in sample deliverable")

    args = parser.parse_args()

    if args.command == "audit":
        run_audit(args.sow, args.deliverable, args.output, args.json)
    elif args.command == "serve":
        from milestoneproof.app import run_server
        run_server(host=args.host, port=args.port, debug=args.debug)
    elif args.command == "demo":
        run_demo()
    else:
        parser.print_help()
        sys.exit(1)


def run_audit(sow_path: str, deliverable_path: str, output_path: str = None, json_output: bool = False):
    print(f"\n🔍 [MilestoneProof] Auditing deliverable: {deliverable_path}")
    print(f"📄 [MilestoneProof] Checking against SOW: {sow_path}\n")

    report = MilestoneVerifier.audit_from_files(sow_path, deliverable_path)

    if json_output:
        print(report.model_dump_json(indent=2) if hasattr(report, "model_dump_json") else report.json(indent=2))
        return

    # Print terminal summary
    print("=" * 65)
    print(f"MILESTONE DELIVERABLE AUDIT REPORT: {report.sow_title}")
    print("=" * 65)
    print(f"Subcontractor:     {report.contractor_name}")
    print(f"Compliance Score:  {report.compliance_score:.1f}%")
    print(f"Verified Criteria: {report.verified_count}/{report.total_criteria}")
    print(f"Partial Criteria:  {report.partial_count}")
    print(f"Missing Criteria:  {report.missing_count}")
    print("-" * 65)
    print("SCOPE VALUATION REFERENCE (INFORMATIVE ONLY):")
    print(f"  Milestone Contract Total:    ${report.settlement.milestone_amount:,.2f} {report.settlement.currency}")
    print(f"  Proportional Scope Complete: ${report.settlement.recommended_release_amount:,.2f} {report.settlement.currency} ({report.settlement.verified_percentage:.1f}%)")
    print(f"  Unverified Scope Value:      ${report.settlement.retained_escrow_amount:,.2f} {report.settlement.currency}")
    print("-" * 65)
    print("VERIFICATION MATRIX:")
    for res in report.results:
        symbol = "✓" if res.status == "VERIFIED" else ("~" if res.status == "PARTIAL" else "✗")
        print(f"  [{symbol}] {res.criterion_id} - {res.title}: {res.status}")
        if res.citations:
            first = res.citations[0]
            print(f"      Evidence: {first.file_path}:{first.line_start}-{first.line_end}")
        if res.gap_description:
            print(f"      Gap: {res.gap_description}")

    if output_path:
        md_content = ReportGenerator.generate_markdown_report(report)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(md_content)
        print(f"\n📝 Full Markdown Audit Report exported to: {output_path}")

    print("\n" + "=" * 65 + "\n")


def run_demo():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sow_path = os.path.join(base_dir, "examples", "sample_sow_auth_payment.md")
    deliverable_path = os.path.join(base_dir, "examples", "sample_deliverable")
    run_audit(sow_path, deliverable_path)


if __name__ == "__main__":
    main()
