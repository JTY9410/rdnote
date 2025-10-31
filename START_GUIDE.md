# WECar 연구개발일지 - 시작 가이드

## 🎉 시스템이 정상 작동 중입니다!

### 📍 접속 정보

- **웹 애플리케이션**: http://localhost:5001
- **데이터베이스**: localhost:5432
- **상태**: ✅ 정상 작동 중

### 🔑 관리자 로그인 정보

#### 계정 1
- **이메일**: jty9410@wecar-m.co.kr
- **비밀번호**: #jeong07209

#### 계정 2
- **이메일**: wecar@wecar-m.co.kr  
- **비밀번호**: #wecarm1004

### 🚀 지금 바로 시작하기

1. **웹 브라우저 열기**
   ```
   http://localhost:5001
   ```

2. **관리자로 로그인**
   - 위 관리자 계정 중 하나를 사용

3. **기능 테스트**
   - 대시보드 확인
   - 워크스페이스 생성
   - 연구과제 생성
   - 파일 업로드

### 📊 컨테이너 확인 명령어

```bash
# 컨테이너 상태 확인
cd /Users/USER/dev/r\&d
docker-compose ps

# 로그 확인
docker-compose logs -f app

# 재시작
docker-compose restart app

# 중지
docker-compose down

# 완전 재시작
docker-compose down && docker-compose up -d
```

### 🔍 문제 해결

#### 1. 접속이 안 될 때
```bash
# 컨테이너 상태 확인
docker ps

# 로그 확인
docker-compose logs app
```

#### 2. 에러가 발생할 때
```bash
# 컨테이너 재시작
docker-compose restart app

# 전체 재빌드
docker-compose down
docker-compose up -d --build
```

#### 3. 데이터베이스 확인
```bash
# 데이터베이스 접속
docker-compose exec db psql -U wecar_user -d wecar_db

# 테이블 목록
\dt

# 사용자 확인
SELECT * FROM users;
```

### 📝 현재 상태

✅ **컨테이너**: 2개 실행 중 (app, db)
✅ **웹 서버**: 정상 작동 (http://localhost:5001)
✅ **데이터베이스**: 정상 작동 (12개 테이블)
✅ **관리자 계정**: 2개 생성 완료
✅ **시스템 설정**: 초기화 완료

### 🎯 다음 단계

1. 브라우저에서 접속
2. 관리자 로그인
3. 대시보드 확인
4. 관리자 기능 테스트

**모든 것이 준비되었습니다!** 🎉

