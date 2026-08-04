#!/usr/bin/env python3
"""
Jules Batch Submitter for LocalMind
Sends tasks to Jules API to create async coding sessions → GitHub PRs.

Usage:
  python3 jules_submit.py               # List all available tasks
  python3 jules_submit.py --task 1      # Submit specific task by number
  python3 jules_submit.py --list        # List available tasks
  python3 jules_submit.py --status      # Check recent session status
  python3 jules_submit.py --file path   # Submit a custom prompt from a file
  python3 jules_submit.py --branch feat # Target a specific branch
"""

import json
import urllib.request
import sys
import os

# ──────────────────────────────────────────────────────────────────────────────
# Config — loads API key from .env.local or .env (never hardcode secrets)
# ──────────────────────────────────────────────────────────────────────────────

def _load_api_key():
    """Read JULES_API_KEY from environment, .env.local, or .env."""
    key = os.environ.get("JULES_API_KEY")
    if key:
        return key
    for envfile in [".env.local", ".env"]:
        # Look in the repo root, not the scripts/ directory
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(repo_root, envfile)
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("JULES_API_KEY="):
                        return line.split("=", 1)[1].strip()
    print("❌ JULES_API_KEY not found in environment, .env.local, or .env")
    sys.exit(1)

API_KEY = _load_api_key()
API_URL = "https://jules.googleapis.com/v1alpha/sessions"

# ── Repo root (one level up from scripts/) ────────────────────────────────────
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── Update this once the GitHub repo is created ──────────────────────────────
REPO_SOURCE = "sources/github/KrushnaVardhanReddy/Local-First_AI_Resume"

# Parse branch from args if provided
BRANCH = "main"
if "--branch" in sys.argv:
    idx = sys.argv.index("--branch")
    if idx + 1 < len(sys.argv):
        BRANCH = sys.argv[idx + 1]

# ──────────────────────────────────────────────────────────────────────────────
# Mandatory safety rules (prepended to every prompt)
# ──────────────────────────────────────────────────────────────────────────────

SAFETY_RULES = """
MANDATORY RULES — VIOLATION = REJECTED PR:
1. NEVER stub, mock, or TODO existing implementation code.
2. Commit message must start with "jules: " prefix.

Project: Local-First AI Resume
Tech stack: Python, RenderCV (Jinja2 + LaTeX)
""".strip()

# ──────────────────────────────────────────────────────────────────────────────
# Task definitions — populate as implementation progresses
# ──────────────────────────────────────────────────────────────────────────────

def _load_prompt(relative_path):
    """Load a prompt file lazily — returns its content or an error string."""
    full_path = os.path.join(REPO_ROOT, relative_path)
    if not os.path.exists(full_path):
        return f"ERROR: Prompt file not found: {full_path}"
    with open(full_path) as f:
        return f.read()


