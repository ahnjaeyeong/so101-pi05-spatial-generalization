"""S16: 가짜 장치 세션을 pty(가짜 터미널) 안에서 돌리고, 실제 키 바이트를 터미널로 쓴다 (lerobot TerminalKeyListener 경로).
끝 메뉴 '선택 >' 에는 'release' 를 입력한다. 결과: _out/S16_adapter_pty_keys/ + check_results."""
import os
import pty
import select
import subprocess
import sys
import time
from pathlib import Path

H = Path(__file__).resolve().parent
KEYS = {"space": b" ", "tab": b"\t", "esc": b"\x1b"}
env = {k: v for k, v in os.environ.items() if k not in ("DISPLAY", "WAYLAND_DISPLAY")}
env.update(CUDA_VISIBLE_DEVICES="", PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1")
env.pop("HIL_TEST_END_CHOICE", None)
master, slave = pty.openpty()
p = subprocess.Popen(["nice", "-n", "19", str(Path.home() / "so101-env/bin/python"), str(H / "test_dagger_fake_e2e.py"), "S16_adapter_pty_keys", "_out"],
                     cwd=H, env=env, stdin=slave, stdout=slave, stderr=slave, close_fds=True, start_new_session=True)
os.close(slave)
buf, log, t0, sent = b"", open(H / "_out/S16_adapter_pty_keys.console.log", "wb"), time.time(), []
answered = False
while True:
    if time.time() - t0 > 200:
        p.kill()
        print("TIMEOUT")
        break
    r, _, _ = select.select([master], [], [], 0.1)
    if r:
        try:
            chunk = os.read(master, 65536)
        except OSError:
            break
        if not chunk:
            break
        log.write(chunk)
        buf += chunk
        while b"@@KEY " in buf:
            i = buf.index(b"@@KEY ")
            j = buf.index(b"@@", i + 6) if b"@@" in buf[i + 6:] else -1
            if j < 0:
                break
            name = buf[i + 6:j].decode()
            os.write(master, KEYS.get(name, name.encode()))
            sent.append((round(time.time() - t0, 2), name))
            buf = buf[j + 2:]
        if not answered and "선택 >".encode() in buf:
            time.sleep(0.8)  # 화면이 '종료 선택' 상태를 그릴 시간 (tap 10 Hz)
            os.write(master, b"release\n")
            sent.append((round(time.time() - t0, 2), "menu:release"))
            answered = True
            buf = b""
        buf = buf[-4096:]
    elif p.poll() is not None:
        break
p.wait(timeout=10)
log.close()
print("child rc", p.returncode, "keys sent", sent)
