from dataclasses import dataclass
from os import stat
import rain_types as rt
from sqlalchemy_utils import get_key_from_column
from sqlalchemy.orm import MANYTOONE, MANYTOMANY, ONETOMANY
from rainmethod import rainmethod
import interp
from pprint import pprint

@dataclass(frozen=True)
class RainT:
    t: str

@dataclass(frozen=True, kw_only=True)
class TableT(RainT):
    t: str = "table"

    @rainmethod([])
    @staticmethod
    def rows(env, db, hints):
        self = env["self"]
        return self.session().query(self.value).all()

    @rainmethod(["func"])
    @staticmethod
    def map(env, db, hints):
        rows = rt.rain_wrap(TableT.rows(None, env, db, hints), db, env)
        return ListT.map(rows, env, db, hints)

    @rainmethod(["func"])
    @staticmethod
    def filter(env, db, hints):
        rows = rt.rain_wrap(TableT.rows(None, env, db, hints), db, env)
        return ListT.filter(rows, env, db, hints)

    @rainmethod(["func"])
    @staticmethod
    def map(env, db, hints):
        rows = rt.rain_wrap(TableT.rows(None, env, db, hints), db, env)
        return ListT.map(rows, env, db, hints)

    @rainmethod(["func", "acc"])
    @staticmethod
    def foldl(env, db, hints):
        rows = rt.rain_wrap(TableT.rows(None, env, db, hints), db, env)
        return ListT.foldl(rows, env, db, hints)

    @rainmethod([])
    @staticmethod
    def rest(env, db, hints):
        rows = rt.rain_wrap(TableT.rows(None, env, db, hints), db, env)
        return ListT.rest(rows, env, db, hints)

    @rainmethod(["joiner"])
    @staticmethod
    def grammatical_join(env, db, hints):
        rows = rt.rain_wrap(TableT.rows(None, env, db, hints), db, env)
        return ListT.grammatical_join(rows, env, db, hints)
    
    @rainmethod(["joiner"])
    @staticmethod
    def gjoin(env, db, hints):
        rows = rt.rain_wrap(TableT.rows(None, env, db, hints), db, env)
        return ListT.grammatical_join(rows, env, db, hints)

    @rainmethod([])
    @staticmethod
    def length(env, db, hints):
        rows = rt.rain_wrap(TableT.rows(None, env, db, hints), db, env)
        return ListT.length(rows, env, db, hints)

    @rainmethod([])
    @staticmethod
    def max(env, db, hints):
        rows = rt.rain_wrap(TableT.rows(None, env, db, hints), db, env)
        return ListT.max(rows, env, db, hints)
    
    @rainmethod([])
    @staticmethod
    def min(env, db, hints):
        rows = rt.rain_wrap(TableT.rows(None, env, db, hints), db, env)
        return ListT.min(rows, env, db, hints)

    @rainmethod([])
    @staticmethod
    def sort(env, db, hints):
        rows = rt.rain_wrap(TableT.rows(None, env, db, hints), db, env)
        return ListT.sort(rows, env, db, hints)

    @rainmethod(["fn"])
    @staticmethod
    def max_by(env, db, hints):
        rows = rt.rain_wrap(TableT.rows(None, env, db, hints), db, env)
        return ListT.max_by(rows, env, db, hints)

    @rainmethod(["fn"])
    @staticmethod
    def min_by(env, db, hints):
        rows = rt.rain_wrap(TableT.rows(None, env, db, hints), db, env)
        return ListT.min_by(rows, env, db, hints)

    @rainmethod(["fn"])
    @staticmethod
    def sort_by(env, db, hints):
        rows = rt.rain_wrap(TableT.rows(None, env, db, hints), db, env)
        return ListT.sort_by(rows, env, db, hints)


@dataclass(frozen=True, kw_only=True)
class CloT(RainT):
    t: str = "closure"

@dataclass(frozen=True, kw_only=True)
class PyCloT(RainT):
    t: str = "py-closure"

