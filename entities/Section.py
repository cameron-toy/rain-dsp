from sqlalchemy import Column, Text, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base
from sqlalchemy.ext.hybrid import hybrid_property

class SectionEnt(Base):
    __tablename__ = "section"
    title = Column(Text, primary_key=True)
    start_time = Column(Text)
    end_time = Column(Text)
    days = Column(Text)

    @hybrid_property
    def section_number(self):
        return self.title.split("-")[-1]

    location_id = Column(Text, ForeignKey("location.id"))
    location = relationship("LocationEnt", back_populates="sections", foreign_keys=[location_id])

    course_title = Column(Text, ForeignKey("course.title"))
    course = relationship("CourseEnt", back_populates="sections", foreign_keys=[course_title])

    instructor = relationship("ProfessorEnt", back_populates="teaches")
    instructor_alias = Column(Text, ForeignKey("professor.alias"))