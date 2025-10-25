# Diccionarios y SETS de palabras reservadas y operadores
palabras_reservadas = {
    "False", "await", "else", "import", "pass",
    "None", "break", "except", "in", "raise",
    "True", "class", "finally", "is", "return",
    "and", "continue", "for", "lambda", "try",
    "as", "def", "from", "nonlocal", "while",
    "assert", "del", "global", "not", "with",
    "async", "elif", "if", "or", "yield"
}

numeros ={"int":"tk_entero","float":"tk_flotante","hex":"tk_hexadecimal","bin":"tk_binario","string":"tk_cadena","char":"tk_caracter"
          ,"bool":"tk_booleano","none":"tk_nulo","list":"tk_lista","tuple":"tk_tupla","set":"tk_conjunto","dict":"tk_diccionario"}

operadores_multiples = { "==":"tk_igual_igual", "!=" :"tk_distinto", "<=":"tk_menor_igual", ">=":"tk_mayor_igual",
    "->":"tk_ejecuta", "=>":"tk_arrow_eq", "//":"tk_floor_div", "**":"tk_pow", "==":"tk_eq"}

operadores_unitarios = {"=":"tk_asig", "+":"tk_suma", "-":"tk_resta", "*":"tk_mul", "/":"tk_div",
    "(": "tk_par_izq", ")":"tk_par_der", ":":"tk_dos_puntos", ",":"tk_coma",
    ".":"tk_punto", "{":"tk_llave_izq", "}":"tk_llave_der", "[":"tk_cor_izq", "]":"tk_cor_der",
    "<":"tk_menor", ">":"tk_mayor"}

class ErrorLexico(Exception):
    pass

class ErrorSintactico(Exception):
    def __init__(self, fila, col, encontrado, esperados):
        self.fila = fila
        self.col = col
        self.encontrado = encontrado
        self.esperados = esperados
        super().__init__(f"<{fila},{col}> Error sintactico: se ecnontro: {encontrado}; se esperaba: {esperados}")


# Administrador de errores lexicos con fila y columna
def error_lexico(fila, col, c):
    raise ErrorLexico(
        f"Error lexico (linea:{fila}, posicion:{col}) el caracter inesperado es '{c}'"
    )


# AFD: Identificadores y Palabras Reservadas
def afd_identificador(source, start_index, fila, col):
    estado = "S0"
    lexema = ""
    i = start_index

    while i < len(source):
        c = source[i]
        if estado == "S0":
            if c.isalpha() or c == "_":
                estado = "S1"
                lexema += c
                i += 1
                col += 1
            else:
                 error_lexico(fila,col, c)

        elif estado == "S1":
            if c.isalnum() or c == "_":
                lexema += c
                i += 1
                col += 1
            else:

               break

    # Estado de aceptacion
    if lexema in palabras_reservadas:
        return (lexema, fila, col - len(lexema)), i, col
    else:
        return ("id", lexema, fila, col - len(lexema)), i, col

 #AFD: Numeros
def afd_numero(source, start_index, fila, col):
    estado = "S0"
    lexema = ""
    i = start_index
    puntos = 0

    while i < len(source):
        c = source[i]

        if estado == "S0":
            if c.isdigit():
                estado = "S1"
                lexema += c
                i += 1
                col += 1
            else:
                break

        elif estado == "S1":
            if c.isdigit():
                lexema += c
                i += 1
                col += 1
            elif c == ".":
                puntos += 1
                if puntos > 1:
                    break
                estado = "S2"
                lexema += c
                i += 1
                col += 1
            else:
                break

        elif estado == "S2":
            if c.isdigit():
                estado = "S3"
                lexema += c
                i += 1
                col += 1
            else:
                break

        elif estado == "S3":
            if c.isdigit():
                lexema += c
                i += 1
                col += 1
            else:
                break

    return ("num", lexema, fila, col - len(lexema)), i, col


# AFD: Cadenas
def afd_cadena(source, start_index, fila, col):
    estado = "S0"
    lexema = ""
    i = start_index
    quote = source[i]
    triple = False

    # Detectar triple comillas
    if i + 2 < len(source) and source[i+1] == quote and source[i+2] == quote:
        triple = True
        i += 3
        col += 3
    else:
        i += 1
        col += 1

    estado = "S1"
    inicio_col = col

    while i < len(source):
        c = source[i]

        if estado == "S1":
            if not triple and c == quote:
                i += 1
                col += 1
                return ("str", f"\"{lexema}\"", fila, inicio_col), i, col
            elif triple and c == quote and i+2 < len(source) and source[i+1] == quote and source[i+2] == quote:
                i += 3
                col += 3
                return ("str", f"\"\"\"{lexema}\"\"\"", fila, inicio_col), i, col
            elif c == "\n" and not triple:
                error_lexico(fila, inicio_col, c)
            else:
                lexema += c
                if c == "\n":
                    fila += 1
                    col = 1
                else:
                    col += 1
                i += 1

    # Si termina sin cerrar
    error_lexico(fila, col,c)

