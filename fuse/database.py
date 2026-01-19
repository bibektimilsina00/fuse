from fuse.auth.crud_user import user as user_crud
from fuse.auth.models import User
from fuse.auth.schemas import UserCreate
from fuse.config import settings
from sqlmodel import Session, create_engine, select

engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))


# make sure all SQLModel models are imported (app.models) before initializing DB
# otherwise, SQLModel might fail to initialize relationships properly
# for more details: https://github.com/fastapi/full-stack-fastapi-template/issues/28


def init_db(session: Session) -> None:
    # Create tables if they don't exist (useful for SQLite)
    # For PostgreSQL in production, use Alembic migrations instead
    from fuse import models  # Import all models to register them
    from sqlmodel import SQLModel

    SQLModel.metadata.create_all(engine)

    user = session.exec(
        select(User).where(User.email == settings.FIRST_USER_EMAIL)
    ).first()
    if not user:
        user_in = UserCreate(
            email=settings.FIRST_USER_EMAIL,
            password=settings.FIRST_USER_PASSWORD,
        )
        user = user_crud.create(session=session, obj_in=user_in)
