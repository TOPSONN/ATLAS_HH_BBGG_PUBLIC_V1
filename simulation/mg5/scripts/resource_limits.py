"""Local generation safeguards independent of MG5 physics and portable validation.

Checks disk usage every five seconds. Stop/timeout terminates only the new
generator process group, preserves its directory and records incomplete status.
"""
from __future__ import annotations

import atexit
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time


class LimitStopped(RuntimeError):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


class RunLimits:
    @staticmethod
    def preflight(output, jobs):
        cpus = len(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else (os.cpu_count() or 1)
        if not 1 <= jobs <= cpus:
            raise ValueError(f"jobs must be between 1 and {cpus} available logical CPUs")
        ancestor = Path(output)
        while not ancestor.exists():
            ancestor = ancestor.parent
        disk = shutil.disk_usage(ancestor)
        if disk.free < 1024 ** 3:
            raise ValueError("less than 1 GiB free on output filesystem")
        memory = {}
        if Path("/proc/meminfo").is_file():
            for line in Path("/proc/meminfo").read_text().splitlines():
                key, value = line.split(":", 1)
                if key in {"MemAvailable", "MemTotal"}:
                    memory[key] = int(value.split()[0]) * 1024
        if memory.get("MemAvailable", 1024 ** 3) < 512 * 1024 ** 2:
            raise ValueError("less than 512 MiB available RAM")
        return {"available_logical_cpus": cpus, "jobs": jobs, "disk_free_bytes": disk.free,
                "ram_total_bytes": memory.get("MemTotal", "UNKNOWN"),
                "ram_available_bytes": memory.get("MemAvailable", "UNKNOWN"),
                "runtime_estimate_seconds": "UNKNOWN", "output_size_estimate_bytes": "UNKNOWN"}

    def __init__(self, output, max_hours, max_disk_gb, resources):
        self.output = Path(output)
        self.max_seconds = max_hours * 3600
        self.max_bytes = max_disk_gb * 1024 ** 3
        self.started = time.monotonic()
        self.last_measure = -10.0
        self.stop_requested = False
        self.completed = False
        self.closed = False
        self.state = {"status": "RUNNING", "publication": "LOCAL_ONLY", "resources": resources,
                      "max_hours": max_hours, "max_disk_gb": max_disk_gb,
                      "disk_budget_units": "GiB (1024^3 bytes)", "pid": os.getpid(),
                      "partial_events_are_accepted": False}
        self.previous_handlers = {s: signal.signal(s, self.request_stop) for s in (signal.SIGINT, signal.SIGTERM)}
        atexit.register(self.close)
        self.write_status()

    def request_stop(self, signum, frame):
        self.stop_requested = True

    def write_status(self):
        self.state["updated_utc"] = datetime.now(timezone.utc).isoformat()
        self.state["elapsed_seconds"] = time.monotonic() - self.started
        temporary = self.output / "run_status.json.tmp"
        temporary.write_text(json.dumps(self.state, indent=2, sort_keys=True) + "\n")
        temporary.replace(self.output / "run_status.json")

    def stop(self, status, message):
        self.state.update(status=status, failure=message)
        self.write_status()
        raise LimitStopped(status, message)

    def check(self, force=False):
        elapsed = time.monotonic() - self.started
        if self.stop_requested or (self.output / "STOP").exists():
            self.stop("PARTIAL_STOPPED", "User stop requested; real partial files retained")
        if elapsed > self.max_seconds:
            self.stop("PARTIAL_TIMEOUT", "Maximum elapsed generation hours reached; partial files retained")
        if force or elapsed - self.last_measure >= 5:
            size = 0
            for directory, _, filenames in os.walk(self.output, followlinks=False):
                for name in filenames:
                    path = Path(directory) / name
                    try:
                        if not path.is_symlink():
                            size += path.stat().st_size
                    except FileNotFoundError:
                        pass
            free = shutil.disk_usage(self.output).free
            self.last_measure = elapsed
            self.state.update(output_bytes=size, available_disk_bytes=free)
            self.write_status()
            if size > self.max_bytes:
                self.stop("PARTIAL_DISK", "Output exceeds max-disk-gb; partial files retained")
            if free < 256 * 1024 ** 2:
                self.stop("PARTIAL_DISK", "Less than 256 MiB free on output filesystem")

    @staticmethod
    def stop_group(process):
        if process.poll() is not None:
            return
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()

    def run(self, command, cwd, log):
        self.state.update(phase=Path(log).stem, log=Path(log).name)
        self.check(force=True)
        started = time.monotonic()
        with Path(log).open("wb") as stream:
            process = subprocess.Popen(command, cwd=cwd, stdout=stream, stderr=subprocess.STDOUT,
                                       start_new_session=True)
            self.state["process_group_id"] = process.pid
            self.write_status()
            try:
                while process.poll() is None:
                    self.check()
                    time.sleep(0.25)
            except BaseException:
                self.stop_group(process)
                raise
        self.state.pop("process_group_id", None)
        result = {"exit_code": process.returncode, "elapsed_seconds": time.monotonic() - started}
        self.check(force=True)
        if process.returncode:
            self.state.update(status="FAILED", failure=f"Generator exit {process.returncode}; see {log}")
            self.write_status()
            raise RuntimeError(self.state["failure"])
        return result

    def finish(self):
        self.completed = True
        self.state.update(status="PASS", phase="validated_complete")
        self.close()

    def close(self):
        if self.closed:
            return
        if not self.completed and self.state["status"] == "RUNNING":
            self.state.update(status="FAILED", failure="CLI ended before validated completion; inspect preserved logs/files")
        self.write_status()
        for s, handler in self.previous_handlers.items():
            signal.signal(s, handler)
        self.closed = True
        atexit.unregister(self.close)
