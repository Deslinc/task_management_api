from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
import requests
from app.core.config import get_settings
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.models.user import User
from firebase_admin import auth as fb_auth

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

IDENTITY_BASE = "https://identitytoolkit.googleapis.com/v1"

class SignupBody(BaseModel):
    email: EmailStr
    password: str
    display_name: str | None = None

class LoginBody(BaseModel):
    email: EmailStr
    password: str

def _idtoolkit_url(path: str) -> str:
    if not settings.firebase_api_key:
        raise HTTPException(status_code=500, detail="FIREBASE_API_KEY not configured")
    return f"{IDENTITY_BASE}/{path}?key={settings.firebase_api_key}"

@router.post("/signup")
def signup(payload: SignupBody, db: Session = Depends(get_db)):
    # 1) Create account via Identity Toolkit
    resp = requests.post(_idtoolkit_url("accounts:signUp"), json={
        "email": payload.email,
        "password": payload.password,
        "returnSecureToken": True
    })
    if not resp.ok:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise HTTPException(status_code=400, detail=detail)

    data = resp.json()  # idToken, email, refreshToken, expiresIn, localId
    id_token = data.get("idToken")
    if not id_token:
        raise HTTPException(status_code=500, detail="No idToken returned from Firebase")

    # 2) Optionally set display name
    if payload.display_name:
        try:
            fb_auth.update_user(data["localId"], display_name=payload.display_name)
        except Exception:
            pass

    # 3) Upsert local SQL user
    uid = data.get("localId")
    if uid:
        user = db.query(User).filter(User.firebase_uid == uid).first()
        if not user:
            user = User(firebase_uid=uid, email=payload.email, display_name=payload.display_name)
            db.add(user); db.commit(); db.refresh(user)

    return {
        "message": "Signup successful",
        "id_token": id_token,
        "refresh_token": data.get("refreshToken"),
        "expires_in": data.get("expiresIn"),
        "uid": data.get("localId"),
        "email": data.get("email")
    }

@router.post("/login")
def login(payload: LoginBody, db: Session = Depends(get_db)):
    resp = requests.post(_idtoolkit_url("accounts:signInWithPassword"), json={
        "email": payload.email,
        "password": payload.password,
        "returnSecureToken": True
    })
    if not resp.ok:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise HTTPException(status_code=400, detail=detail)

    data = resp.json()
    uid = data.get("localId")
    # Ensure user exists locally
    if uid:
        user = db.query(User).filter(User.firebase_uid == uid).first()
        if not user:
            user = User(firebase_uid=uid, email=data.get("email"))
            db.add(user); db.commit(); db.refresh(user)

    return {
        "message": "Login successful",
        "id_token": data.get("idToken"),
        "refresh_token": data.get("refreshToken"),
        "expires_in": data.get("expiresIn"),
        "uid": data.get("localId"),
        "email": data.get("email")
    }

@router.get("/me")
def me(current_user: User = Depends(__import__("app.dependencies.auth", fromlist=["get_current_user"]).get_current_user)):
    return {
        "id": current_user.id,
        "firebase_uid": current_user.firebase_uid,
        "email": current_user.email,
        "display_name": current_user.display_name,
        "message": "Authenticated"
    }
