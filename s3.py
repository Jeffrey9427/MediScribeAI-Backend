import boto3.s3
from models import AudioFile
import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, FastAPI, HTTPException, Depends, UploadFile, Response, status, File, Form
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from settings import *
import uuid
from crud import *
from typing import Annotated

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

class UpdateAudioFilenameRequest(BaseModel):
    new_filename: str


@router.post("/audio/upload")
async def upload_file(doctor_id: Annotated[int, Form()], patient_name: Annotated[str, Form()], file_upload: UploadFile = File(...), db: Session = Depends(get_db), s3 = Depends(get_s3)):
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
        return audio_file_record
    except Exception as e:
        db.rollback()  # Rollback in case of error
        raise HTTPException(status_code=500, detail=f"Failed to save file metadata: {str(e)}")

@router.put("/audio/edit/{s3_key}")
async def edit_AudioFile(s3_key: str, request: UpdateAudioFilenameRequest, s3 = Depends(get_s3), db: Session = Depends(get_db)):
    parts = s3_key.split('_', 2)
    filename_part = parts[-1].split('.')
    file_format = None
    if len(filename_part) > 1:
        file_format = filename_part[-1]
    
    if len(parts) == 3:
        updated_s3_key = f"{parts[0]}_{parts[1]}_{request.new_filename}"
        if file_format: updated_s3_key += f".{file_format}"
    else:
        raise HTTPException(status_code=400, detail="Invalid filename format")

    try:
        original_object = s3.head_object(Bucket=BUCKET_NAME, Key="audios/" + s3_key)
        content_type = original_object.get('ContentType')
        print(f"Original Content Type: {content_type}")

        if not content_type:
            raise HTTPException(status_code=400, detail="Content type is not set for the original object.")

        s3.copy_object(
            Bucket=BUCKET_NAME,
            CopySource={"Bucket": BUCKET_NAME, "Key": "audios/" + s3_key},
            Key="audios/" + updated_s3_key,
            MetadataDirective='REPLACE',
            ContentType=content_type,
            Metadata=original_object.get('Metadata', {})
        )
        s3.delete_object(Bucket=BUCKET_NAME, Key="audios/" + s3_key)

        db_audio = get_AudioFile_by_s3key(s3_key=s3_key, db=db)
        db_audio.s3_key = updated_s3_key
        db_audio.file_name = request.new_filename
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

def get_audio_url(s3_key: str, expires_in: int = 3600, s3: boto3.client = Depends(get_s3)) -> str:
    try:
        url = s3.generate_presigned_url('get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': f'audios/{s3_key}'},
            ExpiresIn=expires_in)  # URL expires in 1 hour (3600 seconds)
        return url
    except ClientError as e:
        print(f"Error generating presigned URL: {e}")
        return None  

@router.get("/audio/get_all_file_detail")
async def get_all_file_detail(db: Session = Depends(get_db), s3 = Depends(get_s3)):
    try:
        file_details = get_AudioFiles(db=db)

        for audio_file in file_details:
            # Add audio_url attribute to each audio_file using presigned URL
            audio_file.audio_url = get_audio_url(audio_file.s3_key, s3=s3)  

        return file_details
    except ClientError as e:
        raise e


@router.get("/audio/download/{s3_key}")
async def download_file(s3_key: str, s3 = Depends(get_s3)):
    try:
        file = s3.get_object(Bucket=BUCKET_NAME, Key="audios/"+s3_key)
        file_content = file['Body'].read()
        file_name = s3_key.split('_')[-1] 
        content_type = file['ContentType'] 

    except ClientError as e:
        raise e

    return Response(
        content=file_content,
        headers={
            "Content-Disposition": f"attachment; filename={file_name}",
            "Content-Type": content_type
        }
    )

@router.delete("/audio/delete/{s3_key}")
async def delete_file(s3_key: str, s3 = Depends(get_s3), db: Session = Depends(get_db)):
    try:
        db_audio = delete_AudioFile(s3_key=s3_key, db=db)
        s3.delete_object(Bucket=BUCKET_NAME, Key="audios/"+s3_key)
        db_audio.commit()

    except:
        print("An error occured")