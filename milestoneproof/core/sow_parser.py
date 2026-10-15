"""
SOW Parser for MilestoneProof.
Parses Markdown, structured text, or JSON Statements of Work into validated
StatementOfWork and AcceptanceCriterion data models.
"""

import re
import json
from typing import Dict, Any, List, Optional
from milestoneproof.core.models import StatementOfWork, AcceptanceCriterion


class SOWParser:
    """Robust parser for Statements of Work in Markdown or text formats."""

    @classmethod
    def parse_file(cls, file_path: str) -> StatementOfWork:
        """Read and parse an SOW file from disk."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return cls.parse_content(content)

    @classmethod
    def parse_content(cls, content: str) -> StatementOfWork:
        """Parse raw SOW content string."""
        content = content.strip()
        if content.startswith("{") and content.endswith("}"):
            try:
                data = json.loads(content)
                return StatementOfWork(**data)
            except Exception:
                pass  # Fallback to markdown parsing

        return cls._parse_markdown(content)

    @classmethod
    def _parse_markdown(cls, text: str) -> StatementOfWork:
        """Extract metadata and criteria from a markdown formatted SOW."""
        title = "Milestone Deliverable SOW"
        project_name = "Client Project"
        contractor_name = "Subcontractor"
        milestone_payout = 1000.0
        currency = "USD"
        due_date = None

        # Extract title from # Heading
        title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()

        # Extract Project Name
        proj_match = re.search(r"\*?\*?(?:Project|Client)\*?\*?:\s*([^\n\r,]+)", text, re.IGNORECASE)
        if proj_match:
            project_name = proj_match.group(1).replace("*", "").strip()

        # Extract Contractor Name
        contractor_match = re.search(r"\*?\*?(?:Contractor|Subcontractor|Freelancer|Assignee)\*?\*?:\s*([^\n\r,]+)", text, re.IGNORECASE)
        if contractor_match:
            raw_cname = contractor_match.group(1).replace("*", "").strip()
            # Clean off any parenthetical title like "(Senior Backend Subcontractor)"
            contractor_name = re.sub(r"\s*\(.*?\)", "", raw_cname).strip()

        # Extract Payout Amount
        payout_match = re.search(r"\*?\*?(?:Payout|Milestone Amount|Budget|Total|Fee)\*?\*?:\s*[\$€£]?\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2})?)\s*([A-Z]{3})?", text, re.IGNORECASE)
        if payout_match:
            raw_amt = payout_match.group(1).replace(",", "")
            milestone_payout = float(raw_amt)
            if payout_match.group(2):
                currency = payout_match.group(2).upper()
        elif "$" in text:
            dollar_match = re.search(r"\$\s*([0-9]+(?:,[0-9]{3})*(?:\.[0-9]{2})?)", text)
            if dollar_match:
                milestone_payout = float(dollar_match.group(1).replace(",", ""))

        # Extract Due Date
        due_match = re.search(r"\*?\*?(?:Due Date|Deadline|Target Delivery)\*?\*?:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}|[A-Za-z]+ \d{1,2},? \d{4})", text, re.IGNORECASE)
        if due_match:
            due_date = due_match.group(1).replace("*", "").strip()

        # Extract Criteria
        criteria = cls._extract_criteria(text)
        if not criteria:
            # Fallback: create at least one generic criterion if none parsed
            criteria = [
                AcceptanceCriterion(
                    id="AC-1",
                    title="Deliverable Code Implementation",
                    description=text[:200] if len(text) > 200 else text,
                    priority="MUST",
                    weight=1.0,
                    verification_type="SEMANTIC"
                )
            ]

        return StatementOfWork(
            title=title,
            project_name=project_name,
            contractor_name=contractor_name,
            milestone_payout=milestone_payout,
            currency=currency,
            due_date=due_date,
            criteria=criteria
        )

    @classmethod
    def _extract_criteria(cls, text: str) -> List[AcceptanceCriterion]:
        """Extract individual criteria from Markdown tables or bullet lists."""
        criteria: List[AcceptanceCriterion] = []

        # 1. Try Markdown Table extraction: | ID | Title / Requirement | Priority | Verification |
        table_rows = re.findall(r"^\|([^|\n\r]+)\|([^|\n\r]+)\|([^|\n\r]+)(?:\|([^|\n\r]+))?\|?$", text, re.MULTILINE)
        if len(table_rows) > 1:
            # Skip header row and separator row
            for row in table_rows:
                col1 = row[0].replace("*", "").strip()
                col2 = row[1].strip()
                col3 = row[2].replace("*", "").strip()
                col4 = row[3].strip() if len(row) > 3 and row[3] else ""

                if "---" in col1 or "ID" in col1.upper() or "CRITERIA" in col1.upper():
                    continue

                if re.match(r"^(?:AC-?\d+|REQ-?\d+|\d+)", col1, re.IGNORECASE):
                    cid = col1
                    title = col2
                    priority = "MUST"
                    if "SHOULD" in col3.upper() or "OPTIONAL" in col3.upper():
                        priority = "SHOULD"
                    elif "COULD" in col3.upper():
                        priority = "COULD"

                    vtype = None
                    for candidate in ["AST_FUNCTION", "SECURITY_CHECK", "TEST_SUITE", "ROUTE"]:
                        if candidate in col4.upper():
                            vtype = candidate
                            break
                    if not vtype:
                        vtype = cls._infer_verification_type(title + " " + col4)

                    keywords = cls._extract_keywords(title + " " + col4)
                    symbols = cls._extract_symbols(title + " " + col4)

                    criteria.append(
                        AcceptanceCriterion(
                            id=cid,
                            title=title,
                            description=f"{title}. {col4}".strip(),
                            priority=priority,
                            weight=1.5 if priority == "MUST" else 1.0,
                            verification_type=vtype,
                            expected_symbols=symbols,
                            keywords=keywords
                        )
                    )

        if criteria:
            return criteria

        # 2. Try Header / Bullet patterns, e.g. "### AC-1: Title" or "- **AC-1: Title**: description"
        pattern = re.compile(
            r"(?:###|\*\*|- \*\*)\s*(AC-?\d+|REQ-?\d+|\d+\.)\s*[:-]?\s*([^\n\*\:]+)\*{0,2}[:\-]?\s*([^\n#]+)?",
            re.IGNORECASE
        )
        matches = pattern.findall(text)
        for m in matches:
            cid = m[0].strip().rstrip(".")
            title = m[1].strip()
            desc = m[2].strip() if m[2] else title

            priority = "MUST"
            combined_text = (title + " " + desc).lower()
            if any(k in combined_text for k in ["optional", "should", "nice to have", "could"]):
                priority = "SHOULD"

            vtype = cls._infer_verification_type(title + " " + desc)
            keywords = cls._extract_keywords(title + " " + desc)
            symbols = cls._extract_symbols(title + " " + desc)

            criteria.append(
                AcceptanceCriterion(
                    id=cid,
                    title=title,
                    description=desc,
                    priority=priority,
                    weight=1.5 if priority == "MUST" else 1.0,
                    verification_type=vtype,
                    expected_symbols=symbols,
                    keywords=keywords
                )
            )

        return criteria

    @staticmethod
    def _infer_verification_type(text: str) -> str:
        """Infer best verification mechanism from requirement description."""
        t = text.lower()
        if any(k in t for k in ["signature", "hmac", "sha256", "cryptographic"]):
            return "SECURITY_CHECK"
        if any(k in t for k in ["test", "pytest", "unit test", "coverage", "mock"]):
            return "TEST_SUITE"
        if any(k in t for k in ["get /", "post /", "put /", "delete /", "webhook"]):
            return "ROUTE"
        if any(k in t for k in ["jwt", "token", "auth", "class", "function", "method", "service"]):
            return "AST_FUNCTION"
        return "SEMANTIC"

    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """Extract key technical identifiers from requirement text."""
        words = re.findall(r"\b[A-Za-z0-9_]{3,}\b", text)
        stopwords = {
            "the", "and", "for", "with", "must", "should", "could", "have", "that", "this",
            "from", "into", "each", "both", "all", "will", "require", "required", "implement",
            "support", "using", "code", "system", "file", "make", "create", "api", "service",
            "endpoint", "handler", "provider", "module", "with"
        }
        return [w.lower() for w in words if w.lower() not in stopwords][:10]

    @staticmethod
    def _extract_symbols(text: str) -> List[str]:
        """Extract explicit function names or code symbols from backticks or identifiers."""
        backticks = re.findall(r"`([A-Za-z0-9_\.\-\/]+)`", text)
        if backticks:
            return backticks
        # Look for CamelCase or snake_case function names
        matches = re.findall(r"\b(?:[a-z]+_[a-z0-9_]+|[A-Z][a-zA-Z0-9]+(?:Service|Handler|Provider|Middleware)?)\b", text)
        return [m for m in matches if len(m) > 4][:5]
