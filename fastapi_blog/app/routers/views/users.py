from fastapi import APIRouter, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

import models
from dependencies import DBSession

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="templates")


@router.get("/users/{user_id}/posts", name="user_posts")
async def user_posts_page(request: Request, user_id: int, db: DBSession):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

    result = await db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )
