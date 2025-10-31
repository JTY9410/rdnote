# WECar 연구개발일지 - 빠른 시작 가이드

## 설치 및 실행 (5분 안에 시작하기)

### 1. 환경 확인
```bash
# Python 3.11 이상
python --version

# Docker가 설치되어 있어야 함
docker --version
docker-compose --version
```

### 2. 애플리케이션 시작
```bash
# Docker Compose로 전체 환경 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f app
```

### 3. 데이터베이스 초기화 및 관리자 계정 생성
```bash
# 초기 설정 스크립트 실행
docker-compose exec app python init_db.py
```

이 명령은 다음을 수행합니다:
- 데이터베이스 테이블 생성
- 시스템 설정 초기화
- 관리자 계정 2개 생성

### 4. 웹 브라우저 접속
```
http://localhost:5000
```

## 관리자 로그인

기본 관리자 계정 2개:

1. **첫 번째 관리자**
   - 이메일: `jty9410@wecar-m.co.kr`
   - 비밀번호: `#jeong07209`

2. **두 번째 관리자**
   - 이메일: `wecar@wecar-m.co.kr`
   - 비밀번호: `#wecarm1004`

## 주요 기능

### 사용자 영역

#### 1. 대시보드 (`/dashboard`)
- 내 워크스페이스 목록
- 내 연구과제 목록
- 최근 업로드 파일
- 최근 다운로드 이력
- 오늘 다운로드 횟수 / 한도

#### 2. 워크스페이스 (`/workspaces`)
- 워크스페이스 생성
- 멤버 초대
- 멤버 역할 관리 (OWNER/MEMBER)

#### 3. 연구노트 (`/notes/<note_id>`)
- 파일 업로드 (Drag & Drop)
- 폴더 생성 및 관리
- 파일 다운로드
- PDF 출력
- 활동 로그 확인

#### 4. 프로필 (`/profile`)
- 기본 정보 수정
- 전자서명 등록
- 비밀번호 변경

### 관리자 영역 (`/admin`)

#### 1. 대시보드 (`/admin`)
- 통계 정보 (사용자수, 워크스페이스, 연구과제 등)
- 보안 리스크 확인
- 최근 24시간 다운로드 TOP5
- 형식적 운영 위험 과제 목록

#### 2. 사용자 관리 (`/admin/users`)
- 사용자 목록 조회
- 사용자 상태 변경 (pending/active/suspended)
- 관리자 권한 부여

#### 3. 워크스페이스 관리 (`/admin/workspaces`)
- 워크스페이스 목록
- 멤버 구성 확인

#### 4. 연구과제 관리 (`/admin/notes`)
- 연구과제 목록
- 멤버 및 권한 확인
- 운영 상태 모니터링

#### 5. 감사 로그 (`/admin/audit`)
- 모든 작업 추적
- 필터링 (날짜, 액션, 사용자)
- CSV 내보내기

#### 6. 다운로드 이력 (`/admin/downloads`)
- 모든 다운로드 기록
- 반출 추적
- 이상행위 경보

#### 7. 시스템 설정 (`/admin/settings`)
- 허용 파일 확장자
- 최대 파일 크기
- 일일 다운로드 한도
- 세션 타임아웃

## 개발 중지 및 재시작

```bash
# 중지
docker-compose down

# 재시작
docker-compose up -d

# 강제 재시작 (캐시 무시)
docker-compose down -v
docker-compose up -d --build
```

## 로그 확인

```bash
# 애플리케이션 로그
docker-compose logs -f app

# 데이터베이스 로그
docker-compose logs -f db

# 전체 로그
docker-compose logs -f
```

## 데이터베이스 백업 및 복원

```bash
# 백업
docker-compose exec db pg_dump -U wecar_user wecar_db > backup.sql

# 복원
docker-compose exec -T db psql -U wecar_user wecar_db < backup.sql
```

## 문제 해결

### 포트 충돌
다른 애플리케이션이 5000 포트를 사용 중인 경우:
```bash
# docker-compose.yml 수정
ports:
  - "5001:5000"  # 외부 포트 변경
```

### 데이터베이스 연결 오류
```bash
# 데이터베이스 컨테이너 상태 확인
docker-compose ps

# 데이터베이스 재시작
docker-compose restart db
```

### 마이그레이션 오류
```bash
# 마이그레이션 상태 확인
docker-compose exec app alembic current

# 마이그레이션 수동 실행
docker-compose exec app alembic upgrade head
```

## 다음 단계

1. **첫 번째 사용자 만들기**
   - 관리자로 로그인
   - 사용자 관리에서 새 사용자 승인

2. **워크스페이스 생성**
   - 사용자로 로그인
   - 워크스페이스 생성

3. **연구과제 만들기**
   - 새 연구개발일지 생성
   - 멤버 초대 및 역할 할당

4. **파일 업로드**
   - 파일 드래그 앤 드롭
   - 메타데이터 입력 (실험일, 설명, 태그)

5. **PDF 출력**
   - 연구과제 상세 페이지에서 PDF 출력
   - 워터마크 및 서명이 포함된 공식 문서 생성

## 도움말

- 사용자 가이드: `/help`
- 프로젝트 문서: `README.md`
- 요구사항 문서: `요구사항.md`

## 문의

문제가 발생하거나 질문이 있으면 시스템 관리자에게 문의하세요.

