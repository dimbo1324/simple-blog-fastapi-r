from typing import List
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

import models
from dependencies import DBSession
from schemas import PostCreate, PostResponse, PostUpdate

router = APIRouter(prefix="/api/posts", tags=["Posts API"])


async def _get_default_user(db: DBSession) -> models.User:
    """Возвращает первого пользователя в БД (гостевой аккаунт)."""
    result = await db.execute(select(models.User))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No users found. Default guest user was not created.",
        )
    return user


@router.get("", response_model=List[PostResponse])
async def get_posts(db: DBSession):
    result = await db.execute(select(models.Post))
    return result.scalars().all()


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(post: PostCreate, db: DBSession):
    # Определяем пользователя
    if post.user_id is not None:
        result = await db.execute(
            select(models.User).where(models.User.id == post.user_id)
        )
        user = result.scalars().first()
        if not user:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
    else:
        user = await _get_default_user(db)

    new_post = models.Post(title=post.title, content=post.content, user_id=user.id)
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return new_post


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db: DBSession):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post


@router.put("/{post_id}", response_model=PostResponse)
async def update_post_full(post_id: int, post_data: PostCreate, db: DBSession):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Post not found")

    if post_data.user_id is not None and post_data.user_id != post.user_id:
        result = await db.execute(
            select(models.User).where(models.User.id == post_data.user_id)
        )
        if not result.scalars().first():
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")
        post.user_id = post_data.user_id

    post.title = post_data.title
    post.content = post_data.content
    await db.commit()
    await db.refresh(post)
    return post


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post_partial(post_id: int, post_data: PostUpdate, db: DBSession):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Post not found")

    for field, value in post_data.model_dump(exclude_unset=True).items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db: DBSession):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Post not found")
    await db.delete(post)
    await db.commit()
