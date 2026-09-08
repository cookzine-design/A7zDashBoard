from pathlib import Path

BASE_DIR = Path("/srv/cubie")
INCOMING_DIR = BASE_DIR / "incoming"
OUTPUT_DIR = BASE_DIR / "output"
ERROR_DIR = BASE_DIR / "error"
ARCHIVE_DIR = BASE_DIR / "archive"
LOG_DIR = BASE_DIR / "logs"

# 변환 명령:
# {input} = 입력 파일
# {output} = 출력 파일
#
# 기본값은 실제 변환 대신 파일을 output으로 복사합니다.
# 설치 후 원하는 변환기로 교체하십시오.
CONVERSION_COMMAND = [
    "/usr/bin/cp",
    "{input}",
    "{output}",
]

# 기본 출력 확장자.
# cp를 그대로 사용할 때는 입력 확장자를 유지합니다.
OUTPUT_EXTENSION = ""

# 감시 대상 파일 확장자. 빈 리스트면 모든 일반 파일을 감시합니다.
WATCH_EXTENSIONS = [
    ".arw", ".jpg", ".jpeg", ".png", ".tif", ".tiff",
    ".mp4", ".mov", ".mkv"
]

POLL_SECONDS = 2
MAX_ACTIVITY_LINES = 100

HOST = "0.0.0.0"
PORT = 8080
