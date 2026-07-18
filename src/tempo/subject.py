"""Stable binding between a warrant and one repository workspace."""
from __future__ import annotations

import os

from .util import Workspace, sha256_json


def repository_ref(workspace: Workspace) -> str:
    """Bind authority to the canonical workspace location without pinning mutable HEAD."""
    root = os.path.normcase(os.path.normpath(str(workspace.root.resolve(strict=True))))
    return "repository:" + sha256_json({"workspace_root": root})[7:]


def validate_repository_ref(workspace: Workspace, expected: str) -> bool:
    """Accept historical name-only warrants, while enforcing all new hash bindings."""
    if not expected.startswith("repository:"):
        return expected == workspace.root.name
    return expected == repository_ref(workspace)
