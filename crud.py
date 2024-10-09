from sqlalchemy.orm import Session, Query
from sqlalchemy.sql import extract
import models
import schemas
from datetime import date, datetime, timedelta
from typing import Optional, Union

def get_AudioFile_by_id(id: int, db: Session):
    return db.query(models.AudioFile).filter(models.AudioFile.id == id).first()

def get_AudioFile_filename_by_id(id: int, db: Session) -> str:
    return get_AudioFile_by_id(id=id, db=db).file_name

def delete_AudioFile(id: int, db: Session):
    db_audio = get_AudioFile_by_id(id=id, db=db)
    db.delete(db_audio)
    return db