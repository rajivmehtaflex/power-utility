#!/usr/bin/env python3
"""Manage named Modal SSH sessions for VS Code Remote-SSH.

This wrapper handles the full lifecycle so the connection command never
changes:

    launch  Start a detached Modal sandbox and write/refresh the SSH config
    stop    Stop the running app(s) by app ID and remove the managed block
    status  Show app state, the SSH config block, and the relay endpoint

It is deliberately stdlib-only and Python 3.9 compatible: it shells out to
the authenticated `modal` CLI for all cloud operations, so it runs under the
system python3 on macOS and Linux without a project venv.

Examples:
    python3 modal_ssh_session.py launch --name g-data-linkup
    python3 modal_ssh_session.py launch --name g-train --gpu L4 --provision
    python3 modal_ssh_session.py status --name g-data-linkup
    python3 modal_ssh_session.py stop --name g-data-linkup
"""
import argparse
import glob
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

SCRIPT_DIR = Path(__file__).resolve().parent
APP_FILE = SCRIPT_DIR / "session_app.py"
SSH_CONFIG = Path.home() / ".ssh" / "config"
NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
DEFAULT_PROVISION_URL = (
    "https://gist.githubusercontent.com/rajivmehtaflex/"
    "aa9975e92049d2bfa62264eee4397fe9/raw/"
    "d1d8bc3d74231de2f2d87335c321697eec57e269/tunnel_ext.sh"
)


def die(message: str) -> None:
    print("ERROR: " + message, file=sys.stderr)
    sys.exit(1)


def info(message: str) -> None:
    print("[modal-deploy-ssh] " + message)


def validate_name(name: str) -> str:
    if not NAME_RE.match(name):
        die(
            "invalid session name {!r}: use letters, digits, dots, dashes, or "
            "underscores, starting with a letter or digit".format(name)
        )
    return name


def find_modal(explicit: Optional[str] = None) -> str:
    """Locate the modal CLI, preferring PATH but falling back to known homes."""
    if explicit:
        candidate = Path(explicit).expanduser()
        if candidate.exists() and os.access(str(candidate), os.X_OK):
            return str(candidate)
        die("modal CLI not found or not executable at {}".format(candidate))

    found = shutil.which("modal")
    if found:
        return found

    candidates = []  # type: List[str]
    candidates.extend(
        glob.glob(str(Path.home() / "Library" / "Python" / "3.*" / "bin" / "modal"))
    )
    candidates.extend(
        [
            str(Path.home() / ".local" / "bin" / "modal"),
            "/usr/local/bin/modal",
            "/opt/homebrew/bin/modal",
        ]
    )
    for candidate in candidates:
        if os.path.exists(candidate) and os.access(candidate, os.X_OK):
            return candidate

    die(
        "modal CLI not found.\n"
        "Install it with `pip install modal` or `uv tool install modal`, then "
        "authenticate with `modal setup`. If it is installed elsewhere, pass "
        "--modal /path/to/modal."
    )
    return ""  # unreachable


def run_streaming(cmd: List[str], env: Optional[Dict[str, str]] = None) -> int:
    """Run a command, stream merged output to the terminal, return exit code."""
    return run_streaming_capture(cmd, env=env)[0]


def run_streaming_capture(
    cmd: List[str], env: Optional[Dict[str, str]] = None
) -> "tuple[int, str]":
    """Run a command, stream merged output, and return (exit code, output)."""
    info("$ " + " ".join(shlex.quote(part) for part in cmd))
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
    )
    assert process.stdout is not None
    lines = []  # type: List[str]
    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()
        lines.append(line)
    return process.wait(), "".join(lines)


def capture(cmd: List[str], env: Optional[Dict[str, str]] = None) -> str:
    result = subprocess.run(
        cmd, capture_output=True, text=True, env=env
    )
    if result.returncode != 0:
        die(
            "command failed ({}): {}\n{}".format(
                result.returncode,
                " ".join(cmd),
                (result.stderr or result.stdout).strip(),
            )
        )
    return result.stdout


