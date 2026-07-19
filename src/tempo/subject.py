"""Stable binding between a warrant and one repository workspace."""
from __future__ import annotations

import os
from pathlib import Path, PureWindowsPath
import re
import subprocess
from urllib.parse import unquote, urlparse

from .errors import CheckerFailure
from .util import Workspace, sha256_json


def _canonical_path(path: Path) -> str:
    return os.path.normcase(os.path.normpath(str(path.resolve(strict=False))))


def _canonical_origin(workspace: Workspace, raw: str) -> str:
    """Normalize a Git origin without retaining credentials or query data."""
    value = raw.strip()
    windows = PureWindowsPath(value)
    scp = None if "://" in value else re.fullmatch(r"(?:[^@/:]+@)?([^/:]+):(.+)", value)
    if scp and not windows.drive:
        host, path = scp.groups()
        clean_path = path.replace("\\", "/").strip("/")
        if clean_path.endswith(".git"):
            clean_path = clean_path[:-4]
        return f"remote:{host.casefold()}/{clean_path}"

    parsed = urlparse(value)
    if parsed.scheme.casefold() in {"http", "https", "ssh", "git"} and parsed.hostname:
        host = parsed.hostname.casefold()
        try:
            parsed_port = parsed.port
        except ValueError as exc:
            raise CheckerFailure(
                "GIT_SUBJECT_UNREADABLE",
                "Git origin contains an invalid network port.",
            ) from exc
        port = f":{parsed_port}" if parsed_port else ""
        clean_path = parsed.path.replace("\\", "/").strip("/")
        if clean_path.endswith(".git"):
            clean_path = clean_path[:-4]
        return f"remote:{host}{port}/{clean_path}"

    if parsed.scheme.casefold() == "file":
        file_path = unquote(parsed.path).replace("\\", "/")
        host = parsed.hostname.casefold() if parsed.hostname else ""
        if host and host != "localhost":
            clean_path = file_path.strip("/")
            if clean_path.endswith(".git"):
                clean_path = clean_path[:-4]
            return f"file-unc:{host}/{clean_path}"
        if re.match(r"^/[A-Za-z]:/", file_path):
            file_path = file_path[1:]
        windows_path = PureWindowsPath(file_path)
        if windows_path.drive:
            clean_path = windows_path.as_posix().rstrip("/")
            if clean_path.casefold().endswith(".git"):
                clean_path = clean_path[:-4]
            return "file-local:" + clean_path.casefold()
        value = file_path
    local = Path(value).expanduser()
    if not local.is_absolute():
        local = workspace.root / local
    return "local:" + _canonical_path(local)


def _git_command(workspace: Workspace, *args: str, optional: bool = False) -> str | None:
    # Repository identity must not be redirected by caller-controlled Git
    # environment variables such as GIT_DIR, GIT_WORK_TREE, or injected
    # GIT_CONFIG_COUNT/KEY/VALUE entries. Preserve the host process environment
    # needed to locate and run Git, then add back only the fixed Git controls
    # used by this inspection.
    environment = {
        key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")
    }
    environment.update(
        {
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_OPTIONAL_LOCKS": "0",
            "LC_ALL": "C",
        }
    )
    try:
        completed = subprocess.run(
            ["git", "-C", str(workspace.root), *args],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            env=environment,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
        if optional:
            return None
        raise CheckerFailure(
            "GIT_SUBJECT_UNREADABLE",
            "Git repository identity could not be inspected locally.",
        ) from exc
    if completed.returncode != 0:
        if optional:
            return None
        raise CheckerFailure(
            "GIT_SUBJECT_UNREADABLE",
            f"Git repository identity command failed: {' '.join(args)}",
            details={"returncode": completed.returncode},
        )
    return completed.stdout.strip()


def _git_binding(workspace: Workspace) -> dict[str, str] | None:
    inside = _git_command(workspace, "rev-parse", "--is-inside-work-tree", optional=True)
    if inside != "true":
        return None

    commit = _git_command(workspace, "rev-parse", "--verify", "HEAD^{commit}")
    top_level = _git_command(workspace, "rev-parse", "--show-toplevel")
    git_dir = _git_command(workspace, "rev-parse", "--path-format=absolute", "--git-dir")
    common_dir = _git_command(
        workspace, "rev-parse", "--path-format=absolute", "--git-common-dir"
    )
    revision = _git_command(workspace, "symbolic-ref", "--quiet", "--short", "HEAD", optional=True)
    origin = _git_command(
        workspace, "config", "--local", "--get", "remote.origin.url", optional=True
    )
    if not commit or not top_level or not git_dir or not common_dir:
        raise CheckerFailure(
            "GIT_SUBJECT_UNREADABLE",
            "Git repository identity is incomplete or has no committed HEAD.",
        )
    return {
        "binding_version": "2",
        "workspace_root": _canonical_path(workspace.root),
        "worktree_root": _canonical_path(Path(top_level)),
        "git_dir": _canonical_path(Path(git_dir)),
        "git_common_dir": _canonical_path(Path(common_dir)),
        "origin": _canonical_origin(workspace, origin) if origin else "remote:none",
        "revision": revision or "DETACHED",
        "commit": commit.casefold(),
    }


def repository_ref(workspace: Workspace, *, allow_fixture: bool = False) -> str:
    """Bind authority to origin, revision, commit, and one exact worktree."""
    binding = _git_binding(workspace)
    if binding is not None:
        return "repository:v2:git:" + sha256_json(binding)[7:]
    if not allow_fixture:
        raise CheckerFailure(
            "GIT_SUBJECT_REQUIRED",
            "Human build authority requires a committed Git repository subject.",
        )
    fixture = {
        "binding_version": "2",
        "kind": "fixture",
        "workspace_root": _canonical_path(workspace.root),
    }
    return "repository:v2:fixture:" + sha256_json(fixture)[7:]


def validate_repository_ref(workspace: Workspace, expected: str) -> bool:
    """Accept only V2 subjects; legacy values remain historical data only."""
    if expected.startswith("repository:v2:git:"):
        return expected == repository_ref(workspace)
    if expected.startswith("repository:v2:fixture:"):
        return expected == repository_ref(workspace, allow_fixture=True)
    return False
