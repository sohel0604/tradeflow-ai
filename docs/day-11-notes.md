# Day 11 Notes — August 14, 2026
## Topic: User & Auth Models — Foreign Keys, Relationships, Security

---

## What we built today

4 models that form the entire auth system:

```
users               ← every person who uses TradeFlow AI
  ↓ one-to-many
auth_tokens         ← refresh tokens (revocable JWTs)
api_keys            ← programmatic access (Business tier)
broker_credentials  ← encrypted broker API keys
```

---

## Foreign Keys — linking tables together

```python
class AuthToken(Base):
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
```

`ForeignKey("users.id")` creates a link:
- Every `auth_tokens` row must reference a valid `users.id`
- You can't create an AuthToken for a user that doesn't exist
- PostgreSQL enforces this automatically

`ondelete="CASCADE"` — what happens when the User is deleted:
- **CASCADE**: automatically delete all their tokens too ✅
- **RESTRICT**: refuse to delete the User if they have tokens ❌
- **SET NULL**: set user_id to NULL (used for optional references)

We use CASCADE for tokens and keys — if a user deletes their account,
all their data goes with them (GDPR compliance).

---

## Relationships — Python-level navigation

```python
class User(Base):
    auth_tokens = relationship(
        "AuthToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

class AuthToken(Base):
    user = relationship("User", back_populates="auth_tokens")
```

This lets you navigate between objects in Python:

```python
# Get all tokens for a user (SQLAlchemy runs SELECT automatically)
user = await session.get(User, user_id)
tokens = user.auth_tokens    # runs: SELECT * FROM auth_tokens WHERE user_id=...

# Get the user from a token
token = await session.get(AuthToken, token_id)
owner = token.user           # runs: SELECT * FROM users WHERE id=...
```

`back_populates="user"` links both sides together.
Change one side → other side updates automatically.

`cascade="all, delete-orphan"` — Python-level cascade:
If you call `session.delete(user)`, SQLAlchemy also deletes
all their tokens, keys, and credentials without needing
a separate delete call.

---

## Why passwords must be hashed

```python
hashed_password = Column(String(255), nullable=False)
```

**Never stored:** `"mypassword123"`
**Always stored:** `"$2b$12$K7s.eHqBQrO9v8Tl7N4Guu8zqEXT.9CZhPiZBWBqNBWB..."`

### Why?
If your database is ever breached:
- Plaintext passwords → attacker has immediate access to everything
- bcrypt hashes → attacker has useless random-looking strings

### How bcrypt works
```python
import bcrypt

# On registration — hash the password
hashed = bcrypt.hashpw("mypassword123".encode(), bcrypt.gensalt(rounds=12))
# $2b$12$randomsalt...hashedvalue — always different even for same password

# On login — verify the password
is_valid = bcrypt.checkpw("mypassword123".encode(), hashed)
# True ✅ — constant time comparison (no timing attacks)
```

`rounds=12` means bcrypt runs 2^12 = 4096 iterations.
This makes brute-force attacks take minutes per guess, not milliseconds.

---

## AuthToken — refresh token security

```python
token_hash = Column(String(255), unique=True, index=True)
```

We store the HASH of the refresh token, not the token itself.

Why?
- Refresh token string: `"a1b2c3d4e5f6..."` → gives full access if leaked
- Hash: `"sha256:8f4a2b1c..."` → useless without the original token

Flow:
```
User logs in
    ↓
Generate: token = secrets.token_urlsafe(32)
Hash it:  token_hash = hashlib.sha256(token.encode()).hexdigest()
Store:    INSERT INTO auth_tokens (token_hash=..., expires_at=...)
Return:   token → user (they store this in their browser)

User refreshes
    ↓
Receive: token from browser
Hash it: token_hash = hashlib.sha256(token.encode()).hexdigest()
Find:    SELECT * FROM auth_tokens WHERE token_hash=...
If found + not revoked + not expired → issue new access token
```

---

## ApiKey — show once, store hash

```python
key_hash = Column(String(255), nullable=False, unique=True)
last_used_at = Column(DateTime(timezone=True), nullable=True)
```

Flow:
```
User clicks "Generate API Key"
    ↓
Generate: key = secrets.token_hex(32)
          # = "a1b2c3d4e5f6g7h8..." (64 chars)
Hash it:  key_hash = bcrypt.hash(key)
Store:    INSERT INTO api_keys (key_hash=..., name="My Bot")
Return:   key → show in a modal ONCE — user must copy it
          We NEVER show this again

User makes API request with header: X-API-Key: a1b2c3d4e5f6...
    ↓
Find all active keys for the user
For each: bcrypt.verify(incoming_key, stored_hash)
If match → authenticated, update last_used_at
```

---

## BrokerCredential — AES-256 encryption

```python
encrypted_api_key = Column(Text, nullable=False)
encrypted_access_token = Column(Text, nullable=False)
```

We use Python's `cryptography` library with Fernet (symmetric encryption):

```python
from cryptography.fernet import Fernet

# ENCRYPTION_KEY is in .env — never in DB
# Generate once: python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
key = Fernet(settings.encryption_key.encode())

# Encrypt before storing
ciphertext = key.encrypt("my_api_key_here".encode()).decode()
# Store this in encrypted_api_key column

# Decrypt when reading
plaintext = key.decrypt(ciphertext.encode()).decode()
# "my_api_key_here" — only works with the correct encryption key
```

If someone steals your database:
- They see: `"gAAAAABm...long_random_string..."` (ciphertext)
- Without the encryption key (in your `.env`), it's unreadable

API response to frontend:
```json
{"broker": "dhan", "linked": true}
```
NEVER return the credentials themselves.

---

## One-to-many relationship pattern

```
One User → Many AuthTokens
One User → Many ApiKeys
One User → Many BrokerCredentials
```

This is the most common database relationship pattern.
In SQL terms:
- The "many" side (AuthToken) holds the foreign key
- The "one" side (User) has the relationship() definition

```sql
-- auth_tokens.user_id → references → users.id
-- One user can have many rows in auth_tokens
-- Each auth_tokens row belongs to exactly one user
```

---

## Tomorrow — Day 12
Write the business logic models:
Signal, BacktestResult, UserWatchlist, Subscription,
UserStrategyConfig, PaperPortfolio, PaperPosition, PaperTrade.
These are all the domain-specific tables for TradeFlow's core features.
