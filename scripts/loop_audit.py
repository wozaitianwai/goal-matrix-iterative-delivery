#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


REQUIRED = {
    "stateFile": ("STATE.md", ("Last run:", "High Priority", "Watch List")),
    "loopConfig": ("LOOP.md", ("Active Loops", "Human Gates", "Budget")),
    "budgetDoc": ("loop-budget.md", ("Max tokens", "Kill Switch")),
    "runLog": ("loop-run-log.md", ("Recent Runs", "outcome")),
}

LEVELS = {
    "L1": "report-only",
    "L2": "assisted-with-verifier",
    "L3": "remote-ci-activity",
}


def has_phrases(root, rel, phrases):
    path = root / rel
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    return all(phrase in text for phrase in phrases)


def has_github_remote(root):
    config = root / ".git" / "config"
    return config.is_file() and "[remote " in config.read_text(encoding="utf-8", errors="ignore")


def unresolved_gaps(root):
    path = root / "LOOP.md"
    if not path.is_file():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    gaps = []
    for line in text.splitlines():
        if not line.startswith("| "):
            continue
        name = line.split("|", 2)[1].strip()
        if name in {"Gap", "---"}:
            continue
        if name in {"remote-ci", "maker-checker", "run-evidence", "distribution", "connectors", "governance"}:
            gaps.append(name)
    return gaps


def has_remote_run_evidence(root):
    path = root / "loop-run-log.md"
    if not path.is_file():
        return False
    text = path.read_text(encoding="utf-8", errors="ignore")
    return "remote-ci-readback" in text or "github-check-run" in text


def audit(root):
    root = Path(root).resolve()
    signals = {name: has_phrases(root, rel, phrases) for name, (rel, phrases) in REQUIRED.items()}
    signals["triage"] = "package-triage" in (root / "LOOP.md").read_text(encoding="utf-8", errors="ignore") if (root / "LOOP.md").is_file() else False
    signals["completionMatrix"] = has_phrases(
        root,
        "LOOP.md",
        ("Loop Engineering Completion Matrix", "Readiness Levels", "remote-ci-activity"),
    )
    signals["verifier"] = has_phrases(
        root,
        "adapters/codex/skills/loop-verifier/SKILL.md",
        ("independent verifier", "truth source", "reject completion"),
    ) or (root / ".codex" / "agents" / "verifier.toml").is_file()
    gaps = unresolved_gaps(root)
    signals["gapRegister"] = bool(gaps)
    signals["githubRemote"] = has_github_remote(root)
    signals["githubWorkflows"] = (root / ".github" / "workflows").is_dir()
    signals["remoteRunEvidence"] = has_remote_run_evidence(root)

    score = 10
    score += 18 if signals["stateFile"] else 0
    score += 9 if signals["loopConfig"] else 0
    score += 3 if signals["budgetDoc"] else 0
    score += 3 if signals["runLog"] else 0
    score += 5 if signals["triage"] else 0
    score += 8 if signals["completionMatrix"] else 0
    score += 14 if signals["verifier"] else 0
    score += 6 if signals["githubRemote"] else 0
    score += 6 if signals["githubWorkflows"] else 0

    if (
        score >= 78
        and signals["verifier"]
        and signals["githubRemote"]
        and signals["githubWorkflows"]
        and signals["remoteRunEvidence"]
    ):
        level = "L3"
    elif score >= 58 and signals["verifier"]:
        level = "L2"
    elif score >= 38 and signals["stateFile"]:
        level = "L1"
    else:
        level = "L0"

    recommendations = []
    blocked = []
    if not signals["verifier"]:
        recommendations.append("Add a separate verifier before L2.")
    if not signals["completionMatrix"]:
        recommendations.append("Document the completion matrix before claiming loop-engineering parity.")
    if not signals["githubRemote"]:
        blocked.append("GitHub remote is missing; G25/G26 cannot be completed.")
    if not signals["githubWorkflows"]:
        recommendations.append("Add CI/audit workflow after GitHub remote exists.")
        blocked.append("GitHub workflow evidence is missing; L3 cannot be claimed.")
    if signals["githubRemote"] and signals["githubWorkflows"] and not signals["remoteRunEvidence"]:
        blocked.append("Remote workflow run evidence is missing; L3 cannot be claimed.")
    if not all(signals[name] for name in REQUIRED):
        recommendations.append("Restore missing L1 spine files.")

    assessment = {
        "L0": "Loop spine incomplete.",
        "L1": "L1 report-only spine present.",
        "L2": "L2 assisted loop present; remote CI is still blocked.",
        "L3": "L3 remote CI loop evidence present.",
    }[level]

    return {
        "target": str(root),
        "score": min(score, 100),
        "level": level,
        "levels": LEVELS,
        "assessment": assessment,
        "signals": signals,
        "unresolvedGaps": gaps,
        "nextAction": "Add GitHub remote, push, and read back the workflow result." if not signals["githubRemote"] else "Append remote-ci-readback evidence after the workflow passes.",
        "blocked": blocked,
        "recommendations": recommendations,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = audit(args.root)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Loop readiness: {result['level']} ({result['score']}/100)")
        for item in result["recommendations"]:
            print(f"- {item}")
    return 0 if result["score"] >= 38 else 2


if __name__ == "__main__":
    raise SystemExit(main())
