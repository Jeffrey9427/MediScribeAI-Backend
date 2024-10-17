from sqlalchemy.orm import Session, Query
from sqlalchemy.sql import extract
import models
import schemas
from datetime import date, datetime, timedelta
from typing import Optional, Union
from settings import *
import boto3
from botocore.exceptions import ClientError

def get_AudioFiles(db:Session):
    return db.query(models.AudioFile).all()

def get_AudioFile_by_s3key(s3_key: str, db: Session):
    return db.query(models.AudioFile).filter(models.AudioFile.s3_key == s3_key).first()

def delete_AudioFile(s3_key: str, db: Session):
    db_audio = get_AudioFile_by_s3key(s3_key=s3_key, db=db)
    db.delete(db_audio)
    return db


def new_AudioFile(doctor_id,patient_name,s3_name,filename, db: Session):
    audio_file_record = models.AudioFile(
        doctor_id=doctor_id,
        file_name=filename,
        s3_key=s3_name,
        patient_name=patient_name
    )
    db.add(audio_file_record)
    db.commit()
    db.refresh(audio_file_record)  # Return the newly added record

    return audio_file_record