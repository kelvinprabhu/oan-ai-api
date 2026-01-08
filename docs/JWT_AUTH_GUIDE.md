# JWT Authentication Guide

This document details the **JSON Web Token (JWT)** authentication mechanism implemented in `app/auth/jwt_auth.py`.

---

## 1. Overview

The backend is designed to be a **Resource Server**. It does **not** issue tokens (Signin/Signup is handled by an external Identity Provider, likely a separate Mobile App or Auth Service).

Instead, this API **verifies** tokens signed by that external provider using **Asymmetric Encryption (RS256)**.

---

## 2. Configuration (`app/config.py`)

The system uses an **RSA Public Key** to verify the signature of incoming tokens.

| Env Variable | Default | Description |
| :--- | :--- | :--- |
| `JWT_ALGORITHM` | `RS256` | The algorithm used for signing (Asymmetric). |
| `JWT_PUBLIC_KEY_PATH` | `jwt_public_key.pem` | Path to the PEM files containing the Public Key. |
| `ENVIRONMENT` | `production` | Controls bypass logic. |

```python
# app/config.py excerpt
class Settings(BaseSettings):
    jwt_algorithm: str = "RS256"
    jwt_public_key_path: str = os.getenv("JWT_PUBLIC_KEY_PATH", "jwt_public_key.pem")
```

---

## 3. Implementation Details (`app/auth/jwt_auth.py`)

### A. Development Bypass
To simplify local development, the system **bypasses authentication** if `ENVIRONMENT=development`.

```python
# app/auth/jwt_auth.py

async def get_current_user(token: str | None = Depends(oauth2_scheme)):
    # 1. Check Support Mode
    if settings.environment == "development":
        logger.info("Development environment detected - bypassing authentication")
        return "development_user"
```
* **Warning:** Ensure `ENVIRONMENT` is set to `production` in live deployments, otherwise the API is open to the world.

### B. Production Verification (RS256)
In production, the system performs strict validation:

1.  **Extract Token:** Uses `OAuth2PasswordBearer` to strip the `Bearer <token>` prefix.
2.  **Load Key:** Reads the `jwt_public_key.pem` file at startup.
3.  **Decode & Verify:**
    ```python
    decoded_token = jwt.decode(
        token,
        public_key,
        algorithms=[settings.jwt_algorithm], # RS256
        options={
            "verify_signature": True,
            "verify_aud": False, # Audience check disabled
            "verify_iss": False  # Issuer check disabled
        }
    )
    ```
4.  **Identity Extraction:** It looks for the `mobile` field in the payload as the User ID.

---

## 4. How to Generate Keys (For Testing)

If you are setting this up locally or need to generate new keys for your Identity Provider:

```bash
# 1. Generate Private Key (Keep this SAFE, used by the issuer)
openssl genrsa -out private.pem 2048

# 2. Extract Public Key (Put this in the API root as jwt_public_key.pem)
openssl rsa -in private.pem -outform PEM -pubout -out jwt_public_key.pem
```

---

## 5. Middleware / Dependency Usage

This logic is applied via **FastAPI Dependencies**. It is not global middleware; it must be explicitly included in routers.

**Example Usage (`app/routers/chat.py` or similar):**
```python
from app.auth.jwt_auth import get_current_user

@router.post("/chat")
async def chat(
    request: ChatRequest, 
    user_mobile: str = Depends(get_current_user) # <--- Enforces Auth
):
    # If we get here, token is valid (or we are in dev mode)
    pass
```

---

## 6. Error Handling

The system returns standard HTTP 401 errors:

| Exception | HTTP Code | Message |
| :--- | :--- | :--- |
| `ExpiredSignatureError` | 401 | "Token has expired" |
| `InvalidTokenError` | 401 | "Invalid token: <details>" |
| `Exception` | 401 | "Token verification failed" |

---

## 7. Sample Token Payload
The API expects a payload similar to:
```json
{
  "mobile": "9876543210",
  "exp": 1735689600,
  "iat": 1704067200
  // ... other standard claims
}
```
*Note: The `mobile` field is currently hardcoded as the user identifier in `jwt_auth.py`.*
