# 독립적으로 계속 떠 있는 브라우저를 띄운다 (CDP 디버깅 포트 개방).
# 이후 배치 스크립트들은 이 브라우저를 새로 켜지 않고 "연결"만 해서 쓴다.
# 즉 로그인을 한 번만 하면, 그 다음 배치부터는 재로그인이 필요 없다.
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
USER_DATA_DIR = BASE_DIR / ".browser_profile"
CHROME_EXE = Path(r"C:\Users\남푸른\AppData\Local\ms-playwright\chromium-1248\chrome-win64\chrome.exe")
CDP_PORT = 9333
# 수집 스크립트들은 "book-item-edit"이 URL에 포함된 탭의 로그인 세션을 재사용한다.
# 이 주소는 직접 열면 400 오류가 나서, 홈으로 시작한 뒤 open_editor_tab.py가 메뉴를 따라 들어간다.
START_URL = "https://adm.mswitch.co.kr/home"

USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

args = [
    str(CHROME_EXE),
    f"--remote-debugging-port={CDP_PORT}",
    f"--user-data-dir={USER_DATA_DIR}",
    "--no-first-run",
    "--no-default-browser-check",
    START_URL,
]

# DETACHED_PROCESS: 이 파이썬 스크립트(와 이를 호출한 셸)가 끝나도 브라우저는 계속 살아있음
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200

proc = subprocess.Popen(
    args,
    creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
    close_fds=True,
)

print(f"[실행됨] PID={proc.pid}", flush=True)
print(f"[CDP 포트] {CDP_PORT}", flush=True)
print("[안내] 이 창은 계속 떠 있습니다. 로그인을 한 번만 해두면 이후 배치에서 재사용됩니다.", flush=True)

# 브라우저가 뜰 때까지 기다렸다가 book-item-edit 탭까지 자동으로 이동한다. (로그인이 풀려 있으면 이동은 중단되니 직접 로그인 후 open_editor_tab.py만 다시 실행)
import sys, time, urllib.request
for _ in range(30):
    try:
        urllib.request.urlopen(f"http://localhost:{CDP_PORT}/json/version", timeout=2)
        break
    except Exception:
        time.sleep(1)
subprocess.run([sys.executable, str(Path(__file__).parent / "open_editor_tab.py")])
