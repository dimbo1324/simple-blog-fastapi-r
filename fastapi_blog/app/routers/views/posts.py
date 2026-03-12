from fastapi import APIRouter, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import selectinload

import models
from dependencies import DBSession

router = APIRouter(include_in_schema=False)
templates = Jinja2Templates(directory="templates")


@router.get("/", name="home")
@router.get("/posts", name="posts")
async def home(request: Request, db: DBSession):
    result = await db.execute(
        select(models.Post).options(selectinload(models.Post.author))
    )
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request, "home.html", {"posts": posts, "title": "Home"}
    )


@router.get("/posts/create", name="post_create")
async def post_create(request: Request):
    return templates.TemplateResponse(request, "create.html", {"title": "New Post"})


@router.get("/posts/{post_id}/edit", name="post_edit")
async def post_edit(request: Request, post_id: int, db: DBSession):
    result = await db.execute(
        select(models.Post)
        .where(models.Post.id == post_id)
        .options(selectinload(models.Post.author))
    )
    post = result.scalars().first()
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Post not found")
    return templates.TemplateResponse(
        request,
        "edit.html",
        {"post": post, "title": f"Edit — {post.title[:40]}"},
    )


@router.get("/posts/{post_id}")
async def post_page(request: Request, post_id: int, db: DBSession):
    result = await db.execute(
        select(models.Post)
        .where(models.Post.id == post_id)
        .options(selectinload(models.Post.author))
    )
    post = result.scalars().first()
    if not post:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Post not found")
    return templates.TemplateResponse(
        request, "post.html", {"post": post, "title": post.title[:50]}
    )
