from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, SessionDep
from app.schemas.auth import GoogleLoginIn, LoginIn, RegisterIn, TokenOut, UserOut
from app.services.auth_service import (
    AuthService,
    EmailAlreadyExists,
    InvalidCredentials,
    InvalidGoogleToken,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterIn, session: SessionDep) -> TokenOut:
    try:
        token = AuthService(session).register(payload.email, payload.password)
    except EmailAlreadyExists as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    return TokenOut(access_token=token)


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, session: SessionDep) -> TokenOut:
    try:
        token = AuthService(session).login(payload.email, payload.password)
    except InvalidCredentials as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
    return TokenOut(access_token=token)


@router.post("/google", response_model=TokenOut)
def login_google(payload: GoogleLoginIn, session: SessionDep) -> TokenOut:
    try:
        token = AuthService(session).login_with_google(payload.id_token)
    except InvalidGoogleToken as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)
