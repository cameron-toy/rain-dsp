from sqlalchemy import Column, Text
from sqlalchemy.orm import relationship, column_property
from .base import Base

class ProfessorEnt(Base):
    __tablename__ = "professor"
    alias = Column(Text, primary_key=True)
    first_name = Column(Text)
    last_name = Column(Text)
    advises = relationship("ClubEnt", back_populates="advisor")
    name = column_property(first_name + " " + last_name)
    email = column_property(alias + "@calpoly.edu")

    #phone_number = Column(Text)
    #office = Column(Text)
    #department = Column(Text)
    #title = Column(Text)
