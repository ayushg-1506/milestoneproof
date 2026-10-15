"""
Security and File Upload Safety Tests for MilestoneProof.
Verifies ZIP extraction safety, Zip Slip path traversal prevention,
size limits, and multipart upload endpoints.
"""

import io
import os
import zipfile
import tempfile
import unittest
from milestoneproof.app import app, safe_extract_zip


class TestUploadAndSafety(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sow_path = os.path.join(base_dir, "examples", "sample_sow_auth_payment.md")
        with open(self.sow_path, "r", encoding="utf-8") as f:
            self.sow_text = f.read()

    def _create_valid_zip_buffer(self) -> io.BytesIO:
        """Create an in-memory zip archive containing a mock python file."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(
                "auth_module.py",
                "def create_access_token():\n    return 'token'\n\ndef verify_token():\n    return True\n"
            )
        buf.seek(0)
        return buf

    def test_safe_extract_valid_zip(self):
        """Verify normal zip extraction succeeds in temporary directory."""
        buf = self._create_valid_zip_buffer()
        with tempfile.TemporaryDirectory() as tmp_dir:
            ok, err = safe_extract_zip(buf, tmp_dir)
            self.assertTrue(ok)
            self.assertIsNone(err)
            self.assertTrue(os.path.exists(os.path.join(tmp_dir, "auth_module.py")))

    def test_safe_extract_rejects_non_zip(self):
        """Verify non-zip bytes are rejected."""
        buf = io.BytesIO(b"this is not a zip file content")
        with tempfile.TemporaryDirectory() as tmp_dir:
            ok, err = safe_extract_zip(buf, tmp_dir)
            self.assertFalse(ok)
            self.assertIn("not a valid ZIP", err)

    def test_safe_extract_rejects_zip_slip_path_traversal(self):
        """Verify that zip archives with directory traversal paths are rejected."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            # Attempt to escape target directory with ..
            zf.writestr("../../escaped_file.txt", "malicious payload")
        buf.seek(0)

        with tempfile.TemporaryDirectory() as tmp_dir:
            ok, err = safe_extract_zip(buf, tmp_dir)
            self.assertFalse(ok)
            self.assertIn("path traversal", err.lower())

    def test_multipart_audit_with_zip_upload(self):
        """Verify /api/audit successfully processes uploaded zip archive."""
        zip_buf = self._create_valid_zip_buffer()

        data = {
            "sow_text": self.sow_text,
            "deliverable_zip": (zip_buf, "deliverable.zip")
        }

        resp = self.client.post(
            "/api/audit",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertTrue(json_data["success"])
        report = json_data["report"]
        self.assertEqual(report["total_criteria"], 5)
        self.assertIn("markdown_export", report)

    def test_multipart_audit_with_sow_file_upload(self):
        """Verify /api/audit accepts an uploaded SOW .md file."""
        zip_buf = self._create_valid_zip_buffer()
        sow_buf = io.BytesIO(self.sow_text.encode("utf-8"))

        data = {
            "sow_file": (sow_buf, "statement_of_work.md"),
            "deliverable_zip": (zip_buf, "codebase.zip")
        }

        resp = self.client.post(
            "/api/audit",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertTrue(json_data["success"])

    def test_multipart_audit_with_demo_toggle(self):
        """Verify /api/audit succeeds when use_sample_deliverable flag is passed."""
        data = {
            "sow_text": self.sow_text,
            "use_sample_deliverable": "true"
        }

        resp = self.client.post(
            "/api/audit",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(resp.status_code, 200)
        json_data = resp.get_json()
        self.assertTrue(json_data["success"])
        self.assertEqual(json_data["report"]["total_criteria"], 5)

    def test_multipart_audit_rejects_invalid_file_extension(self):
        """Verify uploading a non-zip file as deliverable returns 400."""
        text_buf = io.BytesIO(b"just text")
        data = {
            "sow_text": self.sow_text,
            "deliverable_zip": (text_buf, "archive.tar.gz")
        }

        resp = self.client.post(
            "/api/audit",
            data=data,
            content_type="multipart/form-data"
        )
        self.assertEqual(resp.status_code, 400)
        json_data = resp.get_json()
        self.assertFalse(json_data["success"])
        self.assertIn("zip", json_data["error"].lower())


if __name__ == "__main__":
    unittest.main()
