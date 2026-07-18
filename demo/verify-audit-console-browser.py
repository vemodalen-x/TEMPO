#!/usr/bin/env python3
"""Run the audit-console interaction contract in a local headless browser.

The server binds to an ephemeral loopback port and exposes only the demo
directory. The page is self-contained and its in-page test exercises filters,
trace navigation, illustrative receipt examples, export readiness, and
horizontal overflow at desktop and compact responsive viewport sizes.
"""

from __future__ import annotations

import argparse
import functools
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from html.parser import HTMLParser
from typing import NoReturn


EXIT_PASS = 0
EXIT_POLICY_BLOCK = 2
EXIT_CHECKER_FAILURE = 3
EXIT_WARNING = 4

DEMO_DIR = Path(__file__).resolve().parent
PASS_MARKER = "AUDIT_CONSOLE_BROWSER_SELF_TEST_PASSED"


class BrowserExecutionError(RuntimeError):
    """A browser candidate could not execute the contract."""

    def __init__(self, details: dict[str, object]) -> None:
        super().__init__(str(details.get("error", "browser execution failed")))
        self.details = details


class SelfTestDOMParser(HTMLParser):
    """Extract browser-generated self-test state from the dumped DOM."""

    def __init__(self) -> None:
        super().__init__()
        self.body_attributes: dict[str, str | None] = {}
        self.output_text: list[str] = []
        self._inside_output = False

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        attributes = dict(attrs)
        if tag == "body":
            self.body_attributes = attributes
        if tag == "output" and attributes.get("id") == "selfTestResult":
            self._inside_output = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "output":
            self._inside_output = False

    def handle_data(self, data: str) -> None:
        if self._inside_output:
            self.output_text.append(data)


class QuietDemoHandler(SimpleHTTPRequestHandler):
    """Serve only DEMO_DIR without request logging or response caching."""

    def log_message(self, _format: str, *args: object) -> None:
        del args

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()


def emit(outcome: str, **details: object) -> None:
    print(json.dumps({"outcome": outcome, **details}, sort_keys=True))


def fail(code: int, outcome: str, **details: object) -> NoReturn:
    emit(outcome, **details)
    raise SystemExit(code)


def browser_candidates() -> list[Path]:
    candidates: list[Path] = []
    for command in ("msedge", "chrome", "chromium", "google-chrome"):
        resolved = shutil.which(command)
        if resolved:
            candidates.append(Path(resolved))

    roots = [
        os.environ.get("PROGRAMFILES"),
        os.environ.get("PROGRAMFILES(X86)"),
        os.environ.get("LOCALAPPDATA"),
    ]
    suffixes = [
        Path("Microsoft/Edge/Application/msedge.exe"),
        Path("Google/Chrome/Application/chrome.exe"),
        Path("Chromium/Application/chrome.exe"),
    ]
    for root in filter(None, roots):
        for suffix in suffixes:
            candidates.append(Path(root) / suffix)

    candidates.extend(
        [
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
            Path("/Applications/Chromium.app/Contents/MacOS/Chromium"),
        ]
    )

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate.resolve(strict=False)).casefold()
        if key not in seen and candidate.is_file():
            seen.add(key)
            unique.append(candidate)
    return unique


def select_browsers(requested: str | None) -> list[Path]:
    if requested:
        candidate = Path(requested).expanduser().resolve(strict=False)
        return [candidate] if candidate.is_file() else []
    return browser_candidates()


def run_viewport(
    browser: Path,
    url: str,
    name: str,
    width: int,
    height: int,
) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix=f"tempo-audit-{name}-") as profile:
        command = [
            str(browser),
            "--headless=new",
            "--disable-background-networking",
            "--disable-component-update",
            "--disable-default-apps",
            "--disable-extensions",
            "--disable-features=MediaRouter,OptimizationHints,Translate",
            "--disable-sync",
            "--metrics-recording-only",
            "--no-default-browser-check",
            "--no-first-run",
            "--force-device-scale-factor=1",
            f"--user-data-dir={profile}",
            f"--window-size={width},{height}",
            "--virtual-time-budget=5000",
            "--dump-dom",
            url,
        ]
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise BrowserExecutionError(
                {"viewport": name, "error": str(exc)}
            )

    if completed.returncode != 0:
        raise BrowserExecutionError(
            {
                "viewport": name,
                "browser_exit": completed.returncode,
                "stderr": completed.stderr[-1000:],
            }
        )

    parser = SelfTestDOMParser()
    parser.feed(completed.stdout)
    output_text = "".join(parser.output_text)
    viewport = parser.body_attributes.get("data-self-test-viewport", "")
    passed = (
        parser.body_attributes.get("data-self-test") == "passed"
        and PASS_MARKER in output_text
        and isinstance(viewport, str)
        and "x" in viewport
    )
    if not passed:
        failure_line = output_text.strip() or "self-test completion markers were absent"
        fail(
            EXIT_POLICY_BLOCK,
            "AUDIT_CONSOLE_BROWSER_CONTRACT_BLOCKED",
            viewport=name,
            reason=failure_line[:1000],
        )

    try:
        actual_width, actual_height = (int(value) for value in viewport.split("x", 1))
    except (TypeError, ValueError):
        fail(
            EXIT_POLICY_BLOCK,
            "AUDIT_CONSOLE_BROWSER_CONTRACT_BLOCKED",
            viewport=name,
            reason="browser returned an invalid viewport marker",
        )
    return {
        "name": name,
        "requested_width": width,
        "requested_height": height,
        "actual_width": actual_width,
        "actual_height": actual_height,
        "passed": True,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--browser",
        help="explicit path to a Chromium-family browser executable",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    browsers = select_browsers(args.browser)
    if not browsers:
        emit(
            "AUDIT_CONSOLE_BROWSER_UNAVAILABLE",
            warning="install Edge, Chrome, or Chromium, or pass --browser",
        )
        return EXIT_WARNING

    handler = functools.partial(QuietDemoHandler, directory=str(DEMO_DIR))
    try:
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    except OSError as exc:
        fail(EXIT_CHECKER_FAILURE, "AUDIT_CONSOLE_BROWSER_CHECKER_FAILURE", error=str(exc))

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/audit-console.html?selftest=1"
    browser: Path | None = None
    viewports: list[dict[str, object]] = []
    execution_errors: list[dict[str, object]] = []
    try:
        for candidate in browsers:
            try:
                candidate_viewports = [
                    run_viewport(candidate, url, "desktop", 1440, 1000),
                    run_viewport(candidate, url, "compact", 500, 844),
                ]
            except BrowserExecutionError as exc:
                execution_errors.append({"browser": str(candidate), **exc.details})
                continue
            browser = candidate
            viewports = candidate_viewports
            break
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    if browser is None:
        fail(
            EXIT_CHECKER_FAILURE,
            "AUDIT_CONSOLE_BROWSER_CHECKER_FAILURE",
            attempted=execution_errors,
        )

    emit(
        "AUDIT_CONSOLE_BROWSER_VALID",
        browser=str(browser),
        scope="demo-directory-only",
        viewports=viewports,
    )
    return EXIT_PASS


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except KeyboardInterrupt:
        fail(EXIT_CHECKER_FAILURE, "AUDIT_CONSOLE_BROWSER_CHECKER_FAILURE", error="interrupted")
    except Exception as exc:  # last-resort stable exit boundary
        fail(
            EXIT_CHECKER_FAILURE,
            "AUDIT_CONSOLE_BROWSER_CHECKER_FAILURE",
            error=type(exc).__name__,
        )
