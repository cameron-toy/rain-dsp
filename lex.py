from sly import Lexer

# These values are here outside the class to silence the linter
DOTACCESS = None
_ = None
ID = None
NUM = None
STRING = None
EQEQ = None
FN = None
INT = None
FLOAT = None
COMP = None
ARROW = None
PLUS = None
MINUS = None
STAR = None
TIMES = None
SLASH = None
MOD = None
AND = None
OR = None
QQ = None
LET = None
IN = None
FSTRING_START = None
FSTRING_MID = None
FSTRING_END = None
IF = None


class RainValueLexer2(Lexer):
    tokens = {
        ID,
        INT,
        FLOAT,
        STRING,
        COMP,
        FN,
        ARROW,
        LET,
        IN,
        FSTRING_START,
        FSTRING_MID,
        FSTRING_END,
        IF
    }

    ignore = ' \t\n'
    literals = { '(', ')', '.', '[', ']', '=', '#'}

    @_(r'`(.*?)\{')
    def FSTRING_START(self, t):
        t.value = t.value[1:-1]
        return t

    @_(r'\}([^\{}]*?)`')
    def FSTRING_END(self, t):
        t.value = t.value[1:-1]
        return t

    @_(r'\}(.*?)\{')
    def FSTRING_MID(self, t):
        t.value = t.value[1:-1]
        return t

    @_(r'\-{0,1}\d+\.\d+')
    def FLOAT(self, t):
        t.value = float(t.value)
        return t

    @_(r'\-{0,1}\d+')
    def INT(self, t):
        t.value = int(t.value)
        return t

    ARROW = r'->'
    ID = r'[a-zA-Z_$\*\+\-\<\>\?][a-zA-Z_$0-9\*\+\-\<\>\?]*'
    ID["fn"] = FN
    ID["let"] = LET
    ID["in"] = IN
    ID["if"] = IF

    @_(r'"(?:(?:(?!(?<!\\)").)*)"', r'`(.*?)`')
    def STRING(self, t):
        t.value = t.value[1:-1]
        return t
