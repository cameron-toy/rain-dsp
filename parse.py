from sly import Parser
from lex import DBLexer, RainLexer, RainValueLexer
from entities.Professor import ProfessorEnt
from entities.Club import ClubEnt
from db import Database
from qa import generate_answer_function
from rain_types import EntV, LazyEntV, ListV, NumberV, StringV, get_raintype, CloV
from pprint import pprint
from copy import deepcopy

# Silence the linter
_ = 0
debugfile = 0

class RainParser(Parser):
    debugfile = 'parser.out'
    tokens = RainLexer.tokens

    def __init__(self, db):
        super()
        self.value_parser = RainValueParser(db)
        self.db = db

    def parse_with_hints(self, toks, hints):
        self.value_parser.hints = hints
        self.value_parser.names = {k : LazyEntV(self.db.type_map[self.db.entity_types[v[0]]], v[0]) for k, v in hints.items()}
        return self.parse(toks)

    @_('TEXT')
    def text(self, p):
        return p.TEXT

    @_('text text')
    def text(self, p):
        return p.text0 + p.text1
    
    @_('VALUE')
    def text(self, p):
        return self.value_parser.parse(p.VALUE)._
    

class RainValueParser(Parser):
    tokens = RainValueLexer.tokens

    def __init__(self, db):
        super()
        self.names = dict()
        self.hints = dict()
        self.db = db

    def _wrap_in_raintype(self, val):
        val_type = get_raintype(val)
        match val_type:
            case "string": return StringV(val)
            case "number": return NumberV(val)
            case "list": return ListV(val, "empty" if len(val) == 0 else get_raintype(val[0]))
            case "closure": return CloV(val, deepcopy(self.names))
            case "entity":
                tablename = val._sa_instance_state.class_.__name__
                return EntV(val, self.db.type_map[tablename], tablename)
            case _: raise Exception(f"Can't automatically wrap value {val} of type {val_type}")

    @_('ID')
    def val(self, p):
        value = self.names.get(p.ID)
        match value:
            case None:
                raise Exception(f"ID {p.ID} is used before binding")
            case LazyEntV(table, tablename):
                hint = self.hints.get(p.ID)
                if hint is None:
                    raise Exception(f"No variable supplied with name {p.ID}")
                ent_name = hint[1]
                ent = self.db.get_entity_default_search_col(tablename, ent_name)
                ent_val = EntV(ent, table, tablename)
                self.names[p.ID] = ent_val
                return EntV(ent, table, tablename)
            case _:
                return value
    
    @_('val DOTACCESS')
    def val(self, p):
        if isinstance(p.val, EntV):
            ent, table, tablename, _ = p.val
            if p.DOTACCESS not in table:
                raise Exception(f"{p.DOTACCESS} is not a valid attribute of {tablename} {ent}")
            return self._wrap_in_raintype(getattr(ent, p.DOTACCESS))

        attr = p.val._attrs.get(p.DOTACCESS)
        if attr is None:
            raise Exception(f"Value {p.val} has no attribute {p.DOTACCESS}")

        return self._wrap_in_raintype(attr)

    

    @_('NUM', 'STRING')
    def val(self, p):
        return self._wrap_in_raintype(p[0])



