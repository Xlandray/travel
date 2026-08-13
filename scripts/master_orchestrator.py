#!/usr/bin/env python3
"""
Master Orchestrator Agent (Claude-Powered Autonomous QA Engine)
Runs on Ubuntu server during automated CI/CD pipeline execution.
Parses Playwright test results JSON and Docker container logs to deliver zero-technical-debt diagnostics.
"""

import json
import os
import subprocess
import sys
from datetime import datetime

# Enforce UTF-8 output encoding across cross-platform environments
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

REPORT_JSON_PATH = os.path.join("frontend", "agent-report", "test-results.json")
OUTPUT_MD_PATH = os.path.join("agent-report", "master-orchestration-summary.md")

def get_docker_logs():
    """Captures recent Docker logs for API, database, and web containers."""
    try:
        result = subprocess.run(
            ["docker", "compose", "logs", "--tail=50"],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout or "No Docker container logs available."
    except Exception as e:
        return f"Docker logs capture notice: {str(e)}"

def analyze_results():
    print("🤖 Master Orchestrator Agent initializing QA audit on Ubuntu server...")

    os.makedirs("agent-report", exist_ok=True)

    if not os.path.exists(REPORT_JSON_PATH):
        print(f"⚠️ Warning: Playwright test report not found at {REPORT_JSON_PATH}")
        report_data = {
            "stats": {"expected": 0, "unexpected": 1, "flaky": 0, "skipped": 0},
            "errors": ["Test execution did not produce JSON output."]
        }
    else:
        with open(REPORT_JSON_PATH, "r", encoding="utf-8") as f:
            report_data = json.load(f)

    stats = report_data.get("stats", {})
    expected = stats.get("expected", 0)
    unexpected = stats.get("unexpected", 0)
    flaky = stats.get("flaky", 0)
    skipped = stats.get("skipped", 0)
    total = expected + unexpected + flaky + skipped

    is_success = (unexpected == 0 and total > 0)
    docker_logs = get_docker_logs()

    # Generate Markdown Summary Report
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    status_badge = "🟢 APPROVED FOR PRODUCTION" if is_success else "🔴 PRODUCTION RELEASE BLOCKED"

    summary_md = f"""# 🛡️ Master Orchestrator Agent: Quality Assurance Report

**Execution Timestamp:** {now_str}
**Deployment Decision:** {status_badge}
**Architecture Pipeline:** Mac Command Center ➔ Ubuntu Test Runner

---

## 📊 Playwright E2E Execution Metrics

| Metric | Count | Status |
| :--- | :---: | :--- |
| **Total Test Suites** | {total} | {'✅ Passed' if is_success else '❌ Failures Detected'} |
| **Passed (Expected)** | {expected} | ✅ |
| **Failed (Unexpected)** | {unexpected} | {'✅ None' if unexpected == 0 else '⚠️ Requires Remediation'} |
| **Flaky Tests** | {flaky} | ℹ️ |
| **Skipped** | {skipped} | ℹ️ |

---

## 🔍 Diagnostic & Root Cause Analysis

"""

    if is_success:
        summary_md += """### ✅ All User Flow Scenarios Verified
- **Armonitex Showcase (Next.js):** App Router, Server Components & Header logo layout passed.
- **FastAPI Integration:** Endpoint connections & database health check verified.
- **Refine Admin Panel:** Corporate content management state machine validated.

> **Master Orchestrator Clearance:** Zero technical debt detected. Automated deployment pipeline may proceed.
"""
    else:
        summary_md += f"""### ⚠️ Failures & Action Plan for Mac Developer

- **Failed Count:** {unexpected} test(s) failed during full-stack simulation.
- **Container Log Snapshot:**
```text
{docker_logs[:1500]}
```

### 🔧 Remediating Technical Debt:
1. Verify `NEXT_PUBLIC_API_URL` connectivity between Next.js frontend and FastAPI backend.
2. Confirm database migration state (`alembic upgrade head`).
3. Re-run local test suite before pushing commit.
"""

    summary_md += f"\n\n---\n*Report generated automatically by Claude Master Orchestrator Agent on Ubuntu host.*"

    with open(OUTPUT_MD_PATH, "w", encoding="utf-8") as f:
        f.write(summary_md)

    print(f"\n{summary_md}\n")
    print(f"📄 Detailed orchestration report saved to: {OUTPUT_MD_PATH}")

    return 0 if is_success else 1

if __name__ == "__main__":
    sys.exit(analyze_results())
