# ============================================================================
# DICCIONARIOS DE PALABRAS RESERVADAS Y OPERADORES
# ============================================================================

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
    "//": "tk_floor_div", "**": "tk_pow", "==": "tk_igual_igual"
}

operadores_unitarios = {
    "=":"tk_asig", "+":"tk_suma", "-":"tk_resta", "*":"tk_mul", "/":"tk_div",
    "(": "tk_par_izq", ")":"tk_par_der", ":":"tk_dos_puntos", ",":"tk_coma",
    ".":"tk_punto", "{":"tk_llave_izq", "}":"tk_llave_der", "[":"tk_cor_izq",
    "]":"tk_cor_der", "<":"tk_menor", ">":"tk_mayor"
}

# ============================================================================
# EXCEPCIONES
# ============================================================================

class ErrorLexico(Exception):
    pass

class ErrorSintactico(Exception):
    def __init__(self, fila, col, encontrado, esperados):
        self.fila = fila
        self.col = col
        self.encontrado = encontrado
        self.esperados = esperados
        super().__init__(f"<{fila},{col}> Error sintactico: se encontro: \"{encontrado}\"; se esperaba: {esperados}")

# ============================================================================
# TOKEN CLASS
# ============================================================================

class Token:
    def __init__(self, type_, lexeme, line, col):
        self.type = type_
        self.lexeme = lexeme
        self.line = line
        self.col = col
    def __repr__(self):
        return f"Token({self.type}, {self.lexeme!r}, {self.line}, {self.col})"

# ============================================================================
# ANALIZADOR LÉXICO (CON AUTÓMATAS)
# ============================================================================

def error_lexico(fila, col, c):
    raise ErrorLexico(
        f"Error lexico (linea:{fila}, posicion:{col}) el caracter inesperado es '{c}'"
    )

def afd_identificador(source, start_index, fila, col):
    i = start_index
    lexema = ""
    while i < len(source) and (source[i].isalnum() or source[i] == "_"):
        lexema += source[i]
        i += 1
        col += 1
    if lexema in palabras_reservadas:
        return Token(keyword_to_token[lexema], lexema, fila, col), i, col
    return Token("id", lexema, fila, col), i, col


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

    # 🔽 Conversión a tuplas para el parser
    tokens_tuplas = []
    for t in tokens:
        tokens_tuplas.append((t.type, t.lexeme, t.line, t.col))

    return tokens_tuplas


# ============================================================================
# FUNCIONES AUXILIARES DE TOKENS
# ============================================================================

def token_tipo(tok):
    tipo, lexema, fila, col = adaptar_token(tok)
    return tipo

def adaptar_token(tok):
    """
    Convierte un objeto Token (de tu nuevo lexer) a tupla (tipo, lexema, fila, col)
    para que el parser antiguo pueda entenderlo sin romper compatibilidad.
    """
    if isinstance(tok, tuple):
        return tok
    elif hasattr(tok, "type"):  # Si viene del nuevo lexer
        return (tok.type, tok.lexeme, tok.line, tok.col)
    else:
        raise TypeError(f"Token inválido o desconocido: {tok}")


def token_lexema(tok):
    """
    Retorna el lexema real del token traducido al formato que el parser espera.
    Corrige mapeo de tk_id → id, tk_entero → num, tk_cadena → str, etc.
    """
    tipo, lexema, fila, col = adaptar_token(tok)

    # Normalización de tipos
    if tipo == "tk_id" or tipo == "id":
        return "id"
    if tipo in ["tk_entero", "tk_flotante"]:
        return "num"
    if tipo == "tk_cadena":
        return "str"

    # Palabras reservadas (tk_if → if, tk_def → def, etc.)
    if tipo.startswith("tk_"):
        palabra = tipo[3:]
        return palabra

    # En cualquier otro caso, usa el lexema literal
    return lexema


    # Palabras reservadas o tokens tipo tk_def, tk_if, etc.
    if tipo.startswith("tk_"):
        palabra = tipo[3:]  # elimina el prefijo "tk_"
        return palabra

    # Fallback: devuelve el lexema literal
    return lexema


    # Palabras reservadas: remueve el prefijo tk_ y devuelve el nombre real
    if tipo.startswith("tk_"):
        palabra = tipo[3:]  # elimina "tk_"
        return palabra

    # Fallback
    return lexema



    # Palabras reservadas
    if tipo in palabras_reservadas:
        return tipo

    # Operadores (mapear token a símbolo)
    if tipo in TOKEN_A_LEXEMA:
        return TOKEN_A_LEXEMA[tipo]

    return tipo


