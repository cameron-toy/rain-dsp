from db import Database
from entities.Club import ClubEnt
from entities.Professor import ProfessorEnt
import sqlalchemy as sa
from pprint import pprint
from sqlalchemy.orm.context import _ColumnEntity, _MapperEntity
from sqlalchemy.orm.util import AliasedInsp
from sqlalchemy.orm import mapperlib
from inspect import isclass

def get_mapper(mixed):
    """
    Return related SQLAlchemy Mapper for given SQLAlchemy object.
    :param mixed: SQLAlchemy Table / Alias / Mapper / declarative model object
    ::
        from sqlalchemy_utils import get_mapper
        get_mapper(User)
        get_mapper(User())
        get_mapper(User.__table__)
        get_mapper(User.__mapper__)
        get_mapper(sa.orm.aliased(User))
        get_mapper(sa.orm.aliased(User.__table__))
    Raises:
        ValueError: if multiple mappers were found for given argument
    .. versionadded: 0.26.1
    """
    if isinstance(mixed, _MapperEntity):
        mixed = mixed.expr
    elif isinstance(mixed, sa.Column):
        mixed = mixed.table
    elif isinstance(mixed, _ColumnEntity):
        mixed = mixed.expr

    if isinstance(mixed, sa.orm.Mapper):
        return mixed
    if isinstance(mixed, sa.orm.util.AliasedClass):
        return sa.inspect(mixed).mapper
    if isinstance(mixed, sa.sql.selectable.Alias):
        mixed = mixed.element
    if isinstance(mixed, AliasedInsp):
        return mixed.mapper
    if isinstance(mixed, sa.orm.attributes.InstrumentedAttribute):
        mixed = mixed.class_
    if isinstance(mixed, sa.Table):
        if hasattr(mapperlib, '_all_registries'):
            all_mappers = set()
            for mapper_registry in mapperlib._all_registries():
                all_mappers.update(mapper_registry.mappers)
        else:  # SQLAlchemy <1.4
            all_mappers = mapperlib._mapper_registry
        mappers = [
            mapper for mapper in all_mappers
            if mixed in mapper.tables
        ]
        if len(mappers) > 1:
            raise ValueError(
                "Multiple mappers found for table '%s'." % mixed.name
            )
        elif not mappers:
            raise ValueError(
                "Could not get mapper for table '%s'." % mixed.name
            )
        else:
            return mappers[0]
    if not isclass(mixed):
        mixed = type(mixed)
    return sa.inspect(mixed)

def get_classname_from_table(table):
    return get_mapper(table).class_.__name__

def get_key_from_column(col, inspector):
    return inspector.get_property_by_column(col).key

def get_key_type_pairs(inspector):
    pairs = []
    for col in inspector.columns:
        pairs.append((get_key_from_column(col, inspector), str(col.type)))
    for rel in inspector.relationships:
        pairs.append((rel.key, rel.argument))
    return pairs



def main():
    DB_FILE = "calpoly.db"
    db = Database(DB_FILE, [ProfessorEnt, ClubEnt], {ProfessorEnt: "alias", ClubEnt: "name"})

    types = dict()
    for ent in db.entities:
        inspector = sa.inspect(ent)
        table = inspector.tables[0]
        types[get_classname_from_table(table)] = get_key_type_pairs(inspector)

    pprint(types)
    # inspector = sa.inspect(ClubEnt)
    # print(get_classname_from_table(inspector.tables[0]))
    # pairs = get_key_type_pairs(inspector)
    # pprint(pairs)


if __name__=="__main__":
    main()