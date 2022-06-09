from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import relationship, column_property
from .base import Base

class ProfessorEnt(Base):
    __tablename__ = "professor"
    alias = Column(Text, primary_key=True)
    first_name = Column(Text)
    last_name = Column(Text)

    office_id = Column(Text, ForeignKey("location.id"))
    office = relationship("LocationEnt", back_populates="offices", foreign_keys=[office_id])

    name = column_property(first_name + " " + last_name)
    email = column_property(alias + "@calpoly.edu")

    teaches = relationship("SectionEnt", back_populates="instructor")
    advises = relationship("ClubEnt", back_populates="advisor")

    phone_number = Column(Text)
    title = Column(Text)
