import ply.yacc as yacc
import os
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
        self._tiene_flujo_o_funciones = False
        self._decl_tipo_actual = None
        self._decl_id_actual = None
        self._decl_linea_actual = '?'

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
        self._tiene_flujo_o_funciones = False
        self._decl_tipo_actual = None
        self._decl_id_actual = None
        self._decl_linea_actual = '?'

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

    def _costo_conversion(self, source_type, target_type):
        if source_type == target_type:
            return 0
        if source_type == 'char' and target_type == 'int':
            return 1
        if source_type == 'int' and target_type == 'float':
            return 1
        if source_type == 'char' and target_type == 'float':
            return 2
        return None

    def _valor_por_defecto(self, type_name: str, visited=None):
        if type_name in self.DEFAULT_TYPES:
            return self.DEFAULT_TYPES[type_name]

        if type_name not in self.records:
            return None

        if visited is None:
            visited = set()
        if type_name in visited:
            return None

        visited = visited | {type_name}
        record_instance = {'__record_type__': type_name}
        for field_name, field_type in self.records[type_name].items():
            record_instance[field_name] = self._valor_por_defecto(field_type, visited)

        return record_instance

    def _es_tipo_valido(self, type_name):
        return type_name in self.DEFAULT_TYPES or type_name in self.records

    def _registrar_firma_funcion(self, func_name, params, return_type, line='?'):
        if func_name not in self.functions:
            self.functions[func_name] = []

        param_types = [param_type for param_type, _ in params]
        for signature in self.functions[func_name]:
            signature_types = [param_type for param_type, _ in signature.get('params', [])]
            if signature_types == param_types:
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: La función '{func_name}' con esa firma ya fue declarada")
                return False

        self.functions[func_name].append({'params': params, 'return_type': return_type})
        return True

    def _es_tipo_numerico(self, type_name):
        return type_name in ('char', 'int', 'float')

    def _tipo_numerico_comun(self, left_type, right_type):
        if 'float' in (left_type, right_type):
            return 'float'
        if 'int' in (left_type, right_type):
            return 'int'
        return 'char'

    def _convertir_numero(self, value, source_type, target_type):
        if value is None:
            return value

        if source_type == target_type:
            # Para operar/comparar numéricamente dos char, se usa su código ASCII.
            if source_type == 'char' and target_type == 'char':
                if isinstance(value, str) and len(value) == 1:
                    return ord(value)
                return int(value)
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

    def _condicion_es_valida(self, expr, line, contexto):
        expr_type = 'error'
        if isinstance(expr, tuple) and len(expr) == 2:
            expr_type = expr[0]

        if expr_type == 'boolean' or expr_type == 'unknown':
            return True

        if expr_type != 'error':
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: La condición de '{contexto}' debe ser de tipo 'boolean' y recibió '{expr_type}'")
        return False

    def _formatear_valor(self, value):
        if isinstance(value, bool):
            return 'true' if value else 'false'

        if isinstance(value, dict):
            campos = []
            for key, field_value in value.items():
                if key == '__record_type__':
                    continue
                campos.append(f"{key}:{self._formatear_valor(field_value)}")
            return '{' + ','.join(campos) + '}'

        return str(value)

    def exportar_tablas_semanticas(self, input_path):
        base = os.path.splitext(input_path)[0]

        symbols_path = base + '.symbols'
        records_path = base + '.records'
        functions_path = base + '.functions'

        usar_solo_tipos = self._tiene_flujo_o_funciones or bool(self.functions)

        with open(symbols_path, 'w', encoding='utf-8') as out_symbols:
            for name, (type_name, value) in self.symbols.items():
                if usar_solo_tipos:
                    out_symbols.write(f"{name}:{type_name}\n")
                else:
                    out_symbols.write(f"{name}:{type_name},{self._formatear_valor(value)}\n")

        with open(records_path, 'w', encoding='utf-8') as out_records:
            for record_name, record_schema in self.records.items():
                campos = ','.join(f"{field_name}:{field_type}" for field_name, field_type in record_schema.items())
                out_records.write(f"{record_name}:[{campos}]\n")

        with open(functions_path, 'w', encoding='utf-8') as out_functions:
            for function_name, signatures in self.functions.items():
                for signature in signatures:
                    params = signature.get('params', [])
                    params_txt = ','.join(f"{param_name}:{param_type}" for param_type, param_name in params)
                    return_type = signature.get('return_type', 'void')
                    out_functions.write(f"{function_name}:[{params_txt}],{return_type}\n")
    
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
        '''declaracion_funcion_void : VOID ID LPAREN parametros_opt RPAREN inicio_funcion_void bloque_void fin_funcion_void'''
        pass

    def p_inicio_funcion_void(self, p):
        '''inicio_funcion_void :'''
        func_name = p[-4]
        params = p[-2] if isinstance(p[-2], list) else []
        line = getattr(p.lexer, 'lineno', '?')

        self._tiene_flujo_o_funciones = True

        if any(param_type == 'error' for param_type, _ in params):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: No se puede declarar la función '{func_name}' con parámetros de tipo inválido")
        else:
            self._registrar_firma_funcion(func_name, params, 'void', line)

        func_scope = {}
        for param_type, param_name in params:
            if param_name in func_scope:
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: Parámetro '{param_name}' repetido en la función '{func_name}'")
            else:
                func_scope[param_name] = (param_type, None)

        self.stack.append(func_scope)
        self.current_function = {
            'name': func_name,
            'return_type': 'void',
            'has_return': False
        }

    def p_fin_funcion_void(self, p):
        '''fin_funcion_void :'''
        if len(self.stack) > 1:
            self.stack.pop()
        self.current_function = None

    # Reconoce una declaración tipada global o una función con retorno tipado.
    def p_declaracion_o_funcion_tipada(self, p):
        '''declaracion_o_funcion_tipada : tipo ID marcar_declaracion_tipada resto_tipado_programa'''
        type_name, id_name, info = p[1], p[2], p[4]
        line = p.lineno(2)
        scope = self.stack[-1]

        if not self._es_tipo_valido(type_name):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: El tipo '{type_name}' no existe")
            self._decl_tipo_actual = None
            self._decl_id_actual = None
            self._decl_linea_actual = '?'
            return

        # --- Es una función tipada ---
        if info.get('kind') == 'function':
            if not info.get('has_return', False):
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: La función '{id_name}' debe retornar un valor de tipo '{type_name}'")
            self._decl_tipo_actual = None
            self._decl_id_actual = None
            self._decl_linea_actual = '?'
            return

        # --- Es una lista de declaraciones: int a, b, c ---
        if info.get('kind') == 'decl_list':
            for name in [id_name] + info.get('ids', []):
                if name in scope:
                    self.has_semantic_error = True
                    print(f"[ERROR SEMANTICO] Linea {line}: Variable '{name}' ya declarada en este ámbito")
                else:
                    scope[name] = (type_name, self._valor_por_defecto(type_name))
            self._decl_tipo_actual = None
            self._decl_id_actual = None
            self._decl_linea_actual = '?'
            return

        # --- Es una declaración con inicialización: int a = expr ---
        if info.get('kind') != 'init':
            self._decl_tipo_actual = None
            self._decl_id_actual = None
            self._decl_linea_actual = '?'
            return

        if id_name in scope:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: Variable '{id_name}' ya declarada en este ámbito")
            self._decl_tipo_actual = None
            self._decl_id_actual = None
            self._decl_linea_actual = '?'
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
            self._decl_tipo_actual = None
            self._decl_id_actual = None
            self._decl_linea_actual = '?'
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
        self._decl_tipo_actual = None
        self._decl_id_actual = None
        self._decl_linea_actual = '?'

    def p_marcar_declaracion_tipada(self, p):
        '''marcar_declaracion_tipada :'''
        self._decl_tipo_actual = p[-2]
        self._decl_id_actual = p[-1]
        self._decl_linea_actual = getattr(p.lexer, 'lineno', '?')

    # Desambigua si un elemento tipado es función o declaración de variable global.
    def p_resto_tipado_programa(self, p):
        '''resto_tipado_programa : LPAREN parametros_opt RPAREN inicio_funcion_tipada bloque fin_funcion_tipada
                                | ASSIGN expresion SEMICOLON
                                | resto_lista_ids SEMICOLON'''
        if len(p) == 7 and p.slice[1].type == 'LPAREN':
            p[0] = {'kind': 'function', 'has_return': p[6].get('has_return', False)}
        elif len(p) == 4:
            p[0] = {'kind': 'init', 'expr': p[2]}
        else:
            p[0] = {'kind': 'decl_list', 'ids': p[1]}

    def p_inicio_funcion_tipada(self, p):
        '''inicio_funcion_tipada :'''
        return_type = self._decl_tipo_actual
        func_name = self._decl_id_actual
        params = p[-2] if isinstance(p[-2], list) else []
        line = self._decl_linea_actual

        self._tiene_flujo_o_funciones = True

        if any(param_type == 'error' for param_type, _ in params):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: No se puede declarar la función '{func_name}' con parámetros de tipo inválido")
        else:
            self._registrar_firma_funcion(func_name, params, return_type, line)

        func_scope = {}
        for param_type, param_name in params:
            if param_name in func_scope:
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: Parámetro '{param_name}' repetido en la función '{func_name}'")
            else:
                func_scope[param_name] = (param_type, None)

        self.stack.append(func_scope)
        self.current_function = {
            'name': func_name,
            'return_type': return_type,
            'has_return': False
        }

    def p_fin_funcion_tipada(self, p):
        '''fin_funcion_tipada :'''
        has_return = False
        if isinstance(self.current_function, dict):
            has_return = self.current_function.get('has_return', False)

        if len(self.stack) > 1:
            self.stack.pop()
        self.current_function = None

        p[0] = {'has_return': has_return}

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
        self._tiene_flujo_o_funciones = True
        self._condicion_es_valida(p[3], p.lineno(1), 'if')

    # Reconoce la cláusula else opcional dentro de una función void.
    def p_else_void_opt(self, p):
        '''else_void_opt : lambda
                        | ELSE bloque_void'''
        pass

    # Reconoce una sentencia while dentro de una función void.
    def p_sentencia_while_void(self, p):
        '''sentencia_while_void : WHILE LPAREN expresion RPAREN entrar_bucle bloque_void salir_bucle'''
        self._tiene_flujo_o_funciones = True
        self._condicion_es_valida(p[3], p.lineno(1), 'while')

    # Reconoce una sentencia do-while dentro de una función void.
    def p_sentencia_do_while_void(self, p):
        '''sentencia_do_while_void : DO entrar_bucle bloque_void salir_bucle WHILE LPAREN expresion RPAREN'''
        self._tiene_flujo_o_funciones = True
        self._condicion_es_valida(p[7], p.lineno(5), 'do-while')

    # Reconoce sentencias simples válidas dentro de una función void.
    def p_sentencia_simple_void(self, p):
        '''sentencia_simple_void : asignacion
                                | print_stmt
                                | BREAK
                                | expresion'''
        if len(p) == 2 and p.slice[1].type == 'BREAK' and self.loop_depth <= 0:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {p.lineno(1)}: 'break' fuera de un bucle")

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
        self._tiene_flujo_o_funciones = True
        self._condicion_es_valida(p[3], p.lineno(1), 'if')

    # Reconoce la cláusula else opcional en un if general.
    def p_else_opt(self, p):
        '''else_opt : lambda
                   | ELSE bloque'''
        pass

    # Reconoce una sentencia while general del lenguaje.
    def p_sentencia_while(self, p):
        '''sentencia_while : WHILE LPAREN expresion RPAREN entrar_bucle bloque salir_bucle'''
        self._tiene_flujo_o_funciones = True
        self._condicion_es_valida(p[3], p.lineno(1), 'while')

    # Reconoce una sentencia do-while general del lenguaje.
    def p_sentencia_do_while(self, p):
        '''sentencia_do_while : DO entrar_bucle bloque salir_bucle WHILE LPAREN expresion RPAREN'''
        self._tiene_flujo_o_funciones = True
        self._condicion_es_valida(p[7], p.lineno(5), 'do-while')

    def p_entrar_bucle(self, p):
        '''entrar_bucle :'''
        self.loop_depth += 1

    def p_salir_bucle(self, p):
        '''salir_bucle :'''
        self.loop_depth = max(0, self.loop_depth - 1)

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
        if len(p) == 2 and p.slice[1].type == 'BREAK':
            if self.loop_depth <= 0:
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {p.lineno(1)}: 'break' fuera de un bucle")
            return

        if len(p) != 3 or p.slice[1].type != 'RETURN':
            return

        line = p.lineno(1)

        if self.current_function is None:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: 'return' fuera de una función")
            return

        # Marca que existe al menos un return en la función (aunque su tipo falle).
        self.current_function['has_return'] = True

        expected_type = self.current_function.get('return_type', 'void')

        expr_type, _ = ('error', None)
        if isinstance(p[2], tuple) and len(p[2]) == 2:
            expr_type, _ = p[2]

        if expr_type == 'error':
            can_return = False
        elif expr_type == 'unknown':
            can_return = True
        else:
            can_return = self._auto_convert(expr_type, expected_type)

        if not can_return:
            self.has_semantic_error = True
            func_name = self.current_function.get('name', '?')
            print(f"[ERROR SEMANTICO] Linea {line}: Return de tipo '{expr_type}' no compatible con función '{func_name}' de tipo '{expected_type}'")
            return

    # Reconoce declaraciones de variables simples o con inicialización.
    def p_declaracion_variable(self, p):
        '''declaracion_variable : tipo lista_ids
                               | tipo ID ASSIGN expresion'''
        type_name = p[1]
        line = p.lineno(2)
        scope = self.stack[-1]

        if not self._es_tipo_valido(type_name):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: El tipo '{type_name}' no existe")
            return

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

        left_kind = left.get('kind')
        if left_kind not in ('var', 'field'):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: Lado izquierdo de asignación inválido")
            return

        id_name = left.get('name', '?')
        type_name = left.get('type', 'error')

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

        if left_kind == 'var':
            self._actualizar_simbolo(id_name, expr_val)
            return

        root_name = left.get('root')
        path = left.get('path', [])
        if not root_name or not path:
            return

        root_symbol = self._buscar_simbolo(root_name)
        if root_symbol is None:
            return

        _, root_value = root_symbol
        if root_value is None:
            return

        if not isinstance(root_value, dict):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: No se puede acceder a campos sobre '{root_name}'")
            return

        target = root_value
        for field in path[:-1]:
            if not isinstance(target, dict):
                target = None
                break
            target = target.get(field)

        if isinstance(target, dict):
            target[path[-1]] = expr_val
            self._actualizar_simbolo(root_name, root_value)

    # Reconoce una llamada a la función del sistema print.
    def p_print_stmt(self, p):
        '''print_stmt : PRINT LPAREN argumentos_opt RPAREN'''
        args = p[3] if isinstance(p[3], list) else []
        line = p.lineno(1)

        if len(args) == 0:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: 'print' requiere al menos un argumento")
            return

        for arg in args:
            if not (isinstance(arg, tuple) and len(arg) == 2):
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: Argumento inválido en 'print'")
                return

            arg_type, _ = arg
            if arg_type == 'error':
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: Argumento inválido en 'print'")
                return

    # =======================================
    # REGISTROS Y FUNCIONES
    # =======================================

    # Reconoce una declaración global de registro.
    def p_declaracion_record(self, p):
        '''declaracion_record : RECORD ID LPAREN campos_record_opt RPAREN'''
        record_name = p[2]
        fields = p[4] if isinstance(p[4], list) else []
        line = p.lineno(2)

        if record_name in self.records:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: El registro '{record_name}' ya fue declarado")
            return

        record_schema = {}
        has_local_error = False

        for field_type, field_name in fields:
            if field_name in record_schema:
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: El campo '{field_name}' está repetido en el registro '{record_name}'")
                has_local_error = True
                continue

            if not self._es_tipo_valido(field_type):
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: El tipo '{field_type}' no existe para el campo '{field_name}'")
                has_local_error = True
                continue

            record_schema[field_name] = field_type

        if not has_local_error:
            self.records[record_name] = record_schema

    # Permite que la lista de campos de un registro sea vacía u opcional.
    def p_campos_record_opt(self, p):
        '''campos_record_opt : lambda
                            | campos_record'''
        if len(p) == 2 and p.slice[1].type == 'lambda':
            p[0] = []
        else:
            p[0] = p[1]

    # Construye la lista de campos de un registro.
    def p_campos_record(self, p):
        '''campos_record : campos_record COMMA campo_record
                       | campo_record'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    # Reconoce un campo individual dentro de un registro.
    def p_campo_record(self, p):
        '''campo_record : tipo ID'''
        p[0] = (p[1], p[2])

    # Permite que la lista de parámetros de una función sea vacía u opcional.
    def p_parametros_opt(self, p):
        '''parametros_opt : lambda
                         | parametros'''
        if len(p) == 2 and p.slice[1].type == 'lambda':
            p[0] = []
        else:
            p[0] = p[1]

    # Construye la lista de parámetros tipados de una función.
    def p_parametros(self, p):
        '''parametros : parametros COMMA parametro
                     | parametro'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

    # Reconoce un parámetro individual de una función.
    def p_parametro(self, p):
        '''parametro : tipo ID'''
        type_name, id_name = p[1], p[2]
        line = p.lineno(2)

        if not self._es_tipo_valido(type_name):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: El tipo '{type_name}' no existe para el parámetro '{id_name}'")
            p[0] = ('error', id_name)
            return

        p[0] = (type_name, id_name)

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
                'value': symbol[1],
                'root': var_name,
                'path': []
            }
            return

        left_access = p[1]
        field_name = p[3]
        line = getattr(p.slice[3], 'lineno', '?')

        if not isinstance(left_access, dict):
            p[0] = {'kind': 'invalid', 'name': field_name, 'type': 'error', 'value': None}
            return

        left_type = left_access.get('type', 'error')
        if left_type not in self.records:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: El tipo '{left_type}' no tiene el campo '{field_name}'")
            p[0] = {
                'kind': 'invalid',
                'name': f"{left_access.get('name', '?')}.{field_name}",
                'type': 'error',
                'value': None
            }
            return

        if field_name not in self.records[left_type]:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: El registro '{left_type}' no tiene el campo '{field_name}'")
            p[0] = {
                'kind': 'invalid',
                'name': f"{left_access.get('name', '?')}.{field_name}",
                'type': 'error',
                'value': None
            }
            return

        field_type = self.records[left_type][field_name]
        field_value = None
        left_value = left_access.get('value')
        if isinstance(left_value, dict):
            field_value = left_value.get(field_name)

        root_name = left_access.get('root', left_access.get('name', '?'))
        base_path = left_access.get('path', [])
        new_path = base_path + [field_name]

        p[0] = {
            'kind': 'field',
            'name': f"{left_access.get('name', '?')}.{field_name}",
            'type': field_type,
            'value': field_value,
            'root': root_name,
            'path': new_path
        }

    # Reconoce llamadas a funciones con argumentos opcionales.
    def p_llamada(self, p):
        '''llamada : ID LPAREN argumentos_opt RPAREN'''
        func_name = p[1]
        args = p[3] if isinstance(p[3], list) else []
        line = p.lineno(1)

        if self.current_function is not None and func_name == self.current_function.get('name'):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: No se permite invocar '{func_name}' dentro de su propio cuerpo")
            p[0] = ('error', None)
            return

        if func_name not in self.functions:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: La función '{func_name}' no existe")
            p[0] = ('error', None)
            return

        arg_types = []
        for arg in args:
            if isinstance(arg, tuple) and len(arg) == 2:
                arg_types.append(arg[0])
            else:
                arg_types.append('error')

        if 'error' in arg_types:
            p[0] = ('error', None)
            return

        candidates = []
        for signature in self.functions[func_name]:
            params = signature.get('params', [])
            if len(params) != len(arg_types):
                continue

            conversions = 0
            compatible = True
            for arg_type, (param_type, _) in zip(arg_types, params):
                if arg_type == param_type:
                    continue

                if arg_type == 'unknown':
                    conversions += 3
                    continue

                conversion_cost = self._costo_conversion(arg_type, param_type)
                if conversion_cost is not None:
                    conversions += conversion_cost
                else:
                    compatible = False
                    break

            if compatible:
                candidates.append((conversions, signature))

        if not candidates:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: No existe una sobrecarga compatible para '{func_name}'")
            p[0] = ('error', None)
            return

        exact = [signature for conversions, signature in candidates if conversions == 0]
        if len(exact) == 1:
            selected = exact[0]
            p[0] = (selected.get('return_type', 'unknown'), None)
            return

        if len(exact) > 1:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: Llamada ambigua a '{func_name}'")
            p[0] = ('error', None)
            return

        min_conversions = min(conversions for conversions, _ in candidates)
        best = [signature for conversions, signature in candidates if conversions == min_conversions]
        if len(best) != 1:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: Llamada ambigua a '{func_name}'")
            p[0] = ('error', None)
            return

        selected = best[0]
        p[0] = (selected.get('return_type', 'unknown'), None)

    # Reconoce la instanciación de registros mediante new.
    def p_instanciacion(self, p):
        '''instanciacion : NEW ID LPAREN argumentos_opt RPAREN'''
        record_name = p[2]
        args = p[4] if isinstance(p[4], list) else []
        line = p.lineno(1)

        if record_name not in self.records:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: El registro '{record_name}' no existe")
            p[0] = ('error', None)
            return

        field_items = list(self.records[record_name].items())
        if len(args) != len(field_items):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: La instanciación de '{record_name}' requiere {len(field_items)} argumentos y recibió {len(args)}")
            p[0] = ('error', None)
            return

        instance = {'__record_type__': record_name}
        has_local_error = False

        for (field_name, field_type), arg in zip(field_items, args):
            arg_type, arg_value = ('error', None)
            if isinstance(arg, tuple) and len(arg) == 2:
                arg_type, arg_value = arg

            if arg_type == 'error':
                has_local_error = True
                continue

            if arg_type != 'unknown' and not (arg_type == field_type or self._auto_convert(arg_type, field_type)):
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: El argumento para '{field_name}' no es compatible con tipo '{field_type}'")
                has_local_error = True
                continue

            if arg_value is not None and arg_type != field_type:
                arg_value = self._convertir_numero(arg_value, arg_type, field_type)

            instance[field_name] = arg_value

        if has_local_error:
            p[0] = ('error', None)
            return

        p[0] = (record_name, instance)

    # Permite que la lista de argumentos de una llamada sea vacía u opcional.
    def p_argumentos_opt(self, p):
        '''argumentos_opt : lambda
                         | argumentos'''
        if len(p) == 2 and p.slice[1].type == 'lambda':
            p[0] = []
        else:
            p[0] = p[1]

    # Construye la lista de argumentos de una llamada o instanciación.
    def p_argumentos(self, p):
        '''argumentos : argumentos COMMA expresion
                     | expresion'''
        if len(p) == 2:
            p[0] = [p[1]]
        else:
            p[0] = p[1] + [p[3]]

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