from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

class UserService:
    async def get_user_by_username(self, db: AsyncSession, username: str) -> User | None:
        """Find a user by their username."""
        stmt = select(User).where(User.username == username)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, db: AsyncSession, user_in: UserCreate) -> User:
        """Hash the password and save the new user to Postgres."""
        # Hash the password using your security.py function
        hashed_pw = get_password_hash(user_in.password)
        
        # Create the SQLAlchemy model
        db_user = User(
            username=user_in.username,
            hashed_password=hashed_pw
        )
        
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        
        return db_user

user_service = UserService()