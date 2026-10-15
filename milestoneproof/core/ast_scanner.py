"""
Deterministic AST & File Manifest Scanner for MilestoneProof.
Inspects deliverable repositories, extracts Python AST symbols (functions, classes, routes),
detects test suites, and collects empirical evidence citations with exact line numbers.
"""

import os
import ast
import re
from typing import Dict, List, Any, Optional
from milestoneproof.core.models import EvidenceCitation


class ASTScanner:
    """Scans codebases to extract symbols, routes, tests, and line-accurate snippets."""

    IGNORED_DIRS = {
        ".git", "__pycache__", "venv", ".venv", "env", "node_modules",
        ".pytest_cache", ".idea", ".vscode", "dist", "build", ".egg-info"
    }

    def __init__(self, root_path: str):
        self.root_path = os.path.abspath(root_path)
        self.files_manifest: List[str] = []
        self.symbols: Dict[str, List[Dict[str, Any]]] = {}
        self.routes: List[Dict[str, Any]] = []
        self.tests: List[Dict[str, Any]] = []
        self.imports: Dict[str, List[str]] = {}
        self.file_contents: Dict[str, str] = {}

    def scan(self) -> Dict[str, Any]:
        """Perform comprehensive scan of the deliverable directory."""
        if not os.path.exists(self.root_path):
            raise FileNotFoundError(f"Deliverable path does not exist: {self.root_path}")

        for dirpath, dirnames, filenames in os.walk(self.root_path):
            # Prune ignored directories in-place
            dirnames[:] = [d for d in dirnames if d not in self.IGNORED_DIRS]

            for fname in filenames:
                full_path = os.path.join(dirpath, fname)
                rel_path = os.path.relpath(full_path, self.root_path)
                self.files_manifest.append(rel_path)

                # Read and cache file content (if text file)
                try:
                    with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    self.file_contents[rel_path] = content

                    if fname.endswith(".py"):
                        self._scan_python_file(rel_path, content)
                    elif fname.endswith((".js", ".ts")):
                        self._scan_js_file(rel_path, content)

                    if self._is_test_file(rel_path):
                        self._scan_test_file(rel_path, content)

                except Exception as e:
                    # Skip unreadable or binary files safely
                    pass

        return {
            "total_files": len(self.files_manifest),
            "files": self.files_manifest,
            "routes_count": len(self.routes),
            "symbols_count": sum(len(v) for v in self.symbols.values()),
            "tests_count": len(self.tests)
        }

    def _scan_python_file(self, rel_path: str, content: str):
        """Parse Python source code via AST and extract symbols."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Fall back to regex scan if file has syntax error
            self._scan_regex_fallback(rel_path, content)
            return

        lines = content.splitlines()

        for node in ast.walk(tree):
            # 1. Imports
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if rel_path not in self.imports:
                    self.imports[rel_path] = []
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        self.imports[rel_path].append(alias.name)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    self.imports[rel_path].append(node.module)

            # 2. Function Definitions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start = getattr(node, "lineno", 1)
                end = getattr(node, "end_lineno", start + 5)
                snippet = "\n".join(lines[start - 1:end]) if lines else ""

                entry = {
                    "name": node.name,
                    "type": "function",
                    "file": rel_path,
                    "line_start": start,
                    "line_end": end,
                    "snippet": snippet[:500],
                    "docstring": ast.get_docstring(node) or "",
                    "args": [a.arg for a in node.args.args]
                }
                self.symbols.setdefault(node.name.lower(), []).append(entry)

                # Check for web routes via decorators (Flask, FastAPI, etc.)
                for deco in node.decorator_list:
                    deco_str = ast.unparse(deco) if hasattr(ast, "unparse") else ""
                    if any(r in deco_str.lower() for r in ["route", "get", "post", "put", "delete", "patch"]):
                        route_path = self._extract_route_path(deco_str)
                        self.routes.append({
                            "endpoint": node.name,
                            "route": route_path or deco_str,
                            "decorator": deco_str,
                            "file": rel_path,
                            "line_start": start,
                            "line_end": end,
                            "snippet": snippet[:400]
                        })

            # 3. Class Definitions
            elif isinstance(node, ast.ClassDef):
                start = getattr(node, "lineno", 1)
                end = getattr(node, "end_lineno", start + 5)
                snippet = "\n".join(lines[start - 1:min(end, start + 8)]) if lines else ""

                entry = {
                    "name": node.name,
                    "type": "class",
                    "file": rel_path,
                    "line_start": start,
                    "line_end": end,
                    "snippet": snippet[:500],
                    "docstring": ast.get_docstring(node) or ""
                }
                self.symbols.setdefault(node.name.lower(), []).append(entry)

    def _scan_js_file(self, rel_path: str, content: str):
        """Extract routes and exports from JS/TS files."""
        lines = content.splitlines()
        # Find Express/Next/Fastify routes
        route_pattern = re.compile(r"(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
        for i, line in enumerate(lines, start=1):
            match = route_pattern.search(line)
            if match:
                self.routes.append({
                    "endpoint": f"{match.group(1).upper()} {match.group(2)}",
                    "route": match.group(2),
                    "decorator": match.group(0),
                    "file": rel_path,
                    "line_start": i,
                    "line_end": min(i + 5, len(lines)),
                    "snippet": line.strip()
                })

    def _scan_test_file(self, rel_path: str, content: str):
        """Extract test functions and assertion counts."""
        lines = content.splitlines()
        test_pattern = re.compile(r"def\s+(test_[a-zA-Z0-9_]+)\s*\(", re.IGNORECASE)
        assertion_count = len(re.findall(r"\bassert\b", content))

        for i, line in enumerate(lines, start=1):
            m = test_pattern.search(line)
            if m:
                self.tests.append({
                    "test_name": m.group(1),
                    "file": rel_path,
                    "line": i,
                    "snippet": line.strip()
                })

    def _scan_regex_fallback(self, rel_path: str, content: str):
        """Regex fallback for symbol extraction when syntax error is present."""
        lines = content.splitlines()
        func_pattern = re.compile(r"def\s+([a-zA-Z0-9_]+)\s*\(")
        for i, line in enumerate(lines, start=1):
            m = func_pattern.search(line)
            if m:
                self.symbols.setdefault(m.group(1).lower(), []).append({
                    "name": m.group(1),
                    "type": "function",
                    "file": rel_path,
                    "line_start": i,
                    "line_end": min(i + 10, len(lines)),
                    "snippet": line.strip(),
                    "docstring": ""
                })

    def find_evidence_for_criterion(
        self,
        keywords: List[str],
        expected_symbols: List[str],
        verification_type: str
    ) -> List[EvidenceCitation]:
        """Search code manifest and symbol table for empirical proof of a requirement."""
        citations: List[EvidenceCitation] = []
        matched_files = set()

        # 1. Search by exact symbol names
        for sym in expected_symbols:
            sym_clean = sym.strip("`").lower()
            if sym_clean in self.symbols:
                for match in self.symbols[sym_clean]:
                    citations.append(
                        EvidenceCitation(
                            file_path=match["file"],
                            line_start=match["line_start"],
                            line_end=match["line_end"],
                            snippet=match["snippet"],
                            symbol_name=match["name"],
                            symbol_type=match["type"]
                        )
                    )
                    matched_files.add(match["file"])

        # 2. Search routes if verification type is ROUTE or explicit webhook in keywords
        if verification_type == "ROUTE" or any(k in ["route", "webhook"] for k in keywords):
            for r in self.routes:
                if any(k in r["route"].lower() or k in r["endpoint"].lower() for k in keywords):
                    citations.append(
                        EvidenceCitation(
                            file_path=r["file"],
                            line_start=r["line_start"],
                            line_end=r["line_end"],
                            snippet=r["snippet"],
                            symbol_name=r["endpoint"],
                            symbol_type="route"
                        )
                    )
                    matched_files.add(r["file"])

        # 3. Search test suite if verification type is TEST_SUITE
        if verification_type == "TEST_SUITE" or any(k in ["test", "pytest", "coverage"] for k in keywords):
            for t in self.tests:
                if any(k in t["test_name"].lower() for k in keywords) or len(citations) < 3:
                    citations.append(
                        EvidenceCitation(
                            file_path=t["file"],
                            line_start=t["line"],
                            line_end=t["line"] + 4,
                            snippet=t["snippet"],
                            symbol_name=t["test_name"],
                            symbol_type="test"
                        )
                    )
                    matched_files.add(t["file"])
                    if len(citations) >= 4:
                        break

        # 4. Search file contents by keyword combinations
        # If expected symbols were specified but not found, only match if strong domain keywords exist
        for rel_path, content in self.file_contents.items():
            if rel_path in matched_files:
                continue

            content_lower = content.lower()
            matching_kws = [k for k in keywords if k.lower() in content_lower and len(k) > 3]
            if len(matching_kws) >= 2:
                # Locate snippet around first matching keyword
                lines = content.splitlines()
                for i, line in enumerate(lines, start=1):
                    if any(k in line.lower() for k in matching_kws):
                        start_line = max(1, i - 2)
                        end_line = min(len(lines), i + 8)
                        snippet = "\n".join(lines[start_line - 1:end_line])
                        citations.append(
                            EvidenceCitation(
                                file_path=rel_path,
                                line_start=start_line,
                                line_end=end_line,
                                snippet=snippet[:500],
                                symbol_name=None,
                                symbol_type="code_match"
                            )
                        )
                        matched_files.add(rel_path)
                        break

            if len(citations) >= 5:
                break

        return citations

    @staticmethod
    def _is_test_file(path: str) -> bool:
        """Check if file path belongs to a test suite."""
        p = path.lower()
        return "test" in p or p.endswith("_test.py") or p.startswith("test_")

    @staticmethod
    def _extract_route_path(deco_str: str) -> Optional[str]:
        """Extract URL route string from decorator string."""
        m = re.search(r"['\"]([^'\"]+)['\"]", deco_str)
        return m.group(1) if m else None
