from pprint import pprint
from sly import Parser
from sqlalchemy import table
from lex import RainValueLexer2
from entities.Club import ClubEnt
from entities.Professor import ProfessorEnt
from entities.Department import DepartmentEnt
from entities.Course import CourseEnt
from entities.Location import LocationEnt
from entities.Section import SectionEnt
from db import Database
from qa import generate_answer_function
from rain_types import *
from interp import interp
import typeclasses as tcs
import weakref
import rainmethod as rmethod

class Oracle:
    def __init__(self, db):
        self.qa = dict()
        self.db = db
        self.lexer = RainValueLexer2()
        self.parser = RainValueParser2(db)

    def add_qa(self, qformat, aformat):
        self.qa[qformat.lower()] = generate_answer_function(
            self.parser,
            self.lexer,
            qformat,
            aformat
        )
    
    def answer(self, qformat, **kwargs):
        afunction = self.qa.get(qformat)
        if afunction is None:
            raise Exception(f"Answer format for question format '{qformat}' not found")
        parsed = afunction(**kwargs)
        pprint(parsed)
        print()
        return interp(parsed, self.parser.env, self.parser.db, self.parser.hints)

# Silence the linter
_ = None
debugfile = None


DEFAULT_ENV = {
    "true": BoolV(True),
    "false": BoolV(False),
    "none": NoneV(),
    "List": ObjectV(tcs.ListT),
    "Table": ObjectV(tcs.TableT),
    "String": ObjectV(tcs.StringT),
    "+": OpV(rmethod.RAIN_ADD),
    "-": OpV(rmethod.RAIN_SUBTRACT),
    "*": OpV(rmethod.RAIN_MULTIPLY),
    "/": OpV(rmethod.RAIN_DIVIDE),
    "mod": OpV(rmethod.RAIN_MOD),
    "exp": OpV(rmethod.RAIN_EXP),
    "eq?": OpV(rmethod.RAIN_EQUAL),
    "equal?": OpV(rmethod.RAIN_EQUAL),
    "ne?": OpV(rmethod.RAIN_NOT_EQUAL),
    "not-equal?": OpV(rmethod.RAIN_NOT_EQUAL),
    "gt?": OpV(rmethod.RAIN_GREATER_THAN),
    "lt?": OpV(rmethod.RAIN_LESS_THAN),
    "le?": OpV(rmethod.RAIN_LESS_TO_OR_EQUAL),
    "not": OpV(rmethod.RAIN_NOT),
    "and": OpV(rmethod.RAIN_AND),
    "or": OpV(rmethod.RAIN_OR),
    "xor": OpV(rmethod.RAIN_XOR),
    "nand": OpV(rmethod.RAIN_NAND),
    "nor": OpV(rmethod.RAIN_NOR),
    "xnor": OpV(rmethod.RAIN_XNOR),
    "num": OpV(rmethod.RAIN_TO_NUM),
    "str": OpV(rmethod.RAIN_TO_STR)
}

