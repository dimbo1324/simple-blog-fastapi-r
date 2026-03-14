from typing import List

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, select
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing_extensions import Annotated

import models
from auth.dependencies import CurrentUser, OptionalCurrentUser
from auth.jwt import create_access_token
from auth.password import hash_password, verify_password
from database import Base, engine, get_db
from schemas import (
    PostCreate,
    PostResponse,
    PostUpdate,
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
    UserUpdate,
    UserUpdatePassword,
)


Base.metadata.create_all(bind=engine)

app = FastAPI(title="PositiveBlog API", version="1.0.0")
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")

DBSession = Annotated[Session, Depends(get_db)]




@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request, db: DBSession, current_user: OptionalCurrentUser):
    posts = db.execute(select(models.Post)).scalars().all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home", "current_user": current_user},
    )


@app.get("/posts/create", include_in_schema=False, name="post_create")
def post_create_page(request: Request, current_user: CurrentUser):
    return templates.TemplateResponse(
        request,
        "create.html",
        {"title": "New Post", "current_user": current_user},
    )


@app.get("/posts/{post_id}/edit", include_in_schema=False, name="post_edit")
def post_edit_page(
    request: Request,
    post_id: int,
    db: DBSession,
    current_user: CurrentUser,
):
    post = (
        db.execute(select(models.Post).where(models.Post.id == post_id))
        .scalars()
        .first()
    )
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.user_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Access denied")
    return templates.TemplateResponse(
        request,
        "edit.html",
        {
            "post": post,
            "title": f"Edit — {post.title[:40]}",
            "current_user": current_user,
        },
    )


@app.get("/posts/{post_id}", include_in_schema=False)
def post_page(
    request: Request,
    post_id: int,
    db: DBSession,
    current_user: OptionalCurrentUser,
):
    post = (
        db.execute(select(models.Post).where(models.Post.id == post_id))
        .scalars()
        .first()
    )
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Post not found")
    return templates.TemplateResponse(
        request,
        "post.html",
        {"post": post, "title": post.title[:50], "current_user": current_user},
    )


@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
def user_posts_page(
    request: Request,
    user_id: int,
    db: DBSession,
    current_user: OptionalCurrentUser,
):
    user = (
        db.execute(select(models.User).where(models.User.id == user_id))
        .scalars()
        .first()
    )
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    posts = (
        db.execute(select(models.Post).where(models.Post.user_id == user_id))
        .scalars()
        .all()
    )
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {
            "posts": posts,
            "user": user,
            "title": f"{user.username}'s Posts",
            "current_user": current_user,
        },
    )


@app.get("/login", include_in_schema=False, name="login")
def login_page(request: Request, current_user: OptionalCurrentUser):
    if current_user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(
        request,
        "login.html",
        {"title": "Log In", "current_user": None},
    )


@app.get("/register", include_in_schema=False, name="register")
def register_page(request: Request, current_user: OptionalCurrentUser):
    if current_user:
        return RedirectResponse("/", status_code=302)
    return templates.TemplateResponse(
        request,
        "register.html",
        {"title": "Create Account", "current_user": None},
    )


@app.get("/account", include_in_schema=False, name="account")
def account_page(request: Request, current_user: CurrentUser):
    return templates.TemplateResponse(
        request,
        "account.html",
        {"title": "My Account", "current_user": current_user},
    )




@app.post(
    "/api/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Auth"],
    summary="Зарегистрировать нового пользователя",
)
def register(user_in: UserRegister, db: DBSession):
    existing = (
        db.execute(
            select(models.User).where(
                or_(
                    models.User.username == user_in.username,
                    models.User.email == user_in.email,
                )
            )
        )
        .scalars()
        .first()
    )

    if existing:
        field = "Username" if existing.username == user_in.username else "Email"
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=f"{field} already taken.",
        )

    new_user = models.User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.post(
    "/api/auth/login",
    response_model=Token,
    tags=["Auth"],
    summary="Войти и получить JWT-токен",
)
def login(credentials: UserLogin, response: Response, db: DBSession):
    user = (
        db.execute(
            select(models.User).where(
                or_(
                    models.User.username == credentials.username,
                    models.User.email == credentials.username,
                )
            )
        )
        .scalars()
        .first()
    )

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated.",
        )

    token = create_access_token(user.id)

    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=3600,
    )

    return Token(access_token=token)


@app.post(
    "/api/auth/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Auth"],
    summary="Выйти (удалить cookie)",
)
def logout(response: Response):
    response.delete_cookie("access_token")