def app_records(modal: str) -> List[Dict[str, Any]]:
    """Return `modal app list --json` as a list of dicts.

    Field names have varied across Modal versions, so access them through
    first_value() rather than assuming one schema.
    """
    raw = capture([modal, "app", "list", "--json"])
    try:
        parsed = json.loads(raw)
    except ValueError:
        die("could not parse `modal app list --json` output: {!r}".format(raw[:200]))
    if isinstance(parsed, dict):
        for key in ("apps", "items", "data"):
            if isinstance(parsed.get(key), list):
                return parsed[key]
        return [parsed]
    return parsed


def first_value(record: Dict[str, Any], names: List[str], default: str = "") -> str:
    for name in names:
        if name in record and record[name] is not None:
            return str(record[name])
    return default


def app_id(record: Dict[str, Any]) -> str:
    return first_value(record, ["App ID", "app_id", "appId", "id"])


def app_description(record: Dict[str, Any]) -> str:
    return first_value(record, ["Description", "description", "name", "app_name"])


def app_state(record: Dict[str, Any]) -> str:
    return first_value(record, ["State", "state", "status"])


def is_stopped(record: Dict[str, Any]) -> bool:
    return "stop" in app_state(record).lower()


def matching_apps(modal: str, name: str) -> List[Dict[str, Any]]:
    return [rec for rec in app_records(modal) if app_description(rec) == name]


def config_block(name: str, host: str, port: int, identity: str) -> str:
    return (
        "# BEGIN modal-deploy-ssh: {name}\n"
        "Host {name}\n"
        "  HostName {host}\n"
        "  Port {port}\n"
        "  User root\n"
        "  IdentityFile {identity}\n"
        "  StrictHostKeyChecking no\n"
        "  UserKnownHostsFile /dev/null\n"
        "  ServerAliveInterval 30\n"
        "  ServerAliveCountMax 6\n"
        "# END modal-deploy-ssh: {name}\n"
    ).format(
        name=name, host=host, port=port, identity=identity
    )


def upsert_ssh_config(name: str, host: str, port: int, identity: str) -> None:
    """Replace the managed block for `name`, or append it if absent."""
    SSH_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    existing = SSH_CONFIG.read_text() if SSH_CONFIG.exists() else ""
    block = config_block(name, host, port, identity)
    pattern = re.compile(
        r"# BEGIN modal-deploy-ssh: {name}.*?# END modal-deploy-ssh: {name}\n?".format(
            name=re.escape(name)
        ),
        re.DOTALL,
    )
    if pattern.search(existing):
        updated = pattern.sub(block, existing, count=1)
    else:
        if existing and not existing.endswith("\n"):
            existing += "\n"
        updated = existing + ("\n" if existing.strip() else "") + block
    SSH_CONFIG.write_text(updated)
    os.chmod(str(SSH_CONFIG), 0o600)
    info("updated {} (Host {})".format(SSH_CONFIG, name))


def remove_ssh_config(name: str) -> bool:
    if not SSH_CONFIG.exists():
        return False
    existing = SSH_CONFIG.read_text()
    pattern = re.compile(
        r"\n?# BEGIN modal-deploy-ssh: {name}.*?# END modal-deploy-ssh: {name}\n?".format(
            name=re.escape(name)
        ),
        re.DOTALL,
    )
    if not pattern.search(existing):
        return False
    updated = pattern.sub("", existing)
    updated = re.sub(r"\n{3,}", "\n\n", updated)
    SSH_CONFIG.write_text(updated)
    info("removed managed Host {} block from {}".format(name, SSH_CONFIG))
    return True


def show_config(name: str) -> None:
    if not SSH_CONFIG.exists():
        print("SSH config: {} does not exist".format(SSH_CONFIG))
        return
    pattern = re.compile(
        r"# BEGIN modal-deploy-ssh: {name}.*?# END modal-deploy-ssh: {name}".format(
            name=re.escape(name)
        ),
        re.DOTALL,
    )
    match = pattern.search(SSH_CONFIG.read_text())
    if match:
        print(match.group(0))
    else:
        print("SSH config: no managed block for Host {}".format(name))


def preflight(modal: str, pubkey: Path) -> None:
    info("checking Modal authentication ...")
    # An authenticated but empty call: fails when the token is missing.
    app_records(modal)

    if not pubkey.exists():
        die(
            "SSH public key not found: {}\n"
            "Generate one with: ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -N ''".format(
                pubkey
            )
        )
    key_text = pubkey.read_text().strip()
    if not key_text.startswith(("ssh-", "ecdsa-", "sk-")):
        die("{} does not look like an SSH public key.".format(pubkey))

    identity = Path(str(pubkey)[:-4]) if str(pubkey).endswith(".pub") else pubkey
    if not identity.exists():
        print(
            "[modal-deploy-ssh] WARNING: private key {} not found next to the "
            "public key. SSH will rely on your agent or fail to authenticate.".format(
                identity
            )
        )


