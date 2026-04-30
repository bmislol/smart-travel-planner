from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm

from app.db.session import get_db
from app.services.user_service import UserService
from app.core.security import verify_password, create_access_token
from app.schemas.user import UserCreate, UserRead # Import the schemas!

router = APIRouter(tags=["Authentication"])

@router.post("/signup", response_model=UserRead)
async def signup(
    user_in: UserCreate, # Forces FastAPI to use a secure JSON body
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService()
    # Check if user already exists
    existing_user = await user_service.get_user_by_username(db, user_in.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Notice we pass the properties from the Pydantic model
    return await user_service.create_user(db, user_in)

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