class RainValueParser2(Parser):
    tokens = RainValueLexer2.tokens

    def __init__(self, db):
        self.env = RainValueParser2.make_env(db)
        self.hints = dict()
        self.db = db

    @staticmethod
    def make_env(db):
        env = dict()
        for table, config in db.entity_config.items():
            env[config.get("name_remapping") or table.__tablename__] = TableV(table, session=weakref.ref(db.session))
        return { **DEFAULT_ENV, **env }

    def parse_with_hints(self, toks, hints):
        self.hints = hints
        env_from_hints = dict()
        for k, v in hints.items():
            vtype = v[0]
            env_from_hints[k] = LazyEntV(self.db.type_map[self.db.entity_types[vtype]], tablename=vtype)
        # env_from_hints = {k : LazyEntV(self.db.type_map[self.db.entity_types[v[0]]], tablename=v[0]) for k, v in hints.items()}
        self.env = { **RainValueParser2.make_env(self.db), **env_from_hints }
        return self.parse(toks)

    @_('INT', 'FLOAT')
    def expr(val, p):
        return NumC(p[0])
    
    @_('STRING')
    def expr(val, p):
        return StringC(p.STRING)

    # Remove shift/reduce conflict here (ends in expr)
    @_("LET ID '=' expr IN expr")
    def expr(val, p):
        return AppC(
            FnC([p.ID], p.expr1, recurse=True),
            [p.expr0]
        )
    
    @_("FSTRING_START")
    def fstring_frag(val, p):
        return FStringC(p[0], [])

    # Remove shift/reduce conflict here
    @_("fstring_frag expr")
    def fstring_frag(val, p):
        p.fstring_frag.fstring += f"{{{len(p.fstring_frag.exprs)}}}"
        p.fstring_frag.exprs.append(p.expr)
        return p.fstring_frag
    
    @_("fstring_frag FSTRING_MID")
    def fstring_frag(val, p):
        p.fstring_frag.fstring += p.FSTRING_MID
        return p.fstring_frag
    
    @_("fstring_frag FSTRING_END")
    def expr(val, p):
        p.fstring_frag.fstring += p.FSTRING_END
        return p.fstring_frag

    @_("expr '.' ID")
    def expr(val, p):
        return DotAccessC(p.expr, IdC(p.ID))

    @_("expr '#' ID")
    def expr(val, p):
        return PoundAccessC(p.expr, IdC(p.ID))
    
    # @_("expr '[' expr ']'")
    # def expr(val, p):
    #     return BracketAccessC(p.expr0, p.expr1)

    @_("'(' IF expr expr expr ')'")
    def expr(val, p):
        return IfC(p.expr0, p.expr1, p.expr2)

    @_("'(' FN '('")
    def fnargs(val, _):
        return []

    @_("fnargs ID")
    def fnargs(val, p):
        return [*p.fnargs, p.ID]

    @_("fnargs ')' ARROW expr ')'")
    def expr(val, p):
        return FnC(p.fnargs, p.expr)
    
    @_("'['")
    def partial_arr(val, _):
        return []

    # Remove shift/reduce conflcit here
    @_("partial_arr expr")
    def partial_arr(val, p):
        return [*p.partial_arr, p.expr]

    @_("partial_arr ']'")
    def expr(val, p):
        return ArrC(p.partial_arr)

    # Remove shift/reduce conflict here
    @_("'(' expr")
    def partial_app(val, p):
        return (p.expr, [])
    
    # Remove shift/reduce conflict here
    @_("partial_app expr")
    def partial_app(val, p):
        fn, args = p.partial_app
        return (fn, [*args, p.expr])

    @_("partial_app ')'")
    def expr(val, p):
        fn, args = p.partial_app
        return AppC(fn, args)

    # Remove shift/reduce conflict here
    @_("expr COMP expr")
    def expr(val, p):
        return CompC(p.expr0, p.COMP, p.expr1)

    @_('ID')
    def expr(val, p):
        return IdC(p.ID)


def new_parser_test():
    DB_FILE = "calpoly.db"
    db = Database(
        DB_FILE,
        [
            ProfessorEnt,
            ClubEnt,
            DepartmentEnt,
            LocationEnt,
            CourseEnt,
            SectionEnt
        ],
        {
            ProfessorEnt: "alias",
            ClubEnt: "name",
            DepartmentEnt: "name",
            LocationEnt: "id",
            CourseEnt: "title",
            SectionEnt: "title"

        }
    )
    oracle = Oracle(db)
    oracle.add_qa(
        "What is {prof:professor}'s email?",
        "`${prof.name}'s email is ${prof.email}`"
    )

    oracle.add_qa(
        "fntest",
        'let fib = (fn (n) -> (if (le? n 1) n (+ (fib (- n 1)) (fib (- n 2))))) in'
        '(fib 7)'
    )

    oracle.add_qa(
        "fntest2",
        '(List.at ([2 1 3].sort_by (fn (x) -> (* x -1))) 0)'
    )

    oracle.add_qa(
        "Does {prof:professor} advise any clubs?",
        '(if (prof.advises.empty)'
            '`No, {prof.name} does not advise any clubs`'
            '`Yes, {prof.name} advises {(List.gjoin (prof.advises.map (fn (club) -> club.name)) "and")}`)'
    )

    oracle.add_qa(
        "What classes does {prof:professor} teach?",
        '(if (prof.teaches.empty)'
            '`{prof.name} does not teach any courses this quarter`'
            '`{prof.name} teaches {(prof.teaches#course#name.dedup.gjoin "and")}`)'
    )

    print(oracle.answer("fntest2"))
    # print(oracle.answer("What classes does {prof:professor} teach?", prof="husmith"))
    # print(oracle.answer("Does {prof:professor} advise any clubs?", prof="sding01"))


if __name__=="__main__":
    new_parser_test()