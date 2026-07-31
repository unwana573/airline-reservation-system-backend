from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import get_db
from api.core.deps import get_current_user
from api.models import User
from api.schemas.auth import (
    ForgotPasswordRequest,
    GoogleOAuthRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenPair,
    UserLogin,
    UserOut,
    UserRegister,
)
from api.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=201)
async def register(payload: UserRegister, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register_user(db, payload)
    return user


@router.post("/login", response_model=TokenPair)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_user(db, payload)
    return auth_service.issue_token_pair(user, remember_me=payload.remember_me)


@router.post("/token", response_model=TokenPair, include_in_schema=False)
async def login_for_swagger(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """Powers the Swagger 'Authorize' popup only — enter email in the
    'username' field and your password in 'password'. The real frontend
    should call POST /auth/login (JSON) instead of this form-based route."""
    user = await auth_service.authenticate_user(
        db, UserLogin(email=form_data.username, password=form_data.password)
    )
    return auth_service.issue_token_pair(user)


@router.post("/oauth/google", response_model=TokenPair)
async def continue_with_google(payload: GoogleOAuthRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.authenticate_with_google(db, payload.id_token)
    return auth_service.issue_token_pair(user, remember_me=True)


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.refresh_access_token(db, payload.refresh_token)


@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password")
async def forgot_password(payload: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    reset_token = await auth_service.request_password_reset(db, payload.email)
    # TODO (Phase 4 — notifications module): email reset_token to the user via a reset link
    # instead of returning it directly. Returned here only so the flow is testable now.
    if reset_token:
        return {"message": "If that email is registered, a reset link has been sent.", "dev_reset_token": reset_token}
    return {"message": "If that email is registered, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(payload: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    await auth_service.reset_password(db, payload.token, payload.new_password)
    return {"message": "Password updated successfully."}