TASKS = {
    1: {
        "name": "Task 1 — v2 Scaffolding and WorkerPool Integration",
        "phase": "phase-1",
        "prompt": _load_prompt("docs/tasks/phase-1/task1.md"),
    },
    2: {
        "name": "Task 2 — Data Ingestion and Local File Access",
        "phase": "phase-1",
        "prompt": _load_prompt("docs/tasks/phase-1/task2.md"),
    },
    3: {
        "name": "Task 3 — Query Execution and Data Visualization",
        "phase": "phase-1",
        "prompt": _load_prompt("docs/tasks/phase-1/task3.md"),
    },
    4: {
        "name": "Task 4 — Consent-Gated AI Insights",
        "phase": "phase-1",
        "prompt": _load_prompt("docs/tasks/phase-1/task4.md"),
    },
    5: {
        "name": "Task 5 — AI-Assisted Chart Customization",
        "phase": "phase-1",
        "prompt": _load_prompt("docs/tasks/phase-1/task5_ai_chart.md"),
    },
    6: {
        "name": "Task 6 — Multi-File Auto-Joins & Diffing",
        "phase": "phase-1",
        "prompt": _load_prompt("docs/tasks/phase-1/task6_joins_diff.md"),
    },
    71: {
        "name": "Task 7.1 — BI Pivot Builder ECharts Visualization & Chart Type Selector",
        "phase": "phase-1",
        "prompt": _load_prompt("docs/tasks/phase-1/task7_1_bi_chart_selector.md"),
    },
    72: {
        "name": "Task 7.2 — BI Pivot Builder True Pivot, Filters & SQL Panel",
        "phase": "phase-1",
        "prompt": _load_prompt("docs/tasks/phase-1/task7_2_bi_pivot_filters.md"),
    },
    73: {
        "name": "Task 7.3 — BI Pivot Builder Table Polish (Totals, Pagination, Empty State)",
        "phase": "phase-1",
        "prompt": _load_prompt("docs/tasks/phase-1/task7_3_bi_table_polish.md"),
    },
    74: {
        "name": "Task 7.4 — BI Pivot Builder Component Architecture & Premium UI",
        "phase": "phase-1",
        "prompt": _load_prompt("docs/tasks/phase-1/task7_4_bi_component_architecture.md"),
    },
    9: {
        "name": "Task 9 — End-to-End Testing (Phase 1 Full Surface)",
        "phase": "phase-1",
        "prompt": _load_prompt("docs/tasks/phase-1/task9_e2e.md"),
    },
    13: {
        "name": "Task 13 — Network Graph Visualizer",
        "phase": "phase-1",
        "prompt": _load_prompt("docs/tasks/phase-1/task13_network_graph.md"),
    },
    14: {
        "name": "Task 14 — HTML Table Extractor",
        "phase": "phase-1",
        "prompt": _load_prompt("docs/tasks/phase-1/task14_html_extractor.md"),
    },
    # ── Robustness Wave — Ship with/right after MVP1 launch ───────────────────
    90: {
        "name": "CI-1 — GitHub Actions CI/CD Pipeline",
        "phase": "cross_cutting",
        "prompt": _load_prompt("docs/tasks/cross_cutting/task_ci_pipeline.md"),
    },
    91: {
        "name": "CI-2 — Content Security Policy (CSP)",
        "phase": "cross_cutting",
        "prompt": _load_prompt("docs/tasks/cross_cutting/task_csp.md"),
    },
    92: {
        "name": "CI-3 — Service Worker Cache Versioning & WASM Update Strategy",
        "phase": "cross_cutting",
        "prompt": _load_prompt("docs/tasks/cross_cutting/task_sw_versioning.md"),
    },
    93: {
        "name": "CI-4 — Worker Error Boundary & Crash Recovery",
        "phase": "cross_cutting",
        "prompt": _load_prompt("docs/tasks/cross_cutting/task_worker_error_boundary.md"),
    },
    94: {
        "name": "CI-5 — First-Run Onboarding & Empty State",
        "phase": "cross_cutting",
        "prompt": _load_prompt("docs/tasks/cross_cutting/task_onboarding.md"),
    },
    95: {
        "name": "CI-6 — Accessibility (a11y) Audit & Remediation",
        "phase": "cross_cutting",
        "prompt": _load_prompt("docs/tasks/cross_cutting/task_a11y_audit.md"),
    },
    # ── MVP2: Sessions ────────────────────────────────────────────────────────
    100: {
        "name": "Session-1 — Core Session Schema & Local Export",
        "phase": "cross_cutting",
        "prompt": _load_prompt("docs/tasks/cross_cutting/task_session1_core.md"),
    },
    103: {
        "name": "Session-3 — PDF Report Export",
        "phase": "cross_cutting",
        "prompt": _load_prompt("docs/tasks/cross_cutting/task_session3_pdf_export.md"),
    },
    104: {
        "name": "Session-4 — Session Import (Restore from .lm file)",
        "phase": "cross_cutting",
        "prompt": _load_prompt("docs/tasks/cross_cutting/task_session4_import.md"),
    },
    # ── MVP2: Docs Workspace ──────────────────────────────────────────────────
    110: {
        "name": "Docs-1 — Docs Workspace Route & Layout",
        "phase": "phase-2",
        "prompt": _load_prompt("docs/tasks/phase-2/task_docs_workspace.md"),
    },
    # ── Phase 9: LocalMind OS ─────────────────────────────────────────────────
    120: {
        "name": "Task 1 — Macro-Shell Layout & Command Palette",
        "phase": "phase-9",
        "prompt": _load_prompt("docs/tasks/phase-9/task1_macro_shell.md"),
    },
    121: {
        "name": "Task 2 — OPFS File Explorer Sidebar",
        "phase": "phase-9",
        "prompt": _load_prompt("docs/tasks/phase-9/task2_explorer.md"),
    },
    122: {
        "name": "Task 4 — Dynamic Right Inspector Panel",
        "phase": "phase-9",
        "prompt": _load_prompt("docs/tasks/phase-9/task4_inspector.md"),
    },
    123: {
        "name": "Task 5 — Workspace Migration",
        "phase": "phase-9",
        "prompt": _load_prompt("docs/tasks/phase-9/task5_migration.md"),
    },
    # ── POST-V1 DEFERRED TASKS ─────────────────────────────────────────────────
    51: {
        "name": "Set 12 Task 1 — Security / Cryptography Workspace",
        "phase": "phase-6",
        "prompt": _load_prompt("docs/tasks/phase-6/task3_crypto.md"),
    },
    52: {
        "name": "Set 12 Task 2 — Infinite Whiteboard Integration (Excalidraw)",
        "phase": "phase-8",
        "prompt": _load_prompt("docs/tasks/phase-8/task1_whiteboard.md"),
    },
    53: {
        "name": "Set 12 Task 3 — Language Learning Workspace (Polyglot)",
        "phase": "phase-6",
        "prompt": _load_prompt("docs/tasks/phase-6/task5_language.md"),
    },
    # ── Set 16: UX & Product Polish ────────────────────────────────────────────
    81: {
        "name": "UX-1 — Landing Dashboard & Workspace Routing",
        "phase": "cross_cutting",
        "prompt": _load_prompt("docs/tasks/cross_cutting/task_ux1_dashboard_routing.md"),
    },
    82: {
        "name": "UX-2 — Command Palette (Cmd+K)",
        "phase": "cross_cutting",
        "prompt": _load_prompt("docs/tasks/cross_cutting/task_ux2_command_palette.md"),
    },
    83: {
        "name": "UX-3 — Static HTML Report Export",
        "phase": "cross_cutting",
        "prompt": _load_prompt("docs/tasks/cross_cutting/task_ux3_report_export.md"),
    },
    84: {
        "name": "UX-4 — Template Gallery",
        "phase": "cross_cutting",
        "prompt": _load_prompt("docs/tasks/cross_cutting/task_ux4_template_gallery.md"),
    },
    # ── E2E Coverage Wave — All completed phases ──────────────────────────────
    200: {
        "name": "E2E Wave — Phase 2 Docs Plugins (Mermaid, Excalidraw, Doc Diff)",
        "phase": "phase-2",
        "prompt": _load_prompt("docs/tasks/phase-2/task_e2e_docs_plugins.md"),
    },
    201: {
        "name": "E2E Wave — Phase 9 Macro-Shell OS (Explorer, Command Palette, Inspector)",
        "phase": "phase-9",
        "prompt": _load_prompt("docs/tasks/phase-9/task_e2e_macro_shell.md"),
    },
    202: {
        "name": "E2E Wave — Phase 13 Universal Doc Q&A & Directory Search",
        "phase": "phase-13",
        "prompt": _load_prompt("docs/tasks/phase-13/task_e2e_universal_doc.md"),
    },
    203: {
        "name": "E2E Wave — Phase 6 & 3 Niche Plugins (Geo, Finance, Annotate, Diagrams, Pyodide, Study Notes, Summarizer)",
        "phase": "phase-6",
        "prompt": _load_prompt("docs/tasks/phase-6/task_e2e_niche_plugins.md"),
    },
    204: {
        "name": "E2E Wave — Phase 4 DevTools (Formatters, Git, Log, HAR, PCAP, PII, Mock Server)",
        "phase": "phase-4",
        "prompt": _load_prompt("docs/tasks/phase-4/task_e2e_devtools.md"),
    },
}

