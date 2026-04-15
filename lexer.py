import ply.lex as lex

class LexerClass:
    """Clase que encapsula el analizador léxico de Lava usando PLY."""

    def __init__(self):
        """Inicializa el lexer y define las reglas léxicas."""
        self.lexer = lex.lex(module=self)
        self.input_data = ""

    def input(self, data):
        """Carga el input para poder calcular columnas por token."""
        self.input_data = data
        self.lexer.input(data)

    # =========================
    # PALABRAS RESERVADAS
    # =========================

    reserved = {
        'true': 'TRUE',
        'false': 'FALSE',
        'int': 'INT',
        'float': 'FLOAT',
        'char': 'CHAR',
        'boolean': 'BOOLEAN',
        'void': 'VOID',
        'return': 'RETURN',
        'if': 'IF',
        'else': 'ELSE',
        'do': 'DO',
        'while': 'WHILE',
        'print': 'PRINT',
        'new': 'NEW',
        'record': 'RECORD',
        'break': 'BREAK'
    }

    # =========================
    # LISTA DE TOKENS
    # =========================

    tokens = (

        # Identificadores
        'ID',

        # Literales
        'INT_VALUE',
        'FLOAT_VALUE',
        'CHAR_VALUE',

        # Operadores aritméticos
        'PLUS',             # +
        'MINUS',            # -
        'TIMES',            # *
        'DIVIDE',           # /

        # Operadores booleanos
        'AND',              # &&
        'OR',               # ||
        'NOT',              # !

        # Operadores comparativos
        'GREATER',          # >
        'GREATER_EQUAL',    # >=
        'LESS',             # <
        'LESS_EQUAL',       # <=
        'EQUAL',            # ==

        # Operador de asignación
        'ASSIGN',           # =

        # Símbolos de puntuación y delimitadores estructurales
        'SEMICOLON',        #;
        'COMMA',            # ,
        'DOT',              # .
        'LPAREN',           # (
        'RPAREN',           # )
        'LBRACE',           # {
        'RBRACE',           # }

    ) + tuple(reserved.values())


    # =========================
    # OPERADORES Y SÍMBOLOS
    # =========================

    t_PLUS = r'\+'
    t_MINUS = r'-'
    t_TIMES = r'\*'
    t_DIVIDE = r'/'

    t_AND = r'&&'
    t_OR = r'\|\|'
    t_NOT = r'!'

    t_GREATER_EQUAL = r'>='
    t_GREATER = r'>'

    t_LESS_EQUAL = r'<='
    t_LESS = r'<'

    t_EQUAL = r'=='
    t_ASSIGN = r'='

    t_SEMICOLON = r';'
    t_COMMA = r','
    t_DOT = r'\.'

    t_LPAREN = r'\('
    t_RPAREN = r'\)'

    t_LBRACE = r'\{'
    t_RBRACE = r'\}'

    # Caracteres ignorados: espacios en blanco y tabulaciones.
    t_ignore = " \t"

    # =========================
    # COMENTARIOS
    # =========================

    def t_ON_LINE_COMMENT(self, t):
        r'//.*'
        pass

    def t_MULTI_LINE_COMMENT(self, t):
        r'/\*(.|\n)*?\*/'
        # Contar cuántos saltos de línea había dentro del comentario
        saltos_linea = t.value.count("\n")
        t.lexer.lineno += saltos_linea
        pass

    # =========================
    # LITERALES NUMÉRICOS
    # =========================

    # Literales de punto flotante: pueden ser números con parte decimal y/o notación científica 
    def t_FLOAT_VALUE(self, t):
        r'([0-9]+\.[0-9]+([eE][+-]?[0-9]+)?)|([0-9]+[eE][+-]?[0-9]+)'
        t.original = t.value
        t.value = float(t.value)
        return self._set_token_columns(t, t.original)
    
    # Enteros binarios
    def t_INT_VALUE_BIN(self, t):
        r'0b[01]+'
        t.type = 'INT_VALUE'
        t.original = t.value
        t.value = int(t.value, 2)
        return self._set_token_columns(t, t.original)
    
    # Enteros hexadecimales (solo A-F mayúsculas)
    def t_INT_VALUE_HEX(self, t):
        r'0x[0-9A-F]+'
        t.type = 'INT_VALUE'
        t.original = t.value
        t.value = int(t.value, 16)
        return self._set_token_columns(t, t.original)

    # Enteros octales (solo dígitos 0-7)
    def t_INT_VALUE_OCT(self, t):
        r'0[0-7]+'
        t.type = 'INT_VALUE'
        t.original = t.value
        t.value = int(t.value, 8)
        return self._set_token_columns(t, t.original)

    # Enteros decimales
    def t_INT_VALUE(self, t):
        r'([1-9][0-9]*)|0'
        t.original = t.value
        t.value = int(t.value)
        return self._set_token_columns(t, t.original)

    # =========================
    # CARACTERES
    # =========================

    def t_CHAR_VALUE(self, t):
        r"'(?:\\[abfnrtv\\'\"0]|\\x[0-9A-Fa-f]{2}|\\u[0-9A-Fa-f]{4}|\\U[0-9A-Fa-f]{8}|[^\\'\n])'"
        t.original = t.value
        contenido = t.value[1:-1]

        if contenido.startswith('\\'):
            try:
                contenido = bytes(contenido, 'utf-8').decode('unicode_escape')
            except UnicodeDecodeError:
                print(f"Literal de carácter inválido '{t.original}' en la línea {t.lexer.lineno}")
                return None

        if len(contenido) != 1:
            print(f"Literal de carácter inválido '{t.original}' en la línea {t.lexer.lineno}")
            return None

        t.value = contenido
        return self._set_token_columns(t, t.original)

    # =========================
    # IDENTIFICADORES
    # =========================

    def t_ID(self, t):
        r'[a-zA-Z_][a-zA-Z0-9_]*'
        original = t.value
        t.type = self.reserved.get(t.value, 'ID')

        # Para los literales booleanos, se asigna el valor booleano correspondiente.
        if t.type == 'TRUE':
            t.value = True
        elif t.type == 'FALSE':
            t.value = False

        return self._set_token_columns(t, original)

    # =========================
    # NUEVAS LÍNEAS
    # =========================

    def t_newline(self, t):
        r'\n+'
        t.lexer.lineno += t.value.count("\n")

    # =========================
    # ERRORES
    # =========================

    def t_error(self, t):
        print(f"Caracter ilegal '{t.value[0]}' en la línea {t.lexer.lineno}")
        t.lexer.skip(1)

    def _set_token_columns(self, t, original=None):
        if original is None:
            original = getattr(t, 'original', t.value)
        t.original = original
        col_start = self.find_column(self.input_data, t.lexpos)
        t.col_start = col_start
        t.col_end = col_start + len(str(original))
        return t

    # =========================
    # FUNCIÓN AUXILIAR
    # =========================
    # Dada la posición absoluta (lexpos) de un token en el input,
    # calcula la columna (0-based) contando desde el último '\n'.
    # Se usa desde main.py para sacar columna inicio/fin.

    @staticmethod
    def find_column(input, lexpos):
        last_cr = input.rfind('\n', 0, lexpos)
        if last_cr < 0:
            last_cr = -1
        return lexpos - last_cr - 1
    