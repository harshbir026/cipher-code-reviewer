![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=flat-square&logo=openai)
![Streamlit](https://img.shields.io/badge/Streamlit-1.34-FF4B4B?style=flat-square&logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

# CIPHER — AI Code Review Agent

An autonomous AI-powered pipeline that clones a GitHub repository, parses Python source
files using Abstract Syntax Trees, submits code to GPT-4o-mini for analysis, and produces
confidence-rated review comments via a Streamlit dashboard.

🔗 **Live Demo:** [https://cipher-code-reviewer.streamlit.app](https://cipher-code-reviewer.streamlit.app)

## 🎥 Demo Video
[Watch the 2-minute walkthrough on Loom/YouTube](https://www.loom.com/share/0754787c1af0480ca7045993a172aab5)

---

## Architecture
┌─────────────────────────────────────────────────────────┐
│                    CIPHER Pipeline                       │
└─────────────────────────────────────────────────────────┘
│
▼
┌─────────────────┐     validates URL format
│  URL Validator  │ ──► raises ValueError on bad inputs
└────────┬────────┘
│
▼
┌─────────────────┐     depth=1, no_tags=True
│  Git Cloner     │ ──► tempfile.TemporaryDirectory (auto-cleanup)
└────────┬────────┘
│
▼
┌─────────────────┐     skips .git, venv, pycache
│  AST Parser     │ ──► FunctionDef + ClassDef nodes only
└────────┬────────┘     ast.get_source_segment()
│
▼
┌─────────────────┐     tiktoken cl100k_base encoding
│  Token Batcher  │ ──► max 6,000 tokens per batch
└────────┬────────┘
│
▼
┌─────────────────┐     secrets scrubbed before transmission
│ Secret Scrubber │ ──► regex patterns for keys/tokens
└────────┬────────┘
│
▼
┌─────────────────┐     gpt-4o-mini + Pydantic structured outputs
│  LLM Reviewer   │ ──► exponential backoff on rate limits
└────────┬────────┘     model_validator clamps confidence [0,100]
│
▼
┌─────────────────┐     confidence >= 80 → High Confidence
│ Result Bucketer │ ──► confidence <  80 → Needs Verification
└────────┬────────┘
│
▼
┌─────────────────┐     filters, metrics, export, PR comments
│  Streamlit UI   │
└─────────────────┘

---

## Features

- **AST-driven parsing** — Extracts functions and classes structurally, not with regex
- **Token-aware batching** — tiktoken ensures batches never exceed context window limits
- **Structured Outputs** — Pydantic schema enforced at API level, zero parse failures
- **Epistemic humility** — Confidence scores with `needs_verification` flag and bucketed UI
- **Secret scrubbing** — Redacts API keys and tokens before LLM transmission
- **File-level chart** — Visual breakdown of which files have the most issues
- **Scan history** — Tracks multiple repo scans within a session
- **GitHub PR integration** — Posts inline comments directly to pull requests (bonus)
- **Golden dataset evaluation** — Verified against known bugs to measure recall

---

## Setup

### Requirements
- Python 3.11+
- OpenAI API key
- GitHub Personal Access Token (for PR integration only)

### Local Installation

```bash
git clone https://github.com/harshbir026/cipher-code-reviewer
cd cipher-code-reviewer
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your API keys
streamlit run app.py
```

### Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | OpenAI API key |
| `GITHUB_TOKEN` | No | GitHub PAT for PR commenting |

---

## Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Ingestion | GitPython | Shallow clone, no API rate limits |
| Parsing | Python `ast` | Zero dependencies, handles all edge cases |
| Batching | tiktoken | Exact token counting for gpt-4o-mini |
| LLM | OpenAI gpt-4o-mini | Cost-efficient, 128k context, structured outputs |
| Schema | Pydantic v2 | Type-safe, model_validator for post-parse clamping |
| UI | Streamlit | Rapid Python-native dashboard |
| Deployment | Streamlit Cloud | Free, GitHub-integrated, no Docker needed |

---

## Project Structure

cipher-code-reviewer/
├── .streamlit/             # App configuration & theme
├── pipeline/               # Core AI logic (Modularity)
│   ├── ingestion.py        # Git cloning & repository metadata
│   ├── parser.py           # AST & Call graph extraction
│   └── reviewer.py         # LLM orchestration & structured outputs
├── tests/                  # Test suite
│   └── golden_dataset/     # Known vulnerability validation
├── utils/                  # Shared helper functions
│   ├── github_api.py       # PR commenting integration
│   ├── security.py         # Secret scrubbing logic
│   └── token_counter.py    # Tiktoken batching logic
├── submission_screenshots/ # Required assignment evidence
├── api.py                  # FastAPI headless endpoint
├── app.py                  # Streamlit dashboard entrypoint
├── requirements.txt        # Dependency definitions
├── .gitignore              # Excludes secrets/venv/caches
└── README.md               # Documentation

---

## Known Limitations

- Only analyzes `.py` files — Python only (tree-sitter excluded due to M2 build failures)
- Private repositories require token injection into the clone URL
- Very large repositories (1000+ functions) incur significant API cost and latency
- LLM analysis is non-deterministic — rerunning may produce slightly different results
- Session history resets on page refresh (no persistent storage)
- Streamlit Cloud free tier has a 60-second request timeout. 
  Repositories with more than ~8 batches (roughly 200+ functions) 
  should be analyzed locally via `streamlit run app.py` where no 
  timeout applies.
- Scaling Limitation: For demonstration stability on the Free Tier, analysis is
  currently capped at 8 batches (~200 functions). Large repository processing (>70 batches) is 
  recommended to be run locally, where session timeouts do not apply, or handled via an asynchronous
  task queue in a production deployment.

---

## How CIPHER Compares

| Feature | CIPHER | SonarQube | CodeClimate | GitHub Copilot |
|---|---|---|---|---|
| AST-based parsing | ✅ | ✅ | ✅ | ✅ |
| LLM-powered analysis | ✅ | ❌ | ❌ | ✅ |
| Confidence scoring | ✅ | ❌ | ❌ | ❌ |
| Cross-file call graph | ✅ | ✅ | ✅ | ✅ |
| CWE classification | ✅ | ✅ | ✅ | ❌ |
| False positive feedback | ✅ | ❌ | ❌ | ❌ |
| Inline diff view | ✅ | ❌ | ✅ | ✅ |
| REST API | ✅ | ✅ | ✅ | ❌ |
| Real-world impact explainer | ✅ | ❌ | ❌ | ❌ |
| Zero setup deployment | ✅ | ❌ | ❌ | ❌ |
| Open source | ✅ | ✅ | ❌ | ❌ |

## What I Would Build Next

- **Diff-aware analysis** — Only review functions changed in the latest commit, not the entire codebase
- **Persistent cache** — SQLite/Supabase to store results and avoid re-analyzing unchanged files
- **GitHub Actions integration** — Automatic PR review triggered on every push
- **Multi-language support** — tree-sitter once Apple Silicon build issues are resolved
- **Side-by-side diff view** — Show original code alongside suggested fix inline

---

## Evaluation — Golden Dataset

The agent was tested against a controlled golden dataset of Python files with known vulnerabilities:

| Function | Known Issue | Detected |
|---|---|---|
| `unsafe_deserialize` | pickle.loads on untrusted data | ✅ |
| `run_command` | shell=True command injection | ✅ |
| `divide_numbers` | Missing zero division check | ✅ |
| `fetch_all_users` | SQL injection via f-string | ✅ |

**Recall: 100% on golden dataset** (verified locally, 13.40s runtime)

---

## Data Sources Used for Testing

- psf/requests — https://github.com/psf/requests
- pallets/flask — https://github.com/pallets/flask
- tiangolo/fastapi — https://github.com/tiangolo/fastapi

---

## Academic Integrity

AI assistants (Claude, Copilot) were used to generate boilerplate code snippets. All
architectural decisions, prompt design, schema engineering, and integration logic are
original. All code in this repository has been reviewed, understood, and can be defended
in a technical viva.