@app.get(
    "/api/auth/me",
    response_model=UserResponse,
    tags=["Auth"],
    summary="Получить данные текущего пользователя",
)
def me(current_user: CurrentUser):
    return current_user




@app.get("/api/users/{user_id}", response_model=UserResponse, tags=["Users"])
def get_user(user_id: int, db: DBSession):
    user = (
        db.execute(select(models.User).where(models.User.id == user_id))
        .scalars()
        .first()
    )
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@app.patch(
    "/api/users/me",
    response_model=UserResponse,
    tags=["Users"],
    summary="Обновить свой профиль",
)
def update_me(user_update: UserUpdate, db: DBSession, current_user: CurrentUser):
    if user_update.username and user_update.username != current_user.username:
        if (
            db.execute(
                select(models.User).where(models.User.username == user_update.username)
            )
            .scalars()
            .first()
        ):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="Username already taken."
            )

    if user_update.email and user_update.email != current_user.email:
        if (
            db.execute(
                select(models.User).where(models.User.email == user_update.email)
            )
            .scalars()
            .first()
        ):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST, detail="Email already registered."
            )

    for field, value in user_update.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)

    db.commit()
    db.refresh(current_user)
    return current_user


@app.patch(
    "/api/users/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Users"],
    summary="Сменить пароль",
)
def change_password(data: UserUpdatePassword, db: DBSession, current_user: CurrentUser):
    if not verify_password(data.current_password, current_user.hashed_password):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect."
        )
    current_user.hashed_password = hash_password(data.new_password)
    db.commit()


@app.delete(
    "/api/users/me",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Users"],
    summary="Удалить свой аккаунт",
)
def delete_me(response: Response, db: DBSession, current_user: CurrentUser):
    db.delete(current_user)
    db.commit()
    response.delete_cookie("access_token")


@app.get(
    "/api/users/{user_id}/posts",
    response_model=List[PostResponse],
    tags=["Users"],
)
def get_user_posts(user_id: int, db: DBSession):
    if (
        not db.execute(select(models.User).where(models.User.id == user_id))
        .scalars()
        .first()
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    return (
        db.execute(select(models.Post).where(models.Post.user_id == user_id))
        .scalars()
        .all()
    )




@app.get("/api/posts", response_model=List[PostResponse], tags=["Posts"])
def get_posts(db: DBSession):
    return db.execute(select(models.Post)).scalars().all()


@app.post(
    "/api/posts",
    response_model=PostResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Posts"],
)
def create_post(post_in: PostCreate, db: DBSession, current_user: CurrentUser):
    new_post = models.Post(
        title=post_in.title,
        content=post_in.content,
        user_id=current_user.id,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@app.get("/api/posts/{post_id}", response_model=PostResponse, tags=["Posts"])
def get_post(post_id: int, db: DBSession):
    post = (
        db.execute(select(models.Post).where(models.Post.id == post_id))
        .scalars()
        .first()
    )
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@app.patch("/api/posts/{post_id}", response_model=PostResponse, tags=["Posts"])
def update_post(
    post_id: int,
    post_data: PostUpdate,
    db: DBSession,
    current_user: CurrentUser,
):
    post = (
        db.execute(select(models.Post).where(models.Post.id == post_id))
        .scalars()
        .first()
    )
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.user_id != current_user.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="You can only edit your own posts."
        )
    for field, value in post_data.model_dump(exclude_unset=True).items():
        setattr(post, field, value)
    db.commit()
    db.refresh(post)
    return post


@app.delete(
    "/api/posts/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Posts"],
)
def delete_post(post_id: int, db: DBSession, current_user: CurrentUser):
    post = (
        db.execute(select(models.Post).where(models.Post.id == post_id))
        .scalars()
        .first()
    )
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Post not found")
    if post.user_id != current_user.id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="You can only delete your own posts."
        )
    db.delete(post)
    db.commit()




@app.exception_handler(StarletteHTTPException)
def http_exception_handler(request: Request, exc: StarletteHTTPException):
    message = (
        exc.detail or "An error occurred. Please check your request and try again."
    )
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": message},
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exc.status_code,
            "title": exc.status_code,
            "message": message,
            "current_user": None,
        },
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exc: RequestValidationError):
    code = status.HTTP_422_UNPROCESSABLE_ENTITY
    if request.url.path.startswith("/api"):
        return JSONResponse(status_code=code, content={"detail": exc.errors()})
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": code,
            "title": code,
            "message": "Invalid request. Please check your input and try again.",
            "current_user": None,
        },
        status_code=code,
    )
