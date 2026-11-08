"""Private stdin/stdout handshake for fixture-owned effects observations."""
import json
import queue
import subprocess
import threading
import time

PREFIX = "@@LAB_EFFECTS@@"
EVENT_PREFIX = "@@LAB_HANDLING_EVENT@@"
GROUPS = ("cancel-editor", "booking-cancel", "booking-deadline", "booking-single-page", "booking-positive", "handling-single-page", "handling-cargo-voyage", "handling-location", "handling-event", "handling-voyage")
ROLES = ("anonymous", "Reader", "Operator", "Administrator")
STAGES = frozenset(
    group + ":" + role + ":" + phase
    for group in GROUPS
    for role in (("Operator", "Administrator") if group == "booking-positive" else ROLES)
    for phase in ("before", "after")
)

def run_browser_with_effects(command, capture, timeout=300, inspect_event=None):
    process = subprocess.Popen(
        command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT, text=True, bufsize=1,
    )
    lines = queue.Queue()
    def read_output():
        try:
            for line in process.stdout:
                lines.put(line)
        finally:
            lines.put(None)
    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    deadline = time.monotonic() + timeout
    output = []
    next_id = 0
    seen_stages = set()
    last_stage = None
    started = time.monotonic()

    def raise_deadline():
        error = subprocess.TimeoutExpired(command, timeout, output="".join(output)[-8192:])
        error.completed_effect_stages = sorted(seen_stages)
        error.last_completed_effect_stage = last_stage
        error.elapsed_seconds = round(time.monotonic() - started, 3)
        raise error

    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise_deadline()
            try:
                line = lines.get(timeout=min(remaining, 0.5))
            except queue.Empty:
                continue
            if line is None:
                code = process.wait(timeout=max(0.1, deadline - time.monotonic()))
                return subprocess.CompletedProcess(command, code, "".join(output))
            if line.startswith(EVENT_PREFIX):
                request = json.loads(line[len(EVENT_PREFIX):])
                if (inspect_event is None or not isinstance(request, dict)
                        or set(request) != {"id", "tracking_id", "completion_date", "location_code"}
                        or type(request["id"]) is not int or request["id"] != next_id
                        or not isinstance(request["tracking_id"], str)
                        or not __import__("re").fullmatch(r"[A-Z0-9]{8}", request["tracking_id"])
                        or request["completion_date"] != "2032-02-04" or request["location_code"] not in {"USCHI", "DEHAM"}):
                    raise RuntimeError("Invalid handling-event observation request")
                snapshot = inspect_event(request["tracking_id"], request["completion_date"], request["location_code"], deadline-time.monotonic())
                process.stdin.write(json.dumps({"id": next_id, "snapshot": snapshot}) + "\n")
                process.stdin.flush()
                next_id += 1
                continue
            if not line.startswith(PREFIX):
                output.append(line)
                continue
            request = json.loads(line[len(PREFIX):])
            if (not isinstance(request, dict) or set(request) != {"id", "stage"}
                    or type(request["id"]) is not int or request["id"] != next_id
                    or not isinstance(request["stage"], str)
                    or request["stage"] not in STAGES or request["stage"] in seen_stages):
                raise RuntimeError("Invalid effects observation request")
            stem, phase = request["stage"].rsplit(":", 1)
            if phase == "after" and stem + ":before" not in seen_stages:
                raise RuntimeError("Effects after stage preceded before stage")
            try:
                snapshot = capture(request["stage"], deadline - time.monotonic())
            except subprocess.TimeoutExpired as error:
                error.completed_effect_stages = sorted(seen_stages)
                error.last_completed_effect_stage = last_stage
                error.pending_effect_stage = request["stage"]
                error.elapsed_seconds = round(time.monotonic() - started, 3)
                raise
            if time.monotonic() >= deadline:
                raise_deadline()
            response = {"id": next_id, "snapshot": snapshot}
            process.stdin.write(json.dumps(response) + "\n")
            process.stdin.flush()
            seen_stages.add(request["stage"])
            last_stage = request["stage"]
            next_id += 1
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        for stream in (process.stdin, process.stdout):
            try:
                stream.close()
            except OSError:
                pass
        reader.join(timeout=1)
