from sly import Lexer

# These values are here outside the class to silence the linter
LVALUE = None
DOTACCESS = None
ID = None
ARROW = None
INT = None
FLOAT = None
STRING = None
PUNCT = None
NUM = None
CALL = None
_ = None


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


VALUE = 0
TEXT = 0

class RainLexer(Lexer):
    tokens = { VALUE, TEXT }

    def __init__(self):
        self.valueLexer = RainValueLexer()

    @_(r"\{(.*?)\}")
    def VALUE(self, t):
        t.value = self.valueLexer.tokenize(t.value[1:-1])
        return t

    @_(r"[^\{]+")
    def TEXT(self, t):
        return t


class RainValueLexer(Lexer):
    tokens = { DOTACCESS, ID, NUM, STRING }

    ignore = ' \t'
    literals = { '(', ')', ',' }

    @_(r'\.[a-zA-Z_$][a-zA-Z_$0-9]*')
    def DOTACCESS(self, t):
        t.value = t.value[1:]
        return t
    
    ID = r'[a-zA-Z_$][a-zA-Z_$0-9]*'

    @_(r'\d+\.{0,1}\d*')
    def NUM(self, t):
        t.value = float(t.value)
        return t

    STRING = r'".+"'
    

class DBLexer3(Lexer):
    tokens = { DOTACCESS, ID, NUM, PUNCT, STRING }

    ignore = ' \t'
    literals = { '{', '}', '[', ']' }

    @_(r"\.[a-zA-Z_$][a-zA-Z_$0-9]*")
    def DOTACCESS(self, t):
        t.value = t.value[1:]
        return t
    
    ID = r'[a-zA-Z_$][a-zA-Z_$0-9]*'
    NUM = r'\d+\.{0,1}\d*'
    STRING = r'".+"'
    PUNCT = r'[^\w{}\[\]]+'


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


def print_tok(tok, depth=0):
    if tok.type == "VALUE":
        print("\t" * depth, f"type=VALUE")
        for t in tok.value:
            print_tok(t, depth + 1)
    else:
        print("\t" * depth, f"type={tok.type}, value={tok.value}")

if __name__ == '__main__':
    data = "{prof.name} advises {prof.advises(\"hello\", 0)}"
    lexer = RainLexer()
    for tok in lexer.tokenize(data):
        print_tok(tok)
