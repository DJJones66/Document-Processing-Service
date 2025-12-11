#!/usr/bin/env python3
"""
Stop the FastAPI service that was started from the local venv.

Usage:
  python service_scripts/shutdown_with_venv.py

Environment overrides:
  PIDFILE           Path to the pidfile to try first (default: data/service.pid)
  PROCESS_MATCH     Comma-separated markers to identify the process (default: uvicorn,app.main:app)
  SHUTDOWN_TIMEOUT  Seconds to wait before force-killing the process (default: 15)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable, List, Optional

import psutil

from venv_utils import REPO_ROOT

DEFAULT_PIDFILE = REPO_ROOT / "data" / "service.pid"
DEFAULT_PROCESS_MARKERS = ["uvicorn", "app.main:app", REPO_ROOT.name.lower()]
DEFAULT_SHUTDOWN_TIMEOUT = 15.0


def parse_markers(raw: Optional[str]) -> List[str]:
    """
    Split a comma/semicolon separated list of match tokens, falling back to defaults.
    """
    if raw:
        tokens = [token.strip().lower() for token in raw.replace(";", ",").split(",") if token.strip()]
        if tokens:
            return tokens
    return DEFAULT_PROCESS_MARKERS


def pidfile_from_env(default: Path = DEFAULT_PIDFILE) -> Path:
    """
    Resolve the pidfile path from environment variables.
    """
    raw = os.environ.get("PIDFILE") or os.environ.get("PID_FILE")
    return Path(raw) if raw else default


def parse_timeout(raw: Optional[str], default: float) -> float:
    """
    Convert a string timeout to float seconds with a safe default.
    """
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _is_service_process(proc: psutil.Process, markers: Iterable[str]) -> bool:
    """
    Ensure we only kill a process that looks like this service.
    """
    try:
        name = proc.name()
        cmdline_parts = proc.cmdline()
        cwd = proc.cwd()
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False

    cmdline = " ".join(cmdline_parts).lower()
    lower_name = name.lower() if name else ""
    repo_fragment = str(REPO_ROOT).lower()

    marker_match = any(marker in cmdline or marker in lower_name for marker in markers)
    cwd_match = False
    if cwd:
        try:
            cwd_path = Path(cwd).resolve()
            cwd_match = cwd_path == REPO_ROOT or REPO_ROOT in cwd_path.parents
        except (OSError, RuntimeError):
            pass
    return marker_match and (cwd_match or repo_fragment in cmdline)


def _terminate_process(proc: psutil.Process, timeout: float) -> bool:
    """
    Terminate a process (and any children) with a grace period before killing.
    """
    try:
        children = proc.children(recursive=True)
    except psutil.Error:
        children = []

    targets = [proc] + children
    for target in targets:
        try:
            target.terminate()
        except psutil.NoSuchProcess:
            continue
        except psutil.AccessDenied:
            print(f"Permission denied when terminating PID {target.pid}")
            return False

    gone, alive = psutil.wait_procs(targets, timeout=timeout)
    if alive:
        for target in alive:
            try:
                target.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        _, alive = psutil.wait_procs(alive, timeout=5)
    return not alive


def _stop_with_pidfile(pidfile: Path, markers: Iterable[str], timeout: float) -> bool:
    if not pidfile.exists():
        return False

    try:
        pid = int(pidfile.read_text().strip())
    except (OSError, ValueError) as exc:
        print(f"Could not read pidfile at {pidfile}: {exc}")
        return False

    try:
        proc = psutil.Process(pid)
    except psutil.NoSuchProcess:
        print(f"Stale pidfile at {pidfile}; process {pid} is not running.")
        pidfile.unlink(missing_ok=True)
        return False

    if not _is_service_process(proc, markers):
        print(f"Process {pid} does not look like the Document Processing Service. Aborting.")
        return False

    print(f"Stopping service via pidfile {pidfile} (pid={pid})...")
    success = _terminate_process(proc, timeout)
    if success:
        pidfile.unlink(missing_ok=True)
    return success


def _find_processes(markers: Iterable[str]) -> List[psutil.Process]:
    matches: List[psutil.Process] = []
    for proc in psutil.process_iter(["pid", "name", "cmdline", "cwd"]):
        if proc.pid == os.getpid():
            continue
        if _is_service_process(proc, markers):
            matches.append(proc)
    return matches


def _stop_by_search(markers: Iterable[str], timeout: float) -> bool:
    matches = _find_processes(markers)
    if not matches:
        return False

    print(f"Found {len(matches)} candidate process(es). Attempting shutdown...")
    stopped_any = False
    for proc in matches:
        print(f" - PID {proc.pid}: {' '.join(proc.cmdline())}")
        stopped_any = _terminate_process(proc, timeout) or stopped_any
    return stopped_any


def shutdown(pidfile: Optional[Path] = None, process_markers: Optional[Iterable[str]] = None, timeout: float = DEFAULT_SHUTDOWN_TIMEOUT) -> bool:
    """
    Attempt to stop the service using a pidfile first, falling back to a safe process search.
    """
    markers = [marker.lower() for marker in process_markers] if process_markers else DEFAULT_PROCESS_MARKERS
    pid_path = pidfile if pidfile is not None else DEFAULT_PIDFILE

    stopped = _stop_with_pidfile(pid_path, markers, timeout)
    if not stopped:
        stopped = _stop_by_search(markers, timeout)

    if stopped:
        print("Service stopped.")
    else:
        print("No matching service process found. Nothing to do.")
    return stopped


def main() -> None:
    pidfile = pidfile_from_env()
    markers = parse_markers(os.environ.get("PROCESS_MATCH"))
    timeout = parse_timeout(os.environ.get("SHUTDOWN_TIMEOUT"), DEFAULT_SHUTDOWN_TIMEOUT)

    success = shutdown(pidfile=pidfile, process_markers=markers, timeout=timeout)
    if not success:
        sys.exit(0)


if __name__ == "__main__":
    main()
