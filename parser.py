import ply.yacc as yacc
from lexer import LexerClass

class ParserClass:
    """Analizador Sintáctico y Semántico del lenguaje Lava"""

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

    DEFAULT_TYPES = {
        'int': 0, 
        'float': 0.0, 
        'char': '', 
        'boolean': False
    }

    def __init__(self):
        """Inicializa el parser y define las reglas de producción."""
        # Guarda una instancia del lexer.
        self.lexer = LexerClass().lexer

        # Marca si durante el análisis ha aparecido algún error sintáctico.
        self.has_syntax_error = False

        # Marca si durante el análisis ha aparecido algún error semántico.
        self.has_semantic_error = False

        # Tablas semánticas principales.

        # Tabla de variables  { nombre -> tipo }
        self.symbols = {}  
        # Tabla de registros  { nombre -> {campo -> tipo} }     
        self.records = {}  
        # Tabla de funciones  { nombre -> [{'params':[(tipo,id),...], 'return_type':tipo}] }     
        self.functions = {}    

        # Pila de ámbitos. El primero es el ámbito global.
        self.stack = [self.symbols]

        # Contexto de análisis semántico.
        self.current_function = None
        self.loop_depth = 0

        # Construye el parser de PLY a partir de las reglas de esta clase.
        self.parser = yacc.yacc(module=self)

    def _reiniciar_estado_semantico(self):
        """Reinicia tablas y estado semántico para un nuevo parse."""
        self.has_semantic_error = False
        self.symbols = {}
        self.records = {}
        self.functions = {}
        self.stack = [self.symbols]
        self.current_function = None
        self.loop_depth = 0

    # =========================================================
    # UTILIDADES SEMÁNTICAS BÁSICAS 
    # =========================================================

    def _buscar_simbolo(self, name):
        """Busca un símbolo en la pila de ámbitos (de interno a externo)."""
        for elem in reversed(self.stack):
            if name in elem:
                return elem[name]
        return None

    def _actualizar_simbolo(self, name, value):
        """Actualiza el valor de un símbolo ya declarado."""
        for elem in reversed(self.stack):
            if name in elem:
                symbol_type, _ = elem[name]
                elem[name] = (symbol_type, value)
                return True
        return False

    def _auto_convert(self, source_type: str, target_type: str):
        """Reglas de conversión automática ."""
        if source_type == target_type:
            return True
        if source_type == 'char' and target_type in ('int', 'float'):
            return True
        if source_type == 'int' and target_type == 'float':
            return True
        return False

    def _valor_por_defecto(self, type_name: str):
        if type_name in self.DEFAULT_TYPES:
            return self.DEFAULT_TYPES[type_name]
        return None

    def _es_tipo_numerico(self, type_name):
        return type_name in ('char', 'int', 'float')

    def _tipo_numerico_comun(self, left_type, right_type):
        if 'float' in (left_type, right_type):
            return 'float'
        if 'int' in (left_type, right_type):
            return 'int'
        return 'char'

    def _convertir_numero(self, value, source_type, target_type):
        if value is None or source_type == target_type:
            return value

        if source_type == 'char' and target_type == 'int':
            return ord(value) if isinstance(value, str) and len(value) == 1 else int(value)

        if source_type == 'char' and target_type == 'float':
            if isinstance(value, str) and len(value) == 1:
                return float(ord(value))
            return float(value)

        if source_type == 'int' and target_type == 'float':
            return float(value)

        return value

    def _normalizar_operandos_numericos(self, left_type, left_value, right_type, right_value):
        common_type = self._tipo_numerico_comun(left_type, right_type)
        left_num = self._convertir_numero(left_value, left_type, common_type)
        right_num = self._convertir_numero(right_value, right_type, common_type)
        return common_type, left_num, right_num
    
    # =========================================================
    # MÉTODOS DE ENTRADA
    # =========================================================
 
    def parse(self, data: str):
        """Analiza una cadena de entrada."""
        # Reinicia el indicador de error antes de cada análisis.
        self.has_syntax_error = False
        self._reiniciar_estado_semantico()

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
        type_name, id_name, info = p[1], p[2], p[3]
        line = p.lineno(2)
        scope = self.stack[-1]

        # --- Es una función tipada ---
        if info.get('kind') == 'function':
            return

        # --- Es una lista de declaraciones: int a, b, c ---
        if info.get('kind') == 'decl_list':
            for name in [id_name] + info.get('ids', []):
                if name in scope:
                    self.has_semantic_error = True
                    print(f"[ERROR SEMANTICO] Linea {line}: Variable '{name}' ya declarada en este ámbito")
                else:
                    scope[name] = (type_name, self._valor_por_defecto(type_name))
            return

        # --- Es una declaración con inicialización: int a = expr ---
        if info.get('kind') != 'init':
            return

        if id_name in scope:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: Variable '{id_name}' ya declarada en este ámbito")
            return

        expr_type, expr_val = info.get('expr', ('error', None))

        if expr_type == 'error':
            can_assign = False
        elif expr_type == 'unknown':
            can_assign = True
        else:
            can_assign = self._auto_convert(expr_type, type_name)

        if not can_assign:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: No se puede asignar tipo '{expr_type}' a '{id_name}' de tipo '{type_name}'")
            return

        # Conversión de valor si los tipos difieren pero son compatibles
        if expr_val is not None and expr_type != type_name:
            if expr_type == 'char' and isinstance(expr_val, str):
                expr_val = ord(expr_val)
            if type_name == 'float' and expr_type in ('char', 'int'):
                expr_val = float(expr_val)
            elif type_name == 'int' and expr_type == 'char':
                expr_val = int(expr_val)

        scope[id_name] = (type_name, expr_val)

    # Desambigua si un elemento tipado es función o declaración de variable global.
    def p_resto_tipado_programa(self, p):
        '''resto_tipado_programa : LPAREN parametros_opt RPAREN bloque
                                | ASSIGN expresion SEMICOLON
                                | resto_lista_ids SEMICOLON'''
        if len(p) == 5 and p.slice[1].type == 'LPAREN':
            p[0] = {'kind': 'function'}
        elif len(p) == 4:
            p[0] = {'kind': 'init', 'expr': p[2]}
        else:
            p[0] = {'kind': 'decl_list', 'ids': p[1]}

    # Reconoce la continuación de una lista de identificadores separada por comas.
    def p_resto_listas_ids(self, p):
        '''resto_lista_ids : lambda
                         | resto_lista_ids COMMA ID'''
        if len(p) == 2:
            p[0] = []
        else:
            p[0] = p[1] + [p[3]]

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
        type_name = p[1]
        line = p.lineno(2)
        scope = self.stack[-1]

        # --- Es una lista de declaraciones: int a, b, c ---
        if len(p) == 3:
            for name in p[2]:
                if name in scope:
                    self.has_semantic_error = True
                    print(f"[ERROR SEMANTICO] Linea {line}: Variable '{name}' ya declarada en este ámbito")
                else:
                    scope[name] = (type_name, self._valor_por_defecto(type_name))
            return

        # --- Es una declaración con inicialización: int a = expr ---
        id_name = p[2]
        expr_type, expr_val = ('error', None)
        if isinstance(p[4], tuple) and len(p[4]) == 2:
            expr_type, expr_val = p[4]

        if id_name in scope:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: Variable '{id_name}' ya declarada en este ámbito")
            return

        if expr_type == 'error':
            can_assign = False
        elif expr_type == 'unknown':
            can_assign = True
        else:
            can_assign = self._auto_convert(expr_type, type_name)

        if not can_assign:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: No se puede asignar tipo '{expr_type}' a '{id_name}' de tipo '{type_name}'")
            return

        # Conversión de valor si los tipos difieren pero son compatibles
        if expr_val is not None and expr_type != type_name:
            if expr_type == 'char' and isinstance(expr_val, str):
                expr_val = ord(expr_val)
            if type_name == 'float' and expr_type in ('char', 'int'):
                expr_val = float(expr_val)
            elif type_name == 'int' and expr_type == 'char':
                expr_val = int(expr_val)

        scope[id_name] = (type_name, expr_val)

    # Reconoce una lista de identificadores separada por comas.
    def p_lista_ids(self, p):
        '''lista_ids : ID
                    | lista_ids COMMA ID'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    # Reconoce una asignación a una variable o acceso por punto.
    def p_asignacion(self, p):
        '''asignacion : acceso ASSIGN expresion'''
        left = p[1]
        line = p.lineno(2)

        if not isinstance(left, dict):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: Lado izquierdo de asignación inválido")
            return

        if left.get('kind') != 'var':
            # La semántica de asignación a campos de registros se completa en el siguiente paso.
            return

        id_name = left['name']
        type_name = left['type']

        expr_type, expr_val = ('error', None)
        if isinstance(p[3], tuple) and len(p[3]) == 2:
            expr_type, expr_val = p[3]

        if 'error' in (type_name, expr_type):
            can_assign = False
        elif 'unknown' in (type_name, expr_type):
            can_assign = True
        else:
            can_assign = self._auto_convert(expr_type, type_name)

        if not can_assign:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: No se puede asignar tipo '{expr_type}' a '{id_name}' de tipo '{type_name}'")
            return

        # Conversión de valor si los tipos difieren pero son compatibles
        if expr_val is not None and expr_type != type_name:
            if expr_type == 'char' and isinstance(expr_val, str):
                expr_val = ord(expr_val)
            if type_name == 'float' and expr_type in ('char', 'int'):
                expr_val = float(expr_val)
            elif type_name == 'int' and expr_type == 'char':
                expr_val = int(expr_val)

        self._actualizar_simbolo(id_name, expr_val)

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
        p[0] = p[1]

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
        
        left_expr, right_expr = p[1], p[3]
      
        if isinstance(left_expr, tuple) and len(left_expr) == 2:
            left_type, left_value = left_expr
        else:
            left_type, left_value = ('error', None)

        if isinstance(right_expr, tuple) and len(right_expr) == 2:
            right_type, right_value = right_expr
        else:
            right_type, right_value = ('error', None)

        operator_type = p.slice[2].type
        line = getattr(p.slice[2], 'lineno', '?')

        if 'error' in (left_type, right_type):
            p[0] = ('error', None)
            return

        # En este paso se permiten valores desconocidos para no bloquear
        # reglas semánticas aún no implementadas (funciones/registros).
        if 'unknown' in (left_type, right_type):
            p[0] = ('unknown', None)
            return

        if operator_type in ('PLUS', 'MINUS', 'TIMES', 'DIVIDE'):
            if not (self._es_tipo_numerico(left_type) and self._es_tipo_numerico(right_type)):
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: Operación aritmética inválida entre '{left_type}' y '{right_type}'")
                p[0] = ('error', None)
                return

            result_type = self._tipo_numerico_comun(left_type, right_type)
            result_value = None

            if left_value is not None and right_value is not None:
                try:
                    _, l_val, r_val = self._normalizar_operandos_numericos(
                        left_type, left_value, right_type, right_value
                    )

                    if operator_type == 'PLUS':
                        raw = l_val + r_val
                    elif operator_type == 'MINUS':
                        raw = l_val - r_val
                    elif operator_type == 'TIMES':
                        raw = l_val * r_val
                    elif r_val == 0:
                        raw = None
                    elif result_type == 'int':
                        raw = int(l_val / r_val)
                    else:
                        raw = l_val / r_val

                    if raw is not None and result_type == 'char':
                        result_value = chr(int(raw) % 256)
                    else:
                        result_value = raw
                except (TypeError, ValueError, ZeroDivisionError):
                    result_value = None

            p[0] = (result_type, result_value)
            return

        if operator_type in ('GREATER', 'GREATER_EQUAL', 'LESS', 'LESS_EQUAL'):
            if not (self._es_tipo_numerico(left_type) and self._es_tipo_numerico(right_type)):
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: Operación comparativa inválida entre '{left_type}' y '{right_type}'")
                p[0] = ('error', None)
                return

            result_value = None
            if left_value is not None and right_value is not None:
                _, l_val, r_val = self._normalizar_operandos_numericos(
                    left_type, left_value, right_type, right_value
                )

                if operator_type == 'GREATER':
                    result_value = l_val > r_val
                elif operator_type == 'GREATER_EQUAL':
                    result_value = l_val >= r_val
                elif operator_type == 'LESS':
                    result_value = l_val < r_val
                else:
                    result_value = l_val <= r_val

            p[0] = ('boolean', result_value)
            return

        if operator_type == 'EQUAL':
            comparable = (
                left_type == right_type
                or self._auto_convert(left_type, right_type)
                or self._auto_convert(right_type, left_type)
            )
            if not comparable:
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: No se pueden comparar tipos '{left_type}' y '{right_type}' con '=='")
                p[0] = ('error', None)
                return

            result_value = None
            if left_value is not None and right_value is not None:
                if self._es_tipo_numerico(left_type) and self._es_tipo_numerico(right_type):
                    _, l_val, r_val = self._normalizar_operandos_numericos(
                        left_type, left_value, right_type, right_value
                    )
                    result_value = (l_val == r_val)
                else:
                    result_value = (left_value == right_value)

            p[0] = ('boolean', result_value)
            return

        if operator_type in ('AND', 'OR'):
            if left_type != 'boolean' or right_type != 'boolean':
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: Operación lógica inválida entre '{left_type}' y '{right_type}'")
                p[0] = ('error', None)
                return

            result_value = None
            if left_value is not None and right_value is not None:
                if operator_type == 'AND':
                    result_value = left_value and right_value
                else:
                    result_value = left_value or right_value

            p[0] = ('boolean', result_value)
            return

        p[0] = ('error', None)
    
    # Operadores unarios del lenguaje (NOT, +, -).
    def p_expresion_unaria(self, p):
        '''expresion : NOT expresion
                    | MINUS expresion %prec UMINUS
                    | PLUS expresion %prec UPLUS'''
        expr = p[2]
        if isinstance(expr, tuple) and len(expr) == 2:
            expr_type, expr_value = expr
        else:
            expr_type, expr_value = ('error', None)

        operator_type = p.slice[1].type
        line = getattr(p.slice[1], 'lineno', '?')

        if expr_type in ('error', 'unknown'):
            p[0] = (expr_type, None)
            return

        if operator_type == 'NOT':
            if expr_type != 'boolean':
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: El operador '!' requiere boolean y recibió '{expr_type}'")
                p[0] = ('error', None)
                return

            p[0] = ('boolean', None if expr_value is None else (not expr_value))
            return

        if not self._es_tipo_numerico(expr_type):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: El operador unario requiere tipo numérico y recibió '{expr_type}'")
            p[0] = ('error', None)
            return

        if expr_value is None or operator_type == 'PLUS':
            p[0] = (expr_type, expr_value)
            return

        if expr_type == 'char' and isinstance(expr_value, str) and len(expr_value) == 1:
            p[0] = ('char', chr((-ord(expr_value)) % 256))
            return

        p[0] = (expr_type, -expr_value)
    

    # Reduce una expresión al nivel de primario.
    def p_expresion_primaria(self, p):
        '''expresion : primario'''
        p[0] = p[1]

    # Reconoce expresiones primarias del lenguaje.
    def p_primario(self, p):
        '''primario : literal
                   | acceso
                   | llamada
                   | LPAREN expresion RPAREN
                   | instanciacion'''
        if len(p) == 2:
            node = p[1]
            if isinstance(node, tuple) and len(node) == 2:
                p[0] = node
            elif isinstance(node, dict):
                p[0] = (node.get('type', 'unknown'), node.get('value'))
            else:
                p[0] = ('unknown', None)
        else:
            p[0] = p[2]

    # Reconoce accesos a variables o a campos encadenados con punto.
    def p_acceso(self, p):
        '''acceso : ID
                  | acceso DOT ID'''
        if len(p) == 2:
            var_name = p[1]
            symbol = self._buscar_simbolo(var_name)
            if symbol is None:
                self.has_semantic_error = True
                line = getattr(p.slice[1], 'lineno', '?')
                print(f"[ERROR SEMANTICO] Linea {line}: La variable '{var_name}' no ha sido declarada")
                p[0] = {'kind': 'invalid', 'name': var_name, 'type': 'error', 'value': None}
                return

            p[0] = {
                'kind': 'var',
                'name': var_name,
                'type': symbol[0],
                'value': symbol[1]
            }
            return

        # La resolución tipada de campos de registro se implementa en el siguiente paso.
        left_access = p[1]
        field_name = p[3]
        base_name = left_access.get('name', '?') if isinstance(left_access, dict) else '?'
        p[0] = {
            'kind': 'field',
            'name': f"{base_name}.{field_name}",
            'type': 'unknown',
            'value': None
        }

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
        token_type = p.slice[1].type
        if token_type == 'INT_VALUE':
            p[0] = ('int', p[1])
        elif token_type == 'FLOAT_VALUE':
            p[0] = ('float', p[1])
        elif token_type == 'CHAR_VALUE':
            p[0] = ('char', p[1])
        else:
            p[0] = ('boolean', p[1])

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