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

import tempfile
import io
from sqlalchemy import Column, Integer, Float, LargeBinary, String
from sqlalchemy.orm import Session
from database import get_db, Base, engine
from typing import List

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

class AudioUpdateModel(BaseModel):
    new_title: str

class AudioMetadata(BaseModel):
    filename: str
    content_length: int
    last_modified: str
    content_type: str

@router.post("/audio/upload")
async def upload_file(doctor_id: int = Form(...), patient_name: str = Form(...), file_upload: UploadFile = File(...), db:Session = Depends(get_db), s3: Session = Depends(get_s3)):
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

    

    return JSONResponse(content={"message": "File uploaded successfully!", "filename": file_upload.filename}, status_code=200)

@router.get("/audio/get_all_file_detail/{folder_name}")
async def get_all_file_detail(folder_name: str, s3 = Depends(get_s3)):
    try:
        file_details = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=f"{folder_name}/")
    except ClientError as e:
        raise e
    return file_details["Contents"]


@router.get("/audio/download/{filename}")
async def download_file(filename: str, s3 = Depends(get_s3)):
    try:
        file = s3.get_object(Bucket=BUCKET_NAME, Key=f"audios/{filename}")
    except ClientError as e:
        raise e
    return Response(
        content=file['Body'].read(),
        headers={"filename": filename}
    )

@router.delete("/audio/delete/{id}")
async def delete_file(id: int, s3 = Depends(get_s3), db: Session = Depends(get_db)):
    try:
        # filename = get_AudioFile_filename_by_id(id=id, db=db)
        s3_key = get_AudioFile_s3name_by_id(id=id, db=db)
        db_audio = delete_AudioFile(id=id, db=db)
        s3.delete_object(Bucket=BUCKET_NAME, Key="/audios/"+s3_key)
        db_audio.commit()

    except:
        print("An error occured")   

# @router.put("/audio/update/{filename}")
# async def update_filename(filename: str, update: AudioUpdateModel, s3 = Depends(get_s3)):
#     try:
#         print(f"Filename: {filename}")
#         print(f"New Title: {update.new_title}")
        
#         new_key = f"audios/{update.new_title}"
#         s3.copy_object(
#             CopySource={'Bucket': BUCKET_NAME, 'Key': f"audios/{filename}"},
#             Bucket=BUCKET_NAME,
#             Key=new_key
#         ) 

#         s3.delete_object(Bucket=BUCKET_NAME, Key=f"audios/{filename}")
#     except ClientError as e:
#         raise e
#     return JSONResponse(content={"message": f"File title updated to {update.new_title}"}, status_code=200)

    
# @router.get("/audio/metadata", response_model=List[AudioMetadata])
# async def list_audio_metadata(s3 = Depends(get_s3)):
#     try:
#         response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix='audios/')
#         if 'Contents' not in response:
#             return [] 

#         metadata_list = []
#         for obj in response['Contents']:
#             key = obj['Key']
#             filename = key.split('/')[-1]  
#             # Fetching metadata for each file
#             metadata_response = s3.head_object(Bucket=BUCKET_NAME, Key=key)
#             last_modified = metadata_response['LastModified'].strftime("%d/%m/%Y, %H:%M")
#             # duration = get_audio_duration(key)

#             url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{key}"

#             metadata = {
#                 "filename": filename,
#                 "content_length": metadata_response['ContentLength'],
#                 "last_modified": last_modified,
#                 "content_type": metadata_response['ContentType'],
#                 # "duration": duration,
#                 "url": url,
#             }
#             metadata_list.append(metadata)

#     except ClientError as e:
#         raise HTTPException(status_code=500, detail=f"Error fetching audio metadata: {str(e)}")

#     return JSONResponse(content=metadata_list, status_code=200)