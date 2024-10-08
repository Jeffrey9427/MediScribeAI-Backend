import boto3.s3
from models import AudioFile
import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, FastAPI, HTTPException, Depends, UploadFile, Response, status, File
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from settings import *
import uuid

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

def create_s3_name(file_name, doctor_id):
        unique_id = str(uuid.uuid4())
        return f"{doctor_id}_{unique_id}_{file_name}"


@router.post("/audio/upload")
async def upload_file(doctor_id: int, file_upload: UploadFile = File(...),  s3: Session = Depends(get_s3)):
    if not file_upload.size:
        return HTMLResponse(content="File is empty!", status_code=415)

    file: io.BytesIO

    temp = tempfile.TemporaryFile()
    try:
        temp.write(file_upload.file.read())
        temp.seek(0)
        file = io.BytesIO(temp.read())
    finally:
        temp.close()
    
    try:
        s3.upload_fileobj(Fileobj=file, Bucket=BUCKET_NAME, Key=create_s3_name(file_upload.filename, doctor_id))
    except ClientError as e:
        raise e

@router.get("/audio/get_all_file_detail")
async def get_all_file_detail(s3 = Depends(get_s3)):
    try:
        file_details = s3.list_objects_v2(Bucket=BUCKET_NAME)
    except ClientError as e:
        raise e
    return file_details["Contents"]


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

