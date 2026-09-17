"""Pipeline ownership and bounded child execution, without resetting checkpoints."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import uuid


def pid_alive(pid):
    if not isinstance(pid, int) or pid <= 0:
        return True  # Unknown ownership never permits deletion.
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            return ctypes.get_last_error() != 87  # Access denied means unknown/live.
        try:
            code = wintypes.DWORD()
            return not kernel.GetExitCodeProcess(handle, ctypes.byref(code)) or code.value == 259
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


class PipelineLock:
    def __init__(self, path):
        self.path = Path(path)
        self.record = {'pid': os.getpid(), 'host': socket.gethostname(), 'token': uuid.uuid4().hex, 'child_pid': None,
                       'launching': False}

    def __enter__(self):
        try:
            handle = self.path.open('x')
        except FileExistsError:
            guard = self.path.with_suffix('.recovery')
            # Only one reclaimer may inspect/remove the old lock at a time.
            guard.open('x').close()
            try:
                raw = self.path.read_bytes()
                try:
                    old = json.loads(raw)
                except (ValueError, UnicodeDecodeError):
                    raise FileExistsError('Unrecognized pipeline lock; inspect manually')
                if isinstance(old, int):
                    # Legacy locks contain no child ownership information.
                    raise FileExistsError('Legacy pipeline lock; inspect manually')
                if (not isinstance(old, dict)
                        or not {'pid', 'host', 'token', 'child_pid', 'launching'} <= old.keys()
                        or old.get('host') != socket.gethostname()
                        or not old.get('token') or old.get('launching')
                        or pid_alive(old.get('pid'))
                        or (old.get('child_pid') and pid_alive(old['child_pid']))):
                    raise FileExistsError('Pipeline or child may still be active; lock retained')
                if self.path.read_bytes() != raw:
                    raise FileExistsError('Pipeline lock changed; retry')
                self.path.unlink()
                handle = self.path.open('x')
            finally:
                guard.unlink()
        with handle:
            json.dump(self.record, handle)
        return self

    def child(self, pid=None, launching=False):
        self.record.update(child_pid=pid, launching=launching)
        temporary = self.path.with_suffix('.update')
        temporary.write_text(json.dumps(self.record), encoding='utf-8')
        temporary.replace(self.path)

    def __exit__(self, *args):
        try:
            current = json.loads(self.path.read_text())
            if (current.get('token') == self.record['token']
                    and not current.get('launching')
                    and not (current.get('child_pid') and pid_alive(current['child_pid']))):
                self.path.unlink()
        except FileNotFoundError:
            pass


def run_child(command, *, cwd, log, timeout, owner):
    owner.child(launching=True)
    process = None
    try:
        process = subprocess.Popen(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
            **({'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt'
               else {'start_new_session': True}))
        owner.child(process.pid)
        try:
            return subprocess.CompletedProcess(command, process.wait(timeout=timeout))
        except BaseException:
            if os.name == 'nt':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
            else:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            process.wait(timeout=15)
            raise
    finally:
        # Retain child ownership if cleanup failed: recovery must not duplicate it.
        if process is None or process.poll() is not None:
            owner.child()
