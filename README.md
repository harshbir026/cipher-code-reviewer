![Python](https://img.shields.io/badge/Python-3.11-blue?style=flat-square&logo=python)
![TypeScript](https://img.shields.io/badge/TypeScript-Next.js-black?style=flat-square&logo=typescript)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=flat-square&logo=openai)
![TreeSitter](https://img.shields.io/badge/Parsing-tree--sitter-brightgreen?style=flat-square)
![Streamlit](https://img.shields.io/badge/Streamlit-1.34-FF4B4B?style=flat-square&logo=streamlit)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

# CIPHER — Autonomous AI Code Review Agent

An autonomous AI-powered pipeline that clones a GitHub repository, parses source files
across **Python, JavaScript, and TypeScript**, submits code to GPT-4o-mini for analysis,
and produces confidence-rated, CWE-classified review comments — accessible through either
a Streamlit ops dashboard or a Next.js/TypeScript product UI on a shared FastAPI backend.

🔗 **Live Demo:** [https://cipher-code-reviewer.streamlit.app](https://cipher-code-reviewer.streamlit.app)

## 🎥 Demo Video
[Watch the 2-minute walkthrough on Loom](https://www.loom.com/share/0754787c1af0480ca7045993a172aab5)

---

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                       CIPHER Pipeline                          │
└───────────────────────────────────────────────────────────────┘
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
┌───────────────────────────────────────────────────────┐
│                 Language Dispatch                     │
│                                                         │
│   ┌─────────────────┐        ┌─────────────────────┐  │
│   │   AST Parser     │        │  Tree-sitter Parser │  │
│   │   (Python)       │        │  (JS / TS / TSX)    │  │
│   │   ast.walk()     │        │  grammar queries →  │  │
│   │   FunctionDef +  │        │  function/class/    │  │
│   │   ClassDef nodes │        │  method captures    │  │
│   └────────┬────────┘        └──────────┬───────────┘  │
│            └──────────────┬─────────────┘              │
└───────────────────────────┼────────────────────────────┘
▼
┌─────────────────┐     unified block schema, language-tagged
│  Merged Blocks   │ ──► skips .git, venv, node_modules, pycache
└────────┬────────┘
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
│  LLM Reviewer   │ ──► language-aware prompt, exponential backoff
└────────┬────────┘     model_validator clamps confidence [0,100]
│
▼
┌─────────────────┐     confidence >= 80 → High Confidence
│ Result Bucketer │ ──► confidence <  80 → Needs Verification
└────────┬────────┘
│
▼
┌───────────────────────────────────────┐
│         FastAPI REST Endpoint         │
└──────────────┬────────────┬───────────┘
▼            ▼
┌───────────────┐  ┌────────────────────┐
│ Streamlit UI   │  │  Next.js / TS UI    │
│ (ops dashboard)│  │  (product frontend) │
└───────────────┘  └────────────────────┘
```

---

## Features

- **Multi-language parsing** — Python via `ast`, JavaScript/TypeScript/TSX via tree-sitter, unified into a single language-tagged block schema
- **Two interchangeable frontends** — a Streamlit dashboard for fast internal iteration, and a Next.js/TypeScript/Tailwind UI for a production-facing experience, both calling the same FastAPI backend
- **Token-aware batching** — tiktoken ensures batches never exceed context window limits
- **Structured Outputs** — Pydantic schema enforced at API level, zero parse failures
- **Epistemic humility** — Confidence scores with `needs_verification` flag and bucketed UI
- **Secret scrubbing** — Redacts API keys and tokens before LLM transmission
- **File-level and severity charts** — Visual breakdown of where issues concentrate
- **Scan history** — Tracks multiple repo scans across sessions
- **GitHub PR integration** — Posts inline comments directly to pull requests (Streamlit)
- **Golden dataset evaluation** — 100% recall across Python and JS/TS vulnerability fixtures, covering CWE-79 (XSS) and CWE-89 (SQLi)
- **Expanded CWE detection** — 25+ keyword variants covering CWE-79, CWE-89, CWE-78, CWE-502, and 8 other categories, applied uniformly across languages

---

## Setup

### Requirements
- Python 3.11+
- Node.js 20+ (for the Next.js frontend)
- OpenAI API key
- GitHub Personal Access Token (for PR integration only)

### Backend

```bash
git clone https://github.com/harshbir026/cipher-code-reviewer
cd cipher-code-reviewer
python3.11 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # Add your API keys

# Streamlit dashboard
streamlit run app.py

# — or — FastAPI backend, for use with the Next.js frontend
uvicorn api:app --reload
```

### Next.js Frontend

```bash
cd frontend
npm install
npm run dev
```

Requires the FastAPI backend running at `http://localhost:8000` (configurable via
`frontend/.env.local` → `NEXT_PUBLIC_API_URL`).

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
| Parsing (Python) | Python `ast` | Zero dependencies, handles all edge cases |
| Parsing (JS/TS) | tree-sitter | Uniform grammar-query API across languages, incremental parsing |
| Batching | tiktoken | Exact token counting for gpt-4o-mini |
| LLM | OpenAI gpt-4o-mini | Cost-efficient, 128k context, structured outputs |
| Schema | Pydantic v2 | Type-safe, model_validator for post-parse clamping |
| Backend API | FastAPI | Typed, async-ready, shared by both frontends |
| UI (ops) | Streamlit | Rapid Python-native dashboard |
| UI (product) | Next.js 15 + TypeScript + Tailwind CSS v4 | App Router, typed API client, production-grade component architecture |
| Deployment | Streamlit Cloud | Free, GitHub-integrated, no Docker needed |

---

## Project Structure

```
cipher-code-reviewer/
├── .streamlit/              # App configuration & theme
├── pipeline/                # Core AI logic (modularity)
│   ├── ingestion.py         # Git cloning & repository metadata
│   ├── parser.py            # AST parsing + multi-language orchestrator
│   ├── ts_parser.py         # Tree-sitter parser (JS/TS/TSX)
│   ├── languages.py         # Language registry: extensions, queries, ignore dirs
│   └── reviewer.py          # LLM orchestration & structured outputs
├── frontend/                 # Next.js / TypeScript product UI
│   ├── app/                  # App Router pages, layout, global styles
│   ├── components/           # Health gauge, findings, filters, charts
│   └── lib/                  # Typed API client, CWE map, scan history
├── tests/                    # Test suite
│   ├── golden_dataset/        # Known vulnerability validation (Python + JS/TS)
│   └── test_multilang_parser.py
├── utils/                     # Shared helper functions
│   ├── github_api.py          # PR commenting integration
│   ├── security.py            # Secret scrubbing logic
│   └── token_counter.py       # Tiktoken batching logic
├── submission_screenshots/    # Required assignment evidence
├── api.py                     # FastAPI endpoint (shared by both frontends)
├── app.py                     # Streamlit dashboard entrypoint
├── requirements.txt           # Dependency definitions
├── .gitignore                 # Excludes secrets/venv/caches/node_modules
└── README.md                  # Documentation
```

---

## Known Limitations

- Language coverage is Python, JavaScript, TypeScript, and TSX — other languages
  (Go, Java, Rust, etc.) would need an additional tree-sitter grammar and query file,
  which the `languages.py` registry is structured to support
- Cross-file call graph context (`build_call_graph`) is currently Python-only;
  JS/TS blocks are analyzed without caller/callee context
- Private repositories require token injection into the clone URL
- Very large repositories (1000+ functions) incur significant API cost and latency
- LLM analysis is non-deterministic — rerunning may produce slightly different results
- Streamlit session history resets on page refresh; the Next.js frontend persists
  scan history to `localStorage` instead
- Streamlit Cloud free tier has a 60-second request timeout.
  Repositories with more than ~8 batches (roughly 200+ functions)
  should be analyzed locally via `streamlit run app.py` or `uvicorn api:app` where no
  timeout applies
- Scaling limitation: for demonstration stability on the free tier, analysis is
  currently capped at 8 batches (~200 functions). Large repository processing
  (>70 batches) is recommended to run locally, or via an asynchronous task queue
  in a production deployment

---

## How CIPHER Compares

| Feature | CIPHER | SonarQube | CodeClimate | GitHub Copilot |
|---|---|---|---|---|
| AST/grammar-based parsing | ✅ | ✅ | ✅ | ✅ |
| Multi-language support | ✅ (Python, JS, TS) | ✅ | ✅ | ✅ |
| LLM-powered analysis | ✅ | ❌ | ❌ | ✅ |
| Confidence scoring | ✅ | ❌ | ❌ | ❌ |
| Cross-file call graph | ✅ (Python) | ✅ | ✅ | ✅ |
| CWE classification | ✅ | ✅ | ✅ | ❌ |
| False positive feedback | ✅ | ❌ | ❌ | ❌ |
| Inline diff view | ✅ | ❌ | ✅ | ✅ |
| REST API | ✅ | ✅ | ✅ | ❌ |
| Real-world impact explainer | ✅ | ❌ | ❌ | ❌ |
| Zero setup deployment | ✅ | ❌ | ❌ | ❌ |
| Dual frontend (ops + product UI) | ✅ | ❌ | ❌ | ❌ |
| Open source | ✅ | ✅ | ❌ | ❌ |

## What I Would Build Next

- **Diff-aware analysis** — Only review functions changed in the latest commit, not the entire codebase
- **Persistent cache** — SQLite/Supabase to store results and avoid re-analyzing unchanged files
- **GitHub Actions integration** — Automatic PR review triggered on every push
- **Cross-language call graph** — Extend `build_call_graph` to JS/TS via tree-sitter's call-expression queries
- **Additional grammars** — Go, Java, Rust via the existing `languages.py` registry pattern
- **Prisma + persisted scan history** — Replace `localStorage` with a real database behind the Next.js frontend

---

## Evaluation — Golden Dataset

The agent was tested against controlled golden datasets with known vulnerabilities,
across both Python and JavaScript:

| Function | Language | Known Issue | CWE | Detected |
|---|---|---|---|---|
| `unsafe_deserialize` | Python | pickle.loads on untrusted data | CWE-502 | ✅ |
| `run_command` | Python | shell=True command injection | CWE-78 | ✅ |
| `divide_numbers` | Python | Missing zero division check | Bug | ✅ |
| `fetch_all_users` | Python | SQL injection via f-string | CWE-89 | ✅ |
| `get_user_by_email` | Python | SQL injection via string concatenation | CWE-89 | ✅ |
| `render_user_profile` | Python | XSS via unescaped HTML output | CWE-79 | ✅ |
| `getUserByEmail` | JavaScript | SQL injection via template literal | CWE-89 | ✅ |
| `renderComment` | JavaScript | XSS via unescaped `innerHTML` | CWE-79 | ✅ |

**Recall: 100% across all Python and JS/TS golden functions** *(verified locally and in CI)*

New in this release:
- **Multi-language parsing** — tree-sitter integration for JavaScript, TypeScript, and TSX, unified with the existing Python AST parser through a shared block schema
- **Next.js frontend** — TypeScript product UI with health gauge, filterable findings, severity/file charts, and CWE badges, calling the same FastAPI backend as Streamlit

---
## Performance Metrics

| Metric | Result |
|--------|--------|
| Recall on golden vulnerability dataset (Python + JS/TS) | **100%** |
| JSON parse failures | **0** (Pydantic v2 model_validator) |
| Avg scan time per file | **< 5s** |
| Pipeline crash rate on test repos | **0%** |
| Test suite | **40 passing** (`pytest`), CI-verified on every push |

## Data Sources Used for Testing

- kennethreitz/records — https://github.com/kennethreitz/records
- mitsuhiko/pluginbase — https://github.com/mitsuhiko/pluginbase
- realpython/codetiming — https://github.com/realpython/codetiming
- expressjs/express — https://github.com/expressjs/express (JS parsing validation)
- typestack/class-validator — https://github.com/typestack/class-validator (TS class/decorator validation)

---

## Academic Integrity

AI assistants (Claude, Copilot) were used to generate boilerplate code snippets. All
architectural decisions, prompt design, schema engineering, and integration logic are
original. All code in this repository has been reviewed, understood, and can be defended
in a technical viva.
