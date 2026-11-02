"""시험용: 명령을 pty 안에서 실행하고 정해 둔 순서로 키를 보낸다 (사람이 터미널에서 누르는 것과 같은 바이트).

steps: ("wait", 정규식, 제한초) · ("key", bytes) · ("sleep", 초) · ("wait_safe", 제한초) · ("call", fn)
wait_safe = 녹화 프로세스 status.json 의 시작 자세 검사에 BLOCK 이 없을 때까지 기다림 (/dev/shm/r12_live_* 가장 최근).
relay=True 면 자식 출력을 이 프로세스의 표준 출력에도 그대로 쓴다 (xterm 안에서 실제 화면에 보이게).
"""

import glob
import json
import os
import pty
import re
import select
import sys
import time

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07")


class Driver:
    def __init__(self, cmd, env=None, relay=False, cols=160, rows=50):
        import fcntl
        import struct
        import termios

        self.relay = relay
        self.buf = b""
        self.plain = ""
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.execvpe(cmd[0], cmd, env or os.environ)
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack("HHHH", rows, cols, 0, 0))
        self.mark = 0

    def pump(self, t=0.05):
        r, _, _ = select.select([self.fd], [], [], t)
        if r:
            try:
                d = os.read(self.fd, 65536)
            except OSError:
                return False
            if not d:
                return False
            self.buf += d
            self.plain += ANSI.sub("", d.decode(errors="replace"))
            if self.relay:
                os.write(sys.stdout.fileno(), d)
        return True

    def wait(self, pattern, timeout):
        rx = re.compile(pattern)
        end = time.time() + timeout
        while time.time() < end:
            m = rx.search(self.plain, self.mark)
            if m:
                self.mark = m.end()
                return m
            if not self.pump(0.1):
                break
        raise TimeoutError(f"기다린 글이 안 나옴: {pattern!r}\n--- 끝부분 ---\n{self.plain[-1500:]}")

    def key(self, b):
        os.write(self.fd, b)
        self.pump(0.05)

    def sleep(self, s):
        end = time.time() + s
        while time.time() < end:
            self.pump(0.05)

    def wait_safe(self, timeout):
        end = time.time() + timeout
        while time.time() < end:
            self.pump(0.1)
            d = latest_live()
            st = _read(os.path.join(d, "status.json")) if d else None
            if st and st.get("state") and time.time() - st.get("t", 0) < 1.0 and not any(c[0] == "BLOCK" for c in st.get("checks", [])):
                return st
        raise TimeoutError("시작 자세 검사가 통과하는 순간이 오지 않음")

    def run(self, steps):
        for st in steps:
            kind = st[0]
            if kind == "wait":
                self.wait(st[1], st[2])
            elif kind == "key":
                self.key(st[1])
            elif kind == "sleep":
                self.sleep(st[1])
            elif kind == "wait_safe":
                self.wait_safe(st[1])
            elif kind == "call":
                st[1](self)

    def finish(self, timeout=60):
        end = time.time() + timeout
        while time.time() < end:
            if not self.pump(0.1):
                break
        _, status = os.waitpid(self.pid, 0)
        return os.waitstatus_to_exitcode(status)


def _read(p):
    try:
        with open(p) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def latest_live():
    ds = sorted(glob.glob("/dev/shm/r12_live_*"), key=os.path.getmtime)
    return ds[-1] if ds else None


RIGHT, LEFT, ESC = b"\x1b[C", b"\x1b[D", b"\x1b"