def verify_ssh(name: str, attempts: int = 12, delay: int = 3) -> bool:
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=20",
        name,
        "printf 'SSH_OK %s@%s\\n' \"$(whoami)\" \"$(hostname)\"",
    ]
    for attempt in range(1, attempts + 1):
        info("verifying SSH connection (attempt {}/{}) ...".format(attempt, attempts))
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and "SSH_OK" in result.stdout:
            print(result.stdout.strip())
            return True
        if attempt < attempts:
            import time

            time.sleep(delay)
    return False


def provision(name: str, url: str) -> int:
    remote_command = "cd /workspace && curl -fsSL {} | bash".format(shlex.quote(url))
    info("running provisioning script on {} ...".format(name))
    return run_streaming(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=20",
            name,
            remote_command,
        ]
    )


def command_launch(args: argparse.Namespace) -> int:
    name = validate_name(args.name)
    modal = find_modal(args.modal)
    pubkey = Path(args.pubkey).expanduser()
    preflight(modal, pubkey)

    running = [rec for rec in matching_apps(modal, name) if not is_stopped(rec)]
    if running:
        ids = ", ".join(app_id(rec) for rec in running)
        print(
            "[modal-deploy-ssh] WARNING: a non-stopped app named {!r} already "
            "exists ({}). Launching another instance will create a duplicate; "
            "run `stop --name {}` first if that is unintended.".format(
                name, ids, name
            )
        )

    env = os.environ.copy()
    env["MODAL_SSH_NAME"] = name
    env["MODAL_SSH_CPU"] = str(args.cpu)
    env["MODAL_SSH_MEMORY"] = str(args.memory)
    env["MODAL_SSH_GPU"] = args.gpu or ""
    env["MODAL_SSH_TIMEOUT"] = str(args.timeout)
    env["MODAL_SSH_VOLUME"] = args.volume or "{}-ws".format(name)
    env["MODAL_SSH_PUBKEY1"] = pubkey.read_text().strip()
    second = Path(args.pubkey2).expanduser() if args.pubkey2 else None
    env["MODAL_SSH_PUBKEY2"] = second.read_text().strip() if second and second.exists() else ""

    exit_code, output = run_streaming_capture(
        [modal, "run", "--detach", str(APP_FILE)], env=env
    )
    if exit_code != 0:
        print(
            "[modal-deploy-ssh] `modal run --detach` failed. Check `modal app "
            "list` and `modal app logs <app-id>`. GPU models with limited "
            "capacity (H100, B200) can take several minutes to allocate.",
            file=sys.stderr,
        )
        return exit_code

    match = re.search(r"SSH_READY host=(\S+) port=(\d+)", output)
    if not match:
        die(
            "the sandbox started but no SSH_READY line was found. Check the "
            "launch output above and `modal app list`; then run `status "
            "--name {}`.".format(name)
        )

    host, port = match.group(1), int(match.group(2))
    identity = Path(str(pubkey)[:-4]) if str(pubkey).endswith(".pub") else pubkey
    upsert_ssh_config(name, host, port, str(identity))

    if not verify_ssh(name):
        print(
            "[modal-deploy-ssh] SSH verification failed, though the config was "
            "written. Inspect with:\n"
            "  ssh -v {name}\n"
            "  modal app list\n"
            "The relay address may still be warming up; retry `ssh {name}` "
            "in a few seconds.".format(name=name),
            file=sys.stderr,
        )
        return 1

    print("")
    print("Session ready: {}".format(name))
    print("  SSH:      ssh {}".format(name))
    print("  Endpoint: {}:{}".format(host, port))
    print("  GPU:      {}".format(args.gpu or "none (CPU-only)"))
    print("  Stop:     python3 {} stop --name {}".format(Path(__file__).name, name))
    print("  VS Code:  Remote-SSH -> {}".format(name))

    if args.provision is not None:
        rc = provision(name, args.provision)
        if rc != 0:
            print(
                "[modal-deploy-ssh] provisioning exited with {}. The session is "
                "still up; inspect the output above.".format(rc),
                file=sys.stderr,
            )
            return rc
        print("[modal-deploy-ssh] provisioning finished successfully.")

    return 0


