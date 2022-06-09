from sqlalchemy import Column, Text
from sqlalchemy.orm import relationship
from .base import Base

class DepartmentEnt(Base):
    __tablename__ = "department"
    name = Column(Text, primary_key=True)
    courses = relationship("CourseEnt", back_populates="department")
