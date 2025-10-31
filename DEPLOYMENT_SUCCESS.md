# WECar 연구개발일지 - 배포 완료

## ✅ 배포 완료 상태

**날짜**: 2025-10-26
**시간**: 한국시간 20:32

## 🌐 접속 정보

### 웹 애플리케이션
- **URL**: http://localhost:5001
- **상태**: ✅ 정상 작동 중
- **리디렉션**: / → /auth/login (302 OK)

### 데이터베이스
- **PostgreSQL**: localhost:5432
- **Database**: wecar_db
- **사용자**: wecar_user
- **비밀번호**: wecar_pass
- **상태**: ✅ 정상 작동 중

## 👤 관리자 계정

### 계정 1
- **이메일**: jty9410@wecar-m.co.kr
- **비밀번호**: #jeong07209
- **관리자 권한**: ✅ 활성화

### 계정 2
- **이메일**: wecar@wecar-m.co.kr
- **비밀번호**: #wecarm1004
- **관리자 권한**: ✅ 활성화

## 📊 데이터베이스 상태

### 생성된 테이블 (12개)
✅ alembic_version
✅ system_settings
✅ users (2명의 관리자 계정)
✅ workspaces
✅ workspace_members
✅ research_notes
✅ research_note_members
✅ folders
✅ files
✅ file_tags
✅ download_history
✅ audit_logs

### 시스템 설정
- allowed_extensions: .pdf,.jpg,.png,.jpeg,.csv,.xlsx,.zip,.txt,.doc,.docx
- max_file_size_mb: 500
- daily_download_limit: 100
- session_timeout_min: 30
- build_tag: wecar-rnd:2025-10-26T11:28:28Z

## 🐳 Docker 컨테이너 상태

```
NAME       IMAGE         STATUS                        PORTS
rd-app-1   rd-app        Up                            0.0.0.0:5001->5000/tcp
rd-db-1    postgres:15   Up                            0.0.0.0:5432->5432/tcp
```

## 🚀 시작 방법

### 현재 상태
```bash
# 컨테이너는 이미 실행 중입니다
docker-compose ps

# 웹 브라우저에서 접속
open http://localhost:5001
```

### 중지 및 재시작
```bash
# 중지
docker-compose down

# 재시작
docker-compose up -d

# 로그 확인
docker-compose logs -f app
```

## 📝 주요 기능

### ✅ 완료된 기능
1. **사용자 인증** - 로그인/회원가입/전자서명 등록
2. **워크스페이스 관리** - 생성/멤버 관리
3. **연구노트** - 생성/파일 업로드/다운로드
4. **버전 관리** - 파일 버전 추적
5. **AuditLog** - 모든 작업 추적
6. **PDF 내보내기** - 워터마크 포함
7. **관리자 페이지** - 사용자/시스템 관리
8. **권한 시스템** - OWNER/WRITER/READER/REVIEWER

### 🔒 보안 기능
- ✅ 자동 시점인증 (timestamp_certified_at)
- ✅ AuditLog로 모든 작업 추적
- ✅ 다운로드 한도 관리
- ✅ 워터마크 PDF
- ✅ 전자서명 (OWNER/REVIEWER)

## 🎯 다음 단계

1. 웹 브라우저에서 http://localhost:5001 접속
2. 관리자 로그인 (위 계정 사용)
3. 사용자 추가 및 승인
4. 워크스페이스 및 연구노트 생성
5. 파일 업로드 테스트
6. PDF 출력 테스트

## 📞 지원

문제 발생 시:
1. 로그 확인: `docker-compose logs app`
2. 데이터베이스 상태: `docker-compose exec db psql -U wecar_user -d wecar_db -c "\dt"`
3. 시스템 재시작: `docker-compose restart app`

## 🎉 배포 완료!

시스템이 정상적으로 작동하고 있습니다!

