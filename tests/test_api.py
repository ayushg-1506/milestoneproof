"""
Integration tests for Flask API endpoints.
"""

import os
import unittest
from milestoneproof.app import app


class TestAPIEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
        self.client.testing = True
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sow_path = os.path.join(base_dir, "examples", "sample_sow_auth_payment.md")
        self.deliverable_path = os.path.join(base_dir, "examples", "sample_deliverable")

    def test_health_endpoint(self):
        resp = self.client.get("/api/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["app"], "MilestoneProof")
        self.assertEqual(data["status"], "healthy")

    def test_sample_endpoint(self):
        resp = self.client.get("/api/sample")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertIn("sow_content", data)
        self.assertIn("deliverable_path", data)

    def test_audit_endpoint(self):
        with open(self.sow_path, "r", encoding="utf-8") as f:
            sow_text = f.read()

        payload = {
            "sow_text": sow_text,
            "deliverable_path": self.deliverable_path
        }
        resp = self.client.post("/api/audit", json=payload)
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data["success"])
        report = data["report"]
        self.assertEqual(report["total_criteria"], 5)
        self.assertGreater(report["settlement"]["recommended_release_amount"], 0)
        self.assertIn("markdown_export", report)

    def test_audit_invalid_path(self):
        payload = {
            "sow_text": "# Title\n| AC-1 | Test | MUST |",
            "deliverable_path": "/non/existent/path/999"
        }
        resp = self.client.post("/api/audit", json=payload)
        self.assertEqual(resp.status_code, 400)


if __name__ == "__main__":
    unittest.main()
