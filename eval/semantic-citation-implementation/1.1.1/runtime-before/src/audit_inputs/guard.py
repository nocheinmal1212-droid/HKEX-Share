"""Accidental-access guard for a preloaded, single-process Python worker.

Not a hostile-code sandbox: preloaded native code and raw os.read on inherited
descriptors are trusted. The worker receives no data descriptors except stdin.
"""
import os
from pathlib import Path
import sys


def install(reads, writes=()):
    reads = {str(Path(p).resolve()) for p in reads}
    writes = {str(Path(p).resolve()) for p in writes}
    attempts = []

    def deny(event, reason):
        attempts.append({"event": event, "decision": "denied", "reason": reason})
        raise PermissionError(reason)

    def audit(event, args):
        if event == "open":
            target, mode, flags = args
            if isinstance(target, int):
                deny(event, "descriptor opens are forbidden")
            path = Path(os.fsdecode(target))
            if any(p.is_symlink() for p in [path, *path.parents]):
                deny(event, "symlink access is forbidden")
            resolved = str(path.resolve())
            write = (isinstance(mode, str) and any(c in mode for c in "wax+")) or flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC)
            if resolved not in (writes if write else reads):
                deny(event, "unselected file access")
            attempts.append({"event": event, "decision": "allowed", "access": "write" if write else "read", "path": resolved})
        elif event in {"os.listdir", "os.scandir", "subprocess.Popen", "os.system", "socket.__new__", "ctypes.dlopen",
                       "os.exec", "os.posix_spawn", "os.fork", "os.remove", "os.rename", "os.link", "os.symlink", "os.chdir"}:
            deny(event, "runtime discovery, mutation or external execution is forbidden")
    sys.addaudithook(audit)
    return attempts
