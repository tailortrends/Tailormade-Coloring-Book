# Firebase Database SOP

**Layer**: 1 (Architecture)  
**Service**: `backend/app/services/firebase_db.py`  
**Last Updated**: 2026-02-12

---

## Goal

Manage user profiles and book metadata persistence in Firebase Firestore. Provide type-safe access to user data and book records.

---

## Collections

### 1. `users` Collection

**Document ID**: Firebase UID (e.g., `abc123xyz`)

**Schema**:
```json
{
  "uid": "string",
  "email": "string",
  "display_name": "string | null",
  "tier": "free | premium",
  "created_at": "timestamp",
  "total_books": "number",
  "last_generation_date": "ISO8601 string"
}
```

**Purpose**: Store user profile and subscription info

### 2. `books` Collection

**Document ID**: Auto-generated UUID (e.g., `550e8400-e29b-41d4-a716-446655440000`)

**Schema**:
```json
{
  "book_id": "string",
  "user_id": "string",
  "title": "string",
  "theme": "string",
  "age_range": "4-6 | 7-9 | 10-12",
  "art_style": "simple | standard | detailed",
  "page_count": "number",
  "pdf_url": "string",
  "pages": [
    {
      "page_number": "number",
      "image_url": "string",
      "thumbnail_url": "string",
      "description": "string",
      "prompt": "string"
    }
  ],
  "created_at": "timestamp",
  "generation_time_seconds": "number",
  "status": "generating | completed | failed"
}
```

**Purpose**: Store book metadata and generation results

### 3. `usage` Collection

**Document ID**: `{uid}_{date}` (e.g., `abc123_2026-02-12`)

**Schema**:
```json
{
  "uid": "string",
  "date": "string",  // YYYY-MM-DD
  "count": "number"
}
```

**Purpose**: Track daily generation counts for rate limiting

---

## Operations

### User Operations

**Create/Update User**:
```python
def save_user(uid: str, email: str, display_name: str | None):
    db = firestore.client()
    user_ref = db.collection("users").document(uid)
    user_ref.set({
        "uid": uid,
        "email": email,
        "display_name": display_name,
        "tier": "free",  # Default tier
        "created_at": firestore.SERVER_TIMESTAMP,
        "total_books": 0
    }, merge=True)
```

**Get User**:
```python
def get_user(uid: str) -> dict | None:
    db = firestore.client()
    doc = db.collection("users").document(uid).get()
    return doc.to_dict() if doc.exists else None
```

**Update Tier**:
```python
def upgrade_to_premium(uid: str):
    db = firestore.client()
    user_ref = db.collection("users").document(uid)
    user_ref.update({"tier": "premium"})
```

### Book Operations

**Create Book**:
```python
def create_book(book_data: dict) -> str:
    db = firestore.client()
    book_ref = db.collection("books").document()
    book_id = book_ref.id
    book_data["book_id"] = book_id
    book_data["created_at"] = firestore.SERVER_TIMESTAMP
    book_ref.set(book_data)
    return book_id
```

**Get User's Books**:
```python
def get_user_books(uid: str, limit: int = 10) -> list[dict]:
    db = firestore.client()
    books = (
        db.collection("books")
        .where("user_id", "==", uid)
        .order_by("created_at", direction="DESCENDING")
        .limit(limit)
        .stream()
    )
    return [book.to_dict() for book in books]
```

**Update Book Status**:
```python
def update_book_status(book_id: str, status: str):
    db = firestore.client()
    book_ref = db.collection("books").document(book_id)
    book_ref.update({"status": status})
```

---

## Indexes

### Required Composite Indexes

Firestore automatically indexes single fields, but queries with multiple filters need composite indexes:

**Books by User (ordered by date)**:
- Collection: `books`
- Fields: `user_id` (ascending) + `created_at` (descending)
- **Purpose**: User gallery queries

**Usage by Date**:
- Collection: `usage`
- Fields: `uid` (ascending) + `date` (ascending)
- **Purpose**: Historical usage queries (not currently used)

---

## Edge Cases

### User Document Doesn't Exist
- **Scenario**: First-time user signs in
- **Action**: Create user document on first API call
- **Pattern**: Use `merge=True` to avoid overwriting

### Concurrent Book Creation
- **Scenario**: User clicks "Generate" multiple times quickly
- **Action**: Each request gets unique book_id (no collision)
- **Mitigation**: Frontend should disable button during generation

### Book Status Never Updated
- **Scenario**: Backend crashes after creating book document
- **Action**: Book stuck in "generating" status
- **Cleanup**: Implement cron job to mark old "generating" books as "failed"

---

## Error Handling

### Firestore Unavailable
- **Symptom**: `ServiceUnavailable` exception
- **Action**: Retry with exponential backoff (built into SDK)
- **User Impact**: Slower response, automatic retry

### Permission Denied
- **Symptom**: `PermissionDenied` exception
- **Action**: Check Firestore security rules
- **Fix**: Ensure backend service account has read/write access

### Document Not Found
- **Symptom**: `get()` returns `exists=False`
- **Action**: Return `None` or default value
- **User Impact**: Treated as new user or missing book

---

## Performance Requirements

- **Write Operation**: < 100ms
- **Read Operation**: < 50ms
- **Query (10 books)**: < 200ms
- **Transaction**: < 150ms

**Optimization**: Use caching for frequently accessed data (user tier)

---

## Security Rules

Current Firestore rules should enforce:

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users can read/write own profile
    match /users/{uid} {
      allow read, write: if request.auth.uid == uid;
    }
    
    // Users can read/write own books
    match /books/{bookId} {
      allow read: if request.auth.uid == resource.data.user_id;
      allow write: if request.auth.uid == request.resource.data.user_id;
    }
    
    // Usage documents managed by backend
    match /usage/{usageId} {
      allow read, write: if false;  // Backend only via Admin SDK
    }
  }
}
```

**Note**: Backend uses Admin SDK, bypassing rules. Rules protect client-side access.

---

## Dependencies

- `firebase_admin.firestore` for database access
- Firebase service account JSON for authentication
- Environment variable: `FIREBASE_SERVICE_ACCOUNT_PATH`

---

## Testing Checklist

- [ ] Create user document
- [ ] Read existing user
- [ ] Update user tier (free → premium)
- [ ] Create book document
- [ ] Query user's books (ordered by date)
- [ ] Update book status
- [ ] Test with non-existent user (returns None)
- [ ] Test concurrent book creation (no collisions)

---

## Maintenance Notes

### When to Add Indexes
- ✏️ New query patterns with multiple filters
- ✏️ Firestore console will show missing index error
- ✏️ Create via console or `firestore.indexes.json`

### When to Clean Up Old Data
- ✏️ Regularly delete old "generating" books (stuck state)
- ✏️ Archive books older than 1 year
- ✏️ Implement Cloud Function or cron job

### When to Migrate Schema
- ✏️ Adding new fields (use `merge=True` to avoid losing data)
- ✏️ Changing field types (requires migration script)
- ⚠️ Test migration on copy of production data first

---

## Related SOPs

- [Authentication](authentication.md) — Provides uid for user lookups
- [Rate Limiting](rate_limiting.md) — Reads/writes usage collection
- [API Endpoint: Generate Book](../routers/books.md) — Creates/updates book documents
