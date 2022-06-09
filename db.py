from html import entities
import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from entities.Club import ClubEnt
from entities.Professor import ProfessorEnt
from entities.Department import DepartmentEnt
from entities.Course import CourseEnt
from entities.Location import LocationEnt
from entities.Section import SectionEnt
from sqlalchemy_utils import get_classname_from_table, get_key_type_pairs
from typeclasses import get_key_type_pairs
import random
import csv
from pprint import pprint

class Database:
    def __init__(self, database_url, entity_config, echo=False):
        entities = entity_config.keys()
        self.entity_config = entity_config
        self.entity_names = { e.__tablename__: e for e in entities }
        self.entity_types = { e.__tablename__: e.__name__ for e in entities }
        self.engine = sa.create_engine(database_url, echo=echo)
        self.inspector = sa.inspect(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.type_map = self._create_type_mapping()
        
    @property
    def entities(self):
        return self.entity_config.keys()

    @property
    def entity_search_cols(self):
        return {k: v.get("search_col") for k, v in self.entity_config.items()}

    def _create_type_mapping(self):
        type_map = dict()
        for ent in self.entities:
            inspector = sa.inspect(ent)
            table = inspector.tables[0]
            type_map[get_classname_from_table(table)] = get_key_type_pairs(inspector)
        
        return type_map

    def create_all(self):
        for entity in self.entities:
            self._safe_create_table(entity)

    def _safe_create_table(self, entity):
        if not entity.__tablename__ in self.inspector.get_table_names():
            entity.__table__.create(bind=self.engine)
    
    def get_entity(self, ent, ent_col, ent_val):
        table = self.entity_names.get(ent)
        return (
            self.session
            .query(table)
            .filter(getattr(table, ent_col) == ent_val)
            .one_or_none()
        )
    
    def get_entity_default_search_col(self, ent, ent_val):
        search_col = self.entity_search_cols.get(self.entity_names.get(ent))
        return self.get_entity(ent, search_col, ent_val)
    
    def get_prop_from_entity(self, ent, ent_val, prop):
        search_col = self.entity_search_cols.get(self.entity_names.get(ent))
        return getattr(
            self.get_entity(
                ent,
                search_col,
                ent_val
            ), prop)
    

def check_for_ent(session, entType, column, value):
    return (
        session.query(entType)
        .filter(getattr(entType, column) == value)
        .one_or_none()
    )

def add_club(db, name, advisor=None, id=None):
    session = db.session

    # Get the club
    club = check_for_ent(session, ClubEnt, "name", name)

    if club is not None:
        return club

    club = ClubEnt(
        id=id or random.randint(10000, 99999),
        name=name,
        advisor=advisor
    )

    session.add(club)   
    session.commit()

    return club


def add_entity(db, props, entType, idProp, commit=False):
    session = db.session
    ent = check_for_ent(session, entType, idProp, props[idProp])
    if ent is not None:
        return ent

    ent = entType(**props)
    session.add(ent)
    if commit:
        session.commit()

    return ent


def add_row(db, info):
    departmentProps = {
        "name": info["DEPARTMENT"]
    }
    department = add_entity(db, departmentProps, DepartmentEnt, "name")

    officeProps = {
        "id": info["OFFICE"],
        "room": info["OFFICE ROOM"],
        "building": info["OFFICE BUILDING"],
        "name": None
    }
    office = add_entity(db, officeProps, LocationEnt, "id")

    professorProps = {
        "alias": info["ALIAS"],
        "first_name": info["FIRST NAME"],
        "last_name": info["LAST NAME"],
        "office": office,
        "phone_number": info["PHONE"],
        "title": info["TITLE"]
    }
    professor = add_entity(db, professorProps, ProfessorEnt, "alias")

    if "COURSE" not in info:
        return

    roomProps = {
        "id": info["LOCATION"],
        "room": info["SECTION ROOM"],
        "building": info["SECTION BUILDING"],
        "name": None
    }
    room = add_entity(db, roomProps, LocationEnt, "id")

    courseProps = {
        "title": info["COURSE"],
        "name": info["COURSE NAME"],
        "type": info["TYPE"],
        "department": department,
        }
    course = add_entity(db, courseProps, CourseEnt, "title")

    title = f"{info['COURSE']}-{info['SECT']}"
    sectionProps = {
        "title": title, 
        "start_time": info["START"],
        "end_time": info["END"],
        "days": info["DAYS"],
        "course": course,
        "location": room,
        "instructor": professor
    }

    add_entity(db, sectionProps, SectionEnt, "title")

    db.session.commit()


def add_professor(db, alias, name, advises=None):
    session = db.session
    first_name, last_name = name.split(" ")

    # Check if professor exists
    prof = (
        session.query(ProfessorEnt)
        .filter(ProfessorEnt.alias == alias)
        .one_or_none()
    )

    if prof is not None:
        return

    # Create the prof
    prof = ProfessorEnt(
        alias=alias,
        first_name=first_name,
        last_name=last_name
    )

    if advises is not None:
        club = add_club(db, advises, prof)
        club.advisor = prof
        session.add(club)
    
    session.add(prof)
    session.commit()

    return prof


def setup_db(db, inFile="data.csv"):
    db.create_all()

    for row in csv.DictReader(open(inFile)):
        add_row(db, row)


def main():
    DB_FILE = "calpoly.db"
    db = Database(
        f"sqlite:///{DB_FILE}",
        {
            ProfessorEnt: "alias",
            ClubEnt: "name",
            DepartmentEnt: "name",
            LocationEnt: "id",
            CourseEnt: "title",
            SectionEnt: "title"

        }
    )

    setup_db(db)
    
    

if __name__=="__main__":
    main()