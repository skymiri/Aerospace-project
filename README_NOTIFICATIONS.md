# 알림 시스템 설치 및 설정 가이드

이 가이드는 Discord + ntfy를 활용한 알림 시스템의 설치, 설정, 실행 방법을 단계별로 안내합니다.

## 📋 목차

1. [필수 준비사항](#필수-준비사항)
2. [ntfy 설정](#ntfy-설정)
3. [Discord Webhook 설정](#discord-webhook-설정)
4. [프로젝트 설정](#프로젝트-설정)
5. [실행 방법](#실행-방법)
6. [모니터링 이벤트 설명](#모니터링-이벤트-설명)

---

## 필수 준비사항

### 1. Python 패키지 설치

프로젝트 루트 디렉토리에서 다음 명령어를 실행하세요:

```bash
pip install -r requirements.txt
```

필요한 패키지:
- `requests`: HTTP 요청 (ntfy, Discord)
- `python-dotenv`: 환경 변수 관리
- 기타 프로젝트 의존성

---

## ntfy 설정

### 1. ntfy란?

ntfy는 간단한 푸시 알림 서비스입니다. 공개 서버(`https://ntfy.sh`)를 사용하거나 자체 서버를 운영할 수 있습니다.

### 2. 토픽 생성

**방법 1: 공개 토픽 (간단)**

1. 브라우저에서 `https://ntfy.sh` 접속
2. 토픽 이름을 정합니다 (예: `my-drone-alerts-abc123`)
   - **중요**: 랜덤한 문자열을 포함하여 다른 사람이 알림을 받지 못하도록 하세요
3. 토픽 이름을 `.env` 파일의 `NTFY_TOPIC`에 입력

**방법 2: 비공개 토픽 (권장)**

1. 토픽 이름에 랜덤 문자열 포함 (예: `drone-alerts-xyz789`)
2. 토픽을 구독하려면:
   - 모바일 앱: ntfy 앱 설치 후 토픽 구독
   - 웹: `https://ntfy.sh/your-topic-name` 접속
   - 명령줄: `curl -s ntfy.sh/your-topic-name`

### 3. 테스트

터미널에서 다음 명령어로 테스트할 수 있습니다:

```bash
curl -d "테스트 메시지" https://ntfy.sh/your-topic-name
```

브라우저에서 `https://ntfy.sh/your-topic-name`을 열면 메시지를 확인할 수 있습니다.

---

## Discord Webhook 설정

### 1. Discord 서버 준비

Discord 서버가 필요합니다. 없으면 새로 만들거나 기존 서버를 사용하세요.

### 2. 웹후크 생성

1. Discord 서버 열기
2. 서버 설정 (⚙️) 클릭
3. 왼쪽 메뉴에서 **"연동"** 선택
4. **"웹후크"** 탭 클릭
5. **"새 웹후크"** 버튼 클릭
6. 웹후크 이름 설정 (예: "드론 알림 봇")
7. 알림을 받을 채널 선택
8. **"웹후크 URL 복사"** 클릭
9. `.env` 파일의 `DISCORD_WEBHOOK_URL`에 붙여넣기

### 3. 테스트

터미널에서 다음 명령어로 테스트할 수 있습니다:

```bash
curl -H "Content-Type: application/json" \
     -d '{"embeds":[{"title":"테스트","description":"Discord 웹후크 테스트","color":3447003}]}' \
     YOUR_DISCORD_WEBHOOK_URL
```

Discord 채널에 메시지가 나타나면 성공입니다.

---

## 프로젝트 설정

### 1. .env 파일 생성

프로젝트 루트 디렉토리에 `.env` 파일을 생성하세요:

```bash
cp .env.example .env
```

### 2. .env 파일 편집

`.env` 파일을 열고 다음 값들을 설정하세요:

```env
# 필수 설정
NTFY_TOPIC=your-topic-name-here
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN

# 선택적 설정 (기본값 사용 가능)
NTFY_URL=https://ntfy.sh
LATENCY_THRESHOLD=3.0
LATENCY_CHECK_INTERVAL=60
DRONE_CHECK_INTERVAL=30
DRONE_FAILURE_THRESHOLD=3
DRONE_BATTERY_LOW_THRESHOLD=20
SENSOR_CHECK_INTERVAL=60
DB_CHECK_INTERVAL=120
DISK_CHECK_INTERVAL=300
DATABASE_URL=postgresql://user:password@localhost:5432/aerospace_db
```

### 3. 설정 확인

각 모듈을 개별적으로 테스트할 수 있습니다:

```bash
# ntfy 테스트
python notifier.py

# 드론 연결 테스트
python monitor_drone.py

# Latency 테스트
python monitor_latency.py

# 시스템 모니터링 테스트
python monitor_system.py
```

---

## 실행 방법

### 1. 전체 모니터링 시스템 실행

모든 모니터링을 동시에 실행하려면:

```bash
python monitor_main.py
```

이 명령어는 다음을 모두 실행합니다:
- ntfy latency 감시
- 드론 연결 감시
- 센서 데이터 감시
- 데이터베이스 연결 감시
- 디스크 공간 감시

### 2. 개별 모니터링 실행

특정 모니터링만 실행하려면:

```bash
# ntfy latency만 감시
python monitor_latency.py
# (코드에서 monitor_latency_loop() 주석 해제 필요)

# 드론 연결만 감시
python monitor_drone.py
# (코드에서 monitor_drone_connection_loop() 주석 해제 필요)
```

### 3. 백그라운드 실행 (Linux/Mac)

```bash
# nohup으로 백그라운드 실행
nohup python monitor_main.py > monitor.log 2>&1 &

# 프로세스 확인
ps aux | grep monitor_main

# 로그 확인
tail -f monitor.log

# 종료
pkill -f monitor_main.py
```

### 4. systemd 서비스로 등록 (Linux)

`/etc/systemd/system/aerospace-monitor.service` 파일 생성:

```ini
[Unit]
Description=BCIT Aerospace Monitoring System
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/BCITAerospace
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /path/to/BCITAerospace/monitor_main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

서비스 시작:

```bash
sudo systemctl enable aerospace-monitor
sudo systemctl start aerospace-monitor
sudo systemctl status aerospace-monitor
```

---

## 모니터링 이벤트 설명

### 1. ntfy Latency 감시

**목적**: ntfy 서버의 응답 시간을 주기적으로 확인

**동작**:
- 60초마다 ntfy 서버에 ping 메시지 전송
- 응답 시간이 3초를 초과하면 알림 전송
- 서버 연결 실패 시에도 알림 전송

**알림 내용**:
- 현재 지연시간
- 임계값
- 서버 연결 실패 시 연속 실패 횟수

**설정**:
- `LATENCY_THRESHOLD`: 임계값 (초)
- `LATENCY_CHECK_INTERVAL`: 체크 간격 (초)

---

### 2. 드론 연결 감시

**목적**: 드론과의 연결 상태를 주기적으로 확인

**동작**:
- 30초마다 드론 연결 상태 확인
- 연속 3회 실패 시 알림 전송
- 배터리 잔량이 20% 미만이면 경고
- 신호 강도가 30% 미만이면 경고

**알림 내용**:
- 연결 끊김: 연속 실패 횟수, 드론 상태
- 배터리 경고: 현재 배터리 %, 신호 강도, 착륙 권고
- 신호 약함: 신호 강도, 연결 불안정 경고

**설정**:
- `DRONE_CHECK_INTERVAL`: 체크 간격 (초)
- `DRONE_FAILURE_THRESHOLD`: 연속 실패 임계값
- `DRONE_BATTERY_LOW_THRESHOLD`: 배터리 경고 임계값 (%)

**참고**: 현재는 샘플 구현입니다. 실제 드론 SDK를 사용하려면 `monitor_drone.py`의 `check_drone_connection()` 함수를 수정하세요.

---

### 3. 센서 데이터 이상치 감지

**목적**: 센서 데이터에서 비정상적인 값을 감지

**동작**:
- 범위 기반 감지: 측정값이 정상 범위를 벗어나면 알림
- 통계적 감지: Z-score를 사용하여 평균에서 크게 벗어난 값 감지

**감시하는 센서**:
- 풍속 (wind_speed): 0~50 m/s
- 풍향 (wind_direction): 0~360도
- 온도 (temperature): -40~60°C
- 습도 (humidity): 0~100%
- 기압 (pressure): 800~1100 hPa

**알림 내용**:
- 이상치가 감지된 센서 이름
- 측정값
- 정상 범위
- 통계적 이상치의 경우: 평균, 표준편차, Z-score

**설정**:
- `SENSOR_CHECK_INTERVAL`: 체크 간격 (초)

---

### 4. 데이터베이스 연결 감시

**목적**: PostgreSQL 데이터베이스 연결 상태 확인

**동작**:
- 120초마다 데이터베이스 연결 테스트
- 연결 실패 시 알림 전송

**알림 내용**:
- 연결 실패 에러 메시지
- 연속 실패 횟수

**설정**:
- `DATABASE_URL`: 데이터베이스 연결 문자열
- `DB_CHECK_INTERVAL`: 체크 간격 (초)

---

### 5. 디스크 공간 감시

**목적**: 서버 디스크 사용량 모니터링

**동작**:
- 300초(5분)마다 디스크 사용률 확인
- 80% 이상 사용 시 경고
- 90% 이상 사용 시 긴급 알림

**알림 내용**:
- 디스크 사용률 (%)
- 남은 공간 (GB)
- 긴급도에 따른 우선순위

**설정**:
- `DISK_CHECK_INTERVAL`: 체크 간격 (초)

---

### 6. 서버 에러 핸들러

**목적**: Flask 앱에서 발생하는 예외를 자동으로 알림

**사용 방법**:

`app.py`에 다음 코드를 추가하세요:

```python
from monitor_system import handle_server_error

@app.errorhandler(Exception)
def handle_exception(e):
    handle_server_error(e, context="파일 업로드 처리")
    # 기존 에러 처리 로직...
    return "에러가 발생했습니다.", 500
```

**알림 내용**:
- 에러 발생 컨텍스트
- 에러 타입
- 에러 메시지

---

## 추가 이벤트 추천

### 1. 파일 처리 완료 알림

파일 업로드 및 처리 완료 시 알림을 보낼 수 있습니다.

**추천 데이터**:
- 처리된 파일 이름
- 처리 시간
- 처리 결과 (성공/실패)
- 처리된 데이터 포인트 수

**구현 예시** (`app.py`에 추가):

```python
from notifier import send_priority_notification

# 파일 처리 성공 시
send_priority_notification(
    message=f"파일 처리 완료: {filename}\n처리 시간: {processing_time}초",
    title="✅ 파일 처리 완료",
    priority="default",
    tags=["success", "file"]
)
```

### 2. 데이터 임포트 완료 알림

데이터베이스 임포트 완료 시 알림을 보낼 수 있습니다.

**추천 데이터**:
- 임포트된 레코드 수
- 임포트 소요 시간
- 데이터 소스 (드론/풍속계)
- 임포트 날짜/시간

### 3. 분석 완료 알림

데이터 분석이 완료되면 알림을 보낼 수 있습니다.

**추천 데이터**:
- 분석 결과 요약
- 생성된 차트/그래프 링크
- 분석에 사용된 데이터 범위
- 주요 발견사항

### 4. 예약 작업 완료 알림

정기적으로 실행되는 작업(예: 일일 리포트 생성) 완료 시 알림

**추천 데이터**:
- 작업 이름
- 실행 시간
- 작업 결과
- 다음 실행 예정 시간

---

## 문제 해결

### 알림이 오지 않을 때

1. **환경 변수 확인**
   ```bash
   # .env 파일이 올바른 위치에 있는지 확인
   ls -la .env
   
   # 환경 변수가 로드되는지 확인
   python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('NTFY_TOPIC'))"
   ```

2. **ntfy 테스트**
   ```bash
   curl -d "테스트" https://ntfy.sh/your-topic-name
   ```

3. **Discord Webhook 테스트**
   ```bash
   curl -H "Content-Type: application/json" \
        -d '{"content":"테스트"}' \
        YOUR_DISCORD_WEBHOOK_URL
   ```

4. **로그 확인**
   - 터미널 출력 확인
   - 백그라운드 실행 시 로그 파일 확인

### 연결 오류

- **네트워크 확인**: 인터넷 연결 상태 확인
- **방화벽**: 포트 443(HTTPS)이 열려있는지 확인
- **프록시**: 프록시 환경에서는 `requests` 라이브러리 설정 필요

---

## 보안 고려사항

1. **.env 파일 보안**
   - `.env` 파일을 Git에 커밋하지 마세요 (`.gitignore`에 추가)
   - 토픽 이름에 랜덤 문자열 포함
   - Discord Webhook URL은 비밀로 유지

2. **토픽 이름**
   - 예측 가능한 이름 사용 금지
   - 예: `drone-alerts-xyz789` (랜덤 문자열 포함)

3. **자체 ntfy 서버**
   - 프로덕션 환경에서는 자체 ntfy 서버 운영 권장
   - `NTFY_URL`을 자체 서버 주소로 변경

---

## 추가 리소스

- [ntfy 공식 문서](https://ntfy.sh/docs/)
- [Discord Webhook 가이드](https://discord.com/developers/docs/resources/webhook)
- [python-dotenv 문서](https://pypi.org/project/python-dotenv/)

---

## 문의 및 지원

문제가 발생하거나 질문이 있으면 이슈를 생성하거나 프로젝트 관리자에게 문의하세요.