@dataclass(frozen=True, kw_only=True)
class NumberT(RainT):
    t: str = "number"


@dataclass(frozen=True, kw_only=True)
class StringT(RainT):
    t: str = "string"

    @rainmethod(["n"])
    @staticmethod
    def replicate(env, db, hints):
        n = env["n"].value
        selfV = env["self"].value
        return selfV * n

    @rainmethod(["substr"])
    @staticmethod
    def startswith(env, db, hints):
        substr = env["substr"].value
        selfV = env["self"].value
        return selfV.startswith(substr)

    @rainmethod(["substr"])
    @staticmethod
    def endswith(env, db, hints):
        substr = env["substr"].value
        selfV = env["self"].value
        return selfV.endswith(substr)

    @rainmethod(["substr"])
    @staticmethod
    def contains(env, db, hints):
        substr = env["substr"].value
        selfV = env["self"].value
        return selfV.contains(substr)

    @rainmethod([])
    @staticmethod
    def lower(env, db, hints):
        return env["self"].value.lower()

    @rainmethod([])
    @staticmethod
    def upper(env, db, hints):
        return env["self"].value.upper()

    @rainmethod(["bottom", "top"])
    @staticmethod
    def slice(env, db, hints):
        selfV = env["self"].value
        bottom = env["bottom"].value
        top = env["top"].value
        return selfV[bottom:top]

    @rainmethod([])
    @staticmethod
    def spell(env, db, hints):
        selfV = env["self"].value
        splitted = selfV.split()
        return "; ".join(", ".join(s) for s in splitted)

    @rainmethod(["v"])
    @staticmethod
    def find(env, db, hints):
        return env["self"].value.find(env["v"].value)


@dataclass(frozen=True, kw_only=True)
class EntT(RainT):
    t: str = "entity"

@dataclass(frozen=True, kw_only=True)
class LazyEntT(RainT):
    t: str = "lazy-ent"

@dataclass(frozen=True, kw_only=True)
class BoolT(RainT):
    t: str = "bool"

@dataclass(frozen=True, kw_only=True)
class NoneT(RainT):
    t: str = "none"

@dataclass(frozen=True, kw_only=True)
class OpT(RainT):
    t: str = "op"

