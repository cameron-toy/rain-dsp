import re
import copy

def parse_question_format(q):
    pattern = r'\{(.*?)\}'
    matches = re.finditer(pattern, q, re.MULTILINE | re.DOTALL)
    types = dict()

    for m in matches:
        captured = m.group(1)
        splitted = [c.strip() for c in captured.split(":")]
        match splitted:
            case [v, t]:
                types[v] = [t, None]
            case [v]:
                i = 0
                while types.get(f"{v}{i}") is not None:
                    i += 1
                types[f"{v}{i}"] = [v, None]
            case _:
                raise ValueError()
    
    return types

def generate_answer_function(parser, lexer, qformat, aformat):
    _hints = parse_question_format(qformat)
    tokens = lexer.tokenize(aformat)
    
    # for tok in tokens:
    #     print('type=%r, value=%r' % (tok.type, tok.value))

    def wrapped(**kwargs):
        hints = copy.deepcopy(_hints)
        for k, v in kwargs.items():
            hint = hints.get(k)
            if hint is not None:
                hint[1] = v
        return parser.parse_with_hints(tokens, hints)
    
    return wrapped
