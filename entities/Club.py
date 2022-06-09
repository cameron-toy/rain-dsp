from sqlalchemy import Column, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from .base import Base


class ClubEnt(Base):
    __tablename__ = "club"
    id = Column(Integer, primary_key=True)
    name = Column(Text)
    advisor_alias = Column(Text, ForeignKey("professor.alias"))
    advisor = relationship("ProfessorEnt", back_populates="advises", foreign_keys=[advisor_alias])