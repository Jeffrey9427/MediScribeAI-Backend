from models import AudioFile
from botocore.exceptions import ClientError
from fastapi import APIRouter, FastAPI, HTTPException, Depends, UploadFile, Response, status, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import tempfile
import io
from sqlalchemy import Column, Integer, Float, LargeBinary, String
from sqlalchemy.orm import Session
from database import get_db, Base, engine

app = FastAPI()

router = APIRouter(
    prefix="/s3",
    tags=["s3"]
)

@router.post("/audio/upload/{filename}")
async def upload_file(filename: str, upload_file: UploadFile = File(...)):
    file: tuple[io.BytesIO, str]
    tempfile.TemporaryFile()

    temp = tempfile.TemporaryFile()
    try:
        temp.write(upload_file.file.read())
        temp.seek(0)
        file = (io.BytesIO(temp.read()), filename)
    finally:
        temp.close()

@router.get("/audio/get_all_filenames")
async def get_all_filenames(filename: str):
    ...

@router.get("/audio/download/{filename}")
async def download_file(filename: str):
    ...