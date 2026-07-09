import shlex
from pathlib import Path


def normalized_verification(value):
    return str(value).strip().strip("`") if value else ""


def verification_requires_shell(value):
    text = normalized_verification(value)
    return any(operator in text for operator in ("&&", "||", ";", "|"))


def verification_is_metadata_status(value):
    try:
        parts = shlex.split(str(value).strip().strip("`"))
    except ValueError:
        return False
    if any(part in {"&&", "||", ";", "|"} for part in parts):
        return False
    for index, arg in enumerate(parts[:-1]):
        if Path(arg).name != "goal_guard.py" or parts[index + 1] != "status":
            continue
        prefix = parts[:index]
        if prefix and Path(prefix[-1]).name not in {"python", "python3"}:
            return False
        tail = parts[index + 2:]
        while tail:
            if tail[0] == "--root" and len(tail) >= 2:
                tail = tail[2:]
                continue
            if tail[0].startswith("--root="):
                tail = tail[1:]
                continue
            return False
        return True
    return False


def active_goal_iteration_commands(root):
    verify = ["python3", "core/goal_guard.py", "active-verify", "--root", str(root)]
    checkpoint = ["python3", "core/goal_guard.py", "checkpoint", "--root", str(root), "--", *verify]
    return {"verify": shlex.join(verify), "checkpoint": shlex.join(checkpoint)}


def is_metadata_only_verification(verify_command):
    for index, arg in enumerate(verify_command[:-1]):
        if Path(str(arg)).name == "goal_guard.py" and verify_command[index + 1] == "status":
            return True
    return False


def resolve_guard_verify_command(root, verify_command):
    resolved = list(verify_command)
    guard_path = Path(__file__).resolve().with_name("goal_guard.py")
    for index, arg in enumerate(resolved):
        path = Path(str(arg))
        if path.name == "goal_guard.py" and not path.is_absolute() and not (Path(root) / path).is_file():
            resolved[index] = str(guard_path)
    return resolved


def write_checkpoint_evidence(root, goal_id, active_goal, verify_command, result):
    path = Path(root) / ".goal-matrix" / "evidence" / f"{goal_id}.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f"Goal: {active_goal}",
                f"Command: {shlex.join(map(str, verify_command))}",
                f"Exit code: {result.returncode}",
                "Stdout:",
                result.stdout.rstrip(),
                "Stderr:",
                result.stderr.rstrip(),
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path
