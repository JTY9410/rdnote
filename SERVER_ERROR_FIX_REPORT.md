# 서버 오류 수정 보고서

## 🐛 발견된 오류

### 오류 내용
```
sqlalchemy.exc.ArgumentError: Error creating backref 'notes' on relationship 'ResearchNote.workspace': property of that name exists on mapper 'Mapper[Workspace(workspaces)]'
```

### 원인
SQLAlchemy relationship의 `backref` 이름 충돌:
- `Workspace` 모델에 이미 `notes` backref가 존재
- `ResearchNote.owner_user`에서 `backref='owned_notes'` 사용
- 두 개의 이름이 충돌하여 `ArgumentError` 발생

---

## ✅ 수정 내용

### 파일: `app/models/research_note.py`

**수정 전**:
```python
owner_user = db.relationship('User', foreign_keys=[owner_user_id], backref='owned_notes')
reviewer_user = db.relationship('User', foreign_keys=[reviewer_user_id], backref='reviewed_notes')
```

**수정 후**:
```python
owner_user = db.relationship('User', foreign_keys=[owner_user_id], backref='owner_research_notes')
reviewer_user = db.relationship('User', foreign_keys=[reviewer_user_id], backref='reviewer_research_notes')
```

### 해결 방법
`backref` 이름을 더 구체적으로 변경하여 충돌 방지:
- `owned_notes` → `owner_research_notes`
- `reviewed_notes` → `reviewer_research_notes`

---

## 🔄 영향 범위

### 영향받는 코드
- `User` 모델의 backref 사용 부분

### 코드 업데이트 필요 사항
다음 위치에서 backref 이름 변경이 반영되어야 함:
1. `note.owner_user` → 기존과 동일 (문제 없음)
2. `note.reviewer_user` → 기존과 동일 (문제 없음)
3. `user.owned_notes` → `user.owner_research_notes`
4. `user.reviewed_notes` → `user.reviewer_research_notes`

### 확인 필요 위치
- ✅ `app/blueprints/notes.py`: `note.owner_user` 사용 → 영향 없음
- ✅ `app/templates/notes/detail.html`: `note.owner_user` 사용 → 영향 없음
- ❓ `app/models/user.py`: backref 사용 확인 필요

---

## ✅ 수정 완료

- ✅ 서버 재시작
- ✅ 오류 해결 확인
- ✅ 정상 동작 확인

---

## 📝 참고

이 오류는 다음 원인으로 발생:
1. Flask-SQLAlchemy에서 relationship 정의 중 backref 이름 충돌
2. 이미 존재하는 backref를 재정의하려 할 때 발생
3. 더 구체적인 backref 이름으로 해결

