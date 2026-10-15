"""
Flask Web Application & REST API for MilestoneProof.
Provides an interactive dashboard to configure SOWs, scan deliverables,
inspect empirical code citations, and export settlement audit reports.
"""

import os
import tempfile
from flask import Flask, request, jsonify, render_template, send_from_directory
from milestoneproof.core.models import StatementOfWork
from milestoneproof.core.sow_parser import SOWParser
from milestoneproof.core.verifier import MilestoneVerifier
from milestoneproof.core.reporter import ReportGenerator
from milestoneproof.core.llm_engine import LLMEngine

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)
app.config["JSON_SORT_KEYS"] = False

llm_engine = LLMEngine()


@app.route("/")
def index():
    """Serve the single-page dashboard."""
    return render_template("index.html")


@app.route("/api/health")
def health():
    """Return system and local open-weight model status."""
    return jsonify({
        "status": "healthy",
        "app": "MilestoneProof",
        "version": "0.1.0",
        "ollama_connected": llm_engine.is_ollama_available,
        "active_model": llm_engine.model_name,
        "ollama_host": llm_engine.ollama_host
    })


@app.route("/api/sample")
def get_sample():
    """Return default sample SOW and deliverable paths for quick 1-click testing."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sow_path = os.path.join(base_dir, "examples", "sample_sow_auth_payment.md")
    deliverable_path = os.path.join(base_dir, "examples", "sample_deliverable")

    sow_content = ""
    if os.path.exists(sow_path):
        with open(sow_path, "r", encoding="utf-8") as f:
            sow_content = f.read()

    return jsonify({
        "sow_content": sow_content,
        "deliverable_path": deliverable_path,
        "sow_filename": "sample_sow_auth_payment.md"
    })


@app.route("/api/audit", methods=["POST"])
def run_audit():
    """Execute milestone deliverable audit."""
    data = request.get_json() or {}

    sow_text = data.get("sow_text", "")
    sow_path = data.get("sow_path", "")
    deliverable_path = data.get("deliverable_path", "")

    if not deliverable_path or not os.path.exists(deliverable_path):
        return jsonify({
            "error": f"Deliverable path '{deliverable_path}' does not exist on disk."
        }), 400

    try:
        if sow_text:
            sow = SOWParser.parse_content(sow_text)
        elif sow_path and os.path.exists(sow_path):
            sow = SOWParser.parse_file(sow_path)
        else:
            return jsonify({"error": "Either 'sow_text' or valid 'sow_path' must be provided."}), 400

        verifier = MilestoneVerifier(llm_engine=llm_engine)
        report = verifier.audit_deliverable(sow, deliverable_path)
        markdown_report = ReportGenerator.generate_markdown_report(report)

        report_dict = report.model_dump() if hasattr(report, "model_dump") else report.dict()
        report_dict["markdown_export"] = markdown_report

        return jsonify({
            "success": True,
            "report": report_dict
        })

    except Exception as e:
        return jsonify({"error": f"Audit execution failed: {str(e)}"}), 500


def run_server(host: str = "127.0.0.1", port: int = 5000, debug: bool = False):
    """Run server entrypoint."""
    port = int(os.environ.get("PORT", port))
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server()
