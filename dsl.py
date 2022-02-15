def tokenize(s):
    if len(s) == 0:
        return []

    toks = []
    tstart = 0
    depth = 0
    i = 0

    while i < len(s):
        c = s[i]
        if c == "[":
            if depth == 0:
                tstart = i
            depth += 1
        elif c == "]":
            depth -= 1
            if depth == 0:
                toks.append(s[tstart:i+1])
                i += 1
                tstart = i + 1
        elif c == " " and depth == 0:
            toks.append(s[tstart:i])
            tstart = i + 1
        i += 1
    
    if (tstart < len(s)):
        toks.append(s[tstart:len(s)])
    
    return toks


def interp(db, s):
    result = []
    for tok in tokenize(s):
        if not tok.startswith("["):
            result.append(tok)
            continue
        
        subtokens = tok[1:-1].split(".")
        if len(subtokens) == 3:
            table, val, col = subtokens
            result.append(db.get_prop_from_entity(table, val, col))
    
    return " ".join(result)
