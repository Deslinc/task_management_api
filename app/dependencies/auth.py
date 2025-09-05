from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
import firebase_admin
from firebase_admin import auth as fb_auth, credentials
from app.db.session import get_db
from app.models.user import User
from app.core.config import get_settings
import os

# Initialize Firebase Admin (idempotent)
if not firebase_admin._apps:
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if not creds_path or not os.path.exists(creds_path):
        raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS is not set or the file doesn't exist.")
    cred = credentials.Certificate(creds_path)
    firebase_admin.initialize_app(cred)

def _extract_bearer(authorization: Optional[str]) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if parts[0].lower() != "bearer" or len(parts) != 2:
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    return parts[1]

def get_current_user(
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None),
) -> User:
    token = _extract_bearer(authorization)
    try:
        decoded = fb_auth.verify_id_token(token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid or expired token: {e}")

    uid = decoded.get("uid")
    email = decoded.get("email")
    name = decoded.get("name")

    if not uid:
        raise HTTPException(status_code=401, detail="Token missing uid claim")

    # Ensure a local SQL user exists (auto-provision)
    user = db.query(User).filter(User.firebase_uid == uid).first()
    if not user:
        user = User(firebase_uid=uid, email=email or f"{uid}@unknown.local", display_name=name)
        db.add(user)
        db.commit()
        db.refresh(user)

    return user
