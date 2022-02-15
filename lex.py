from sly import Lexer

# These values are here outside the class to silence the linter
LVALUE = 0
ID = 0
ARROW = 0
INT = 0
FLOAT = 0
STRING = 0
PUNCT = 0
NUM = 0
_ = 0


class DBLexer(Lexer):
    tokens = { LVALUE, ID, NUM, PUNCT }

    ignore = ' \t'
    literals = { '{', '}'}

    @_(r'[a-zA-Z_$][a-zA-Z_$0-9]*(\.[a-zA-Z_$][a-zA-Z_$0-9]*)+')
    def LVALUE(self, t):
        t.value = t.value.split(".")
        return t
    
    ID = r'[a-zA-Z_$][a-zA-Z_$0-9]*'
    NUM = r'\d+\.{0,1}\d*'
    PUNCT = r'[^{}\w]+'


class DBLexer2(Lexer):
    def __init__(self):
        super()

    tokens = {
        LVALUE,
        ID,
        NUM,
        ARROW,
        INT,
        FLOAT,
        STRING,
        PUNCT,
    }

    ignore = ' \t'
    literals = { '=', '+', '-', '*', '/', '(', ')', '{', '}'}
    ARROW = r'=>'
    STRING = r'".+"'

    @_(r'[a-zA-Z_$][a-zA-Z_$0-9]*(\.[a-zA-Z_$][a-zA-Z_$0-9]*)+')
    def LVALUE(self, t):
        t.value = t.value.split(".")
        return t
    
    ID = r'[a-zA-Z_$][a-zA-Z_$0-9]*'

    @_(r'\d+\.\d+')
    def FLOAT(self, t):
        t.value = float(t.value)
        return t

    @_(r'\d+')
    def INT(self, t):
        t.value = int(t.value)
        return t
        
    # literals excluded
    PUNCT = r'[^=\(\){}\+\*/-]'


if __name__ == '__main__':
    data = "{PROF}'s phone number is {PROF.phone_number} \"string\" 456 232.45 hello.world.xyz () => * / + -"
    lexer = DBLexer()
    for tok in lexer.tokenize(data):
        print('type=%r, value=%r' % (tok.type, tok.value))
