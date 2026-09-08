# Cubie Server Dashboard

Cubie A7Z 1GB / Debian 13 CLI용 경량 서버 대시보드입니다.

## 기능

- 브라우저에서 여러 파일 업로드
- 업로드 즉시 Watch Directory(incoming)로 이동하여 자동 변환 대기
- Flask 웹 대시보드
- CPU 사용률 / load average
- RAM 사용량
- 저장장치 사용량
- CPU 온도 자동 탐색(thermal_zone)
- Watch Directory 기반 파일 감시
- 파일 변환 Worker
- 처리 대기열 / 성공 / 실패 표시
- Activity 로그
- systemd 자동 시작
- 웹에서 Worker 재시작 / 서버 재부팅
- 1GB RAM을 고려한 외부 JS/CSS 프레임워크 없는 UI

## 기본 디렉터리

    /opt/cubie-dashboard/
      app.py
      config.py
      requirements.txt
      templates/index.html
      static/style.css
      static/app.js
      worker/watcher.py
      worker/converter.py

    /srv/cubie/
      incoming/   # 새 파일을 넣는 곳
      output/     # 변환 결과
      error/      # 실패 파일
      archive/    # 성공 원본
      logs/

## 설치

Debian 13에서 root로:

    chmod +x install.sh
    sudo ./install.sh

설치가 끝나면:

    systemctl status cubie-dashboard
    systemctl status cubie-worker

브라우저:

    http://CUBIE_A7Z_IP:8080

## 파일 변환

기본 동작은 안전한 테스트를 위해 입력 파일을 output으로 복사합니다.

실제 변환은 `/opt/cubie-dashboard/config.py`의 `CONVERSION_COMMAND`를 수정하십시오.

예:

    CONVERSION_COMMAND = [
        "/usr/bin/magick",
        "{input}",
        "-quality", "92",
        "{output}"
    ]

명령어에서 `{input}`, `{output}`을 사용할 수 있습니다.

Sony RAW(ARW)를 사용할 경우에는 먼저 Cubie에서 사용할 RAW 변환 프로그램의 경로와 명령 옵션을 확인한 뒤 이 값을 지정하십시오.

변환 명령을 변경한 후:

    sudo systemctl restart cubie-worker

## 로그

    journalctl -u cubie-dashboard -f
    journalctl -u cubie-worker -f

웹 Activity 로그:

    /srv/cubie/logs/activity.log

## 서비스 제어

대시보드의 Worker Restart / Reboot 버튼은 sudoers에 허용된 명령만 실행합니다.

웹 서버 자체를 root로 실행하지 않습니다.
