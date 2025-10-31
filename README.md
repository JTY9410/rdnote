# WECar 연구개발일지 (전자연구노트 시스템)

## 개요

WECar 연구개발일지는 정부과제 평가, 특허 분쟁, 기술이전 협상, 외부 감사를 대비한 **법적 효력**을 갖는 전자연구노트 시스템입니다.

## 주요 기능

### 사용자 영역
- 로그인/회원가입 및 전자서명 등록
- 연구과제(연구개발일지) 생성 및 관리
- 참여자 역할 부여 (OWNER/WRITER/READER/REVIEWER)
- 연구 증빙자료 업로드 (Drag & Drop)
- **자동 시점인증** (timestamp_certified_at)
- 파일 버전 관리 및 변경 이력 보존
- **AuditLog**로 모든 작업 추적
- PDF 출력 (워터마크, 서명 포함)
- 다운로드 이력 및 일일 한도 관리

### 관리자 영역
- 신규 가입자 승인 및 계정 관리
- 워크스페이스 및 연구과제 멤버 구성
- 감사 로그 및 반출 추적
- 대량 다운로드 경보
- 시스템 설정 (허용 확장자, 용량 제한, 다운로드 한도)

## 기술 스택

- **Backend**: Python 3.11, Flask, gunicorn
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy + Alembic (마이그레이션)
- **Frontend**: Jinja2, Bootstrap 5
- **PDF**: WeasyPrint
- **Container**: Docker & Docker Compose

## 설치 및 실행

### 1. 환경 설정

```bash
cp .env.example .env
# .env 파일을 수정하여 필요한 환경변수 설정
```

### 2. Docker Compose로 실행

```bash
docker-compose up -d
```

이 명령은 다음을 수행합니다:
- PostgreSQL 데이터베이스 컨테이너 시작
- Flask 애플리케이션 컨테이너 빌드 및 시작
- Alembic 마이그레이션 자동 실행
- uploads/ 및 exports/ 디렉토리 생성

### 3. 관리자 계정 초기화

```bash
docker-compose exec app python init_db.py
```

이 명령은 다음 관리자 계정을 생성합니다:
- **jty9410@wecar-m.co.kr** (비밀번호: #jeong07209)
- **wecar@wecar-m.co.kr** (비밀번호: #wecarm1004)

### 4. 애플리케이션 접속

웹 브라우저에서 http://localhost:5000 접속

## 프로젝트 구조

```
.
├── app/
│   ├── __init__.py          # Flask 앱 초기화
│   ├── blueprints/          # Blueprint 모듈
│   │   ├── auth.py         # 인증
│   │   ├── dashboard.py    # 대시보드
│   │   ├── profile.py      # 프로필
│   │   ├── workspaces.py   # 워크스페이스
│   │   ├── notes.py        # 연구노트
│   │   ├── folders.py      # 폴더
│   │   ├── files.py        # 파일
│   │   ├── export.py       # PDF 내보내기
│   │   ├── admin.py        # 관리자
│   │   └── help.py         # 도움말
│   ├── models/             # 데이터베이스 모델
│   │   ├── user.py
│   │   ├── workspace.py
│   │   ├── research_note.py
│   │   ├── folder.py
│   │   ├── file.py
│   │   ├── download_history.py
│   │   ├── audit_log.py
│   │   └── system_settings.py
│   ├── templates/          # Jinja2 템플릿
│   └── utils/               # 유틸리티
│       ├── auth.py
│       └── permissions.py
├── migrations/              # Alembic 마이그레이션
├── docker-compose.yml       # Docker Compose 설정
├── Dockerfile              # Docker 이미지 설정
├── requirements.txt        # Python 패키지
└── init_db.py             # 초기 데이터베이스 설정
```

## 데이터베이스 마이그레이션

### 새로운 마이그레이션 생성

```bash
docker-compose exec app alembic revision --autogenerate -m "description"
```

### 마이그레이션 적용

```bash
docker-compose exec app alembic upgrade head
```

## 주요 기능 설명

### 자동 시점인증 (timestamp_certified_at)

파일 업로드 시 서버 시간을 자동으로 기록하여 "이 데이터가 해당 시점에 존재했다"는 사실을 법적으로 증빙합니다.

### AuditLog (감사 로그)

모든 작업(수정/삭제/권한변경/소유권 이전)을 AuditLog로 추적하여 위변조 방지 및 법적 효력 확보.

### 버전 관리

파일 수정 시 overwrite 대신 새 버전 추가하여 변경 이력 전체를 보존합니다.

### 워터마크

PDF 출력 시 모든 페이지에 워터마크를 삽입하여 유출자 추적이 가능하도록 합니다:
```
WECar 연구개발일지 / {과제명} / 기밀 / 무단배포금지 / {생성일시} / {반출자 이메일}
```

### 다운로드 한도

일일 다운로드 한도 설정 및 초과 시 자동 차단 및 관리자 경보.

## 개발 가이드

### 로컬 개발 환경

```bash
# 가상환경 생성
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는 venv\Scripts\activate  # Windows

# 패키지 설치
pip install -r requirements.txt

# 환경변수 설정
export DATABASE_URL="postgresql://wecar_user:wecar_pass@localhost:5432/wecar_db"
export SECRET_KEY="dev-secret-key"

# 애플리케이션 실행
python run.py
```

### 코드 스타일

- PEP 8 준수
- 4 spaces 들여쓰기
- docstring 작성 권장

## 라이선스

내부 사용 전용

## 지원

문제 발생 시 관리자에게 문의하세요.

