"""POSIX owned-session supervisor; cancellation time is inside the launch ceiling."""
import json
import os
import signal
import subprocess
import time


class DeadlineExpired(TimeoutError):
    pass


class Deadline:
    def __init__(self, started, seconds):
        self.started = started
        self.end = started + seconds
        self.cleanup_seconds = min(1.0, seconds / 10)
        self.work_end = self.end - self.cleanup_seconds

    def remaining(self, cap):
        left = self.work_end - time.monotonic()
        if left <= 0:
            raise DeadlineExpired('total deadline: work stopped for owned-process cleanup')
        return min(cap, left)


def supervise(argv, payload, deadline, env=None):
    """Only this newly created session is killed. No executor exists in the supervisor."""
    deadline.remaining(180)
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, close_fds=True,
                            start_new_session=True, env=env)
    timed_out = False
    stdout = stderr = ''
    try:
        try:
            stdout, stderr = proc.communicate(json.dumps(payload), timeout=deadline.remaining(900))
        except (subprocess.TimeoutExpired, DeadlineExpired):
            timed_out = True
    finally:
        # Kill the whole owned group even when its leader has exited: a descendant may
        # retain pipes or outlive it. Nested runtime subprocesses never create sessions.
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        left = deadline.end - time.monotonic()
        if left <= 0:
            raise DeadlineExpired('cleanup ceiling exhausted; termination sent, reaping unverified')
        try:
            stdout, stderr = proc.communicate(timeout=left)
        except subprocess.TimeoutExpired as exc:
            raise DeadlineExpired('owned process cleanup not verified within ceiling') from exc
    return {'timed_out': timed_out, 'returncode': proc.returncode,
            'stdout': stdout, 'stderr': stderr, 'pid': proc.pid,
            'elapsed_seconds': time.monotonic() - deadline.started,
            'direct_child_reaped': proc.poll() is not None}
