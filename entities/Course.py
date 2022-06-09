from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy.ext.hybrid import hybrid_property

class CourseEnt(Base):
    __tablename__ = "course"
    title = Column(Text, primary_key=True)
    name = Column(Text)
    type = Column(Text)
    
    @hybrid_property
    def course_number(self):
        return self.title.split()[-1]

    department_name = Column(Text, ForeignKey("department.name"))
    department = relationship("DepartmentEnt", back_populates="courses", foreign_keys=[department_name])
    sections = relationship("SectionEnt", back_populates="course")