class DBParser(Parser):
    def __init__(self, db):
        super()
        self.names = dict()
        self.hints = dict()
        self.db = db

    def parse_with_hints(self, toks, hints):
        self.hints = hints
        self.names = {k:v[1] for k, v in hints.items()}
        return self.parse(toks)

    debugfile = 'parser.out'
    tokens = DBLexer.tokens

    @_('"{" expr "}"')
    def expr(self, p):
        return p.expr

    @_('ID')
    def expr(self, p):
        return self.names.get(p.ID) or p.ID
    
    @_('LVALUE')
    def expr(self, p):
        hint = self.hints.get(p.LVALUE[0])
        if hint == None:
            raise ValueError(f"No bound variable with name {p.LVALUE[0]}")
        
        table, ent_name = hint
        prop_name = p.LVALUE[1]
        current_ent = self.db.entity_types[table]
        attr_type = self.db.type_map[current_ent].get(prop_name)
        if prop_name not in self.db.type_map[current_ent]:
            raise Exception(f"'{prop_name} is not an attribute of {self.db.entity_types[table]}")

        prop = self.db.get_prop_from_entity(table, ent_name, prop_name)

        current_ent = attr_type.key

        for i in range(2, len(p.LVALUE)):
            attr_name = p.LVALUE[i]
            attr_type = self.db.type_map[current_ent].get(attr_name)
            if attr_type is None:
                raise Exception(f"'{attr_name}' is not an attribute of '{current_ent}'")
            
            current_ent = attr_type.key

            prop = getattr(prop, attr_name)

        return prop
    
    @_('NUM')
    def expr(self, p):
        return p.NUM

    @_('expr expr')
    def expr(self, p):
        return f"{p.expr0} {p.expr1}"
    
    @_('expr PUNCT')
    def expr(self, p):
        return f"{p.expr}{p.PUNCT}"

    @_('PUNCT')
    def expr(self, p):
        return p.PUNCT
    

def main():
    DB_FILE = "calpoly.db"
    db = Database(DB_FILE, [ProfessorEnt, ClubEnt], {ProfessorEnt: "alias", ClubEnt: "name"})
    
    lexer = DBLexer()
    parser = DBParser(db)

    get_prof_email = generate_answer_function(parser, lexer,
        "What is {prof:professor}'s email?",
        "{prof.name}'s email is {prof.email}"
    )

    get_club_advisor_alias = generate_answer_function(parser, lexer,
        "Who is the advisor of {club}?",
        "{club.advisor_alias} advises {club}"
    )

    get_club_advisor_email = generate_answer_function(parser, lexer,
        "What is the email of {club}'s advisor?",
        "{club.name}'s advisor is {club.advisor.name} and their email is {club.advisor.email}."
    )

    error1 = generate_answer_function(parser, lexer,
        "What is the ssn of {club}'s advisor?",
        "{club.name}'s advisor is {club.advisor.name} and their ssn is {club.advisor.ssn}"
    )

    print()
    print(get_prof_email(prof="foaad"))
    print(get_club_advisor_alias(club="Cal Poly Mycology Club"))
    print(get_club_advisor_email(club="Cal Poly Mycology Club"))

    print(error1(club="Cal Poly Mycology Club"))


def new_parser_test():
    DB_FILE = "calpoly.db"
    db = Database(DB_FILE, [ProfessorEnt, ClubEnt], {ProfessorEnt: "alias", ClubEnt: "name"})
    
    lexer = RainLexer()
    parser = RainParser(db)

    get_prof_email = generate_answer_function(parser, lexer,
        "What is {prof:professor}'s email?",
        "{prof.name}'s email is {prof.email}"
    )

    # get_club_advisor_alias = generate_answer_function(parser, lexer,
    #     "Who is the advisor of {club}?",
    #     "{club.advisor_alias} advises {club}"
    # )

    get_club_advisor_email = generate_answer_function(parser, lexer,
        "What is the email of {club}'s advisor?",
        "{club.name}'s advisor is {club.advisor.name} and their email is {club.advisor.email}."
    )

    # error1 = generate_answer_function(parser, lexer,
    #     "What is the ssn of {club}'s advisor?",
    #     "{club.name}'s advisor is {club.advisor.name} and their ssn is {club.advisor.ssn}"
    # )

    print()
    print(get_prof_email(prof="foaad"))
    # print(get_club_advisor_alias(club="Cal Poly Mycology Club"))
    print(get_club_advisor_email(club="Cal Poly Mycology Club"))

    # print(error1(club="Cal Poly Mycology Club"))


if __name__=="__main__":
    new_parser_test()

