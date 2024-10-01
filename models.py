from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base

class AudioFile(Base):
    __tablename__ = "audiofiles"

    id = Column(Integer, primary_key=True)
    file = Column(String)

class Transcription(Base):
    __tablename__ = "transcription"

    id = Column(Integer, primary_key=True)
    file = Column(String)