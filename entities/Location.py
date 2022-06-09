from sqlalchemy import Column, Text
from sqlalchemy.orm import relationship, column_property
from .base import Base

class LocationEnt(Base):
    __tablename__ = "location"
    id = Column(Text, primary_key=True)
    name = Column(Text, nullable=True)
    building = Column(Text)
    room = Column(Text)
    offices = relationship("ProfessorEnt", back_populates="office")
    sections = relationship("SectionEnt", back_populates="location")