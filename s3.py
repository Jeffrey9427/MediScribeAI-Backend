import boto3.s3
from models import AudioFile
import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, FastAPI, HTTPException, Depends, UploadFile, Response, status, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from settings import *
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

s3 = boto3.client(
        's3',
        aws_access_key_id = AWS_ACCESS_KEY_ID,
        aws_secret_access_key = AWS_SECRET_ACCESS_KEY
    )

def get_s3():
    return s3

@router.post("/audio/upload/{filename}")
async def upload_file(filename: str, upload_file: UploadFile = File(...), s3 = Depends(get_s3)):
    file: tuple[io.BytesIO, str]
    tempfile.TemporaryFile()

    temp = tempfile.TemporaryFile()
    try:
        temp.write(upload_file.file.read())
        temp.seek(0)
        file = (io.BytesIO(temp.read()), filename)
    finally:
        temp.close()
    
    try:
        s3.upload_fileobj(Fileobj=file[0], Bucket=BUCKET_NAME, Key=file[1])
    except ClientError as e:
        raise e

@router.get("/audio/get_all_file_detail")
async def get_all_file_detail(s3 = Depends(get_s3)):
    try:
        file_details = s3.list_objects_v2(Bucket=BUCKET_NAME)
    except ClientError as e:
        raise e
    return JSONResponse(content=file_details["Contents"], status_code=200)

@router.get("/audio/download/{filename}")
async def download_file(filename: str, s3 = Depends(get_s3)):
    try:
        file = s3.get_object(Bucket=BUCKET_NAME, Key=filename)
    except ClientError as e:
        raise e
    return Response(
        content=file['Body'].read(),
        headers={"filename": filename}
    )