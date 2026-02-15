# Security Improvements: Household Invites

## Problem: Insecure Invite Links

**Before:**
- Invite links used incrementing household IDs: `/household/join/1`, `/household/join/2`, etc.
- **Vulnerability:** Anyone could brute-force guess household IDs
- **Attack:** Attacker tries `/household/join/1`, `/household/join/2`, etc. until finding valid households
- **Risk:** Unauthorized access, data privacy violation, household takeover

## Solution: Cryptographic Token-Based Invites

**After:**
- Invite links use random, unguessable tokens: `/household/join/a7f3d9c2-8e1b-4a5f-9c3d-2b8e1f4a5c7d`
- Tokens expire automatically (7 days)
- Tokens are one-time use only
- All invites are tracked and revocable

### Security Features

#### 1. **Cryptographic Randomness**
```python
token = secrets.token_urlsafe(32)  # 256 bits of entropy
```
- Uses Python's `secrets` module (cryptographically secure)
- 32 bytes = 2^256 possible combinations
- **Impossible to guess:** Would take billions of years to brute-force
- **URL-safe:** Encoded for use in URLs

#### 2. **Automatic Expiration**
```python
expires_at = datetime.utcnow() + timedelta(days=7)
```
- Invites expire after 7 days
- If link is leaked, it becomes useless after 7 days
- Reduces attack window significantly

#### 3. **One-Time Use**
```python
invite.accepted = True
invite.accepted_by = current_user.id
```
- Once someone joins using an invite, it's marked as used
- Same link cannot be used again
- Prevents reuse if link is intercepted

#### 4. **Tracking & Revocation**
```python
accepted_by = db.Column(db.Integer, db.ForeignKey('user.id'))
accepted_at = db.Column(db.DateTime)
```
- Household creator can see:
  - Who created each invite
  - When it was created
  - Who accepted it (if anyone)
  - When it expires
- Household creator can revoke unused invites immediately

### Database Model

```python
class HouseholdInvite(db.Model):
    id                  # Primary key
    household_id        # Which household this invites to
    token              # Random 256-bit token (URL-safe)
    created_by         # Which user created this invite
    created_at         # When invite was created
    expires_at         # 7 days from creation
    accepted           # Has it been used?
    accepted_by        # Which user used it?
    accepted_at        # When it was used?
```

## Comparison

| Aspect | Before | After |
|--------|--------|-------|
| **Format** | Incrementing ID (1, 2, 3...) | Random token (256-bit) |
| **Guessability** | ✗ Easy to guess | ✓ Impossible (2^256 options) |
| **Expiration** | Never | 7 days |
| **One-time use** | No | Yes |
| **Trackable** | No | Yes (who, when, accepted by whom) |
| **Revocable** | No | Yes |
| **Brute-forceable** | Yes (try IDs sequentially) | No (random tokens) |

## Implementation Details

### New Endpoints

1. **`/household/invite`** (GET/POST)
   - Shows household creator list of active invites
   - Generate button creates new random token
   - Displays invite URLs with expiration times
   - Shows revoke button for unused invites

2. **`/household/join/<token>`** (GET)
   - Shows confirmation page with household details
   - Displays expiration time
   - Validates token before showing anything

3. **`/household/join/<token>`** (POST)
   - Confirms household membership
   - Marks invite as accepted
   - Records who accepted and when
   - Prevents accidental joins

4. **`/household/invite/<token>/revoke`** (POST)
   - Only accessible to household creator
   - Deletes unused invites
   - Prevents revocation of already-accepted invites

## Attack Scenarios: Before vs After

### Scenario 1: Brute Force Attack

**Before:**
```
Attacker: /household/join/1 → "Invalid"
Attacker: /household/join/2 → "Invalid"
Attacker: /household/join/3 → "Invalid"
...
Attacker: /household/join/42 → JOINS household with 42 IDs attempted
```

**After:**
```
Attacker: /household/join/random123 → "Invalid token"
Attacker: /household/join/random456 → "Invalid token"
... (would need 2^256 attempts, literally impossible)
```

### Scenario 2: Link Interception (via email)

**Before:**
```
User: "Click this link: /household/join/5"
Attacker intercepts email and joins household 5
Household 5 is now compromised
```

**After:**
```
User: "Click this link: /household/join/a7f3d9c2-8e1b...xyz"
Attacker intercepts email
If attacker clicks link:
  - Must click within 7 days
  - Only works one time
  - Household creator sees "attacker joined" and can kick them out
  - Can revoke the link if needed
Household creator is alerted and can act
```

### Scenario 3: Link Shared Publicly (accident)

**Before:**
```
User accidentally posts to forum: "My invite code: 5"
Attacker joins household 5 permanently
No way to track who joined or revoke the invite
```

**After:**
```
User accidentally posts to forum: "My invite link: /household/join/a7f3d9c2..."
Link expires in 7 days (even if still public)
Link is one-time use (anyone who uses it is recorded)
Household creator sees unexpected person joined
Can kick them out immediately
Can revoke the link
```

## Migration Required

You'll need to create a database migration:

```bash
export FLASK_APP=run.py
flask db migrate -m "Add HouseholdInvite model for secure invites"
flask db upgrade
```

## Next Steps

1. **Create migration:**
   ```bash
   flask db migrate -m "Add HouseholdInvite model for secure invites"
   ```

2. **Review migration file** (check it looks right)

3. **Apply migration:**
   - Development: `flask db upgrade`
   - Production: SSH to server and run `flask db upgrade`

4. **Update invite template** to show the new secure token format

5. **Update any documentation** linking to old invite format

## Best Practices Going Forward

✅ **DO:**
- Share full invite links (with token), not just household IDs
- Set expiration for invites (7 days is reasonable)
- Log who joins and when
- Let users revoke unused invites
- Alert household creator when someone joins

❌ **DON'T:**
- Use incrementing IDs for anything security-sensitive
- Put household IDs directly in URLs
- Allow unlimited invites from a single token
- Ignore who joins your household
- Forget to expire invites

## Additional Security Considerations

For even more security, consider:

1. **Rate limiting:** Limit failed join attempts per IP
2. **Email confirmation:** Send email when someone joins your household
3. **IP logging:** Track which IPs joined, alert on suspicious activity
4. **Invite quotas:** Limit how many active invites per household
5. **Security key option:** For very sensitive households, require 2FA on join

This implementation provides strong security while remaining user-friendly and maintainable. 🔒
