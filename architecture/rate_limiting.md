# Rate Limiting SOP

**Layer**: 1 (Architecture)  
**Service**: `backend/app/middleware/rate_limit.py`  
**Last Updated**: 2026-02-12

---

## Goal

Enforce daily generation limits per user tier to prevent abuse and manage API costs. Only increment usage counter **after successful generation** to avoid penalizing failed attempts.

---

## Input

- `user` (FirebaseUser): Authenticated user from `get_current_user` dependency

---

## Output

- `user` (FirebaseUser): Same user object with `tier` field populated
- **Side Effect**: Raises `HTTPException` (429) if limit exceeded

---

## Process

### Function 1: `check_rate_limit` (Check Only)

**Purpose**: Verify user hasn't exceeded daily limit **before** generation starts.

**CRITICAL**: This function does NOT increment the counter. Use `increment_usage()` after success.

1. **Get Today's Date Key**:
   - Format: `YYYY-MM-DD` (UTC timezone)
   - Example: `2026-02-12`
   - **Rationale**: Ensures consistent daily reset regardless of user timezone

2. **Lookup User Tier** (with 5-minute cache):
   - Check in-memory `_tier_cache` first
   - If miss, read from Firestore: `users/{uid}.tier`
   - Default: "free" if not set
   - Cache for 300 seconds (reduces Firestore reads by ~80%)

3. **Determine Daily Limit**:
   - **Free tier**: `settings.free_daily_limit` (default: 5)
   - **Premium tier**: `settings.premium_daily_limit` (default: 10)

4. **Check Current Usage**:
   - Read from Firestore: `usage/{uid}_{date}.count`
   - Default: 0 if document doesn't exist

5. **Enforce Limit**:
   - If `count >= limit` → Raise 429 HTTPException
   - If `count < limit` → Return user with tier populated

### Function 2: `increment_usage` (Increment Only)

**Purpose**: Atomically increment usage counter **after successful generation**.

**CRITICAL**: Only call this AFTER PDF is generated and uploaded.

1. **Build Document Reference**:
   - Collection: `usage`
   - Document ID: `{uid}_{date}` (e.g., `abc123_2026-02-12`)

2. **Atomic Transaction**:
   - Read current count
   - Increment by 1
   - Write back with merge
   - **Rationale**: Prevents race conditions (multiple concurrent requests)

3. **Document Structure**:
   ```json
   {
     "count": 3,
     "uid": "abc123",
     "date": "2026-02-12"
   }
   ```

4. **Log Success**:
   - `usage_incremented uid={uid} date={date}`

---

## Error Handling

### Firestore Unavailable
- **Scenario**: Firestore connection fails during tier lookup
- **Action**: Let exception propagate (fail-closed security model)
- **User Impact**: Cannot generate book until Firestore is available

### Transaction Conflict
- **Scenario**: Multiple concurrent requests from same user
- **Action**: Firestore transaction retries automatically (up to 5 times)
- **User Impact**: Slightly slower response, transparent retry

### Tier Cache Stale
- **Scenario**: User upgrades to premium, cache still shows "free"
- **Action**: Wait up to 5 minutes for cache to expire
- **Workaround**: Clear cache manually or restart backend

---

## Edge Cases

### User Upgrades Mid-Day
- **Scenario**: User was at 5/5 (free limit), upgrades to premium
- **Current Behavior**: Limit increases to 10 immediately after cache expires
- **User Impact**: Can generate 5 more books same day

### Midnight Rollover
- **Scenario**: User generates book at 11:59 PM UTC, another at 12:01 AM UTC
- **Behavior**: Second generation is on new date, counter resets to 0
- **User Impact**: Both succeed (different days)

### Failed Generations
- **Scenario**: Content safety fails, fal.ai timeout, PDF error
- **Behavior**: `increment_usage()` never called
- **User Impact**: Failed attempts don't count toward quota ✅

### Timezone Confusion
- **Scenario**: User in PST thinks day resets at midnight PST
- **Behavior**: Resets at midnight UTC (potentially 8 hours earlier)
- **User Impact**: May seem like limit resets "early"

---

## Performance Requirements

- **Tier Lookup (cached)**: < 1ms (in-memory)
- **Tier Lookup (uncached)**: < 100ms (single Firestore read)
- **Usage Check**: < 100ms (single Firestore read)
- **Usage Increment**: < 150ms (Firestore transaction)

---

## Constants

### Cache Settings
- **TTL**: 300 seconds (5 minutes)
- **Max Size**: 10,000 users
- **Rationale**: Balance freshness vs Firestore cost

### Daily Limits (from Settings)
- `settings.free_daily_limit`: Default 5
- `settings.premium_daily_limit`: Default 10
- **Configuration**: Set in `.env` file

---

## Dependencies

- `firebase_admin.firestore` for persistence
- `cachetools.TTLCache` for tier caching
- `app.config.get_settings()` for limit values
- `app.middleware.auth.get_current_user` for user context

---

## Testing Checklist

- [ ] Test free user at 0/5, 4/5, and 5/5 (pass/pass/block)
- [ ] Test premium user at 0/10, 9/10, and 10/10
- [ ] Test usage increment is atomic (concurrent requests)
- [ ] Test failed generation doesn't increment counter
- [ ] Test tier cache expiration (5 minutes)
- [ ] Test midnight UTC rollover (new day, counter resets)
- [ ] Test upgrade from free to premium mid-day

---

## Integration Workflow

### Correct Usage Pattern

```python
@router.post("/books/generate")
async def generate_book(
    request: BookRequest,
    user: FirebaseUser = Depends(check_rate_limit),  # ← Check FIRST
):
    # Generate book (content safety, images, PDF)
    book_id = await create_book(request, user.uid)
    
    # Only increment if generation succeeded
    increment_usage(user.uid)  # ← Increment at END
    
    return BookResponse(book_id=book_id)
```

### ❌ INCORRECT: Increment Before Success

```python
# DON'T DO THIS
async def generate_book(...):
    increment_usage(user.uid)  # Too early!
    result = await create_book()  # If this fails, user loses quota
```

---

## Maintenance Notes

### When to Adjust Limits
- ✏️ User feedback: Limits too restrictive
- ✏️ API cost analysis: Need to reduce usage
- ✏️ Update `.env` values:
  - `FREE_DAILY_LIMIT=10`
  - `PREMIUM_DAILY_LIMIT=20`

### When to Clear Cache
- ✏️ User reports tier not updating
- ✏️ Mass tier migrations
- ⚠️ Requires backend restart to clear in-memory cache

### When to Implement Hourly Limits
- ✏️ If daily limits insufficient to prevent burst abuse
- ✏️ Add `hourly` cache key in addition to `daily`
- ⚠️ Increases Firestore reads/writes

---

## Monitoring

### Key Metrics
- **429 Rate Limit Errors**: Track by tier (free vs premium)
- **Average Usage Per User**: Identify power users
- **Cache Hit Rate**: Should be > 80% (if lower, increase TTL)

### Alerts
- ⚠️ Alert if 429 errors > 10% of total requests
- ⚠️ Alert if Firestore transaction failures > 1%

---

## Related SOPs

- [Authentication](authentication.md) — Provides user context
- [API Endpoint: Generate Book](../routers/books.md) — Implements check + increment pattern
- [Firebase Database](firebase_db.md) — Storage for tier and usage data
