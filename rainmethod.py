from pprint import pprint

def rainmethod(paramNames, standalone=False):
    if standalone is False:
        paramNames.insert(0, "self")

    def decorator(fn):
        def wrapped(self, env, db, hints, *args):
            args = [*args]
            if self is not None:
                args.insert(0, self)
            zipped_args = dict(zip(paramNames, args))
            return fn({**env, **zipped_args}, db, hints)
        return wrapped
    return decorator


@rainmethod(["l", "r"], standalone=True)
def RAIN_ADD(env, db, hints):
    return env["l"].value + env["r"].value

@rainmethod(["l", "r"], standalone=True)
def RAIN_SUBTRACT(env, db, hints):
    return env["l"].value - env["r"].value

@rainmethod(["l", "r"], standalone=True)
def RAIN_MULTIPLY(env, db, hints):
    return env["l"].value * env["r"].value

@rainmethod(["l", "r"], standalone=True)
def RAIN_DIVIDE(env, db, hints):
    return env["l"].value / env["r"].value

@rainmethod(["l", "r"], standalone=True)
def RAIN_MOD(env, db, hints):
    return env["l"].value % env["r"].value

@rainmethod(["l", "r"], standalone=True)
def RAIN_EXP(env, db, hints):
    return env["l"].value ** env["r"].value 

@rainmethod(["l", "r"], standalone=True)
def RAIN_EQUAL(env, db, hints):
    return env["l"].value == env["r"].value

@rainmethod(["l", "r"], standalone=True)
def RAIN_NOT_EQUAL(env, db, hints):
    return env["l"].value != env["r"].value

@rainmethod(["l", "r"], standalone=True)
def RAIN_GREATER_THAN(env, db, hints):
    return env["l"].value > env["r"].value

@rainmethod(["l", "r"], standalone=True)
def RAIN_GREATER_TO_OR_EQUAL(env, db, hints):
    return env["l"].value >= env["r"].value

@rainmethod(["l", "r"], standalone=True)
def RAIN_LESS_THAN(env, db, hints):
    return env["l"].value < env["r"].value

@rainmethod(["l", "r"], standalone=True)
def RAIN_LESS_TO_OR_EQUAL(env, db, hints):
    return env["l"].value <= env["r"].value

@rainmethod(["val"], standalone=True)
def RAIN_NOT(env, db, hints):
    match env["val"].value:
        case True: return False
        case False: return True
        case notBool: raise Exception(f"Attempted not of non-bool value {notBool}")

@rainmethod(["l", "r"], standalone=True)
def RAIN_AND(env, db, hints):
    match [env["l"].value, env["r"].value]:
        case [True, True]:
            return True
        case [v1, v2] if type(v1) == type(v2) == bool:
            return False
        case [notBool1, notBool2]:
            raise Exception(f"Attempted and of non-bool value {notBool1} or {notBool2}")

@rainmethod(["l", "r"], standalone=True)
def RAIN_OR(env, db, hints):
    match [env["l"].value, env["r"].value]:
        case [False, False]:
            return False
        case [v1, v2] if type(v1) == type(v2) == bool:
            return True
        case [notBool1, notBool2]:
            raise Exception(f"Attempted or of non-bool value {notBool1} or {notBool2}")

@rainmethod(["l", "r"], standalone=True)
def RAIN_XOR(env, db, hints):
    match [env["l"].value, env["r"].value]:
        case [True, True] | [False, False]:
            return False
        case [True, False] | [False, True]:
            return True
        case [notBool1, notBool2]:
            raise Exception(f"Attempted xor of non-bool value {notBool1} or {notBool2}")

@rainmethod(["l", "r"], standalone=True)
def RAIN_NAND(env, db, hints):
    match [env["l"].value, env["r"].value]:
        case [True, True]:
            return False
        case [v1, v2] if type(v1) == type(v2) == bool:
            return True
        case [notBool1, notBool2]:
            raise Exception(f"Attempted nand of non-bool value {notBool1} or {notBool2}")

@rainmethod(["l", "r"], standalone=True)
def RAIN_NOR(env, db, hints):
    match [env["l"].value, env["r"].value]:
        case [False, False]:
            return True
        case [v1, v2] if type(v1) == type(v2) == bool:
            return False
        case [notBool1, notBool2]:
            raise Exception(f"Attempted nor of non-bool value {notBool1} or {notBool2}")

@rainmethod(["l", "r"], standalone=True)
def RAIN_XNOR(env, db, hints):
    match [env["l"].value, env["r"].value]:
        case [True, True] | [False, False]:
            return True
        case [True, False] | [False, True]:
            return False
        case [notBool1, notBool2]:
            raise Exception(f"Attempted xor of non-bool value {notBool1} or {notBool2}")

@rainmethod(["s"], standalone=True)
def RAIN_TO_NUM(env, db, hints):
    sVal = env["s"].value
    try:
        return int(sVal)
    except ValueError:
        return float(sVal)
    except:
        return None

@rainmethod(["n"], standalone=True)
def RAIN_TO_STR(env, db, hints):
    try:
        return str(env["n"].value)
    except:
        return None