# AFD: Operadores y simbolos
def afd_operador_unitario(source, start_index, fila, col):
    i = start_index
    c = source[i]
    lexema = c
    i += 1
    col += 1

    # Probar operadores de 1 caracter
    if i < len(source):
        posible = c + source[i]
        if posible in operadores_unitarios:
            lexema = posible
            i += 1
            col += 1

    if lexema in operadores_unitarios:
        return (operadores_unitarios[lexema], fila, col - len(lexema)), i, col
    else:
        error_lexico(fila, col,c)

# Operadores multiples
def afd_operador_multiple(source, start_index, fila, col):
    i = start_index
    c = source[i]
    lexema = c
    i += 1
    col += 1

    if i < len(source):
        posible = c + source[i]
        if posible in operadores_multiples:
            lexema = posible
            i += 1
            col += 1

    if lexema in operadores_multiples:
        return (operadores_multiples[lexema], fila, col - len(lexema)), i, col
    else:
        error_lexico(fila, col,c)

# Bucle principal
def analizar(source):
    tokens = []
    fila, col = 1, 1
    i = 0
    while i < len(source):
        c = source[i]

        if c in " \t":
            i += 1
            col += 1
        elif c == "\n":
            i += 1
            fila += 1
            col = 1
        elif c == "#":
            while i < len(source) and source[i] != "\n":
                i += 1
        elif c.isalpha() or c == "_":
            token, i, col = afd_identificador(source, i, fila, col)
            tokens.append(token)
        elif c.isdigit():
            token, i, col = afd_numero(source, i, fila, col)
            tokens.append(token)
        elif c in ["'", '"']:
            token, i, col = afd_cadena(source, i, fila, col)
            tokens.append(token)
        elif i + 1 < len(source) and source[i:i+2] in operadores_multiples:
            token, i, col = afd_operador_multiple(source, i, fila, col)
            tokens.append(token)

        elif c in operadores_unitarios:
            token, i, col = afd_operador_unitario(source, i, fila, col)
            tokens.append(token)
        else:
            error_lexico(fila, col,c)

    return tokens

# Construir mapas inversos para recuperar lexemas de tokens de operadores
operadores_unitarios_inv = {v: k for k, v in operadores_unitarios.items()}
operadores_multiples_inv = {v: k for k, v in operadores_multiples.items()}

# Helpers para token
def token_len(tok):
    return len(tok)

def token_lexema(tok):
    if token_len(tok) == 4:
        return tok[1]
    else:
        if tok[0] in palabras_reservadas:
            return tok[0]
        if tok[0] in operadores_unitarios_inv:
            return operadores_unitarios_inv[tok[0]]
        if tok[0] in operadores_multiples_inv:
            return operadores_multiples_inv[tok[0]]
        return tok[0]

