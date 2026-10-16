# 🛡️ MilestoneProof

> **SOW & Subcontractor Deliverable Verification Engine with Open-Weight AI**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hacktoberfest 2026](https://img.shields.io/badge/Hacktoberfest-2026%20Week%202-orange.svg)](https://dev.to/challenges/hacktoberfest-week2-2026-10-12)
[![Models](https://img.shields.io/badge/Models-Llama--3.2%20%7C%20Gemma%202%20%7C%20Qwen-indigo.svg)](https://huggingface.co)

---

## The Problem: The Milestone Verification Bottleneck

In technical freelancing and agency operations, consultants, solo founders, and technical leads outsource discrete modules to subcontractors on platforms like Upwork, Contra, or direct contract agreements: an authentication flow, a payment webhook handler, or a data ingestion pipeline.

When a contractor marks a milestone ready for review, you face an immediate verification bottleneck:
1. **Inspection Overhead**: Manually checking dozens of source files against the Statement of Work (SOW), inspecting route definitions, checking test suites, and confirming that acceptance criteria are actually met consumes substantial unbilled attention.
2. **Incomplete Delivery Risk**: Subcontractors sometimes miss specific requirements—such as omitting cryptographic signature verification on webhooks, leaving rate-limiting middleware unimplemented, or writing minimal happy-path tests. If an incomplete deliverable is accepted without inspection, the hiring developer inherits technical debt and unbilled rework.
3. **Subjective Communication Friction**: Addressing unverified deliverables without concrete, file-by-file citations can feel confrontational. Clear, line-level evidence helps keep communication professional, constructive, and productive.

---

## The Solution: MilestoneProof

**MilestoneProof** is a deliverable verification application designed to run locally or deploy directly on Render. It compares a Markdown Statement of Work with a deliverable codebase, using deterministic Python Abstract Syntax Tree (AST) scanning combined with open-weight model evaluation (or a transparent deterministic rule engine).

```mermaid
graph TD
    A[Contract SOW / Markdown Spec] --> B[SOW Parser & Criteria Decomposer]
    C[Uploaded ZIP Codebase / PR Extract] --> D[Secure Tempdir Extraction & AST Scanner]
    B --> E[Verification Engine<br/>External Open-Weight Model or Deterministic Rules]
    D --> E
    E --> F[Milestone Verification Matrix<br/>VERIFIED | PARTIAL | MISSING]
    F --> G[Proportional Scope Valuation Reference<br/>Informational Completed vs. Unverified Scope]
    F --> H[Collaborative Contractor Review Letter]
    F --> I[Exportable Markdown & HTML Audit Dossier]
```

### Key Capabilities

- 📦 **Browser ZIP Codebase Upload**: Upload deliverable code as a `.zip` archive. The server safely validates against path traversal (Zip Slip), unpacks in an isolated temporary directory, and automatically cleans up after the audit.
- 🔍 **Line-Accurate Evidence Citations**: Every requirement is traced to exact source files, function signatures, route decorators, and line numbers on disk.
- 🤖 **Configurable Open-Weight Model Engine**: Connects via environment variables to any OpenAI-compatible open-weight inference provider (Groq, Hugging Face Serverless, OpenRouter) or local/remote Ollama.
- ⚙️ **Transparent Attribution**: Every finding is explicitly labeled with its evaluator (`AI_MODEL`, `DETERMINISTIC_ENGINE`, or `DETERMINISTIC_FALLBACK`). Deterministic results are never misattributed as AI findings.
- ⚖️ **Proportional Scope Valuation Reference**: Computes an informational scope completion score derived from weighted criteria.
- ⚠️ **Legal & Reviewer Advisory Disclaimer**: All findings and financial calculations are informative references. All contractual compliance determinations, milestone acceptance decisions, and financial disbursements remain under the sole discretion and authority of the human reviewer.

---

## Quickstart: Local Setup

### 1. Prerequisites
- Python 3.10+
- (Optional) Free API key from an open-weight inference provider (e.g. [Groq](https://console.groq.com), [Hugging Face](https://huggingface.co/settings/tokens), or [OpenRouter](https://openrouter.ai)). If no key is provided, MilestoneProof runs in deterministic demo mode.

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/ayushg-1506/milestoneproof.git
cd milestoneproof

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration (Optional)
Copy `.env.example` to `.env` to configure an open-weight inference provider:
```bash
cp .env.example .env
```

Example configuration for Groq (free tier):
```env
MODEL_API_BASE=https://api.groq.com/openai/v1
MODEL_API_KEY=your_groq_api_key_here
MODEL_NAME=llama-3.1-8b-instant
```

Example configuration for Hugging Face Serverless (free with HF user token):
```env
MODEL_API_BASE=https://api-inference.huggingface.co/v1
MODEL_API_KEY=your_hf_token_here
MODEL_NAME=meta-llama/Llama-3.2-3B-Instruct
```

### 4. Run the Web Application
```bash
python -m milestoneproof.app
```
Or with Gunicorn (production server):
```bash
gunicorn -w 2 -b 0.0.0.0:5000 milestoneproof.app:app
```
Open **http://localhost:5000** in your browser to inspect the application.

### 5. Run the CLI Demo
```bash
python -m milestoneproof.cli demo
```

---

## Deploying on Render (Free Python Web Service)

MilestoneProof is ready for 1-click deployment on [Render](https://render.com).

### Step-by-Step Render Deployment:
1. **Push your repository** to GitHub (private or public).
2. **Log into Render** ([render.com](https://render.com)) and click **New +** -> **Web Service**.
3. **Connect your GitHub repository**.
4. Configure the service settings:
   - **Name**: `milestoneproof`
   - **Environment**: `Python 3`
   - **Region**: Choose the closest region
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 2 -b 0.0.0.0:$PORT milestoneproof.app:app`
   - **Plan**: `Free`
5. **Set Environment Variables** (under **Environment** tab):
   - `PORT`: `10000`
   - `FLASK_ENV`: `production`
   - `MODEL_API_BASE`: (e.g. `https://api.groq.com/openai/v1` or `https://api-inference.huggingface.co/v1`)
   - `MODEL_API_KEY`: Your secret API key
   - `MODEL_NAME`: (e.g. `llama-3.1-8b-instant` or `meta-llama/Llama-3.2-3B-Instruct`)
   *(Note: If you omit `MODEL_API_KEY`, MilestoneProof deploys and runs cleanly in Deterministic Demo Mode).*
6. Click **Deploy Web Service**. Render builds the service and exposes a public HTTPS URL (e.g. `https://milestoneproof.onrender.com`).

Alternatively, use the included `render.yaml` blueprint:
1. In Render, select **Blueprints** -> **New Blueprint Instance**.
2. Connect your repo; Render will automatically detect `render.yaml` and configure the free web service with zero credential prompts.
3. The application deploys and runs immediately in Deterministic Demo Mode. You can optionally add `MODEL_API_KEY`, `MODEL_API_BASE`, and `MODEL_NAME` under the service's Environment settings at any time to enable external AI inference.

---

## Testing & Quality Verification

MilestoneProof includes 28 automated unit and integration tests covering AST scanning, SOW parsing, ZIP upload safety, model response parsing, and error fallback:

```bash
python -m unittest discover tests
```

### Test Coverage Highlights:
- **ZIP Safety & Sandboxing**: Verifies that directory traversal (`../../etc/passwd`), non-zip payloads, and oversized archives are blocked.
- **Multipart API Uploads**: Verifies browser uploads of SOW files and deliverable ZIP archives.
- **External Model Parsing**: Verifies JSON schema compliance, markdown fence stripping, and list-to-string normalization.
- **Transparent Fallback**: Verifies that API timeouts, 429 rate limits, and network errors gracefully fall back to deterministic AST rules with explicit attribution.

---

## License

MIT License. Built for the Hacktoberfest 2026 Week 2 Open-Source AI Challenge.
