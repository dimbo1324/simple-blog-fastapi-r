from data import posts
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request, HTTPException, status

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")


@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
async def home(request: Request):
    return templates.TemplateResponse(
        request, "home.html", {"posts": posts, "title": "Home"}
    )


@app.get("/api/posts")
def get_posts():
    return posts


@app.get("/api/posts/{post_id}")
def get_posts(post_id: int):
    for post in posts:
        if post.get("id") == post_id:
            return post
    # err_msg = {"error": "Post not found"}
    # return err_msg
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