def token_pos(tok):
    if token_len(tok) == 4:
        return tok[2], tok[3]
    else:
        return tok[1], tok[2]

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0
        self.n = len(tokens)

    def at_end(self):
        return self.i >= self.n

    def peek(self):
        if self.at_end():
            return None
        return self.tokens[self.i]

    def advance(self):
        t = self.peek()
        self.i += 1
        return t

    def match_lexemas(self, choices):
        t = self.peek()
        if t is None:
            return False
        lex = token_lexema(t)
        return lex in choices

    def expect(self, expected_list):
        t = self.peek()
        if t is None:
            if self.n>0:
                last = self.tokens[-1]
                fila, col = token_pos(last)
            else:
                fila, col = 1,1
            raise ErrorSintactico(fila, col+1, "<EOF>", ','.join(['"'+e+'"' for e in expected_list]))
        if token_lexema(t) in expected_list:
            return self.advance()
        fila, col = token_pos(t)
        encontrado = token_lexema(t)
        esperados_str = ','.join(['"'+e+'"' for e in expected_list])
        raise ErrorSintactico(fila, col, encontrado, esperados_str)

    # Gramática simplificada
    def parse(self):
        while not self.at_end():
            self.stmt()
        return True

    def stmt(self):
        t = self.peek()
        if t is None:
            return
        lex = token_lexema(t)
        if lex == 'if':
            self.if_stmt()
        elif lex == 'def':
            self.def_stmt()
        elif lex == 'pass':
            self.advance()
        elif lex == 'return':
            self.advance()
            if not self.at_end():
                next_tok = self.peek()
                if token_pos(next_tok)[0] == token_pos(t)[0]:
                    self.expr()
        else:
            self.simple_stmt()

    def simple_stmt(self):
        t = self.peek()
        if t is None:
            return
        if token_len(t) == 4 and t[0] == 'id':
            if self.i+1 < self.n:
                next_tok = self.tokens[self.i+1]
                next_lex = token_lexema(next_tok)
                if next_lex == '=' or next_tok[0] == 'tk_asig' or next_lex == 'tk_asig':
                    idtok = self.advance()
                    if self.match_lexemas(['=']):
                        self.advance()
                    else:
                        self.expect(['='])
                    self.expr()
                    return
        self.expr()

    def if_stmt(self):
        t = self.expect(['if'])
        self.expr()
        if self.match_lexemas([':']):
            self.advance()
        else:
            self.expect([':'])
        if not self.at_end():
            nexttok = self.peek()
            if token_pos(nexttok)[0] == token_pos(t)[0]:
                self.stmt()
            else:
                self.stmt()

    def def_stmt(self):
        self.expect(['def'])
        t = self.peek()
        if t is None:
            self.expect(['id'])
        if not (token_len(t) == 4 and t[0] == 'id'):
            fila, col = token_pos(t) if t else (1,1)
            raise ErrorSintactico(fila, col, token_lexema(t), '"id"')
        self.advance()
        if self.match_lexemas(['(']):
            self.advance()
        else:
            self.expect(['('])
        if not self.match_lexemas([')']):
            while True:
                t = self.peek()
                if not (token_len(t) == 4 and t[0] == 'id'):
                    fila, col = token_pos(t)
                    raise ErrorSintactico(fila, col, token_lexema(t), '"id"')
                self.advance()
                if self.match_lexemas([',']):
                    self.advance()
                    continue
                else:
                    break
        self.expect([')'])
        self.expect([':'])
        if not self.at_end():
            self.stmt()

    def expr(self):
        self.term()
        while not self.at_end():
            t = self.peek()
            if t is None:
                break
            lex = token_lexema(t)
            if lex in operadores_unitarios.values() or lex in operadores_multiples.values():
                break
            if lex in ['+', '-', '*', '/', '==', '!=', '<', '>', '<=', '>=', '**', '//']:
                self.advance()
                self.term()
                continue
            if lex in [':', ',', ')', ']', '}', ]:
                break
            break

    def term(self):
        t = self.peek()
        if t is None:
            return
        lex = token_lexema(t)
        if token_len(t) == 4:
            if t[0] == 'id':
                self.advance()
                if not self.at_end() and token_lexema(self.peek()) == '(':
                    self.advance()
                    if token_lexema(self.peek()) != ')':
                        while True:
                            self.expr()
                            if token_lexema(self.peek()) == ',':
                                self.advance()
                                continue
                            else:
                                break
                    self.expect([')'])
                return
            elif t[0] == 'num' or t[0] == 'str':
                self.advance()
                return
        else:
            if lex == '(':
                self.advance()
                self.expr()
                self.expect([')'])
                return
            if lex == '[':
                self.advance()
                if token_lexema(self.peek()) != ']':
                    while True:
                        self.expr()
                        if token_lexema(self.peek()) == ',':
                            self.advance()
                            continue
                        else:
                            break
                self.expect([']'])
                return
        if t is None:
            fila, col = 1,1
            raise ErrorSintactico(fila, col, '<EOF>', '"expresion"')
        fila, col = token_pos(t)
        raise ErrorSintactico(fila, col, token_lexema(t), '"expresion"')


def main():
    with open("entrada.py", "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tokens = analizar(source)
        parser = Parser(tokens)
        parser.parse()
        with open("salida.txt", "w", encoding="utf-8") as f:
            f.write("El analisis sintactico ha finalizado exitosamente")
    except ErrorLexico as e:
        with open("salida.txt", "w", encoding="utf-8") as f:
            f.write(str(e) + "\n")
    except ErrorSintactico as e:
        with open("salida.txt", "w", encoding="utf-8") as f:
            f.write(f"<{e.fila},{e.col}> Error sintactico: se ecnontro: {e.encontrado}; se esperaba: {e.esperados}")


if __name__ == "__main__":
    main()