@dataclass(frozen=True, kw_only=True)
class ListT(RainT):
    subtype: RainT
    t: str = "list"

    @rainmethod(["func"])
    @staticmethod
    def map(env, db, hints):
        selfV = env["self"].value
        return [interp.interp_appC(env["func"], [arg], env, db, hints, False) for arg in selfV]
    
    @rainmethod(["func"])
    @staticmethod
    def filter(env, db, hints):
        selfV = env["self"].value
        return [v for v in selfV if interp.interp_appC(env["func"], [v], env, db, hints, False).value is True]

    @rainmethod([])
    @staticmethod
    def first(env, db, hints):
        selfV = env["self"].value
        return selfV[0] if len(selfV) > 0 else None
    
    @rainmethod([])
    @staticmethod
    def rest(env, db, hints):
        selfV = env["self"].value
        return selfV[1:] if len(selfV) > 0 else []

    @rainmethod([])
    @staticmethod
    def empty(env, db, hints):
        return len(env["self"].value) == 0

    @rainmethod(["val"])
    @staticmethod
    def contains(env, db, hints):
        selfV = env["self"].value
        searchVal = env["val"].value
        return searchVal in (wrapped.value for wrapped in selfV)
    
    @rainmethod(["joiner"])
    @staticmethod
    def grammatical_join(env, db, hints):
        selfV = env["self"].value
        joiner = env["joiner"].value
        match selfV:
            case []: return ""
            case [x]: return x.value
            case [x, y]: return f"{x.value} {joiner} {y.value}"
            case [*body, foot]: return f"{', '.join([str(v.value) for v in body])}, {joiner} {foot.value}"

    @rainmethod(["joiner"])
    @staticmethod
    def gjoin(env, db, hints):
        return ListT.grammatical_join(env["self"], env, db, hints)

    @rainmethod([])
    @staticmethod
    def length(env, db, hints):
        return len(env["self"].value)
    
    @rainmethod(["fn", "acc"])
    def foldl(env, db, hints):
        fn = env["fn"]
        acc = env["acc"]
        for subval in env["self"].value:
            acc = interp.interp_appC(fn, [acc, subval], env, db, hints, False)
        return acc

    @rainmethod([])
    @staticmethod
    def dedup(env, db, hints):
        return list(set(env["self"].value))

    @rainmethod(["v"])
    @staticmethod
    def find(env, db, hints):
        selfV = env["self"].value
        return [subval.value for subval in selfV].index(env["v"].value)

    @rainmethod([])
    def max(env, db, hints):
        return max((item.value for item in env["self"].value))

    @rainmethod([])
    def min(env, db, hints):
        return min((item.value for item in env["self"].value))

    @rainmethod([])
    def sort(env, db, hints):
        return sorted((item.value for item in env["self"].value))

    @rainmethod(["fn"])
    def max_by(env, db, hints):
        fn = env["fn"]
        selfV = env["self"].value

        maxVal = None
        maxInterpedVal = None
        for val in selfV:
            interpedVal = interp.interp_appC(fn, [val], env, db, hints, False)
            if maxInterpedVal is None or interpedVal.value > maxInterpedVal.value:
                maxInterpedVal = interpedVal
                maxVal = val
        
        return maxVal.value
    
    @rainmethod(["fn"])
    def min_by(env, db, hints):
        fn = env["fn"]
        selfV = env["self"].value

        minVal = None
        minInterpedVal = None
        for val in selfV:
            interpedVal = interp.interp_appC(fn, [val], env, db, hints, False)
            if minInterpedVal is None or interpedVal.value < minInterpedVal.value:
                minInterpedVal = interpedVal
                minVal = val
        
        return minVal.value

    @rainmethod(["fn"])
    def sort_by(env, db, hints):
        fn = env["fn"]
        selfV = env["self"].value

        return sorted(selfV, key=lambda x: interp.interp_appC(fn, [x], env, db, hints, False).value)

    @rainmethod(["i"])
    def at(env, db, hints):
        return env["self"].value[env["i"].value]




@dataclass(frozen=True, kw_only=True)
class ObjectT(RainT):
    t: str = "object"


_TYPECLASSES = [NumberT, StringT, EntT, ListT, LazyEntT, CloT, BoolT, NoneT, TableT, PyCloT, ObjectT]
VALUE_MAP = { v.t : v for v in _TYPECLASSES }

def get_raintype_class_from_val(val):
    # Invalid vals should be caught by get_raintype_string
    return VALUE_MAP[rt.get_raintype_string_from_val(val)]


DEFAULT_COLTYPE_MAP = {
    "TEXT": StringT,
    "STRING": StringT,
    "INTEGER": NumberT,
    "FLOAT": NumberT,
    "NUMERIC": NumberT,
    "SMALLINT": NumberT,
    "BIGINT": NumberT,
    "BOOLEAN": BoolT
    # Unicode?
}

def get_raintype_class_from_coltype(coltype):
    try:
        return DEFAULT_COLTYPE_MAP[str(coltype)]
    except KeyError:
        raise Exception(f"Invalid coltype: {coltype}")

def get_key_type_pairs(inspector):
    pairs = dict()
    # Get types of explicitly-defined columns
    for col in inspector.columns:
        pairs[get_key_from_column(col, inspector)] = get_raintype_class_from_coltype(col.type)
    
    # Get types of relationships
    for rel in inspector.relationships:
        if rel.direction == MANYTOMANY or rel.direction == ONETOMANY:
            t = ListT(subtype=EntT)
        elif rel.direction == MANYTOONE:
            t = EntT
        else:
            raise Exception("Unknown rel.direction")

        pairs[rel.key] = t
    return pairs