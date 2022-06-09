from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from copy import deepcopy

#
#
# Core expression types
#
#

class ExprC:
    pass

@dataclass
class IdC(ExprC):
    id: str

@dataclass
class StringC(ExprC):
    string: str

@dataclass
class NumC(ExprC):
    num: int

@dataclass
class DotAccessC(ExprC):
    expr: ExprC
    id: IdC

@dataclass
class PoundAccessC(ExprC):
    expr: ExprC
    id: IdC

@dataclass
class BracketAccessC(ExprC):
    expr0: ExprC
    expr1: ExprC

@dataclass
class FnC(ExprC):
    args: list[IdC]
    body: ExprC
    recurse: bool = False

@dataclass
class AppC(ExprC):
    fn: ExprC
    args: list[ExprC]

@dataclass
class CompC(ExprC):
    expr0: ExprC
    comp: str
    expr1: ExprC

@dataclass
class ArrC(ExprC):
    vals: list[ExprC]

@dataclass
class IfC(ExprC):
    cond: ExprC
    l: ExprC
    r: ExprC

@dataclass
class FStringC(ExprC):
    fstring: str
    exprs: list[ExprC]

#
#
# Value types
#
#

@dataclass(frozen=True)
class RainVBase:
    value: any

    def __str__(self):
        return str(self.value)

@dataclass(frozen=True, kw_only=True)
class RainV(RainVBase):
    t: str

@dataclass(frozen=True, kw_only=True)
class ObjectV(RainV):
    t: str = "object"

@dataclass(frozen=True, kw_only=True)
class TableV(RainV):
    session: Any
    t: str = "table"

@dataclass(frozen=True, kw_only=True)
class CloV(RainV):
    env: dict
    args: list[IdC] = None
    recurse: bool = False
    t: str = "closure"

@dataclass(frozen=True, kw_only=True)
class OpV(RainV):
    t: str = "op"

@dataclass(frozen=True, kw_only=True)
class PyCloV(RainV):
    env: dict
    selfValue: RainV = None
    t: str = "py-closure"

@dataclass(frozen=True, kw_only=True)
class NumberV(RainV):
    t: str = "number"

@dataclass(frozen=True, kw_only=True)
class StringV(RainV):
    t: str = "string"

@dataclass(frozen=True, kw_only=True)
class EntV(RainV):
    table: dict
    tablename: str
    t: str = "entity"

@dataclass(frozen=True, kw_only=True)
class LazyEntV(RainV):
    # 'value' is a dictionary of the entity's columns and types
    tablename: str
    t: str = "lazy-ent"

@dataclass(frozen=True, kw_only=True)
class BoolV(RainV):
    t: str = "bool"

    def __str__(self):
        return "true" if self.value is True else "false"

@dataclass(frozen=True, kw_only=True)
class NoneV(RainV):
    t: str = "none"

    value: None = None

@dataclass(frozen=True, kw_only=True)
class ListV(RainV):
    t: str = "list"

    def __str__(self):
        return str([v.value for v in self.value])

def get_raintype_string_from_val(val):
    if isinstance(val, RainV):
        return "raintype"
    elif val is True or val is False:
        return "bool"
    elif val is None:
        return "none"
    elif isinstance(val, str):
        return "string"
    elif isinstance(val, int) or isinstance(val, float):
        return "number"
    elif isinstance(val, list):
        return "list"
    elif isinstance(val, dict):
        return "object"
    elif callable(val):
        return "py-closure"
    elif hasattr(val, "_sa_instance_state"):
        return "entity"
    else:
        raise Exception(f"Unrecognized raw value {val} of type {type(val)}")

def rain_wrap(val, db, env, typestring=None):
    val_type = typestring or get_raintype_string_from_val(val)
    match val_type:
        case "raintype": return val
        case "string": return StringV(val)
        case "number": return NumberV(val)
        case "list": return ListV([rain_wrap(subval, db, env) for subval in val])
        case "py-closure": return PyCloV(val, env=deepcopy(env))
        case "none": return NoneV()
        case "bool": return BoolV(val)
        case "object": return ObjectV({k: rain_wrap(v, db, env) for k, v in val.items()})
        case "entity":
            val = val.value if type(val) == EntV else val
            tablename = val._sa_instance_state.class_.__name__
            return EntV(val, table=db.type_map[tablename], tablename=tablename)
        case _: raise Exception(f"Can't automatically wrap value {val} of type {val_type}")