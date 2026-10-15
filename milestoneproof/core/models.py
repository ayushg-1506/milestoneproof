"""
Core data models for MilestoneProof.
Defines structured schemas for SOW specifications, deliverable code artifacts,
audit verification results, and financial settlement calculations.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class AcceptanceCriterion(BaseModel):
    """An individual verifiable requirement extracted from an SOW."""
    id: str = Field(..., description="Unique criterion identifier, e.g. AC-1")
    title: str = Field(..., description="Concise requirement title")
    description: str = Field(..., description="Detailed specification or acceptance condition")
    priority: str = Field(default="MUST", description="MUST, SHOULD, or COULD")
    weight: float = Field(default=1.0, description="Relative weighting for financial payout calculation")
    verification_type: str = Field(
        default="SEMANTIC",
        description="Type: AST_FUNCTION, ROUTE, TEST_SUITE, SECURITY_CHECK, or SEMANTIC"
    )
    expected_symbols: List[str] = Field(default_factory=list, description="Target functions, routes, or class names")
    keywords: List[str] = Field(default_factory=list, description="Keywords to match in code and comments")


class StatementOfWork(BaseModel):
    """A structured Statement of Work representing a subcontracted milestone."""
    title: str = Field(..., description="Milestone title")
    project_name: str = Field(default="Client Project", description="Parent project name")
    contractor_name: str = Field(default="Subcontractor", description="Contractor / freelance entity name")
    milestone_payout: float = Field(..., description="Agreed milestone payment amount")
    currency: str = Field(default="USD", description="Currency symbol/code, e.g. USD")
    due_date: Optional[str] = Field(default=None, description="Agreed delivery deadline")
    criteria: List[AcceptanceCriterion] = Field(default_factory=list, description="List of acceptance criteria")


class EvidenceCitation(BaseModel):
    """An empirical citation linking a requirement to actual lines of code on disk."""
    file_path: str = Field(..., description="Relative file path within deliverable repository")
    line_start: int = Field(..., description="Starting line number (1-indexed)")
    line_end: int = Field(..., description="Ending line number (1-indexed)")
    snippet: str = Field(..., description="Extract of actual source code or configuration")
    symbol_name: Optional[str] = Field(default=None, description="Function, class, or route name if applicable")
    symbol_type: Optional[str] = Field(default=None, description="function, class, route, or test")


class CriterionVerification(BaseModel):
    """The verification verdict for a single acceptance criterion."""
    criterion_id: str
    title: str
    priority: str
    status: str = Field(..., description="VERIFIED, PARTIAL, MISSING, or OUT_OF_SCOPE")
    confidence: float = Field(default=1.0, description="Confidence score between 0.0 and 1.0")
    citations: List[EvidenceCitation] = Field(default_factory=list)
    reasoning: str = Field(..., description="Clear explanation of the verdict")
    gap_description: Optional[str] = Field(default=None, description="Exact missing implementation detail if any")
    remediation_steps: Optional[str] = Field(default=None, description="Actionable checklist item for contractor")
    evaluator: str = Field(
        default="DETERMINISTIC_ENGINE",
        description="AI_MODEL, DETERMINISTIC_ENGINE, or DETERMINISTIC_FALLBACK"
    )
    evaluator_details: Optional[str] = Field(
        default=None,
        description="Model name, provider, or fallback explanation"
    )


class FinancialSettlement(BaseModel):
    """Informative milestone valuation reference based on verified deliverable weights."""
    milestone_amount: float
    currency: str = "USD"
    verified_percentage: float = Field(..., description="Percentage of weighted criteria verified (0-100)")
    recommended_release_amount: float = Field(..., description="Proportional value of verified deliverables (reference only)")
    retained_escrow_amount: float = Field(..., description="Remaining milestone value associated with unverified or gap criteria")
    deductions: List[Dict[str, Any]] = Field(default_factory=list, description="Itemized breakdown of unverified criteria and associated values")
    disclaimer: str = Field(
        default="Informative mathematical reference only. All acceptance and payment decisions remain at the sole discretion of the human reviewer.",
        description="Legal and contractual disclaimer"
    )


class AuditReport(BaseModel):
    """Complete milestone deliverable audit report."""
    sow_title: str
    contractor_name: str
    project_name: str
    scan_timestamp: str
    total_criteria: int
    verified_count: int
    partial_count: int
    missing_count: int
    compliance_score: float
    results: List[CriterionVerification]
    settlement: FinancialSettlement
    contractor_letter: str
    audit_mode: str = Field(
        default="DETERMINISTIC_ENGINE",
        description="AI_MODEL, HYBRID, or DETERMINISTIC_ENGINE"
    )
    model_name: Optional[str] = Field(
        default=None,
        description="Name of the open-weight model if AI evaluated"
    )
    disclaimer: str = Field(
        default="Advisory verification findings only. All contractual compliance determinations and financial disbursement decisions remain at the sole discretion of the human reviewer.",
        description="Legal and contractual disclaimer"
    )
