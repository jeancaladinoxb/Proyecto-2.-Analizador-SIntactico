palabras_reservadas = {
    "False", "await", "else", "import", "pass",
    "None", "break", "except", "in", "raise",
    "True", "class", "finally", "is", "return",
    "and", "continue", "for", "lambda", "try",
    "as", "def", "from", "nonlocal", "while",
    "assert", "del", "global", "not", "with",
    "async", "elif", "if", "or", "yield"
}

keyword_to_token = {kw: f"tk_{kw}" for kw in palabras_reservadas}

operadores_multiples = {
    "!=": "tk_distinto", "<=": "tk_menor_igual", ">=": "tk_mayor_igual",
    "//": "tk_floor_div", "**": "tk_pow", "==":"tk_igual_igual"
}

operadores_unitarios = {
    "=":"tk_asig", "+":"tk_suma", "-":"tk_resta", "*":"tk_mul", "/":"tk_div",
    "(": "tk_par_izq", ")":"tk_par_der", ":":"tk_dos_puntos", ",":"tk_coma",
    ".":"tk_punto", "{":"tk_llave_izq", "}":"tk_llave_der", "[":"tk_cor_izq",
    "]":"tk_cor_der", "<":"tk_menor", ">":"tk_mayor"
}

class ErrorLexico(Exception):
    pass

def error_lexico(fila, col, c):
    raise ErrorLexico(
        f"Error lexico (linea:{fila}, posicion:{col}) el caracter inesperado es '{c}'"
    )

class Token:
    def __init__(self, type_, lexeme, line, col):
        self.type = type_
        self.lexeme = lexeme
        self.line = line
        self.col = col
    def __repr__(self):
        return f"Token({self.type}, {self.lexeme!r}, {self.line}, {self.col})"

def afd_identificador(source, start_index, fila, col):
    i = start_index
    lexema = ""
    while i < len(source) and (source[i].isalnum() or source[i] == "_"):
        lexema += source[i]
        i += 1
        col += 1
    if lexema in palabras_reservadas:
        return Token(keyword_to_token[lexema], lexema, fila, col), i, col
    return Token("tk_id", lexema, fila, col), i, col

def afd_numero(source, start_index, fila, col):
    i = start_index
    lexema = ""
    puntos = 0
    while i < len(source):
        if source[i].isdigit():
            lexema += source[i]
            i += 1
            col += 1
        elif source[i] == ".":
            puntos += 1
            if puntos > 1:
                break
            lexema += source[i]
            i += 1
            col += 1
        else:
            break
    token_type = "tk_flotante" if "." in lexema else "tk_entero"
    return Token(token_type, lexema, fila, col), i, col

def afd_cadena(source, start_index, fila, col):
    i = start_index
    quote = source[i]
    lexema = quote
    i += 1
    col += 1
    while i < len(source):
        lexema += source[i]
        if source[i] == quote:
            i += 1
            col += 1
            return Token("tk_cadena", lexema, fila, col), i, col
        i += 1
        col += 1
    error_lexico(fila, col, quote)

def afd_operador_multiple(source, start_index, fila, col):
    if start_index + 1 >= len(source):
        return None, start_index, col
    posible = source[start_index:start_index+2]
    if posible in operadores_multiples:
        return Token(operadores_multiples[posible], posible, fila, col+2), start_index+2, col+2
    return None, start_index, col

def afd_operador_unitario(source, start_index, fila, col):
    c = source[start_index]
    if c in operadores_unitarios:
        return Token(operadores_unitarios[c], c, fila, col+1), start_index+1, col+1
    error_lexico(fila, col, c)

def analizar(source):
    tokens = []
    fila, col, i = 1, 1, 0

    while i < len(source):
        c = source[i]
        if c in " \t":
            i += 1
            col += 1
            continue
        if c == "\n":
            fila += 1
            col = 1
            i += 1
            continue
        if c == "#":
            while i < len(source) and source[i] != "\n":
                i += 1
            continue
        if c.isalpha() or c == "_":
            tok, i, col = afd_identificador(source, i, fila, col)
            tokens.append(tok)
            continue
        if c.isdigit():
            tok, i, col = afd_numero(source, i, fila, col)
            tokens.append(tok)
            continue
        if c in ("'", '"'):
            tok, i, col = afd_cadena(source, i, fila, col)
            tokens.append(tok)
            continue
        tok, new_i, new_col = afd_operador_multiple(source, i, fila, col)
        if tok:
            tokens.append(tok)
            i, col = new_i, new_col
            continue
        if c in operadores_unitarios:
            tok, i, col = afd_operador_unitario(source, i, fila, col)
            tokens.append(tok)
            continue
        error_lexico(fila, col, c)

    tokens.append(Token("EOF", "<EOF>", fila, col))
    return tokens

def main():
    with open("entrada.py", "r", encoding="utf-8") as f:
        source = f.read()
    try:
        tokens = analizar(source)
        with open("salida.txt", "w", encoding="utf-8") as f:
            for t in tokens:
                f.write(repr(t) + "\n")
    except ErrorLexico as e:
        with open("salida.txt", "w", encoding="utf-8") as f:
            f.write(str(e) + "\n")

if __name__ == "__main__":
    main()