def command_stop(args: argparse.Namespace) -> int:
    name = validate_name(args.name)
    modal = find_modal(args.modal)

    targets = [rec for rec in matching_apps(modal, name) if not is_stopped(rec)]
    if not targets:
        info("no running app named {!r} found.".format(name))
    for record in targets:
        identifier = app_id(record)
        if not identifier:
            print(
                "[modal-deploy-ssh] WARNING: could not determine an app ID for "
                "{!r}; skipping. Stop it from the Modal dashboard.".format(
                    app_state(record)
                ),
                file=sys.stderr,
            )
            continue
        info("stopping app {} ({}) ...".format(identifier, app_state(record)))
        rc = run_streaming([modal, "app", "stop", identifier])
        if rc != 0:
            print(
                "[modal-deploy-ssh] failed to stop {} (exit {}).".format(
                    identifier, rc
                ),
                file=sys.stderr,
            )
            return rc

    if args.keep_config:
        info("keeping the managed SSH config block (--keep-config).")
    else:
        remove_ssh_config(name)

    info("done. The persistent volume was not touched.")
    return 0


def command_status(args: argparse.Namespace) -> int:
    name = validate_name(args.name)
    modal = find_modal(args.modal)

    print("Session: {}".format(name))
    print("")
    records = matching_apps(modal, name)
    if records:
        print("Modal apps:")
        for record in records:
            print(
                "  {}  state={}  tasks={}".format(
                    app_id(record) or "<unknown>",
                    app_state(record) or "<unknown>",
                    first_value(record, ["Tasks", "tasks", "task_count"], "?"),
                )
            )
    else:
        print("Modal apps: none (never launched, or aged out of `modal app list`)")
    print("")
    print("SSH config:")
    show_config(name)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="modal_ssh_session.py",
        description="Launch, verify, and stop named Modal SSH sessions.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  launch --name g-data-linkup\n"
            "  launch --name g-train --gpu L4 --provision\n"
            "  status --name g-data-linkup\n"
            "  stop --name g-data-linkup\n"
        ),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    launch = subparsers.add_parser(
        "launch",
        help="start a detached Modal sandbox and configure SSH",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    launch.add_argument("--name", required=True, help="session/app name")
    launch.add_argument("--cpu", type=float, default=8, help="CPU cores")
    launch.add_argument("--memory", type=int, default=32768, help="memory in MiB")
    launch.add_argument(
        "--gpu", default="", help='GPU spec such as "L4" or "H100:2"; empty = CPU-only'
    )
    launch.add_argument("--timeout", type=int, default=86400, help="lifetime in seconds")
    launch.add_argument(
        "--volume", default="", help="persistent volume name (default: <name>-ws)"
    )
    launch.add_argument(
        "--pubkey",
        default=str(Path.home() / ".ssh" / "id_ed25519.pub"),
        help="SSH public key to authorize",
    )
    launch.add_argument(
        "--pubkey2", default="", help="optional second SSH public key to authorize"
    )
    launch.add_argument(
        "--provision",
        nargs="?",
        const=DEFAULT_PROVISION_URL,
        default=None,
        metavar="URL",
        help=(
            "run a provisioning script on the VM after launch; with no URL, "
            "uses the maintainer script at DEFAULT_PROVISION_URL"
        ),
    )
    launch.add_argument("--modal", default=None, help="path to the modal CLI")
    launch.set_defaults(func=command_launch)

    stop = subparsers.add_parser(
        "stop", help="stop the session's app(s) and remove the managed SSH block"
    )
    stop.add_argument("--name", required=True, help="session/app name")
    stop.add_argument(
        "--keep-config",
        action="store_true",
        help="leave the managed SSH config block in place",
    )
    stop.add_argument("--modal", default=None, help="path to the modal CLI")
    stop.set_defaults(func=command_stop)

    status = subparsers.add_parser(
        "status", help="show app state and the managed SSH config block"
    )
    status.add_argument("--name", required=True, help="session/app name")
    status.add_argument("--modal", default=None, help="path to the modal CLI")
    status.set_defaults(func=command_status)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
