from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
from app.db.session import get_db
from app.services.user_service import UserService
from app.core.security import verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/signup")
async def signup(
    username: str, 
    password: str, 
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService()
    # Check if user already exists
    existing_user = await user_service.get_user_by_username(db, username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    return await user_service.create_user(db, username, password)

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService()
    user = await user_service.get_user_by_username(db, form_data.username)
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    access_token = create_access_token(subject=user.username)
    return {"access_token": access_token, "token_type": "bearer"}