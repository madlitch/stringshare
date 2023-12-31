from fastapi import FastAPI, Depends, status, Request, UploadFile
from fastapi.security import OAuth2PasswordRequestForm
from uuid import UUID
from typing import List

import time
import logging
import random
import string
import helper

import models
import database
import methods
import auth

app = FastAPI()

# Configure logging to file 'info.log' with INFO level.
logging.basicConfig(filename='info.log', level=logging.INFO)
logger = logging.getLogger(__name__)


@app.middleware('http')
async def log_requests(request: Request, call_next):
    # Middleware to log HTTP requests. Generates a unique ID for each request and logs the request path and
    # processing time.
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
    # Startup event handler to connect to the database when the application starts.
    await database.database.connect()


@app.on_event("shutdown")
async def shutdown():
    # Shutdown event handler to disconnect from the database when the application stops.
    await database.database.disconnect()


# API Routes

# Routes are defined with decorators specifying HTTP methods and paths (e.g., @app.get("/path")).
# 'status_code' sets the HTTP status for successful responses (e.g., 200 OK).
# 'response_model' defines the structure of the response data using Pydantic models.
# 'Depends()' is used for dependency injection, in this case for user authentication.
# Route functions handle the logic and return the response conforming to the 'response_model'.


# Util --

@app.get("/reset_database")
async def reset_database():
    await helper.reset_database()


@app.get("/util")
async def util():
    pass


# Auth --

@app.post("/token", response_model=models.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    token = await auth.login(form_data)
    return token


# Foreign Server Endpoints --

@app.get("/server/search", status_code=status.HTTP_200_OK, response_model=List[models.SearchUser])
async def search_users(search_user: models.ServerSearchUser):
    return await methods.search_users(search_user.search_query, search_user)


@app.post("/server/follow", status_code=status.HTTP_201_CREATED, response_model=models.ServerUser)
async def server_follow_user(users: models.ServerFollowUser):
    return await methods.server_follow_user(users.username, users.user)


@app.post("/server/post", status_code=status.HTTP_201_CREATED)
async def server_create_post(
        post_id: str,
        post: str,
        latitude: float,
        longitude: float,
        username: str,
        photo: UploadFile = None
):
    await methods.server_create_post(post_id, post, latitude, longitude, photo, username)


@app.post("/server/comment", status_code=status.HTTP_201_CREATED)
async def receive_comment(comment: models.ServerComment):
    return await methods.server_create_comment(comment)


@app.post("/server/like", status_code=status.HTTP_201_CREATED)
async def receive_like(like: models.ServerLike):
    return await methods.server_create_like(like)


# User --

@app.post("/client/signup", status_code=status.HTTP_201_CREATED)
async def create_user(user: models.UserIn):
    await methods.create_user(user)


@app.get("/client/me", status_code=status.HTTP_200_OK, response_model=models.UserOut)
async def get_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return await methods.get_user_profile(current_user.username, current_user)


@app.get("/client/users", status_code=status.HTTP_200_OK, response_model=models.UserOut)
async def get_user_profile(username: str, current_user: models.User = Depends(auth.get_current_active_user)):
    return await methods.get_user_profile(username, current_user)


@app.get("/client/activity", status_code=status.HTTP_200_OK, response_model=List[models.ActivityOut])
async def get_activity(current_user: models.User = Depends(auth.get_current_active_user)):
    return await methods.get_activity(current_user)


@app.get("/client/search", status_code=status.HTTP_200_OK, response_model=List[models.SearchUser])
async def search_users(search_query: str, current_user: models.User = Depends(auth.get_current_active_user)):
    return await methods.search_users(search_query, current_user)


@app.post("/client/follow", status_code=status.HTTP_201_CREATED)
async def follow_user(username: str, current_user: models.User = Depends(auth.get_current_active_user)):
    return await methods.follow_user(username, current_user)


@app.get("/client/followers", status_code=status.HTTP_200_OK, response_model=List[models.FollowerOut])
async def get_followers(current_user: models.User = Depends(auth.get_current_active_user)):
    return await methods.get_followers(current_user)


@app.get("/client/following", status_code=status.HTTP_200_OK, response_model=List[models.FollowingOut])
async def get_following(current_user: models.User = Depends(auth.get_current_active_user)):
    return await methods.get_following(current_user)


@app.post("/client/bio", status_code=status.HTTP_201_CREATED)
async def create_bio(bio: str, current_user: models.User = Depends(auth.get_current_active_user)):
    return await methods.create_bio(bio, current_user)


@app.post("/client/avatar", status_code=status.HTTP_201_CREATED)
async def update_avatar(file: UploadFile, current_user: models.User = Depends(auth.get_current_active_user)):
    await methods.update_avatar(file, current_user)


# Posts, Comments, Likes, & Media --

@app.get("/client/posts", status_code=status.HTTP_200_OK, response_model=List[models.PostOut])
async def get_feed(current_user: models.User = Depends(auth.get_current_active_user)):
    return await methods.get_feed(current_user)


@app.get("/client/post", status_code=status.HTTP_200_OK, response_model=models.PostOut)
async def get_post(post_id: UUID, current_user: models.User = Depends(auth.get_current_active_user)):
    return await methods.get_post(post_id, current_user)


@app.get("/client/likes", status_code=status.HTTP_200_OK, response_model=List[models.LikeOut])
async def get_post_likes(post_id: UUID, current_user: models.User = Depends(auth.get_current_active_user)):
    return await methods.get_post_likes(post_id)


@app.get("/client/comments", status_code=status.HTTP_200_OK, response_model=List[models.CommentOut])
async def get_comments(post_id: UUID, current_user: models.User = Depends(auth.get_current_active_user)):
    return await methods.get_post_comments(post_id)


@app.post("/client/post", status_code=status.HTTP_201_CREATED)
async def create_post(
        post: str,
        latitude: float,
        longitude: float,
        photo: UploadFile = None,
        current_user: models.User = Depends(auth.get_current_active_user)
):
    return await methods.create_post(post, latitude, longitude, photo, current_user)


@app.post("/client/comment", status_code=status.HTTP_201_CREATED)
async def create_comment(comment: models.Comment, current_user: models.User = Depends(auth.get_current_active_user)):
    return await methods.create_comment(comment, current_user)


@app.post("/client/like", status_code=status.HTTP_201_CREATED)
async def create_like(post_id: UUID, current_user: models.User = Depends(auth.get_current_active_user)):
    return await methods.create_like(post_id, current_user)


@app.get("/client/media/", status_code=status.HTTP_200_OK)
async def get_photo(url: str = None):
    return await methods.get_photo(url)
