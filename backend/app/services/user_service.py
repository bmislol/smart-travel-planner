from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import User
from app.core.security import get_password_hash

class UserService:
    async def get_user_by_username(self, db: AsyncSession, username: str):
        """Standard SELECT operation."""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def create_user(self, db: AsyncSession, username: str, password: str):
        """Standard INSERT operation."""
        hashed_password = get_password_hash(password)
        db_user = User(username=username, hashed_password=hashed_password)
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user