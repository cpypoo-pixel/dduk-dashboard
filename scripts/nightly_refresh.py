# -*- coding: utf-8 -*-
"""매일 자동 실행되어 교재+내신 데이터를 처음부터 다시 수집하고 통합 데이터를 재생성한다.
전제: launch_persistent_browser.py로 띄운 CDP 브라우저(포트 9333)가 로그인된 채로 계속 떠 있어야 한다.
세션이 끊겨 있으면 이 스크립트는 실패하고 로그만 남긴다(자동 로그인은 하지 않음 - 보안 원칙)."""
import subprocess, sys, time, json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SCRIPTS_DIR = BASE_DIR / "scripts"
PYTHON = r"C:\Users\남푸른\AppData\Local\Programs\Python\Python312\python.exe"
LOG_FILE = DATA_DIR / "refresh_log.txt"
MAX_LOOPS = 10


def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def reset_outputs(items_csv, summary_csv, done_file, item_header, summary_header):
    import csv
    with open(items_csv, "w", newline="", encoding="utf-8-sig") as f:
        csv.DictWriter(f, fieldnames=item_header).writeheader()
    with open(summary_csv, "w", newline="", encoding="utf-8-sig") as f:
        csv.DictWriter(f, fieldnames=summary_header).writeheader()
    if done_file.exists():
        done_file.unlink()


def check_cdp_alive():
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:9333/json/version", timeout=5) as r:
            return r.status == 200
    except Exception as e:
        log(f"[오류] CDP 브라우저(포트 9333)에 연결할 수 없습니다: {e}")
        return False


def run_until_done(script_name, match_file, label):
    with open(match_file, encoding="utf-8") as f:
        total = len(json.load(f)["matched"])

    for i in range(MAX_LOOPS):
        log(f"[{label}] 실행 {i+1}/{MAX_LOOPS}회차 시작 (목표 {total}건)")
        result = subprocess.run([PYTHON, str(SCRIPTS_DIR / script_name)], cwd=str(BASE_DIR),
                                 capture_output=True, text=True, encoding="utf-8")
        log(result.stdout[-1500:] if result.stdout else "(출력 없음)")
        if result.returncode != 0:
            log(f"[{label}] 오류 종료 (code={result.returncode}): {result.stderr[-1000:]}")
            return False
        if "전체" in result.stdout and "끝났습니다" in result.stdout:
            log(f"[{label}] 완료")
            return True
    log(f"[{label}] {MAX_LOOPS}회 반복해도 끝나지 않음 - 중단")
    return False


def main():
    log("===== 야간 자동 갱신 시작 =====")

    if not check_cdp_alive():
        log("[중단] 브라우저 세션이 꺼져 있어 갱신을 건너뜁니다. 수동으로 재로그인 후 다시 시도해주세요.")
        return

    ITEM_FIELDNAMES = [
        "book_id", "textbook_name", "sheet", "page", "item_num", "item_id",
        "item_kind_nm", "difficulty_nm", "is_review_status", "is_text_conversion_status",
        "del_yn", "upper1_taxo_nm", "upper2_taxo_nm", "upper3_taxo_nm", "taxo_nm",
        "last_review_complete_date", "twin_count", "similar_count", "other_relation_count",
        "collected_at",
    ]
    BOOK_FIELDNAMES = [
        "book_id", "textbook_name", "sheet", "excel_item_count", "api_item_count",
        "is_review_complete", "review_done_count", "review_pending_count",
        "deleted_count", "twin_total", "similar_total", "status", "collected_at",
    ]

    log("[초기화] 기존 수집 결과를 비우고 처음부터 다시 수집합니다")
    reset_outputs(
        DATA_DIR / "step8_all_items.csv", DATA_DIR / "step8_book_summary.csv",
        DATA_DIR / "step8_done_books.txt", ITEM_FIELDNAMES, BOOK_FIELDNAMES,
    )
    reset_outputs(
        DATA_DIR / "step9_all_items.csv", DATA_DIR / "step9_exam_summary.csv",
        DATA_DIR / "step9_done_exams.txt", ITEM_FIELDNAMES, BOOK_FIELDNAMES,
    )

    ok1 = run_until_done("step8_collect_all_books_api.py", DATA_DIR / "book_match_result.json", "교재")
    ok2 = run_until_done("step9_collect_all_exams_api.py", DATA_DIR / "exam_match_result.json", "내신")

    if not (ok1 and ok2):
        log("[중단] 일부 수집이 끝나지 않아 통합 데이터는 재생성하지 않습니다.")
        return

    log("[통합] 지역/학년 메타데이터 재병합 및 unified_summary.csv 재생성")
    subprocess.run([PYTHON, str(SCRIPTS_DIR / "enrich_exam_summary.py")], cwd=str(BASE_DIR), check=False)
    subprocess.run([PYTHON, str(SCRIPTS_DIR / "build_unified_data.py")], cwd=str(BASE_DIR), check=False)

    push_to_github()

    log("===== 야간 자동 갱신 완료 =====")


def push_to_github():
    """새로 수집된 데이터를 GitHub(dduk-dashboard)에 올려 배포본(Streamlit Cloud)도 자동 갱신되게 한다."""
    data_files = [
        "data/unified_summary.csv",
        "data/step8_all_items.csv",
        "data/step9_all_items.csv",
    ]
    git = lambda *args: subprocess.run(["git", *args], cwd=str(BASE_DIR), capture_output=True, text=True, encoding="utf-8")

    add_result = git("add", *data_files)
    if add_result.returncode != 0:
        log(f"[GitHub] git add 실패: {add_result.stderr.strip()}")
        return

    diff_result = git("diff", "--cached", "--quiet")
    if diff_result.returncode == 0:
        log("[GitHub] 변경된 데이터 없음 - 커밋 생략")
        return

    commit_msg = f"Nightly data refresh ({time.strftime('%Y-%m-%d')})"
    commit_result = git("commit", "-m", commit_msg)
    if commit_result.returncode != 0:
        log(f"[GitHub] 커밋 실패: {commit_result.stderr.strip()}")
        return

    push_result = git("push", "origin", "main")
    if push_result.returncode != 0:
        log(f"[GitHub] 푸시 실패 (로컬 커밋은 완료됨, 다음 실행 때 재시도하거나 수동 push 필요): {push_result.stderr.strip()}")
        return

    log("[GitHub] 푸시 완료 - Streamlit Cloud가 자동으로 재배포합니다")


if __name__ == "__main__":
    main()
