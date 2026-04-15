import ply.yacc as yacc
from lexer import LexerClass

class ParserClass:
    """Analizador Sintáctico del lenguaje Lava"""

    # Reutiliza la lista de tokens definida en el lexer.
    tokens = LexerClass.tokens

    # Símbolo inicial de la gramática.
    start = 'programa'

    # =========================================================
    # PRECEDENCIA DE OPERADORES
    # =========================================================

    # Orden de precedencia y asociatividad de operadores.
    # Se usa para resolver ambigüedades en expresiones.
    precedence = (
        ('left',     'OR'),
        ('left',     'AND'),
        ('nonassoc', 'EQUAL', 'GREATER', 'GREATER_EQUAL', 'LESS', 'LESS_EQUAL'),
        ('left',     'PLUS', 'MINUS'),
        ('left',     'TIMES', 'DIVIDE'),
        ('right',    'NOT', 'UMINUS', 'UPLUS'),
        ('left',     'DOT'),            
    )

    def __init__(self):
        """Inicializa el parser y define las reglas de producción."""
       # Guarda una instancia del lexer.
        self.lexer = LexerClass().lexer

        # Marca si durante el análisis ha aparecido algún error sintáctico.
        self.has_syntax_error = False

        # Construye el parser de PLY a partir de las reglas de esta clase.
        self.parser = yacc.yacc(module=self)
    
    # =========================================================
    # MÉTODOS DE ENTRADA
    # =========================================================
 
    def parse(self, data: str):
        """Analiza una cadena de entrada."""
        # Reinicia el indicador de error antes de cada análisis.
        self.has_syntax_error = False

        # Crea un lexer nuevo para esta entrada concreta.
        lexer_instance = LexerClass()
        lexer_instance.input(data)

        # Ejecuta el parser usando el lexer recién inicializado.
        return self.parser.parse(lexer=lexer_instance.lexer)
 
    def test_with_file(self, path: str):
        """Analiza el contenido de un fichero."""
        # Si no se indica ruta, usa "input" por defecto.
        if not path:
            path = "input"
        try:
            # Abre el fichero y analiza su contenido completo.
            with open(path, "r", encoding="utf-8") as fichero:
                return self.parse(fichero.read())
        except FileNotFoundError:
            # Error específico si el fichero no existe.
            print("ERROR: Fichero no encontrado")
        except Exception as e:
            # Captura cualquier otro error inesperado.
            print("ERROR: error inesperado:", e)
    
    # =========================================================
    # REGLAS DE PRODUCCIÓN
    # =========================================================
    
    # =======================================
    # PROGRAMA
    # =======================================
 
    # El programa es la raíz de la gramática y puede contener múltiples elementos o estar vacío.
    def p_programa(self, p):
        '''programa : elementos_opt'''
        pass

    def p_elementos_opt(self, p):
        '''elementos_opt : lambda
                        | elementos'''
        pass
    
    # Lista de elementos del programa.
    def p_elementos(self, p):
        '''elementos : elementos elemento
                    | elemento'''
        pass

    # Cada elemento del programa puede ser una declaración de función, un bloque de código, 
    # una declaración de variable, etc.
    def p_elemento(self, p):
        '''elemento : SEMICOLON
                   | declaracion_funcion_void
                   | declaracion_o_funcion_tipada
                   | declaracion_record SEMICOLON
                   | sentencia_bloque
                   | sentencia_simple SEMICOLON'''
        pass
    
    # =======================================
    # DECLARACIONES GLOBALES Y FUNCIONES
    # =======================================

    # Reconoce una declaración de función con retorno void.
    def p_declaracion_funcion_void(self, p):
        '''declaracion_funcion_void : VOID ID LPAREN parametros_opt RPAREN bloque_void'''
        pass

    # Reconoce una declaración tipada global o una función con retorno tipado.
    def p_declaracion_o_funcion_tipada(self, p):
        '''declaracion_o_funcion_tipada : tipo ID resto_tipado_programa'''
        pass

    # Desambigua si un elemento tipado es función o declaración de variable global.
    def p_resto_tipado_programa(self, p):
        '''resto_tipado_programa : LPAREN parametros_opt RPAREN bloque
                                | ASSIGN expresion SEMICOLON
                                | resto_lista_ids SEMICOLON'''
        pass

    # Reconoce la continuación de una lista de identificadores separada por comas.
    def p_resto_listas_ids(self, p):
        '''resto_lista_ids : lambda
                         | resto_lista_ids COMMA ID'''
        pass

    # =======================================
    # BLOQUES Y CONTROL DE FLUJO 
    # (VOID --> sin return)
    # =======================================

    # Reconoce un bloque perteneciente a una función void.
    def p_bloque_void(self, p):
        '''bloque_void : LBRACE elementos_bloque_void_opt RBRACE'''
        pass

    # Permite que el contenido de un bloque void sea vacío u opcional.
    def p_elementos_bloque_void_opt(self, p):
        '''elementos_bloque_void_opt : lambda
                                    | elementos_bloque_void'''
        pass

    # Construye la secuencia de elementos dentro de un bloque void.
    def p_elementos_bloque_void(self, p):
        '''elementos_bloque_void : elementos_bloque_void elemento_bloque_void
                                 | elemento_bloque_void'''
        pass

    # Reconoce un elemento válido dentro de un bloque void.
    def p_elemento_bloque_void(self, p):
        '''elemento_bloque_void : SEMICOLON
                               | sentencia_bloque_void
                               | declaracion_variable SEMICOLON
                               | sentencia_simple_void SEMICOLON'''
        pass

    # Reconoce sentencias con bloque dentro de una función void.
    def p_sentencia_bloque_void(self, p):
        '''sentencia_bloque_void : bloque_void
                                | sentencia_if_void
                                | sentencia_while_void
                                | sentencia_do_while_void'''
        pass

    # Reconoce una sentencia if dentro de una función void.
    def p_sentencia_if_void(self, p):
        '''sentencia_if_void : IF LPAREN expresion RPAREN bloque_void else_void_opt'''
        pass

    # Reconoce la cláusula else opcional dentro de una función void.
    def p_else_void_opt(self, p):
        '''else_void_opt : lambda
                        | ELSE bloque_void'''
        pass

    # Reconoce una sentencia while dentro de una función void.
    def p_sentencia_while_void(self, p):
        '''sentencia_while_void : WHILE LPAREN expresion RPAREN bloque_void'''
        pass

    # Reconoce una sentencia do-while dentro de una función void.
    def p_sentencia_do_while_void(self, p):
        '''sentencia_do_while_void : DO bloque_void WHILE LPAREN expresion RPAREN'''
        pass

    # Reconoce sentencias simples válidas dentro de una función void.
    def p_sentencia_simple_void(self, p):
        '''sentencia_simple_void : asignacion
                                | print_stmt
                                | BREAK
                                | expresion'''
        pass

    # =======================================
    # BLOQUES Y CONTROL DE FLUJO (con return)
    # =======================================

    # Reconoce sentencias con bloque en contextos donde return está permitido.
    def p_sentencia_bloque(self, p):
        '''sentencia_bloque : bloque
                           | sentencia_if
                           | sentencia_while
                           | sentencia_do_while'''

    # Reconoce un bloque general del lenguaje.
    def p_bloque(self, p):
        '''bloque : LBRACE elementos_bloque_opt RBRACE'''
        pass

    # Permite que el contenido de un bloque general sea vacío u opcional.
    def p_elementos_bloque_opt(self, p):
        '''elementos_bloque_opt : lambda
                               | elementos_bloque'''
        pass

    # Construye la secuencia de elementos dentro de un bloque general.
    def p_elementos_bloque(self, p):
        '''elementos_bloque : elementos_bloque elemento_bloque
                          | elemento_bloque'''
        pass

    # Reconoce un elemento válido dentro de un bloque general.
    def p_elemento_bloque(self, p):
        '''elemento_bloque : SEMICOLON
                          | sentencia_bloque
                          | declaracion_variable SEMICOLON
                          | sentencia_simple SEMICOLON'''
        pass

    # Reconoce una sentencia if general del lenguaje.
    def p_sentencia_if(self, p):
        '''sentencia_if : IF LPAREN expresion RPAREN bloque else_opt'''
        pass

    # Reconoce la cláusula else opcional en un if general.
    def p_else_opt(self, p):
        '''else_opt : lambda
                   | ELSE bloque'''
        pass

    # Reconoce una sentencia while general del lenguaje.
    def p_sentencia_while(self, p):
        '''sentencia_while : WHILE LPAREN expresion RPAREN bloque'''
        pass

    # Reconoce una sentencia do-while general del lenguaje.
    def p_sentencia_do_while(self, p):
        '''sentencia_do_while : DO bloque WHILE LPAREN expresion RPAREN'''
        pass

    # =======================================
    # DECLARACIONES Y SENTENCIAS SIMPLES
    # =======================================

    # Reconoce sentencias simples en contextos donde return está permitido.
    def p_sentencia_simple(self, p):
        '''sentencia_simple : asignacion
                           | print_stmt
                           | BREAK
                           | RETURN expresion
                           | expresion'''
        pass

    # Reconoce declaraciones de variables simples o con inicialización.
    def p_declaracion_variable(self, p):
        '''declaracion_variable : tipo lista_ids
                               | tipo ID ASSIGN expresion'''
        pass

    # Reconoce una lista de identificadores separada por comas.
    def p_lista_ids(self, p):
        '''lista_ids : ID
                    | lista_ids COMMA ID'''
        pass

    # Reconoce una asignación a una variable o acceso por punto.
    def p_asignacion(self, p):
        '''asignacion : acceso ASSIGN expresion'''
        pass

    # Reconoce una llamada a la función del sistema print.
    def p_print_stmt(self, p):
        '''print_stmt : PRINT LPAREN argumentos_opt RPAREN'''
        pass

    # =======================================
    # REGISTROS Y FUNCIONES
    # =======================================

    # Reconoce una declaración global de registro.
    def p_declaracion_record(self, p):
        '''declaracion_record : RECORD ID LPAREN campos_record_opt RPAREN'''
        pass

    # Permite que la lista de campos de un registro sea vacía u opcional.
    def p_campos_record_opt(self, p):
        '''campos_record_opt : lambda
                            | campos_record'''
        pass

    # Construye la lista de campos de un registro.
    def p_campos_record(self, p):
        '''campos_record : campos_record COMMA campo_record
                       | campo_record'''
        pass

    # Reconoce un campo individual dentro de un registro.
    def p_campo_record(self, p):
        '''campo_record : tipo ID'''
        pass

    # Permite que la lista de parámetros de una función sea vacía u opcional.
    def p_parametros_opt(self, p):
        '''parametros_opt : lambda
                         | parametros'''
        pass

    # Construye la lista de parámetros tipados de una función.
    def p_parametros(self, p):
        '''parametros : parametros COMMA parametro
                     | parametro'''
        pass

    # Reconoce un parámetro individual de una función.
    def p_parametro(self, p):
        '''parametro : tipo ID'''
        pass

    # Reconoce un tipo básico o el nombre de un registro definido por el usuario.
    def p_tipo(self, p):
        '''tipo : INT
                | FLOAT
                | CHAR
                | BOOLEAN
                | ID'''
        pass

    # =======================================
    # EXPRESIONES
    # =======================================

    # Expresiones binarias del lenguaje.
    def p_expresion_binaria(self, p):
        '''expresion : expresion OR expresion
                    | expresion AND expresion
                    | expresion EQUAL expresion
                    | expresion GREATER expresion
                    | expresion GREATER_EQUAL expresion
                    | expresion LESS expresion
                    | expresion LESS_EQUAL expresion
                    | expresion PLUS expresion
                    | expresion MINUS expresion
                    | expresion TIMES expresion
                    | expresion DIVIDE expresion'''
        pass
    
    # Operadores unarios del lenguaje (NOT, +, -).
    def p_expresion_unaria(self, p):
        '''expresion : NOT expresion
                    | MINUS expresion %prec UMINUS
                    | PLUS expresion %prec UPLUS'''
        pass
    

    # Reduce una expresión al nivel de primario.
    def p_expresion_primaria(self, p):
        '''expresion : primario'''
        pass

    # Reconoce expresiones primarias del lenguaje.
    def p_primario(self, p):
        '''primario : literal
                   | acceso
                   | llamada
                   | LPAREN expresion RPAREN
                   | instanciacion'''
        pass

    # Reconoce accesos a variables o a campos encadenados con punto.
    def p_acceso(self, p):
        '''acceso : ID
                  | acceso DOT ID'''
        pass

    # Reconoce llamadas a funciones con argumentos opcionales.
    def p_llamada(self, p):
        '''llamada : ID LPAREN argumentos_opt RPAREN'''
        pass

    # Reconoce la instanciación de registros mediante new.
    def p_instanciacion(self, p):
        '''instanciacion : NEW ID LPAREN argumentos_opt RPAREN'''
        pass

    # Permite que la lista de argumentos de una llamada sea vacía u opcional.
    def p_argumentos_opt(self, p):
        '''argumentos_opt : lambda
                         | argumentos'''
        pass

    # Construye la lista de argumentos de una llamada o instanciación.
    def p_argumentos(self, p):
        '''argumentos : argumentos COMMA expresion
                     | expresion'''
        pass

    # Reconoce los literales básicos del lenguaje.
    def p_literal(self, p):
        '''literal : INT_VALUE
                  | FLOAT_VALUE
                  | CHAR_VALUE
                  | TRUE
                  | FALSE'''
        pass

    # =======================================
    # PRODUCCIÓN VACÍA
    # =======================================

    def p_lambda(self, p):
        '''lambda : '''
        pass

    # =======================================
    # GESTIÓN DE ERRORES
    # =======================================

    def p_error(self, p):
        """Gestiona errores sintácticos."""
        # Marca que el análisis ha encontrado al menos un error.
        self.has_syntax_error = True
        if p:
            # Error sobre un token concreto.
            print(f"[ERROR] Token '{p.type}' inesperado en la línea {p.lineno}")
        else:
            # Error al llegar al final del fichero de forma inesperada.
            print("[ERROR] Error sintáctico al final del fichero")