# ──────────────────────────────────────────────────────────────────────────────
# Submission logic
# ──────────────────────────────────────────────────────────────────────────────

def submit_task(task_num):
    if task_num not in TASKS:
        print(f"❌ Task {task_num} not found. Use --list to see available tasks.")
        sys.exit(1)

    task = TASKS[task_num]
    full_prompt = SAFETY_RULES + "\n\n---\n\n" + task["prompt"]

    payload = json.dumps({
        "prompt": full_prompt,
        "sourceContext": {
            "source": REPO_SOURCE,
            "githubRepoContext": {
                "startingBranch": BRANCH
            }
        }
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY
        },
        method="POST"
    )

    print(f"🚀 Submitting: [{task_num}] {task['name']} → branch: {BRANCH}")
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            session_id = result.get("name", "unknown").split("/")[-1]
            print(f"✅ Session created: {session_id}")
            print(f"   View at: https://jules.google.com/session/{session_id}")
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code}: {e.read().decode()}")
        sys.exit(1)


def submit_file(filepath):
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        sys.exit(1)
    with open(filepath) as f:
        prompt_content = f.read()

    full_prompt = SAFETY_RULES + "\n\n---\n\n" + prompt_content
    payload = json.dumps({
        "prompt": full_prompt,
        "sourceContext": {
            "source": REPO_SOURCE,
            "githubRepoContext": {
                "startingBranch": BRANCH
            }
        }
    }).encode()

    req = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY
        },
        method="POST"
    )

    print(f"🚀 Submitting custom prompt from: {filepath} → branch: {BRANCH}")
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            session_id = result.get("name", "unknown").split("/")[-1]
            print(f"✅ Session created: {session_id}")
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP {e.code}: {e.read().decode()}")
        sys.exit(1)


def list_tasks():
    print("\n📋 Available LocalMind Jules Tasks:\n")
    for num, task in sorted(TASKS.items()):
        print(f"  [{num:>3}] {task['name']}  ({task['phase']})")
    print()


def main():
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print(__doc__)
        sys.exit(0)

    if "--list" in args:
        list_tasks()
        sys.exit(0)

    if "--file" in args:
        idx = args.index("--file")
        if idx + 1 >= len(args):
            print("❌ Please specify a file path after --file.")
            sys.exit(1)
        submit_file(args[idx + 1])
        sys.exit(0)

    if "--task" in args:
        idx = args.index("--task")
        if idx + 1 >= len(args):
            print("❌ Please specify a task number after --task.")
            sys.exit(1)
        submit_task(int(args[idx + 1]))
        sys.exit(0)

    # Default: list tasks
    list_tasks()


if __name__ == "__main__":
    main()
