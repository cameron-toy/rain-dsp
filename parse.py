from sly import Parser
from lex import DBLexer
from entities.Professor import ProfessorEnt
from entities.Club import ClubEnt
from db import Database
from qa import generate_answer_function

# Silence the linter
_ = 0
debugfile = 0


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
        else:
            table, ent_name = hint
            return self.db.get_prop_from_entity(table, ent_name, p.LVALUE[1])
    
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
    

if __name__=="__main__":
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
        "{club0.advisor_alias} advises {club0}"
    )

    print()
    print(get_prof_email(prof="foaad"))
    print(get_club_advisor_alias(club0="Cal Poly Mycology Club"))

