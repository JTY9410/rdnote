# Vercel "Not Found" 오류 수정

## 문제

Vercel에서 "Not Found" 오류가 발생했습니다. 이는 Flask 앱이 제대로 export되지 않아서 발생한 문제였습니다.

## 수정 사항

### 1. WSGI 핸들러 명시적 Export

`api/index.py` 파일 끝에 다음을 추가했습니다:

```python
# Vercel Python builder requires explicit export
handler = app
application = app  # Some WSGI servers use 'application'
```

### 2. App 변수 초기화

`app` 변수를 먼저 선언하여 모든 코드 경로에서 접근 가능하도록 했습니다:

```python
app = None  # Flask app will be initialized below
```

## 확인 방법

재배포 후 다음 URL로 확인:

1. **Health Check:**
   ```
   https://your-app.vercel.app/health
   ```

2. **루트 경로:**
   ```
   https://your-app.vercel.app/
   ```

## 추가 문제 해결

### 만약 여전히 "Not Found"가 발생한다면:

1. **Vercel 로그 확인:**
   ```bash
   vercel logs --follow
   ```

2. **배포 상태 확인:**
   ```bash
   vercel inspect
   ```

3. **환경변수 확인:**
   ```bash
   vercel env ls
   ```

4. **`vercel.json` 라우팅 확인:**
   - `routes` 설정이 올바른지 확인
   - `dest`가 `api/index.py`를 가리키는지 확인

## 참고

Vercel Python 빌더(`@vercel/python`)는 일반적으로 Flask 앱을 자동으로 감지하지만, 명시적으로 export하는 것이 더 안전합니다.