def token_pos(tok):
    tipo, lexema, fila, col = adaptar_token(tok)
    return fila, col

def lexema_para_error(tok):
    if tok is None:
        return "<EOF>"
    return tok.lexeme

# ============================================================================
# A PARTIR DE AQUÍ, TODO EL PARSER SIGUE IGUAL
# ============================================================================

# Diccionarios inversos para recuperar lexemas desde tokens
operadores_unitarios_inv = {v: k for k, v in operadores_unitarios.items()}
operadores_multiples_inv = {v: k for k, v in operadores_multiples.items()}

# Mapeo de tokens a lexemas para comparación sintáctica
TOKEN_A_LEXEMA = {
    # Operadores unitarios
    'tk_asig': '=',
    'tk_suma': '+',
    'tk_resta': '-',
    'tk_mul': '*',
    'tk_div': '/',
    'tk_par_izq': '(',
    'tk_par_der': ')',
    'tk_dos_puntos': ':',
    'tk_coma': ',',
    'tk_punto': '.',
    'tk_llave_izq': '{',
    'tk_llave_der': '}',
    'tk_cor_izq': '[',
    'tk_cor_der': ']',
    'tk_menor': '<',
    'tk_mayor': '>',

    # Operadores múltiples
    'tk_igual_igual': '==',
    'tk_distinto': '!=',
    'tk_menor_igual': '<=',
    'tk_mayor_igual': '>=',
    'tk_ejecuta': '->',
    'tk_arrow_eq': '=>',
    'tk_floor_div': '//',
    'tk_pow': '**',
}

def token_tipo(tok):
    """Retorna el tipo/categoría del token"""
    if len(tok) == 4:
        return tok[0]  # id, num, str
    else:
        return tok[0]  # palabra reservada u operador

def token_lexema(tok):
    """
    Retorna el lexema real del token para comparaciones sintácticas.
    CRUCIAL: Mapea tokens de operadores a sus símbolos originales.
    """
    if len(tok) == 4:
        # Token con lexema explícito (id, num, str)
        return tok[1]
    else:
        tipo = tok[0]

        # Palabras reservadas
        if tipo in palabras_reservadas:
            return tipo

        # Operadores (mapear token a símbolo)
        if tipo in TOKEN_A_LEXEMA:
            return TOKEN_A_LEXEMA[tipo]

        # Fallback: buscar en diccionarios inversos
        if tipo in operadores_unitarios_inv:
            return operadores_unitarios_inv[tipo]
        if tipo in operadores_multiples_inv:
            return operadores_multiples_inv[tipo]

        return tipo

def token_pos(tok):
    """Retorna la posición (fila, columna) del token"""
    if len(tok) == 4:
        return tok[2], tok[3]
    else:
        return tok[1], tok[2]

def lexema_para_error(tok):
    """
    Retorna el lexema para mostrar en mensajes de error.
    Siempre muestra el símbolo original, no el token interno.
    """
    if tok is None:
        return "<EOF>"
    return token_lexema(tok)

# ============================================================================
# CÁLCULO DE CONJUNTOS PRIMEROS
# ============================================================================

