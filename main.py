import uvicorn
from fastapi import FastAPI, Depends, HTTPException, APIRouter, Request, status
from sqlalchemy.orm import Session
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from database import get_db, engine
import models

import s3,transcribe

models.Base.metadata.create_all(bind = engine)

app = FastAPI()

router = APIRouter()

app.include_router(s3.router)
app.include_router(transcribe.router)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 404:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "Oops! That resource does not exist."},
        )
    else:
        content = {"message": exc.detail}
        return JSONResponse(status_code=exc.status_code, content=content)
    return await request.app.default_exception_handler(request, exc)

origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    # add other origins here
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_dependency = Annotated[Session, Depends(get_db)]


# @app.get("/")
# async def root():
#     return {"message": "Hello, world!"}

get_db()

@app.get("/", status_code=status.HTTP_200_OK)
async def user(user: None, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    return {"User": user}

if __name__ == '__main__':
    uvicorn.run("main:app", host="127.0.0.1", reload=True)