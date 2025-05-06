from fastapi import APIRouter, status, Depends, HTTPException
from schemas.auth import UserCreate, UserResponse, TokenCreate, TokenResponse
from models.auth import User, Token
from typing import Annotated
from sqlalchemy.orm import Session
from postgres.database import get_db
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from jose.exceptions import JWTError
import logging

SECRET_KEY = "96ff43373544ebcc0035be313c7ad4bd5e1c4a77cb62d5c5287123f9cfb62537"
ALGORITHM = "HS256"

# create router
router = APIRouter(prefix="/auth", tags=["auth"])
db_dependency = Annotated[Session, Depends(get_db)]

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str, db):
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            return False
        if not verify_password(password, user.hashed_password):
            return False

        return user
    except Exception as e:
        logging.error("Could not authenticate user: {}".format(e))


def create_access_token(username: str, user_id: int, expires_delta: timedelta):
    try:
        encode = {"sub": username, "id": user_id}
        expires = datetime.now() + expires_delta
        encode.update({"exp": expires})

        return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)
    except Exception as e:
        logging.error("Could not create access token: {}".format(e))


def verify_refresh_token(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("id")

        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user",
            )

        return {"username": username, "id": user_id}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user"
        )


def create_token_logs(
    user_id: str,
    access_token: str,
    refresh_token: str,
    access_token_expiry: str,
    refresh_token_expiry: str,
    db: db_dependency,
):
    try:
        token_info = Token(
            user_id=user_id,
            access_token=access_token,
            refresh_token=refresh_token,
            access_token_expiry=access_token_expiry,
            refresh_token_expiry=refresh_token_expiry,
            # token_type="bearer"
        )
        db.add(token_info)
        db.commit()

        return
    except Exception as e:
        logging.error("Something went wrong in create_token_logs method: {}".format(e))

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="token logs entry not created in db",
        )


def get_current_user(
    token: str = Depends(oauth2_bearer), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")

        if username is None or user_id is None:
            raise credentials_exception

        user = db.query(User).filter(User.id == user_id).first()

        # user = db.query(User).filter(User.id == user_id).first()
        # if user is None or user.role != "admin":  # Example role check
        #     raise credentials_exception
        
        if user is None:
            raise credentials_exception

        return user
    except JWTError:
        raise credentials_exception


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db: db_dependency):
    # Check if user exist
    user_exist = db.query(User).filter(User.username == user.username).first()
    if user_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exist",
        )

    # Add new user
    hashed_pw = hash_password(user.password)
    db_user = User(
        username=user.username, hashed_password=hashed_pw
    )  # models.UserLogin(**user.dict())

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        logging.error("Database error during user registration: {}".format(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User could not be created",
        )

    return {"message": "User created successfully"}


@router.post("/login", status_code=status.HTTP_200_OK)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate user"
        )

    access_token = create_access_token(user.username, user.id, timedelta(minutes=20))
    refresh_token = create_access_token(
        user.username, user.id, timedelta(days=7)
    )  # Only time will be different

    # Create token log entry in db
    create_token_logs(
        user_id=user.id,
        access_token=access_token,
        refresh_token=refresh_token,
        access_token_expiry=str(datetime.now() + timedelta(minutes=20)),
        refresh_token_expiry=str(datetime.now() + timedelta(days=7)),
        db=db,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/token/refresh", status_code=status.HTTP_200_OK)
async def refresh_token(refresh_token: str, db: db_dependency):
    # Verify the refresh token
    payload = verify_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

    # Create a new access token
    user_id = payload.get("id")
    username = payload.get("username")
    logging.info(
        "Generating access token from refresh token for user_id: {} & username: {}".format(
            user_id, username
        )
    )
    new_access_token = create_access_token(username, user_id, timedelta(minutes=20))

    # Create token log entry in db
    create_token_logs(
        user_id=user_id,
        access_token=new_access_token,
        refresh_token=refresh_token,
        access_token_expiry=str(datetime.now() + timedelta(minutes=20)),
        refresh_token_expiry=str(datetime.now() + timedelta(days=7)),
        db=db,
    )

    return {"access_token": new_access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
