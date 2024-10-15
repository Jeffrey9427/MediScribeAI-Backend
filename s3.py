import boto3.s3
from models import AudioFile
import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, FastAPI, HTTPException, Depends, UploadFile, Response, status, File
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from settings import *
import uuid
from crud import *

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
async def upload_file(doctor_id: int, patient_name: str, file_upload: UploadFile = File(...), db:Session = Depends(get_db), s3 = Depends(get_s3)):
    if not file_upload.size:
        return HTTPException(status_code=415, detail="File is empty!")

    file: io.BytesIO

    temp = tempfile.TemporaryFile()
    try:
        temp.write(file_upload.file.read())
        temp.seek(0)
        file = io.BytesIO(temp.read())
    finally:
        temp.close()
            
    # Create a unique name for the S3 file
    s3_name = create_s3_name(file_upload.filename, doctor_id)
    
    # Upload file to S3
    try:
        s3.upload_fileobj(Fileobj=file, Bucket=BUCKET_NAME, Key="audios/" + s3_name)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file to S3: {str(e)}")
    
    # Add the uploaded file metadata to the database
    try:
        
        audio_file_record = new_AudioFile(doctor_id, patient_name, s3_name, file_upload.filename , db)
        return {"message": "File uploaded successfully", "audio_file": audio_file_record}
    except Exception as e:
        db.rollback()  # Rollback in case of error
        raise HTTPException(status_code=500, detail=f"Failed to save file metadata: {str(e)}")

@router.post("/audio/edit/{id}")
async def edit_AudioFile(id: int, new_filename: str, s3 = Depends(get_s3), db: Session = Depends(get_db)):
    filename = get_AudioFile_filename_by_id(id, db=db)
    try:
        s3.copy_object(Bucket = BUCKET_NAME, CopySource = "audios/" + filename, Key = "audios/" + new_filename)
        s3.delete_object(Bucket = BUCKET_NAME, Key = "audios/" + filename)
        db_audio = get_AudioFile_by_id(id=id, db=db)
        db_audio.file_name = new_filename
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occured: {e}")


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

@router.delete("/audio/delete/{id}")
async def delete_file(id: int, s3 = Depends(get_s3), db: Session = Depends(get_db)):
    try:
        filename = get_AudioFile_filename_by_id(id=id, db=db)
        db_audio = delete_AudioFile(id=id, db=db)
        s3.delete_object(Bucket=BUCKET_NAME, Key="/Audio/"+filename)
        db_audio.commit()

    except:
        print("An error occured")