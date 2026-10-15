"""
Flask Web Application & REST API for MilestoneProof.
Provides an interactive web dashboard and API to audit subcontracted code deliverables
against contractual SOW acceptance criteria using external open-weight AI or
deterministic AST scanning. Supports browser ZIP uploads with secure extraction.
"""

import os
import zipfile
import tempfile
import logging
from typing import Tuple, Optional
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from milestoneproof.core.sow_parser import SOWParser
from milestoneproof.core.verifier import MilestoneVerifier
from milestoneproof.core.reporter import ReportGenerator
from milestoneproof.core.llm_engine import LLMEngine

logger = logging.getLogger(__name__)

app = Flask(
    __name__,
    static_folder="static",
    template_folder="templates"
)
app.config["JSON_SORT_KEYS"] = False
# Enforce a 25 MB max upload size limit for server safety
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024

llm_engine = LLMEngine()


@app.errorhandler(RequestEntityTooLarge)
def handle_file_too_large(e):
    return jsonify({
        "success": False,
        "error": "Uploaded archive exceeds the 25 MB maximum size limit."
    }), 413


def safe_extract_zip(
    zip_source,
    target_dir: str,
    max_files: int = 1500,
    max_total_size: int = 100 * 1024 * 1024
) -> Tuple[bool, Optional[str]]:
    """
    Safely extract a ZIP archive into target_dir.
    Protects against Zip Slip (path traversal), symlink attacks, and zip bombs.
    """
    target_dir = os.path.abspath(target_dir)

    try:
        if not zipfile.is_zipfile(zip_source):
            return False, "Uploaded file is not a valid ZIP archive."
    except Exception as e:
        return False, f"Failed to inspect archive: {str(e)}"

    total_size = 0
    file_count = 0

    with zipfile.ZipFile(zip_source, "r") as zf:
        for member in zf.infolist():
            file_count += 1
            if file_count > max_files:
                return False, f"Archive exceeds maximum allowable file count ({max_files} files)."

            total_size += member.file_size
            if total_size > max_total_size:
                return False, "Archive uncompressed size exceeds maximum allowable limit (100 MB)."

            # Path traversal / Zip Slip prevention
            filename = member.filename
            if ".." in filename or filename.startswith("/") or filename.startswith("\\"):
                return False, f"Archive contains illegal path traversal reference: '{filename}'"

            # Check absolute destination path
            dest_path = os.path.abspath(os.path.join(target_dir, filename))
            try:
                common = os.path.commonpath([target_dir, dest_path])
            except ValueError:
                return False, f"Archive contains file path outside destination: '{filename}'"

            if common != target_dir:
                return False, f"Archive path escapes destination directory: '{filename}'"

            # Check for symlink flags in external attributes
            is_symlink = (member.external_attr >> 16) & 0o120000 == 0o120000
            if is_symlink:
                return False, f"Archive contains disallowed symbolic link: '{filename}'"

        # If all members are safe, perform extraction
        zf.extractall(target_dir)

    return True, None


@app.route("/")
def index():
    """Serve the single-page dashboard."""
    return render_template("index.html")


@app.route("/api/health")
def health():
    """Return system, provider, and model configuration status without exposing secrets."""
    return jsonify({
        "status": "healthy",
        "app": "MilestoneProof",
        "version": "0.2.0",
        "model_configured": llm_engine.is_model_available,
        "provider": llm_engine.provider,
        "active_model": llm_engine.model_name if llm_engine.is_model_available else None,
        "mode": "AI-Assisted" if llm_engine.is_model_available else "Deterministic Demo (AST Rules)",
        "disclaimer": "All audit findings and financial calculations are informative references. Human reviewers retain sole authority for contractual and payment decisions."
    })


@app.route("/api/sample")
def get_sample():
    """Return default sample SOW content and bundled sample deliverable indicator."""
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
        "has_sample_deliverable": os.path.exists(deliverable_path),
        "sow_filename": "sample_sow_auth_payment.md"
    })


