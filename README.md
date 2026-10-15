# 🛡️ MilestoneProof

> **Edge-Native Statement of Work (SOW) & Subcontractor Deliverable Verification Engine with Open-Weight AI**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hacktoberfest 2026](https://img.shields.io/badge/Hacktoberfest-2026%20Week%202-orange.svg)](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)
[![Local Models](https://img.shields.io/badge/Model-Phi--3%20%7C%20Gemma%202-indigo.svg)](https://ollama.ai)

---

## The Problem: The Milestone Verification Dilemma

In the modern freelance and agency economy, solopreneurs, boutique dev studios, and fractional technical leaders outsource discrete modules to subcontractors on platforms like Upwork, Contra, or direct contracts.

A contractor submits an invoice claiming:
> *"Milestone 2 complete! Implemented auth, Stripe webhooks, and rate limiting. Please release the $2,500 milestone."*

The hiring project lead faces a tedious and sensitive dilemma:
1. **The Verification Drain**: Manually inspecting dozens of source code files, route definitions, and test fixtures against the contractual Statement of Work (SOW) requires extensive manual diffing.
2. **The Incomplete Deliverable Risk**: Deliverables can easily miss key requirements—such as omitted cryptographic signature verification, skipped rate limiting, or stubbed mock tests. If approved hastily, the agency must fix the gaps or absorb client churn.
3. **The Interpersonal Friction**: Addressing unverified deliverables without clear, line-level evidence can provoke disputes and strain contractor relationships.

Existing tools fail this workflow:
- **Receipt sorters** only categorize past business expenses into CSVs.
- **Contract scanners** only check for clauses before signing.
- **Generic code linters** focus on syntax and formatting, unaware of contractual milestone acceptance criteria.

---

## The Solution: MilestoneProof

**MilestoneProof** is an edge-native deliverable auditor that runs locally on your machine. It pairs deterministic Python AST parsing with local open-weight AI (such as Phi-3 or Gemma via Ollama) to trace deliverable code against contractual acceptance criteria.

```mermaid
graph TD
    A[Contract SOW / Markdown Spec] --> B[SOW Parser & Criteria Decomposer]
    C[Deliverable Repository / PR] --> D[Deterministic AST & File Manifest Scanner]
    B --> E[Compliance Engine<br/>Local Model via Ollama or AST Rule Fallback]
    D --> E
    E --> F[Milestone Verification Matrix<br/>VERIFIED | PARTIAL | MISSING]
    F --> G[Proportional Scope Valuation<br/>Informational Completed vs. Unverified Scope]
    F --> H[Collaborative Contractor Review Letter]
    F --> I[Exportable Markdown & HTML Audit Dossier]
```

### Key Capabilities

- 🔍 **Line-Accurate Evidence Citations**: Every requirement is traced to exact source files, function signatures, route decorators, and line numbers on disk.
- ⚖️ **Proportional Scope Valuation (Reference Only)**: Computes proportional financial scope completed and itemizes unverified scope value for reviewer reference. Payment and contractual decisions remain entirely with the human reviewer.
- ✉️ **Collaborative Contractor Feedback Draft**: Synthesizes a constructive review letter acknowledging verified deliverables and outlining specific checklist items needed to complete remaining requirements.
- 🔒 **100% On-Device Privacy**: Deliverable code and contract terms are analyzed locally without transmitting proprietary code to multi-tenant cloud APIs. Zero cloud token bills.

---

## Why Open-Source & Local Processing Matters

1. **Client NDAs & Code Privacy**: Sharing unreleased client source code and proprietary milestone specifications with third-party cloud APIs can raise confidentiality and compliance issues. Local processing on developer workstations protects privacy.
2. **Zero Marginal Inference Cost**: Auditing milestones and PR iterations locally incurs zero ongoing cloud token fees.
3. **Deterministic Verification**: Deterministic AST extractors ensure that every cited symbol and line number exists on disk.

---

## Quickstart & Installation

### 1. Prerequisites
- Python 3.10+
- (Optional) [Ollama](https://ollama.ai/) with `phi3:latest` or `gemma:2b` for semantic reasoning.
  > **Note**: When local LLM inference is unavailable or constrained by host RAM, MilestoneProof routes automatically to its deterministic AST/regex rule engine (which operates via rule-based inspection rather than AI inference).

### 2. Setup
```bash
# Clone the repository
git clone https://github.com/ayushg-1506/milestoneproof.git
cd milestoneproof

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Built-In Synthetic Demo Audit
```bash
python -m milestoneproof.cli demo
```

### 4. Audit Your Own Deliverable
```bash
python -m milestoneproof.cli audit \
  --sow ./examples/sample_sow_auth_payment.md \
  --deliverable ./examples/sample_deliverable \
  --output ./audit_report.md
```

### 5. Launch Interactive Web Dashboard
```bash
python -m milestoneproof.cli serve --port 5000
```
Open [http://localhost:5000](http://localhost:5000) in your browser to inspect the interactive dashboard, view AST citations, review proportional reference calculations, and export findings.

---

## Testing & Verification

MilestoneProof includes an automated test suite with 15 tests:

```bash
python -m unittest discover tests
```

Tests verify:
- Markdown table and bullet SOW criteria parsing.
- Deterministic AST function, route, and test suite extraction.
- Edge-case security detection (e.g., catching missing Stripe webhook HMAC signatures).
- Proportional scope reference calculations and capping logic.
- End-to-end audit pipelines and Flask REST API endpoints.

---

## Plausible Commercialization

MilestoneProof is architected as an edge-native micro-SaaS:
- **Solo Freelance / Consultant Tier**: $19/month or $49 one-time desktop license.
- **Agency Studio Tier**: $79/month with multi-repo support and team templates.
- **Value Proposition**: Catching unverified or missing deliverables before milestone sign-off prevents unpaid rework and streamlines code review.

---

## License

MIT License. Open-source for Hacktoberfest 2026 Week 2: Side Hustle.
