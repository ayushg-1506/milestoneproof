"""
Unit tests for AST & File Manifest Scanner.
"""

import os
import unittest
from milestoneproof.core.ast_scanner import ASTScanner


class TestASTScanner(unittest.TestCase):

    def setUp(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.sample_dir = os.path.join(base_dir, "examples", "sample_deliverable")

    def test_scanner_manifest(self):
        scanner = ASTScanner(self.sample_dir)
        summary = scanner.scan()

        self.assertGreater(summary["total_files"], 3)
        self.assertIn("src/auth_service.py", scanner.files_manifest)
        self.assertIn("src/routes.py", scanner.files_manifest)
        self.assertIn("tests/test_auth.py", scanner.files_manifest)

    def test_symbol_extraction(self):
        scanner = ASTScanner(self.sample_dir)
        scanner.scan()

        # Check function extraction
        self.assertIn("create_access_token", scanner.symbols)
        self.assertIn("verify_token", scanner.symbols)

        # Check route extraction
        routes = [r["endpoint"] for r in scanner.routes]
        self.assertTrue(any("login" in r or "google" in r for r in routes))

        # Check test extraction
        test_names = [t["test_name"] for t in scanner.tests]
        self.assertIn("test_create_and_verify_token", test_names)

    def test_find_evidence(self):
        scanner = ASTScanner(self.sample_dir)
        scanner.scan()

        citations = scanner.find_evidence_for_criterion(
            keywords=["jwt", "token", "access"],
            expected_symbols=["create_access_token"],
            verification_type="AST_FUNCTION"
        )
        self.assertTrue(len(citations) > 0)
        first = citations[0]
        self.assertEqual(first.file_path, "src/auth_service.py")
        self.assertGreater(first.line_start, 0)
        self.assertIn("create_access_token", first.snippet)


if __name__ == "__main__":
    unittest.main()
