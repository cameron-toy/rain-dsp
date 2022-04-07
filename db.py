import sqlalchemy as sa
from sqlalchemy.orm import sessionmaker
from entities.Club import ClubEnt
from entities.Professor import ProfessorEnt
from sqlalchemy_utils import get_classname_from_table, get_key_type_pairs
from rain_types import get_key_type_pairs
import random
import dsl
from pprint import pprint


class Database:
    def __init__(self, db_file, entities=[], entity_search_cols={}, echo=False):
        self.db_file = db_file
        self.entities = entities
        self.entity_names = { e.__tablename__: e for e in entities }
        self.entity_types = { e.__tablename__: e.__name__ for e in entities }
        print(self.entity_types)
        self.entity_search_cols = entity_search_cols
        self.engine = sa.create_engine(f"sqlite:///{db_file}", echo=echo)
        self.inspector = sa.inspect(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.type_map = self._create_type_mapping()
        
    def _create_type_mapping(self):
        type_map = dict()
        for ent in self.entities:
            inspector = sa.inspect(ent)
            table = inspector.tables[0]
            type_map[get_classname_from_table(table)] = get_key_type_pairs(inspector)
        
        pprint(type_map)
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
    

def add_club(db, name, advisor=None, id=None):
    session = db.session

    # Get the club
    club = (
        session.query(ClubEnt)
        .filter(ClubEnt.name == name)
        .one_or_none()
    )

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


def setup_db(db):
    db.create_all()

    add_club(db, "Cal Poly CSAI")
    add_club(db, "Cal Poly Computer Engineering Society")

    add_professor(db, "sding01", "Shunping Ding", "Cal Poly Mycology Club")
    add_professor(db, "husmith", "Hugh Smith")
    add_professor(db, "srbeard", "Stephen Beard")
    add_professor(db, "foaad", "Foaad Khosmood", "Cal Poly CSAI")



def main():
    DB_FILE = "calpoly.db"
    db = Database(DB_FILE, [ProfessorEnt, ClubEnt], {ProfessorEnt: "alias", ClubEnt: "name"})

    setup_db(db)
    
    print()

    print(
        f"Dr. Ding advises {[club.name for club in db.get_entity('professor', 'first_name', 'Shunping').advises][0]}"
    )
    print(
        f"The advisor for Cal Poly CSAI is {db.get_entity('club', 'name', 'Cal Poly CSAI').advisor.name}"
    )
    print(
        f"Dr. Khosmood's email is {db.get_prop_from_entity('professor', 'foaad', 'email')}"
    )
    print(
        dsl.interp(db, "Dr. Khosmood's email is [professor.foaad.email]")   
    )

    # "What is the phone number of the advisor of Cal Poly Mycology club?"
    # "The phone number of the advisor of Cal Poly Mycology is [club.advisor.phone_number]"

    print(hasattr(db.get_entity_default_search_col("club", "Cal Poly CSAI"), "_sa_instance_state"))

    print()


if __name__=="__main__":
    main()