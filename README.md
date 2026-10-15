# 🛡️ MilestoneProof

> **Edge-Native Statement of Work (SOW) & Subcontractor Deliverable Verification Engine with Open-Weight AI**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hacktoberfest 2026](https://img.shields.io/badge/Hacktoberfest-2026%20Week%202-orange.svg)](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)
[![Local Gemma & Phi-3](https://img.shields.io/badge/Model-Gemma%202%20%7C%20Phi--3-indigo.svg)](https://ai.google.dev/gemma)

---

## The Problem: The $2,500 Subcontractor Blindspot

In the modern freelance and agency economy, solopreneurs, boutique dev studios, and fractional technical leaders outsource discrete milestones to subcontractors on platforms like Upwork, Contra, or direct contracts.

A contractor submits an invoice claiming:
> *"Milestone 2 complete! Implemented auth, Stripe webhooks, and rate limiting. Please release the $2,500."*

The hiring agency lead is stuck in an expensive dilemma:
1. **The Verification Drain**: Manually inspecting dozens of source code files, route definitions, and test fixtures against the contractual Statement of Work (SOW) takes 2 to 4 hours of unbilled management overhead.
2. **The "Silent Incomplete" Failure**: Subcontractors routinely miss 20% to 35% of requirements—omitting cryptographic signature verification, skipping rate limiting, or stubbing out mock tests. If approved hastily, the agency must fix the bugs for free or absorb client churn.
3. **The Discrepancy Hostility Trap**: Rejecting a milestone payment without concrete, line-accurate evidence provokes emotional arguments, platform disputes, and damaged working relationships.

Existing tools fail this workflow:
- **Receipt sorters** only categorize past business expenses into CSVs.
- **Contract scanners** only check for indemnification clauses before signing.
- **Generic code reviewers** nag about style and syntax, completely unaware of contractual milestone obligations.

---

## The Solution: MilestoneProof

**MilestoneProof** is an edge-native deliverable auditor that runs 100% on your laptop. It pairs deterministic Python AST parsing with local open-weight AI (Google Gemma 2 / Phi-3 via Ollama) to verify deliverable code against contractual acceptance criteria.

```mermaid
graph TD
    A[Contract SOW / Markdown Spec] --> B[SOW Parser & Criteria Decomposer]
    C[Deliverable Repository / PR] --> D[Deterministic AST & File Manifest Scanner]
    B --> E[Semantic Compliance Engine<br/>Local Gemma 2 / Phi-3 via Ollama]
    D --> E
    E --> F[Milestone Verification Matrix<br/>VERIFIED | PARTIAL | MISSING]
    F --> G[Deterministic Settlement Calculator<br/>Immediate Release vs. Retained Escrow]
    F --> H[Diplomatic Contractor Review Letter]
    F --> I[Exportable Markdown & HTML Audit Dossier]
```

### Key Capabilities

- 🔍 **Line-Accurate Evidence Citations**: Every requirement is traced to exact source files, function signatures, route decorators, and line numbers on disk. Zero hallucinated file names.
- ⚖️ **Contractual Payout & Escrow Calculator**: Automatically calculates a safe, defensible immediate release sum (e.g., $1,500) and itemizes exact retained escrow sums (e.g., $1,000) for missing or partial deliverables.
- ✉️ **Diplomatic Contractor Feedback Draft**: Automatically synthesizes a constructive, collaborative review letter that thanks the contractor, highlights verified deliverables, and provides a clear checklist to unblock held funds without interpersonal conflict.
- 🔒 **100% On-Device Privacy**: Proprietary client source code and confidential freelance agreements never leave your machine. Zero cloud token bills.

---

## Why Open Innovation Matters

1. **Strict Client NDAs & IP Protection**: Uploading unreleased client source code and proprietary statements of work to multi-tenant public AI APIs violates client Master Services Agreements (MSAs). Local open-weight models running on the user's laptop are the *only* legally compliant solution for independent agencies.
2. **Zero Marginal Inference Cost**: Auditing 10 milestones and 50 PR iterations per month costs $0 in cloud token bills.
3. **Deterministic Grounding**: By binding Google Gemma 2 to deterministic AST extractors, MilestoneProof guarantees that every cited code snippet exists on disk.

---

## Quickstart & Installation

### 1. Prerequisites
- Python 3.10+
- (Optional) [Ollama](https://ollama.ai/) with `gemma:2b` or `phi3:latest` for enhanced semantic reasoning. MilestoneProof automatically falls back to its deterministic semantic engine if Ollama is offline.

### 2. Setup
```bash
# Clone the repository
git clone https://github.com/ayushg-1506/milestoneproof.git
cd milestoneproof

# Install dependencies
pip install -r requirements.txt
```

### 3. Run Built-In Demo Audit
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
Open [http://localhost:5000](http://localhost:5000) in your browser to interact with the glassmorphism dashboard, review live AST citations, adjust payouts, and copy ready-to-send contractor letters.

---

## Testing & Verification

MilestoneProof includes a comprehensive 15-test unit and integration test suite:

```bash
python -m unittest discover tests
```

Tests verify:
- Markdown table and bullet SOW criteria parsing.
- Deterministic AST function, route, and test suite extraction.
- Edge-case security detection (e.g., catching missing Stripe webhook HMAC signatures).
- Escrow retention calculations and safety payout caps.
- End-to-end audit pipelines and Flask REST API endpoints.

---

## Commercial Viability & Monetization Model

MilestoneProof is designed as an edge-native micro-SaaS:
- **Solo Freelance / Consultant Tier**: $19/month or $49 one-time perpetual desktop license.
- **Agency Studio Tier**: $79/month with team workspace, Git PR webhook hooks, and customizable SOW templates.
- **Value Proposition**: Catching just one incomplete $2,500 milestone prevents unbilled rework and saves 3+ hours of manual review per project.

---

## License

MIT License. Open-source for Hacktoberfest 2026 Week 2: Side Hustle.
