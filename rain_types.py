from __future__ import annotations
from sqlalchemy_utils import get_key_from_column
from sqlalchemy.orm import MANYTOONE, MANYTOMANY, ONETOMANY
from dataclasses import dataclass
from typing import Any, Callable


class RainV:
    pass

@dataclass(frozen = True)
class CloV(RainV):
    _: Callable
    env: dict
    t: str = "closure"

    def __iter__(self):
        return iter((self._, self.env, self.t))


@dataclass(frozen = True)
class NumberV(RainV):
    _: float
    t: str = "number"

    def __iter__(self):
        return iter((self._, self.t))

@dataclass(frozen = True)
class StringV(RainV):
    _: str
    t: str = "string"

    def __iter__(self):
        return iter((self._, self.t))

@dataclass(frozen = True)
class EntV(RainV):
    _: Any
    table: dict
    tablename: str
    t: str = "entity"

    def __iter__(self):
        return iter((self._, self.table, self.tablename, self.t))

@dataclass(frozen = True)
class LazyEntV(RainV):
    _: dict
    tablename: str
    t: str = "lazy-ent"

    def __iter__(self):
        return iter((self._, self.tablename, self.t))

@dataclass(frozen = True)
class ListV:
    _: list
    subtype: str
    t: str = "list"

    def __iter__(self):
        return iter((self._, self.subtype, self.t))

_VALUES = [NumberV, StringV, EntV, ListV]
VALUE_MAP = { v.t : v for v in _VALUES }


def get_raintype(val):
    if isinstance(val, RainV):
        return val.t
    elif isinstance(val, str):
        return "string"
    elif isinstance(val, int) or isinstance(val, float):
        return "number"
    elif isinstance(val, list):
        return "list"
    elif callable(val):
        return "closure"
    elif hasattr(val, "_sa_instance_state"):
        return "entity"
    else:
        raise Exception(f"Unrecognized raw value {val} of type {type(val)}")


class RainType:
    key: str
    listof: bool

    def __init__(self, key, listof=False):
        self.key = key
        self.listof = listof

    def __repr__(self):
        return f"RainType({self.key}, list={self.listof})"

    def __eq__(self, other):
        if type(other) == str:
            return other == self.key
        elif isinstance(other, RainType):
            return other.key == self.key and other.listof == self.listof
        else:
            return False

def get_key_type_pairs(inspector):
    pairs = dict()
    for col in inspector.columns:
        t = RainType(str(col.type))
        pairs[get_key_from_column(col, inspector)] = t
    for rel in inspector.relationships:
        if rel.direction == MANYTOMANY or rel.direction == ONETOMANY:
            t = RainType(rel.mapper.class_.__name__, True)
        elif rel.direction == MANYTOONE:
            t = RainType(rel.mapper.class_.__name__)
        else:
            raise Exception("Unknown rel.direction")


        pairs[rel.key] = t
    return pairs