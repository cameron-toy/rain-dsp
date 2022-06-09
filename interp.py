from rain_types import *
from copy import deepcopy
import re
import typeclasses as tcs
from pprint import pprint
import sqlalchemy as sqa

def rain_compare(val0, val1, comp):
    match comp:
        case "==": return BoolV(val0 == val1)
        case "!=": return BoolV(val0 != val1)
        case ">=": return BoolV(val0 >= val1)
        case "<=": return BoolV(val0 <= val1)
        case ">": return BoolV(val0 > val1)
        case "<": return BoolV(val0 < val1)
        case _: raise Exception(f"Unknown comparison operator {comp}")

def interp_appC(expr, appArgs, env, db, hints, interpArgs=True):
    match expr:
        case CloV(expr, env=cloEnv, args=cloArgs, recurse=recurse):
            if len(cloArgs) != len(appArgs):
                raise Exception(f"Invalid number of arguments for fn {expr}")
            if interpArgs is False:
                interpedArgs = appArgs
            # handle recursive arguments in let statements
            elif recurse is True:
                interpedArgs = []
                for argName, arg in zip(cloArgs, appArgs):
                    match arg:
                        case FnC(args, body):
                            clo = CloV(body, env=deepcopy(env), args=args)
                            clo.env[argName] = clo
                            interpedArgs.append(clo)
                        case _:
                            interpedArgs.append(interp(arg, env, db, hints))
            else:
                interpedArgs = [interp(arg, env, db, hints) for arg in appArgs]
            return interp(expr, {**cloEnv, **dict(zip(cloArgs, interpedArgs))}, db, hints)
        case PyCloV(fn, env=pyCloEnv, selfValue=selfValue):
            interpedArgs = [interp(arg, env, db, hints) for arg in appArgs] if interpArgs else appArgs
            return rain_wrap(fn(selfValue, pyCloEnv, db, hints, *interpedArgs), db, env)
        case OpV(fn):
            interpedArgs = [interp(arg, env, db, hints) for arg in appArgs] if interpArgs else appArgs
            return rain_wrap(fn(None, env, db, hints, *interpedArgs), db, env)
        case nonCallable:
            raise Exception(f"Attempting to apply non-callable expression {nonCallable}")

def interp(expr, env, db, hints=dict()):
    match expr:
        case StringC(s):
            return StringV(s)
        case NumC(n):
            return NumberV(n)
        case FnC(args, body, recurse=recurse):
            return CloV(body, env=deepcopy(env), args=args, recurse=recurse)
        case ArrC(exprs):
            return ListV([interp(subexpr, env, db, hints) for subexpr in exprs])
        case IdC(id):
            match env.get(id):
                case None:
                    raise Exception(f"ID {id} is used before binding")
                case LazyEntV(table, tablename=tablename):
                    hint = hints.get(id)
                    if hint is None:
                        raise Exception(f"No variable supplied with name {id}")
                    ent_name = hint[1]
                    ent = db.get_entity_default_search_col(tablename, ent_name)
                    ent_val = EntV(ent, table=table, tablename=tablename)
                    env[id] = ent_val
                    return ent_val
                case val:
                    return val
        case DotAccessC(expr, idc):
            match [interp(expr, env, db, hints), idc]:
                case [EntV(ent, table=table, tablename=tablename), IdC(id)]:
                    if id not in table:
                        raise Exception(f"{id} is not a valid attribute of {tablename}: {ent}")
                    return rain_wrap(getattr(ent, id), db, env)
                case [PyCloV(fn, env=pyCloEnv, selfValue=selfValue), IdC(id)]:
                    val = rain_wrap(fn(selfValue, pyCloEnv, db, hints), db, env)
                    typeclass = tcs.VALUE_MAP[val.t]
                    attr = getattr(typeclass, id, None)
                    if not callable(attr):
                        raise Exception(f"Value '{val}' of type {val.t} has no method '{id}'")
                    return PyCloV(attr, env=deepcopy(env), selfValue=val)
                case [ObjectV(contents), IdC(id)]:
                    attr = getattr(contents, id, None)
                    if not callable(attr):
                        raise Exception(f"Value '{val}' of type object has no method '{id}'")
                    return PyCloV(attr, env=deepcopy(env), selfValue=None)
                case [TableV(table, session=session) as val, IdC(id)]:
                    # id refers to column
                    inspected = sqa.inspect(table)
                    # id refers to relationship
                    if id in sqa.inspect(table).relationships.keys():
                        rel = getattr(table, id)
                        query = session().query(table).filter(rel.has())
                    # id refers to column
                    elif id in table.__table__.c.keys():
                        col = sqa.sql.column(id)
                        query = session().query(table).filter(col != None)
                    # id refers to column property
                    elif id in [col.key for col in sqa.inspect(table).attrs]:
                        values = []
                        for row in session().query(table).all():
                            attr = getattr(row, id, None)
                            if attr is not None:
                                values.append(attr)
                        return values
                    # id refers to method
                    else:
                        attr = getattr(tcs.TableT, id, None)
                        if not callable(attr):
                            raise Exception(f"Value '{val}' of type table has no method '{id}'")
                        return PyCloV(attr, env=deepcopy(env), selfValue=val)

                    values = [getattr(ent, id) for ent in query]
                    return rain_wrap(values, db, env)
                case [RainV() as val, IdC(id)]:
                    typeclass = tcs.VALUE_MAP[val.t]
                    attr = getattr(typeclass, id, None)
                    if not callable(attr):
                        raise Exception(f"Value '{val}' of type {val.t} has no method '{id}'")
                    return PyCloV(attr, env=deepcopy(env), selfValue=val)
                case _:
                    raise Exception(f"Attempted dotaccess with non-id expr {idc}")
        case PoundAccessC(expr, idc):
            match [interp(expr, env, db, hints), idc]:
                case [ListV(values), IdC(id)]:
                    return rain_wrap([getattr(subval.value, id) for subval in values], db, env)
                case [ListV(), notId]:
                    raise Exception(f"Attemped pound access with non-id {notId}")
                case [notList, _]:
                    raise Exception(f"Attemped pound access on non-list {notList}")
        case BracketAccessC(expr0, expr1):
            id = interp(expr1, env, db, hints)
            if not isinstance(id, StringV):
                raise Exception(f"Attempted bracketed access with non-string value {id}")
            elif not re.match(r'[a-zA-Z_$][a-zA-Z_$0-9]*', id.value):
                raise Exception(f"Invalid bracket access string '{id.value}'")
            return interp(DotAccessC(expr0, IdC(id.value)), env, db, hints)
        case AppC(fnExpr, appArgs):
            return interp_appC(interp(fnExpr, env, db, hints), appArgs, env, db, hints)
        case FStringC(fstring, exprs):
            interped_exprs = [interp(expr, env, db, hints) for expr in exprs]
            return StringV(fstring.format(*interped_exprs))
        case CompC(expr0, comp, expr1):
            match [interp(expr0, env, db, hints), interp(expr1, env, db, hints)]:
                case [NumberV(n1), NumberV(n2)]: return rain_compare(n1, n2, comp)
                case [StringV(s1), StringV(s2)]: return rain_compare(s1, s2, comp)
                case [_, _]: return BoolV(False)
        case IfC(cond, l, r):
            match interp(cond, env, db, hints):
                case BoolV(True): return interp(l, env, db, hints)
                case BoolV(False): return interp(r, env, db, hints)
                case notBool: raise Exception("Non-bool if condition", notBool)