def calcular_primeros():
    """
    Calcula los conjuntos PRIMEROS para cada no-terminal de la gramática.
    """
    PRIMEROS = {}

    # Terminales (usando lexemas reales, no tokens internos)
    PRIMEROS['def'] = {'def'}
    PRIMEROS['if'] = {'if'}
    PRIMEROS['return'] = {'return'}
    PRIMEROS['pass'] = {'pass'}
    PRIMEROS['id'] = {'id'}
    PRIMEROS['num'] = {'num'}
    PRIMEROS['str'] = {'str'}
    PRIMEROS['('] = {'('}
    PRIMEROS['['] = {'['}
    PRIMEROS[')'] = {')'}
    PRIMEROS[']'] = {']'}
    PRIMEROS[':'] = {':'}
    PRIMEROS[','] = {','}
    PRIMEROS['='] = {'='}
    PRIMEROS['+'] = {'+'}
    PRIMEROS['-'] = {'-'}
    PRIMEROS['*'] = {'*'}
    PRIMEROS['/'] = {'/'}
    PRIMEROS['//'] = {'//'}
    PRIMEROS['**'] = {'**'}
    PRIMEROS['=='] = {'=='}
    PRIMEROS['!='] = {'!='}
    PRIMEROS['<'] = {'<'}
    PRIMEROS['>'] = {'>'}
    PRIMEROS['<='] = {'<='}
    PRIMEROS['>='] = {'>='}
    PRIMEROS['and'] = {'and'}
    PRIMEROS['or'] = {'or'}

    # No-terminales
    PRIMEROS['program'] = {'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '['}
    PRIMEROS['stmt_list'] = {'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '['}
    PRIMEROS["stmt_list'"] = {'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', 'ε'}
    PRIMEROS['stmt'] = {'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '['}
    PRIMEROS['def_stmt'] = {'def'}
    PRIMEROS['if_stmt'] = {'if'}
    PRIMEROS['assignment'] = {'id'}
    PRIMEROS['return_stmt'] = {'return'}
    PRIMEROS['pass_stmt'] = {'pass'}
    PRIMEROS['expr_stmt'] = {'(', 'id', 'num', 'str', '['}

    PRIMEROS['params'] = {'id', 'ε'}
    PRIMEROS["params'"] = {',', 'ε'}

    PRIMEROS['return_tail'] = {'(', 'id', 'num', 'str', '[', 'ε'}

    PRIMEROS['expr'] = {'(', 'id', 'num', 'str', '['}
    PRIMEROS["expr'"] = {'and', 'or', 'ε'}

    PRIMEROS['comp_expr'] = {'(', 'id', 'num', 'str', '['}
    PRIMEROS["comp_expr'"] = {'==', '!=', '<', '>', '<=', '>=', 'ε'}
    PRIMEROS['comp_op'] = {'==', '!=', '<', '>', '<=', '>='}

    PRIMEROS['arith_expr'] = {'(', 'id', 'num', 'str', '['}
    PRIMEROS["arith_expr'"] = {'+', '-', 'ε'}

    PRIMEROS['term'] = {'(', 'id', 'num', 'str', '['}
    PRIMEROS["term'"] = {'*', '/', '//', '**', 'ε'}

    PRIMEROS['factor'] = {'(', 'id', 'num', 'str', '['}
    PRIMEROS["factor'"] = {'(', '[', 'ε'}

    PRIMEROS['list_literal'] = {'['}
    PRIMEROS['list_items'] = {'(', 'id', 'num', 'str', '[', 'ε'}
    PRIMEROS["list_items'"] = {',', 'ε'}

    PRIMEROS['args'] = {'(', 'id', 'num', 'str', '[', 'ε'}
    PRIMEROS["args'"] = {',', 'ε'}

    return PRIMEROS

# ============================================================================
# CÁLCULO DE CONJUNTOS SIGUIENTES
# ============================================================================

def calcular_siguientes():
    """
    Calcula los conjuntos SIGUIENTES para cada no-terminal de la gramática.
    """
    SIGUIENTES = {}

    SIGUIENTES['program'] = {'$'}
    SIGUIENTES['stmt_list'] = {'$'}
    SIGUIENTES["stmt_list'"] = {'$'}

    SIGUIENTES['stmt'] = {'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}

    SIGUIENTES['def_stmt'] = {'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}
    SIGUIENTES['if_stmt'] = {'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}
    SIGUIENTES['assignment'] = {'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}
    SIGUIENTES['return_stmt'] = {'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}
    SIGUIENTES['pass_stmt'] = {'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}
    SIGUIENTES['expr_stmt'] = {'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}

    SIGUIENTES['params'] = {')'}
    SIGUIENTES["params'"] = {')'}

    SIGUIENTES['return_tail'] = {'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}

    SIGUIENTES['expr'] = {':', ',', ')', ']', 'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}
    SIGUIENTES["expr'"] = {':', ',', ')', ']', 'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}

    SIGUIENTES['comp_expr'] = {'and', 'or', ':', ',', ')', ']', 'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}
    SIGUIENTES["comp_expr'"] = {'and', 'or', ':', ',', ')', ']', 'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}
    SIGUIENTES['comp_op'] = {'(', 'id', 'num', 'str', '['}

    SIGUIENTES['arith_expr'] = {'==', '!=', '<', '>', '<=', '>=', 'and', 'or', ':', ',', ')', ']', 'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}
    SIGUIENTES["arith_expr'"] = {'==', '!=', '<', '>', '<=', '>=', 'and', 'or', ':', ',', ')', ']', 'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}

    SIGUIENTES['term'] = {'+', '-', '==', '!=', '<', '>', '<=', '>=', 'and', 'or', ':', ',', ')', ']', 'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}
    SIGUIENTES["term'"] = {'+', '-', '==', '!=', '<', '>', '<=', '>=', 'and', 'or', ':', ',', ')', ']', 'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}

    SIGUIENTES['factor'] = {'*', '/', '//', '**', '+', '-', '==', '!=', '<', '>', '<=', '>=', 'and', 'or', ':', ',', ')', ']', 'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}
    SIGUIENTES["factor'"] = {'*', '/', '//', '**', '+', '-', '==', '!=', '<', '>', '<=', '>=', 'and', 'or', ':', ',', ')', ']', 'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}

    SIGUIENTES['list_literal'] = {'*', '/', '//', '**', '+', '-', '==', '!=', '<', '>', '<=', '>=', 'and', 'or', ':', ',', ')', ']', 'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$'}
    SIGUIENTES['list_items'] = {']'}
    SIGUIENTES["list_items'"] = {']'}

    SIGUIENTES['args'] = {')'}
    SIGUIENTES["args'"] = {')'}

    return SIGUIENTES

# ============================================================================
# TABLA DE PREDICCIÓN LL(1)
# ============================================================================

def construir_tabla_prediccion():
    """
    Construye la tabla de predicción M[No-terminal, Terminal] = Producción
    """
    TABLA = {}

    # program → stmt_list
    for t in ['def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[']:
        TABLA[('program', t)] = 'program → stmt_list'

    # stmt_list → stmt stmt_list'
    for t in ['def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[']:
        TABLA[('stmt_list', t)] = "stmt_list → stmt stmt_list'"

    # stmt_list' → stmt stmt_list' | ε
    for t in ['def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[']:
        TABLA[("stmt_list'", t)] = "stmt_list' → stmt stmt_list'"
    TABLA[("stmt_list'", '$')] = "stmt_list' → ε"

    # stmt → def_stmt | if_stmt | assignment | return_stmt | pass_stmt | expr_stmt
    TABLA[('stmt', 'def')] = 'stmt → def_stmt'
    TABLA[('stmt', 'if')] = 'stmt → if_stmt'
    TABLA[('stmt', 'id')] = 'stmt → assignment | expr_stmt'  # Necesita lookahead adicional
    TABLA[('stmt', 'return')] = 'stmt → return_stmt'
    TABLA[('stmt', 'pass')] = 'stmt → pass_stmt'
    for t in ['(', 'num', 'str', '[']:
        TABLA[('stmt', t)] = 'stmt → expr_stmt'

    # def_stmt → def id ( params ) : stmt_list
    TABLA[('def_stmt', 'def')] = 'def_stmt → def id ( params ) : stmt_list'


    # params → id params' | ε
    TABLA[('params', 'id')] = "params → id params'"
    TABLA[('params', ')')] = 'params → ε'

    # params' → , id params' | ε
    TABLA[("params'", ',')] = "params' → , id params'"
    TABLA[("params'", ')')] = "params' → ε"

    # if_stmt → if expr : stmt
    TABLA[('if_stmt', 'if')] = 'if_stmt → if expr : stmt'

    # assignment → id = expr
    TABLA[('assignment', 'id')] = 'assignment → id = expr'

    # return_stmt → return return_tail
    TABLA[('return_stmt', 'return')] = 'return_stmt → return return_tail'

    # return_tail → expr | ε
    for t in ['(', 'id', 'num', 'str', '[']:
        TABLA[('return_tail', t)] = 'return_tail → expr'
    for t in ['def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$']:
        if ('return_tail', t) not in TABLA:
            TABLA[('return_tail', t)] = 'return_tail → ε'

    # pass_stmt → pass
    TABLA[('pass_stmt', 'pass')] = 'pass_stmt → pass'

    # expr_stmt → expr
    for t in ['(', 'id', 'num', 'str', '[']:
        TABLA[('expr_stmt', t)] = 'expr_stmt → expr'

    # expr → comp_expr expr'
    for t in ['(', 'id', 'num', 'str', '[']:
        TABLA[('expr', t)] = "expr → comp_expr expr'"

    # expr' → and comp_expr expr' | or comp_expr expr' | ε
    TABLA[("expr'", 'and')] = "expr' → and comp_expr expr'"
    TABLA[("expr'", 'or')] = "expr' → or comp_expr expr'"
    for t in [':', ',', ')', ']', 'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$']:
        if ("expr'", t) not in TABLA:
            TABLA[("expr'", t)] = "expr' → ε"

    # comp_expr → arith_expr comp_expr'
    for t in ['(', 'id', 'num', 'str', '[']:
        TABLA[('comp_expr', t)] = "comp_expr → arith_expr comp_expr'"

    # comp_expr' → comp_op arith_expr comp_expr' | ε
    for op in ['==', '!=', '<', '>', '<=', '>=']:
        TABLA[("comp_expr'", op)] = "comp_expr' → comp_op arith_expr comp_expr'"
    for t in ['and', 'or', ':', ',', ')', ']', 'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$']:
        if ("comp_expr'", t) not in TABLA:
            TABLA[("comp_expr'", t)] = "comp_expr' → ε"

    # comp_op → == | != | < | > | <= | >="""
    for op in ['==', '!=', '<', '>', '<=', '>=']:
        TABLA[('comp_op', op)] = f'comp_op → {op}'

    # arith_expr → term arith_expr'
    for t in ['(', 'id', 'num', 'str', '[']:
        TABLA[('arith_expr', t)] = "arith_expr → term arith_expr'"

    # arith_expr' → + term arith_expr' | - term arith_expr' | ε
    TABLA[("arith_expr'", '+')] = "arith_expr' → + term arith_expr'"
    TABLA[("arith_expr'", '-')] = "arith_expr' → - term arith_expr'"
    for t in ['==', '!=', '<', '>', '<=', '>=', 'and', 'or', ':', ',', ')', ']', 'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$']:
        if ("arith_expr'", t) not in TABLA:
            TABLA[("arith_expr'", t)] = "arith_expr' → ε"

    # term → factor term'
    for t in ['(', 'id', 'num', 'str', '[']:
        TABLA[('term', t)] = "term → factor term'"

    # term' → * factor term' | / factor term' | // factor term' | ** factor term' | ε
    TABLA[("term'", '*')] = "term' → * factor term'"
    TABLA[("term'", '/')] = "term' → / factor term'"
    TABLA[("term'", '//')] = "term' → // factor term'"
    TABLA[("term'", '**')] = "term' → ** factor term'"
    for t in ['+', '-', '==', '!=', '<', '>', '<=', '>=', 'and', 'or', ':', ',', ')', ']', 'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$']:
        if ("term'", t) not in TABLA:
            TABLA[("term'", t)] = "term' → ε"

    # factor → ( expr ) | id factor' | num | str | list_literal
    TABLA[('factor', '(')] = 'factor → ( expr )'
    TABLA[('factor', 'id')] = "factor → id factor'"
    TABLA[('factor', 'num')] = 'factor → num'
    TABLA[('factor', 'str')] = 'factor → str'
    TABLA[('factor', '[')] = 'factor → list_literal'

    # factor' → ( args ) | [ expr ] | ε
    TABLA[("factor'", '(')] = "factor' → ( args )"
    TABLA[("factor'", '[')] = "factor' → [ expr ]"
    for t in ['*', '/', '//', '**', '+', '-', '==', '!=', '<', '>', '<=', '>=', 'and', 'or', ':', ',', ')', ']', 'def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[', '$']:
        if ("factor'", t) not in TABLA:
            TABLA[("factor'", t)] = "factor' → ε"

    # list_literal → [ list_items ]
    TABLA[('list_literal', '[')] = 'list_literal → [ list_items ]'

    # list_items → expr list_items' | ε
    for t in ['(', 'id', 'num', 'str', '[']:
        TABLA[('list_items', t)] = "list_items → expr list_items'"
    TABLA[('list_items', ']')] = 'list_items → ε'

    # list_items' → , expr list_items' | ε
    TABLA[("list_items'", ',')] = "list_items' → , expr list_items'"
    TABLA[("list_items'", ']')] = "list_items' → ε"

    # args → expr args' | ε
    for t in ['(', 'id', 'num', 'str', '[']:
        TABLA[('args', t)] = "args → expr args'"
    TABLA[('args', ')')] = 'args → ε'

    # args' → , expr args' | ε
    TABLA[("args'", ',')] = "args' → , expr args'"
    TABLA[("args'", ')')] = "args' → ε"

    return TABLA

# ============================================================================
# ANALIZADOR SINTÁCTICO LL(1) DIRIGIDO POR TABLA
# ============================================================================

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.i = 0
        self.n = len(tokens)
        self.PRIMEROS = calcular_primeros()
        self.SIGUIENTES = calcular_siguientes()
        self.TABLA = construir_tabla_prediccion()

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

    def current_lexema(self):
        """Retorna el lexema del token actual (mapeado correctamente)"""
        t = self.peek()
        if t is None:
            return '$'
        return token_lexema(t)

    def match(self, expected):
        """
        Verifica si el token actual coincide con el esperado.
        CRUCIAL: Compara usando lexemas mapeados, no tokens internos.
        """
        lex = self.current_lexema()

        # Comparación directa de lexemas
        if lex == expected:
            return True

        # Para tokens especiales (id, num, str)
        t = self.peek()
        if t and token_tipo(t) == expected:
            return True

        return False

    def expect(self, expected):
        """
        Consume un token esperado o lanza error con el lexema correcto.
        """
        if self.match(expected):
            return self.advance()

        # Error: construir mensaje con lexema real
        t = self.peek()
        if t is None:
            if self.n > 0:
                last = self.tokens[-1]
                fila, col = token_pos(last)
                # Calcular posición después del último token
                lex_last = token_lexema(last)
                col += len(str(lex_last))
            else:
                fila, col = 1, 1
            encontrado = "<EOF>"
        else:
            fila, col = token_pos(t)
            encontrado = token_lexema(t)  # Usa lexema mapeado

        raise ErrorSintactico(fila, col, encontrado, f'"{expected}"')

    def calcular_esperados(self, nonterminal):
        """
        Calcula qué terminales se esperan para un no-terminal dado.
        """
        lex = self.current_lexema()
        esperados = set()

        # Buscar en la tabla qué producciones son válidas
        for key in self.TABLA:
            if key[0] == nonterminal:
                esperados.add(f'"{key[1]}"')

        return ', '.join(sorted(esperados)) if esperados else '"expresion valida"'

    def error_esperados(self, nonterminal):
        """
        Lanza error con los símbolos esperados calculados desde la tabla.
        """
        t = self.peek()
        if t is None:
            if self.n > 0:
                last = self.tokens[-1]
                fila, col = token_pos(last)
                lex_last = token_lexema(last)
                col += len(str(lex_last))
            else:
                fila, col = 1, 1
            encontrado = "<EOF>"
        else:
            fila, col = token_pos(t)
            encontrado = token_lexema(t)  # Usa lexema mapeado

        esperados = self.calcular_esperados(nonterminal)
        raise ErrorSintactico(fila, col, encontrado, esperados)

    # ========================================================================
    # MÉTODOS DE PARSING PARA CADA NO-TERMINAL
    # ========================================================================

    def parse(self):
        """Punto de entrada: program → stmt_list"""
        self.program()
        return True

    def program(self):
        """program → stmt_list"""
        self.stmt_list()

    def stmt_list(self):
        """stmt_list → stmt stmt_list'"""
        if self.at_end():
            return
        self.stmt()
        self.stmt_list_prima()

    def stmt_list_prima(self):
        """stmt_list' → stmt stmt_list' | ε"""
        if self.at_end():
            return  # ε

        lex = self.current_lexema()
        if lex in ['def', 'if', 'id', 'return', 'pass', '(', 'num', 'str', '[']:
            self.stmt()
            self.stmt_list_prima()
        # else ε

    def stmt(self):
        """stmt → def_stmt | if_stmt | assignment | return_stmt | pass_stmt | expr_stmt"""
        lex = self.current_lexema()

        if lex == 'def':
            self.def_stmt()
        elif lex == 'if':
            self.if_stmt()
        elif lex == 'return':
            self.return_stmt()
        elif lex == 'pass':
            self.pass_stmt()
        elif lex == 'id':
            # Lookahead para distinguir assignment vs expr_stmt
            if self.i + 1 < self.n:
                next_tok = self.tokens[self.i + 1]
                next_lex = token_lexema(next_tok)  # Usa mapeo correcto
                if next_lex == '=':
                    self.assignment()
                else:
                    self.expr_stmt()
            else:
                self.expr_stmt()
        elif lex in ['(', 'num', 'str', '[']:
            self.expr_stmt()
        else:
            self.error_esperados('stmt')

    def def_stmt(self):
        """def_stmt → def id ( params ) : stmt_list"""
        self.expect('def')

        # Consumir identificador obligatorio después de def
        t = self.peek()
        if t and token_tipo(t) == 'id':
            self.advance()
        else:
            self.expect('id')

        # Paréntesis y parámetros SIEMPRE deben venir aquí (fuera del else)
        self.expect('(')
        self.params()
        self.expect(')')
        self.expect(':')

        # Permitir múltiples sentencias dentro del def
        if not self.at_end():
            self.stmt_list()


    def params(self):
        """params → id params' | ε"""
        lex = self.current_lexema()
        if lex == 'id':
         self.advance()
         self.params_prima()
    # else ε (cuando el siguiente token es ')')

    def params_prima(self):
       """params' → , id params' | ε"""
       lex = self.current_lexema()
       if lex == ',':
        self.advance()
        if self.match('id'):
            self.advance()
            self.params_prima()  # <- esta recursión es la clave
        else:
            self.expect('id')
    # else ε (cuando viene ')')



    def if_stmt(self):
        """if_stmt → if expr : stmt"""
        self.expect('if')
        self.expr()
        self.expect(':')

        if not self.at_end():
            self.stmt()

    def assignment(self):
        """assignment → id = expr"""
        t = self.peek()
        if t and token_tipo(t) == 'id':
            self.advance()
        else:
            self.expect('id')

        self.expect('=')
        self.expr()

    def return_stmt(self):
        """return_stmt → return return_tail"""
        self.expect('return')
        self.return_tail()

    def return_tail(self):
        """return_tail → expr | ε"""
        lex = self.current_lexema()
        if lex in ['(', 'id', 'num', 'str', '[']:
            self.expr()
        # else ε (cuando es fin de stmt)

    def pass_stmt(self):
        """pass_stmt → pass"""
        self.expect('pass')

    def expr_stmt(self):
        """expr_stmt → expr"""
        self.expr()

    def expr(self):
        """expr → comp_expr expr'"""
        self.comp_expr()
        self.expr_prima()

    def expr_prima(self):
        """expr' → and comp_expr expr' | or comp_expr expr' | ε"""
        lex = self.current_lexema()
        if lex == 'and':
            self.advance()
            self.comp_expr()
            self.expr_prima()
        elif lex == 'or':
            self.advance()
            self.comp_expr()
            self.expr_prima()
        # else ε

    def comp_expr(self):
        """comp_expr → arith_expr comp_expr'"""
        self.arith_expr()
        self.comp_expr_prima()

    def comp_expr_prima(self):
        """comp_expr' → comp_op arith_expr comp_expr' | ε"""
        lex = self.current_lexema()
        if lex in ['==', '!=', '<', '>', '<=', '>=']:
            self.comp_op()
            self.arith_expr()
            self.comp_expr_prima()
        # else ε

    def comp_op(self):
        """comp_op → == | != | < | > | <= | >="""
        lex = self.current_lexema()
        if lex in ['==', '!=', '<', '>', '<=', '>=']:
            self.advance()
        else:
            self.error_esperados('comp_op')

    def arith_expr(self):
        """arith_expr → term arith_expr'"""
        self.term()
        self.arith_expr_prima()

    def arith_expr_prima(self):
        """arith_expr' → + term arith_expr' | - term arith_expr' | ε"""
        lex = self.current_lexema()
        if lex == '+':
            self.advance()
            self.term()
            self.arith_expr_prima()
        elif lex == '-':
            self.advance()
            self.term()
            self.arith_expr_prima()
        # else ε

    def term(self):
        """term → factor term'"""
        self.factor()
        self.term_prima()

    def term_prima(self):
        """term' → * factor term' | / factor term' | // factor term' | ** factor term' | ε"""
        lex = self.current_lexema()
        if lex == '*':
            self.advance()
            self.factor()
            self.term_prima()
        elif lex == '/':
            self.advance()
            self.factor()
            self.term_prima()
        elif lex == '//':
            self.advance()
            self.factor()
            self.term_prima()
        elif lex == '**':
            self.advance()
            self.factor()
            self.term_prima()
        # else ε

    def factor(self):
        """factor → ( expr ) | id factor' | num | str | list_literal"""
        lex = self.current_lexema()
        t = self.peek()

        if lex == '(':
            self.advance()
            self.expr()
            self.expect(')')
        elif t and token_tipo(t) == 'id':
            self.advance()
            self.factor_prima()
        elif t and token_tipo(t) == 'num':
            self.advance()
        elif t and token_tipo(t) == 'str':
            self.advance()
        elif lex == '[':
            self.list_literal()
        else:
            self.error_esperados('factor')

    def factor_prima(self):
        """factor' → ( args ) | [ expr ] | ε"""
        lex = self.current_lexema()

        if lex == '(':
            self.advance()
            self.args()
            self.expect(')')
        elif lex == '[':
            self.advance()
            self.expr()
            self.expect(']')
        # else ε

    def list_literal(self):
        """list_literal → [ list_items ]"""
        self.expect('[')
        self.list_items()
        self.expect(']')

    def list_items(self):
        """list_items → expr list_items' | ε"""
        lex = self.current_lexema()
        if lex in ['(', 'id', 'num', 'str', '[']:
            self.expr()
            self.list_items_prima()
        # else ε (cuando es ']')

    def list_items_prima(self):
        """list_items' → , expr list_items' | ε"""
        if self.match(','):
            self.advance()
            self.expr()
            self.list_items_prima()
        # else ε

    def args(self):
        """args → expr args' | ε"""
        lex = self.current_lexema()
        if lex in ['(', 'id', 'num', 'str', '[']:
            self.expr()
            self.args_prima()
        # else ε (cuando es ')')

    def args_prima(self):
        """args' → , expr args' | ε"""
        if self.match(','):
            self.advance()
            self.expr()
            self.args_prima()
        # else ε

# ============================================================================
# FUNCIÓN PRINCIPAL
# ============================================================================

def main():
    with open("entrada.py", "r", encoding="utf-8") as f:
        source = f.read()

    try:
        # Fase 1: Análisis léxico
        tokens = analizar(source)

        print("TOKENS DETECTADOS:")
        for t in tokens:
           if hasattr(t, "tipo"):
               print(t.tipo, t.lexema)
           else:
              print(t)


        # Fase 2: Análisis sintáctico
        parser = Parser(tokens)
        parser.parse()

        # Éxito
        with open("salida.txt", "w", encoding="utf-8") as f:
            f.write("El analisis sintactico ha finalizado exitosamente\n")

    except ErrorLexico as e:
        with open("salida.txt", "w", encoding="utf-8") as f:
            f.write(str(e) + "\n")

    except ErrorSintactico as e:
        with open("salida.txt", "w", encoding="utf-8") as f:
            f.write(str(e) + "\n")

if __name__ == "__main__":
    main()