#!/usr/bin/env python3
"""
里程碑门禁检查 — 对照需求文档 M1~M5 与 TC-01~TC-10。

用法:
  python scripts/check_milestone.py              # 静态检查（代码/目录是否存在）
  python scripts/check_milestone.py --from-pytest # 结合最近一次 pytest 结果摘要
  python scripts/check_milestone.py --milestone M1
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


@dataclass
class Milestone:
    id: str
    name: str
    deliverables: list[str]
    reqs: list[str]
    test_markers: list[str]
    tc_ids: list[str]
    code_checks: list[str] = field(default_factory=list)


MILESTONES: list[Milestone] = [
    Milestone(
        id="M1",
        name="Agent 核心",
        deliverables=["ReAct 图", "read_file", "流式 SSE"],
        reqs=["REQ-004", "REQ-005", "REQ-010", "REQ-020"],
        test_markers=["milestone_m1"],
        tc_ids=["TC-01", "TC-02"],
        code_checks=[
            "code/app/func/graph/nodes/llm_call.py",
            "code/app/func/graph/nodes/tool_node.py",
            "code/app/func/graph/edges/should_continue.py",
            "code/app/func/graph/tools/file_tool.py",
        ],
    ),
    Milestone(
        id="M2",
        name="Workspace",
        deliverables=["模板", "ContextAssembler"],
        reqs=["REQ-007", "REQ-008"],
        test_markers=["milestone_m2"],
        tc_ids=["TC-05"],
        code_checks=[
            "code/app/func/graph/workspace/manager.py",
            "code/app/func/graph/workspace/context_assembler.py",
            "workspace/default/SOUL.md",
        ],
    ),
    Milestone(
        id="M3",
        name="Tools 与 KB",
        deliverables=["search_knowledge", "Skills", "exec", "web 工具"],
        reqs=["REQ-009", "REQ-015", "REQ-019", "REQ-023", "REQ-024"],
        test_markers=["milestone_m3"],
        tc_ids=["TC-03", "TC-08", "TC-09", "TC-10"],
        code_checks=[
            "code/app/func/graph/tools/web_tool.py",
            "code/app/func/graph/tools/tool_registry.py",
            "workspace/default/skills/kb-qa/SKILL.md",
        ],
    ),
    Milestone(
        id="M4",
        name="Memory",
        deliverables=["memory 工具", "stop"],
        reqs=["REQ-012", "REQ-013", "REQ-014", "REQ-002"],
        test_markers=["milestone_m4"],
        tc_ids=["TC-06", "TC-07"],
        code_checks=[
            "code/app/func/graph/tools/memory_tool.py",
        ],
    ),
    Milestone(
        id="M5",
        name="验收",
        deliverables=["全部 TC 通过", "Postman/文档"],
        reqs=["全部 REQ"],
        test_markers=["milestone_m5"],
        tc_ids=["TC-04"],
        code_checks=[],
    ),
]


def check_files_exist(paths: list[str]) -> tuple[int, int]:
    ok = 0
    for rel in paths:
        if (REPO_ROOT / rel).exists():
            ok += 1
    return ok, len(paths)


def run_pytest_markers(markers: list[str]) -> dict[str, str]:
    """返回 marker -> passed|failed|skipped"""
    results: dict[str, str] = {}
    for marker in markers:
        cmd = [
            sys.executable,
            "-m",
            "pytest",
            "tests/",
            "-m",
            marker,
            "-q",
            "--tb=no",
        ]
        proc = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            results[marker] = "passed"
        else:
            # 区分无测试 vs 失败
            if "no tests ran" in proc.stdout.lower() or proc.returncode == 5:
                results[marker] = "no_tests"
            else:
                results[marker] = "failed"
    return results


def print_report(focus: str | None = None) -> int:
    print("=" * 60)
    print(" NewHuman MVP 里程碑检查")
    print("=" * 60)

    all_markers = []
    for m in MILESTONES:
        all_markers.extend(m.test_markers)

    pytest_results = run_pytest_markers(all_markers) if focus else {}

    current: str | None = None
    for m in MILESTONES:
        if focus and m.id != focus:
            continue

        file_ok, file_total = check_files_exist(m.code_checks)
        test_status = pytest_results.get(m.test_markers[0], "—") if m.test_markers else "—"

        if file_total == 0:
            file_status = "n/a"
        elif file_ok == file_total:
            file_status = f"{file_ok}/{file_total} OK"
        else:
            file_status = f"{file_ok}/{file_total} MISSING"

        done = (
            file_total > 0
            and file_ok == file_total
            and test_status == "passed"
        ) or (file_total == 0 and test_status == "passed")

        status_icon = "[OK]" if done else "[  ]"
        if not done and current is None:
            current = m.id

        print(f"\n{status_icon} {m.id} — {m.name}")
        print(f"   交付: {', '.join(m.deliverables)}")
        print(f"   需求: {', '.join(m.reqs)}")
        print(f"   用例: {', '.join(m.tc_ids)}")
        print(f"   代码文件: {file_status}")
        if test_status != "—":
            print(f"   自动化测试: {test_status}")

    print("\n" + "-" * 60)
    if current:
        print(f"建议当前迭代目标: {current}")
        print(f"  1. 阅读 docs/1_设计文档/MVP设计文档_v1.0.md §6.4")
        print(f"  2. 实现 {current} 交付物")
        print(f"  3. .\\scripts\\run_tests.ps1 -Milestone {current}")
    else:
        print("All milestones complete.")

    print("-" * 60)
    return 0 if current is None else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="MVP 里程碑门禁")
    parser.add_argument("--milestone", choices=["M1", "M2", "M3", "M4", "M5"])
    parser.add_argument("--from-pytest", action="store_true", help="pytest 运行后打印摘要")
    parser.add_argument("--failed", action="store_true", help="标记为失败上下文")
    parser.add_argument("--json", action="store_true", help="JSON 输出（供 CI）")
    args = parser.parse_args()

    if args.json:
        data = []
        for m in MILESTONES:
            ok, total = check_files_exist(m.code_checks)
            data.append(
                {
                    "id": m.id,
                    "files_ok": ok,
                    "files_total": total,
                    "tc_ids": m.tc_ids,
                }
            )
        print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0

    if args.from_pytest:
        print("\n--- 里程碑摘要 ---")
    return print_report(focus=args.milestone)


if __name__ == "__main__":
    sys.exit(main())