@app.route("/api/audit", methods=["POST"])
def run_audit():
    """
    Execute milestone deliverable audit.
    Accepts multipart/form-data (browser file uploads) or application/json.
    Safely extracts ZIP archives into temporary directories and cleans up after audit.
    """
    sow_text = ""
    deliverable_path = ""
    temp_extract_dir: Optional[tempfile.TemporaryDirectory] = None

    try:
        # 1. Parse SOW input (form text, uploaded .md file, or JSON)
        if request.content_type and "multipart/form-data" in request.content_type:
            sow_text = request.form.get("sow_text", "").strip()

            if "sow_file" in request.files:
                sow_file = request.files["sow_file"]
                if sow_file and sow_file.filename:
                    if not (sow_file.filename.endswith(".md") or sow_file.filename.endswith(".txt")):
                        return jsonify({"success": False, "error": "SOW file must be a .md or .txt file."}), 400
                    sow_text = sow_file.read().decode("utf-8", errors="replace")

            use_sample = request.form.get("use_sample_deliverable", "false").lower() in ["true", "1", "yes"]

            # 2. Parse deliverable (uploaded ZIP or demo flag)
            if "deliverable_zip" in request.files and request.files["deliverable_zip"].filename:
                zip_file = request.files["deliverable_zip"]
                if not zip_file.filename.lower().endswith(".zip"):
                    return jsonify({"success": False, "error": "Deliverable codebase must be uploaded as a .zip archive."}), 400

                temp_extract_dir = tempfile.TemporaryDirectory(prefix="mp_audit_")
                ok, err = safe_extract_zip(zip_file, temp_extract_dir.name)
                if not ok:
                    return jsonify({"success": False, "error": f"ZIP archive safety validation failed: {err}"}), 400

                deliverable_path = temp_extract_dir.name

            elif use_sample:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                deliverable_path = os.path.join(base_dir, "examples", "sample_deliverable")

            else:
                raw_path = request.form.get("deliverable_path", "").strip()
                if raw_path and os.path.exists(raw_path):
                    deliverable_path = raw_path
                else:
                    return jsonify({
                        "success": False,
                        "error": "Please upload a .zip archive of the deliverable codebase or select 'Use Bundled Demo Deliverable'."
                    }), 400

        else:
            # JSON Payload support
            data = request.get_json() or {}
            sow_text = data.get("sow_text", "").strip()
            use_sample = data.get("use_sample_deliverable", False)

            if use_sample:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                deliverable_path = os.path.join(base_dir, "examples", "sample_deliverable")
            else:
                deliverable_path = data.get("deliverable_path", "").strip()
                if not deliverable_path or not os.path.exists(deliverable_path):
                    return jsonify({
                        "success": False,
                        "error": f"Deliverable path '{deliverable_path}' does not exist on disk."
                    }), 400

        # Validate SOW presence
        if not sow_text:
            return jsonify({
                "success": False,
                "error": "Please provide a Statement of Work (paste Markdown content or upload a .md file)."
            }), 400

        # Parse SOW criteria
        sow = SOWParser.parse_content(sow_text)
        if not sow.criteria:
            return jsonify({
                "success": False,
                "error": "No acceptance criteria could be parsed from the provided Statement of Work. Ensure criteria use headings, bullet points, or markdown tables."
            }), 400

        # Execute deliverable audit
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
        logger.exception("Audit execution failed")
        return jsonify({
            "success": False,
            "error": f"Audit execution error: {str(e)}"
        }), 500

    finally:
        # Always clean up temporary extracted files
        if temp_extract_dir:
            try:
                temp_extract_dir.cleanup()
            except Exception as e:
                logger.warning(f"Failed to clean up temp extract dir: {e}")


def run_server(host: str = "0.0.0.0", port: int = 5000, debug: bool = False):
    """Run server entrypoint binding to 0.0.0.0 and PORT env var for Render/local."""
    port = int(os.environ.get("PORT", port))
    host = os.environ.get("HOST", host)
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    run_server()
