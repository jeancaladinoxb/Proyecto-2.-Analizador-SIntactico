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

numeros = {"int":"tk_entero","float":"tk_flotante","hex":"tk_hexadecimal","bin":"tk_binario"}

operadores_multiples = {
    "!=": "tk_distinto", "<=": "tk_menor_igual", ">=": "tk_mayor_igual",
    "->": "tk_ejecuta", "=>": "tk_arrow_eq", "//": "tk_floor_div",
    "**": "tk_pow", "==":"tk_igual_igual"
}

operadores_unitarios = {
    "=":"tk_asig", "+":"tk_suma", "-":"tk_resta", "*":"tk_mul", "/":"tk_div",
    "(": "tk_par_izq", ")":"tk_par_der", ":":"tk_dos_puntos", ",":"tk_coma",
    ".":"tk_punto", "{":"tk_llave_izq", "}":"tk_llave_der", "[":"tk_cor_izq", "]":"tk_cor_der",
    "<":"tk_menor", ">":"tk_mayor"
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
        return f"Token({self.type!r}, {self.lexeme!r}, {self.line}, {self.col})"

def afd_identificador(source, start_index, fila, col):
    i = start_index
    lexema = ""
    if not (source[i].isalpha() or source[i] == "_"):
        error_lexico(fila, col, source[i])
    while i < len(source) and (source[i].isalnum() or source[i] == "_"):
        lexema += source[i]
        i += 1
        col += 1
    if lexema in palabras_reservadas:
        tk_type = keyword_to_token[lexema]
        return Token(tk_type, lexema, fila, col - len(lexema)), i, col
    else:
        return Token("tk_id", lexema, fila, col - len(lexema)), i, col

def afd_numero(source, start_index, fila, col):
    i = start_index
    lexema = ""
    puntos = 0
    while i < len(source):
        c = source[i]
        if c.isdigit():
            lexema += c
            i += 1
            col += 1
        elif c == ".":
            puntos += 1
            if puntos > 1:
                break
            lexema += c
            i += 1
            col += 1
        else:
            break
    if "." in lexema:
        return Token("tk_flotante", lexema, fila, col - len(lexema)), i, col
    else:
        return Token("tk_entero", lexema, fila, col - len(lexema)), i, col

def afd_cadena(source, start_index, fila, col):
    i = start_index
    quote = source[i]
    lexema = quote
    i += 1
    col += 1
    triple = False
    if i + 1 < len(source) and source[i] == quote and source[i+1] == quote:
        triple = True
        lexema += quote + quote
        i += 2
        col += 2
    inicio_col = col
    while i < len(source):
        c = source[i]
        lexema += c
        i += 1
        if c == "\n":
            fila += 1
            col = 1
        else:
            col += 1
        if not triple and c == quote:
            return Token("tk_cadena", lexema, fila, inicio_col-1), i, col
        if triple and i+1 < len(source) and source[i] == quote and source[i+1] == quote:
            lexema += quote + quote
            i += 2
            col += 2
            return Token("tk_cadena", lexema, fila, inicio_col-1), i, col
    error_lexico(fila, col, source[i-1] if i-1 < len(source) else "")

def afd_operador_multiple(source, start_index, fila, col):
    i = start_index
    if i+1 >= len(source):
        return None, start_index, col
    posible = source[i:i+2]
    if posible in operadores_multiples:
        tk = operadores_multiples[posible]
        i += 2
        col += 2
        return Token(tk, posible, fila, col-2), i, col
    return None, start_index, col

def afd_operador_unitario(source, start_index, fila, col):
    i = start_index
    c = source[i]
    if c in operadores_unitarios:
        tk = operadores_unitarios[c]
        i += 1
        col += 1
        return Token(tk, c, fila, col-1), i, col
    else:
        error_lexico(fila, col, c)

def analizar(source):
    tokens = []
    fila, col = 1, 1
    i = 0
    indent_stack = [0]
    start_of_line = True

    while i < len(source):
        if start_of_line:
            j = i
            espacio = 0
            while j < len(source) and source[j] in (" ", "\t"):
                if source[j] == " ":
                    espacio += 1
                else:
                    espacio += 8
                j += 1

            if j >= len(source):
                i = j
                start_of_line = True
                continue
            if source[j] == "\n":
                i = j
                start_of_line = True
            elif source[j] == "#":
                i = j
                while i < len(source) and source[i] != "\n":
                    i += 1
                start_of_line = True
                continue
            else:
                current = indent_stack[-1]
                if espacio > current:
                    indent_stack.append(espacio)
                    tokens.append(Token("INDENT", "<INDENT>", fila, 1))
                else:
                    while espacio < indent_stack[-1]:
                        indent_stack.pop()
                        tokens.append(Token("DEDENT", "<DEDENT>", fila, 1))
                    if espacio != indent_stack[-1]:
                        raise ErrorLexico(f"Error lexico (linea:{fila}) indentacion invalida (col {col})")
                i = j
                col = espacio + 1
                start_of_line = False
                continue

        c = source[i]

        if c == " " or c == "\t":
            i += 1
            col += 1
            continue
        if c == "\n":
            tokens.append(Token("NEWLINE", "\\n", fila, col))
            i += 1
            fila += 1
            col = 1
            start_of_line = True
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
        if i + 1 < len(source):
            tok, new_i, new_col = afd_operador_multiple(source, i, fila, col)
            if tok is not None:
                tokens.append(tok)
                i, col = new_i, new_col
                continue
        if c in operadores_unitarios:
            tok, i, col = afd_operador_unitario(source, i, fila, col)
            tokens.append(tok)
            continue

        error_lexico(fila, col, c)

    while len(indent_stack) > 1:
        indent_stack.pop()
        tokens.append(Token("DEDENT", "<DEDENT>", fila, 1))

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
