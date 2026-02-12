# Authentication SOP

**Layer**: 1 (Architecture)  
**Service**: `backend/app/middleware/auth.py`  
**Last Updated**: 2026-02-12

---

## Goal

Verify Firebase ID tokens from authenticated users and provide type-safe user context to protected endpoints. Support both required and optional authentication.

---

## Input

- `credentials` (HTTPAuthorizationCredentials): Bearer token from `Authorization` header
  - Format: `Authorization: Bearer <firebase_id_token>`

---

## Output

- `FirebaseUser` object with typed fields:
  - `uid` (string): Unique Firebase user ID
  - `email` (string): User's email address
  - `display_name` (string | None): User's display name
  - `tier` (string): Subscription tier ("free" or "premium")

---

## Process

### Function 1: `get_current_user` (Required Auth)

**Purpose**: Enforce authentication on protected endpoints.

1. **Extract Token**:
   - Get Bearer token from `Authorization` header
   - FastAPI's `HTTPBearer` dependency handles extraction

2. **Verify with Firebase Admin SDK**:
   - Call `firebase_auth.verify_id_token(token)`
   - Returns decoded token payload with claims

3. **Create User Object**:
   - Parse decoded token into `FirebaseUser` model
   - Extract: `uid`, `email`, `name` (optional)
   - Log: `auth_success uid={uid}` for observability

4. **Return User**:
   - Type-safe `FirebaseUser` object
   - Available as dependency in endpoint handlers

### Function 2: `get_optional_user` (Optional Auth)

**Purpose**: Allow endpoints to check auth status without requiring it.

1. **Check for Credentials**:
   - `HTTPBearer(auto_error=False)` returns None if header missing
   - If None → Return None (not authenticated)

2. **Attempt Verification**:
   - Try `verify_id_token()`
   - On success → Return `FirebaseUser`
   - On failure → Return None (don't raise exception)

3. **Use Case**:
   - Public endpoints with premium features
   - Anonymous analytics with optional user context

---

## Error Handling

### Expired Token
- **Exception**: `firebase_auth.ExpiredIdTokenError`
- **Response**: 401 Unauthorized
- **Message**: "Token has expired. Please sign in again."
- **Frontend Action**: Trigger re-authentication flow

### Invalid Token
- **Exception**: `firebase_auth.InvalidIdTokenError`
- **Response**: 401 Unauthorized
- **Message**: "Invalid authentication token."
- **Possible Causes**: Malformed JWT, wrong project, revoked token

### Generic Auth Failure
- **Exception**: Any other exception
- **Logging**: `logger.exception("auth_failed")` with full stack trace
- **Response**: 401 Unauthorized
- **Message**: "Could not validate credentials."
- **Security**: Never expose internal error details to client

### Missing Authorization Header
- **Scenario**: Request without `Authorization` header
- **Action**: FastAPI's `HTTPBearer` returns 403 Forbidden
- **Message**: "Not authenticated"

---

## Edge Cases

### Token from Different Firebase Project
- **Scenario**: User has valid Firebase token from another app
- **Action**: `verify_id_token()` validates project ID
- **Result**: Invalid token error (401)

### Revoked Token
- **Scenario**: User signs out on another device
- **Action**: Firebase Admin SDK validates against revocation list
- **Result**: Invalid token error (401)

### Clock Skew
- **Scenario**: Server time significantly different from token issue time
- **Action**: Firebase SDK allows 5-minute clock skew tolerance
- **Result**: Usually succeeds; expired if beyond tolerance

---

## Performance Requirements

- **Token Verification**: < 100ms (local verification, no API call)
- **Caching**: Firebase Admin SDK caches public keys (no network hit per request)
- **Concurrency**: Thread-safe for async endpoints

---

## Security Considerations

### Token Storage
- ✅ **Client**: Store token in memory or secure storage (not localStorage)
- ❌ **Never**: Log full token contents (only log uid)
- ❌ **Never**: Include token in error messages

### Token Transmission
- ✅ **HTTPS Only**: Never send tokens over HTTP
- ✅ **Header Only**: Use `Authorization` header, not query params
- ❌ **Never**: Include token in URL (logged in access logs)

### Token Validation
- ✅ **Always Verify**: Even if token looks valid, always call `verify_id_token()`
- ❌ **Never Trust**: Don't just decode JWT without verification
- ✅ **Check Expiration**: Firebase SDK handles this automatically

---

## Dependencies

- `firebase_admin.auth` for token verification
- `fastapi.security.HTTPBearer` for token extraction
- `app.models.user.FirebaseUser` for type safety

---

## Testing Checklist

- [ ] Test valid token from authenticated user
- [ ] Test expired token (401 response)
- [ ] Test invalid token (401 response)
- [ ] Test missing Authorization header (403 response)
- [ ] Test token from different Firebase project (401 response)
- [ ] Test optional auth with missing credentials (returns None)
- [ ] Test optional auth with valid credentials (returns user)

---

## Integration

### Frontend Flow

1. **User Signs In**:
   - Firebase Auth SDK: `signInWithPopup(googleProvider)`
   - Receive Firebase ID token

2. **Token Refresh**:
   - Call `auth.currentUser.getIdToken(forceRefresh=true)`
   - Attach to every API request

3. **Axios Interceptor** (Frontend):
   ```javascript
   axios.interceptors.request.use(async (config) => {
     const token = await auth.currentUser?.getIdToken()
     config.headers.Authorization = `Bearer ${token}`
     return config
   })
   ```

4. **Backend Verification**:
   - `get_current_user` dependency extracts and verifies token

### Usage in Endpoints

**Required Auth**:
```python
@router.post("/books/generate")
async def generate_book(
    user: FirebaseUser = Depends(get_current_user)  # Enforced
):
    # user.uid, user.email available here
```

**Optional Auth**:
```python
@router.get("/public/gallery")
async def public_gallery(
    user: FirebaseUser | None = Depends(get_optional_user)
):
    # user is None if not authenticated
    # user has data if authenticated
```

---

## Maintenance Notes

### When Firebase Config Changes
- ✏️ Update service account JSON path in `backend/app/main.py`
- ✏️ Restart backend to reload credentials
- ⚠️ Never commit service account JSON to git

### When to Add Custom Claims
- ✏️ Need additional user metadata in token
- ✏️ Set via Firebase Admin SDK: `auth.set_custom_user_claims(uid, {"tier": "premium"})`
- ✏️ Access in `decoded` token payload

### When to Implement Token Revocation
- ✏️ User reports account compromise
- ✏️ Call `firebase_auth.revoke_refresh_tokens(uid)`
- ✏️ User must sign in again to get new token

---

## Related SOPs

- [Rate Limiting](rate_limiting.md) — Uses authenticated user context
- [API Endpoint: Auth](../routers/auth.md) — Login endpoint
- [Frontend: Auth Store](../frontend/stores/auth.md) — Token management
