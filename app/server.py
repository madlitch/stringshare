from fastapi import FastAPI, Depends, status, Request, File, UploadFile, Form
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


from models import *
from database import *
from constants import *
from uuid import UUID

import methods
import auth
import time
import logging
import random
import string
import helper

app = FastAPI()

app.mount("/static", StaticFiles(directory="{}static".format(APP_ROOT)), name="static")

logging.basicConfig(filename='info.log', level=logging.INFO)
logger = logging.getLogger(__name__)


@app.middleware('http')
async def log_requests(request: Request, call_next):
    idem = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    logger.info(f"rid={idem} start request path={request.url.path}")
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    formatted_process_time = '{0:.2f}'.format(process_time)
    logger.info(f"rid={idem} completed_in={formatted_process_time}ms status_code={response.status_code}")
    return response


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


# API Routes

# Util --

@app.get("/reset_database")
async def reset_database():
    await helper.reset_database()


@app.get("/util")
async def util():
    print("helping!")
    await methods.helper()


# Auth --

@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    token = await auth.login(form_data)
    return token


# User --

@app.post("/client/signup", status_code=status.HTTP_201_CREATED)
async def create_user(user: UserIn):
    await methods.create_user(user)


@app.get("/client/me", status_code=status.HTTP_200_OK, response_model=UserOut)
async def get_me(current_user: User = Depends(auth.get_current_active_user)):
    return await methods.get_user_profile(current_user.username)


@app.get("/client/users", status_code=status.HTTP_200_OK, response_model=UserOut)
async def get_user_profile(username: str, current_user: User = Depends(auth.get_current_active_user)):
    return await methods.get_user_profile(username)


@app.get("/client/search", status_code=status.HTTP_200_OK, response_model=List[SearchUser])
async def search_users(search_query: str, current_user: User = Depends(auth.get_current_active_user)):
    return await methods.search_users(search_query, current_user)


@app.post("/client/follow", status_code=status.HTTP_201_CREATED)
async def follow_user(username: str, current_user: User = Depends(auth.get_current_active_user)):
    return await methods.follow_user(username, current_user)


@app.get("/client/followers", status_code=status.HTTP_200_OK, response_model=List[FollowerOut])
async def get_followers(current_user: User = Depends(auth.get_current_active_user)):
    return await methods.get_followers(current_user)


@app.get("/client/following", status_code=status.HTTP_200_OK, response_model=List[FollowingOut])
async def get_following(current_user: User = Depends(auth.get_current_active_user)):
    return await methods.get_following(current_user)


@app.post("/client/bio", status_code=status.HTTP_201_CREATED)
async def create_bio(bio: str, current_user: User = Depends(auth.get_current_active_user)):
    return await methods.create_bio(bio, current_user)


@app.post("/client/avatar", status_code=status.HTTP_201_CREATED)
async def update_avatar(file: UploadFile, current_user: User = Depends(auth.get_current_active_user)):
    await methods.update_avatar(file, current_user)


# Post, Comments, & Likes --

@app.get("/client/posts", status_code=status.HTTP_200_OK, response_model=List[PostOut])
async def get_feed(current_user: User = Depends(auth.get_current_active_user)):
    return await methods.get_feed(current_user)


@app.get("/client/likes", status_code=status.HTTP_200_OK, response_model=List[LikeOut])
async def get_post_likes(post_id: UUID, current_user: User = Depends(auth.get_current_active_user)):
    return await methods.get_post_likes(post_id)


@app.get("/client/comments", status_code=status.HTTP_200_OK, response_model=List[CommentOut])
async def get_comments(post_id: UUID, current_user: User = Depends(auth.get_current_active_user)):
    return await methods.get_post_comments(post_id)


@app.post("/client/post", status_code=status.HTTP_201_CREATED)
async def create_post(
        post: str,
        latitude: float,
        longitude: float,
        photo: UploadFile,
        current_user: User = Depends(auth.get_current_active_user)
):
    return await methods.create_post(post, latitude, longitude, photo, current_user)


@app.post("/client/comment", status_code=status.HTTP_201_CREATED)
async def create_comment(comment: CommentIn, current_user: User = Depends(auth.get_current_active_user)):
    return await methods.create_comment(comment, current_user)


@app.post("/client/like", status_code=status.HTTP_201_CREATED)
async def create_like(post_id: UUID, current_user: User = Depends(auth.get_current_active_user)):
    return await methods.create_like(post_id, current_user)


@app.get("/client/media/", status_code=status.HTTP_200_OK, response_class=FileResponse)
async def get_photo(url: str):
    return os.path.join(MEDIA_ROOT, url)
