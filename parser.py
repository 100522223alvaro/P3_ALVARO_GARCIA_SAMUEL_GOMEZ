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

    # Valores por defecto de cada tipo básico
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

        # Pila de ámbitos.
        self.stack = [self.symbols]

        # Función que se está analizando en este momento (si hay alguna)
        self.current_function = None
        # Número de bucles anidados abiertos en este momento
        self.loop_depth = 0
        # True si el programa contiene estructuras de control o funciones
        self._has_flow = False
        
        # Tipo, nombre y línea de la declaración que se está procesando
        self._decl_type = None
        self._decl_name = None
        self._decl_line = '?'

        # Estructuras para la generación de cuartetos.
        # Almacena los cuartetos emitidos durante el parseo.
        self.quartets = []
        # Cuenta temporales para generar nombres únicos (@T1, @T2, ...).
        self._temp_counter = 0
        # Cuenta etiquetas para generar saltos únicos (@L1, @L2, ...).
        self._label_counter = 0
        # Guarda el contexto de if/else activos para resolver saltos.
        self._if_codegen_stack = []
        # Guarda el contexto de bucles activos para break y cierres.
        self._loop_codegen_stack = []

        # Construye el parser de PLY a partir de las reglas de esta clase.
        self.parser = yacc.yacc(module=self)
    
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
    
    def _reiniciar_estado_semantico(self):
        """Reinicia tablas y estado semántico para un nuevo parse."""
        self.has_semantic_error = False
        self.symbols = {}
        self.records = {}
        self.functions = {}
        self.stack = [self.symbols]
        self.current_function = None
        self.loop_depth = 0
        self._has_flow = False
        self._decl_type = None
        self._decl_name = None
        self._decl_line = '?'

        # Reinicia el estado de generación de cuartetos.
        self.quartets = []
        self._temp_counter = 0
        self._label_counter = 0
        self._if_codegen_stack = []
        self._loop_codegen_stack = []

    # =========================================================
    # MÉTODOS DE APOYO PARA GENERACIÓN DE CUARTETOS
    # =========================================================

    def _expr(self, type_name, value, ref=None):
        """Crea un resultado de expresión con referencia opcional."""
        # Si no llega referencia, intenta derivarla del valor inmediato.
        if ref is None:
            ref = self._valor_a_operando(value, type_name)

        # Devuelve la representación canónica usada por el parser.
        return (type_name, value, ref)

    def _extraer_expr(self, expr):
        """Extrae tipo, valor y referencia de una expresión."""
        # Valida el formato mínimo de una expresión tipada.
        if not (isinstance(expr, tuple) and len(expr) >= 2):
            return 'error', None, None

        # Obtiene tipo y valor de las dos primeras posiciones.
        expr_type, expr_value = expr[0], expr[1]

        # Toma la referencia explícita si la tupla la incluye.
        expr_ref = expr[2] if len(expr) >= 3 else None

        # Si no hay referencia explícita, intenta usar el literal como operando.
        if expr_ref is None:
            expr_ref = self._valor_a_operando(expr_value, expr_type)

        return expr_type, expr_value, expr_ref

    def _nuevo_temporal(self):
        """Genera un nuevo nombre de temporal para cuartetos."""
        # Incrementa el contador global de temporales.
        self._temp_counter += 1

        # Construye el identificador con formato @Tn.
        return f"@T{self._temp_counter}"

    def _nueva_etiqueta(self):
        """Genera un nuevo nombre de etiqueta para cuartetos."""
        # Incrementa el contador global de etiquetas.
        self._label_counter += 1

        # Construye el identificador con formato @Ln.
        return f"@L{self._label_counter}"

    def _normalizar_operando_cuarteto(self, operand):
        """Convierte un operando al formato texto usado en .quartets."""
        # Representa operandos ausentes con el marcador vacío estándar.
        if operand is None:
            return '_'

        # Fuerza el formato textual de booleanos en minúsculas.
        if isinstance(operand, bool):
            return 'true' if operand else 'false'

        # Serializa cualquier otro operando como cadena.
        return str(operand)

    def _emit(self, operator, arg1='_', arg2='_', result='_'):
        """Añade un cuarteto a la lista de salida."""
        # Normaliza cada campo antes de almacenarlo en el buffer.
        self.quartets.append(
            (
                self._normalizar_operando_cuarteto(operator),
                self._normalizar_operando_cuarteto(arg1),
                self._normalizar_operando_cuarteto(arg2),
                self._normalizar_operando_cuarteto(result),
            )
        )

    def _valor_a_operando(self, value, value_type=None):
        """Convierte un valor inmediato al formato de operando de cuarteto."""
        # Los valores nulos no generan operando directo.
        if value is None:
            return None

        # Serializa booleanos al formato textual del IR.
        if isinstance(value, bool):
            return 'true' if value else 'false'

        # Serializa enteros y flotantes sin adornos.
        if isinstance(value, (int, float)):
            return str(value)

        # Procesa literales de texto y, en especial, caracteres.
        if isinstance(value, str):
            if value_type == 'char':
                # Escapa barra invertida y comilla simple para el fichero.
                escaped = value.replace('\\', '\\\\').replace("'", "\\'")
                return f"'{escaped}'"
            return value

        # Si no se reconoce el tipo, no se emite operando inmediato.
        return None

    def _asegurar_tipo_en_cuartetos(self, ref, source_type, target_type):
        """Inserta conversiones de cuartetos cuando un operando cambia de tipo."""
        # Si no hay conversión que hacer, conserva la referencia original.
        if ref is None or source_type == target_type:
            return ref

        # Convierte char -> int mediante temporal intermedio.
        if source_type == 'char' and target_type == 'int':
            temp = self._nuevo_temporal()
            self._emit('CHAR_TO_INT', ref, '_', temp)
            return temp

        # Convierte int -> float mediante temporal intermedio.
        if source_type == 'int' and target_type == 'float':
            temp = self._nuevo_temporal()
            self._emit('INT_TO_FLOAT', ref, '_', temp)
            return temp

        # Convierte char -> float en dos pasos: char->int y luego int->float.
        if source_type == 'char' and target_type == 'float':
            temp_int = self._nuevo_temporal()
            self._emit('CHAR_TO_INT', ref, '_', temp_int)
            temp_float = self._nuevo_temporal()
            self._emit('INT_TO_FLOAT', temp_int, '_', temp_float)
            return temp_float

        # Si la conversión no está modelada en IR, mantiene la referencia.
        return ref

    def _operador_binario_a_cuarteto(self, operator_type):
        """Mapea un operador binario de la gramática a su instrucción de cuarteto."""
        # Tabla de traducción token de gramática -> opcode de cuarteto.
        mapping = {
            'PLUS': 'ADD',
            'MINUS': 'SUB',
            'TIMES': 'MUL',
            'DIVIDE': 'DIV',
            'GREATER': 'GT',
            'GREATER_EQUAL': 'GTE',
            'LESS': 'LT',
            'LESS_EQUAL': 'LTE',
            'EQUAL': 'EQ',
            'AND': 'AND',
            'OR': 'OR',
        }

        # Devuelve el opcode o None si no existe mapeo.
        return mapping.get(operator_type)

    def _operador_unario_a_cuarteto(self, operator_type):
        """Mapea un operador unario de la gramática a su instrucción de cuarteto."""
        # Tabla de traducción para operadores unarios.
        mapping = {
            'NOT': 'NOT',
            'MINUS': 'UMINUS',
            'PLUS': 'UPLUS',
        }

        # Devuelve el opcode o None si no existe mapeo.
        return mapping.get(operator_type)

    # =========================================================
    # MÉTODOS DE GESTIÓN DE LA TABLA DE SÍMBOLOS
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

    # =========================================================
    # MÉTODOS DE COMPROBACIÓN Y CONVERSIÓN DE TIPOS
    # =========================================================

    def _es_tipo_valido(self, type_name):
        """Comprueba si un tipo existe en tipos básicos o registros."""
        return type_name in self.DEFAULT_TYPES or type_name in self.records

    def _es_tipo_numerico(self, type_name):
        """Comprueba si un tipo es numérico."""
        return type_name in ('char', 'int', 'float')

    def _auto_convert(self, source_type: str, target_type: str):
        """Indica si se permite conversión automática entre dos tipos."""
        if source_type == target_type:
            return True
        if source_type == 'char' and target_type in ('int', 'float'):
            return True
        if source_type == 'int' and target_type == 'float':
            return True
        return False

    def _costo_conversion(self, source_type, target_type):
        """Devuelve el coste de conversión entre tipos compatibles."""
        if source_type == target_type:
            return 0
        if source_type == 'char' and target_type == 'int':
            return 1
        if source_type == 'int' and target_type == 'float':
            return 1
        if source_type == 'char' and target_type == 'float':
            return 2
        return None

    def _tipo_numerico_comun(self, left_type, right_type):
        """Obtiene el tipo numérico común para dos operandos."""
        if 'float' in (left_type, right_type):
            return 'float'
        if 'int' in (left_type, right_type):
            return 'int'
        return 'char'

    def _convertir_numero(self, value, source_type, target_type):
        """Convierte un valor numérico al tipo objetivo."""
        # Si no hay valor, no se convierte nada.
        if value is None:
            return value

        # Si llega un char vacío, se toma como cero.
        if source_type == 'char' and isinstance(value, str) and len(value) == 0:
            if target_type == 'char':
                return 0
            if target_type == 'int':
                return 0
            if target_type == 'float':
                return 0.0
            return 0

        # Si ambos tipos son iguales, solo se normaliza el caso de char.
        if source_type == target_type:
            if source_type == 'char' and target_type == 'char':
                if isinstance(value, str) and len(value) == 1:
                    return ord(value)
                return int(value)
            return value

        # Convierte de char a int.
        if source_type == 'char' and target_type == 'int':
            return ord(value) if isinstance(value, str) and len(value) == 1 else int(value)

        # Convierte de char a float.
        if source_type == 'char' and target_type == 'float':
            if isinstance(value, str) and len(value) == 1:
                return float(ord(value))
            return float(value)

        # Convierte de int a float.
        if source_type == 'int' and target_type == 'float':
            return float(value)

        # Si no hay regla específica, devuelve el valor original.
        return value

    def _normalizar_operandos_numericos(self, left_type, left_value, right_type, right_value):
        """Convierte dos operandos al mismo tipo numérico común."""
        # Calcula el tipo común para ambos operandos.
        common_type = self._tipo_numerico_comun(left_type, right_type)

        # Convierte el operando izquierdo al tipo común.
        left_num = self._convertir_numero(left_value, left_type, common_type)

        # Convierte el operando derecho al tipo común.
        right_num = self._convertir_numero(right_value, right_type, common_type)
        return common_type, left_num, right_num
    
    def _convertir_valor_asignacion(self, value, source_type, target_type):
        """Convierte un valor al tipo destino en una asignación."""
        # Si no hace falta convertir, devuelve el valor tal cual.
        if value is None or source_type == target_type:
            return value

        # Normaliza chars a valor numérico antes de convertir.
        if source_type == 'char' and isinstance(value, str):
            value = ord(value) if len(value) == 1 else 0

        # Convierte hacia float cuando el destino es float.
        if target_type == 'float' and source_type in ('char', 'int'):
            return float(value)

        # Convierte hacia int cuando el destino es int desde char.
        elif target_type == 'int' and source_type == 'char':
            return int(value)

        # Si no aplica ninguna regla, conserva el valor.
        return value

    def _valor_por_defecto(self, type_name: str, visited=None):
        """Genera el valor por defecto de un tipo, incluidos registros."""
        # Devuelve el valor por defecto de tipos básicos.
        if type_name in self.DEFAULT_TYPES:
            return self.DEFAULT_TYPES[type_name]

        # Si el registro no existe, no hay valor por defecto.
        if type_name not in self.records:
            return None

        # Inicializa el conjunto de visitados para cortar ciclos.
        if visited is None:
            visited = set()

        # Evita recursión infinita en registros cíclicos.
        if type_name in visited:
            return None

        # Marca el tipo actual como visitado.
        visited = visited | {type_name}

        # Crea la instancia base del registro.
        record_instance = {'__record_type__': type_name}

        # Genera recursivamente el valor por defecto de cada campo.
        for field_name, field_type in self.records[type_name].items():
            record_instance[field_name] = self._valor_por_defecto(field_type, visited)

        return record_instance

    # =========================================================
    # MÉTODOS DE VALIDACIÓN SEMÁNTICA
    # =========================================================

    def _condicion_es_valida(self, expr, line, contexto):
        """Valida que una condición sea de tipo boolean."""
        # Asume error hasta poder inferir tipo válido.
        expr_type = 'error'

        # Extrae el tipo cuando la expresión viene tipada.
        if isinstance(expr, tuple) and len(expr) >= 2:
            expr_type = expr[0]

        # Acepta condiciones booleanas o desconocidas.
        if expr_type == 'boolean' or expr_type == 'unknown':
            return True

        # Reporta error semántico cuando el tipo no es válido.
        if expr_type != 'error':
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: La condición de '{contexto}' debe ser de tipo 'boolean' y recibió '{expr_type}'")
        return False

    def _registrar_firma_funcion(self, func_name, params, return_type, line='?'):
        """Registra una firma de función evitando duplicados."""
        # Crea la entrada de la función si aún no existe.
        if func_name not in self.functions:
            self.functions[func_name] = []

        # Obtiene la firma solo con tipos de parámetros.
        param_types = [param_type for param_type, _ in params]

        # Verifica si ya existe una firma idéntica.
        for signature in self.functions[func_name]:
            signature_types = [param_type for param_type, _ in signature.get('params', [])]
            if signature_types == param_types:
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: La función '{func_name}' con esa firma ya fue declarada")
                return False

        # Registra la nueva firma válida.
        self.functions[func_name].append({'params': params, 'return_type': return_type})
        return True

    # =========================================================
    # MÉTODOS DE EXPORTACIÓN DE TABLAS (FICHEROS DE SALIDA)
    # =========================================================

    def _formatear_valor(self, value):
        """Formatea un valor para exportarlo a fichero."""
        # Convierte booleanos al formato textual esperado.
        if isinstance(value, bool):
            return 'true' if value else 'false'

        # Formatea registros como pares campo:valor.
        if isinstance(value, dict):
            campos = []
            for key, field_value in value.items():
                # Oculta el metadato interno del tipo de registro.
                if key == '__record_type__':
                    continue
                campos.append(f"{key}:{self._formatear_valor(field_value)}")
            return '{' + ','.join(campos) + '}'

        # Convierte cualquier otro valor a cadena.
        return str(value)

    def exportar_tablas_semanticas(self, input_path):
        """Exporta las tablas semánticas a ficheros de salida."""
        # Calcula el nombre base a partir del fichero de entrada.
        base = os.path.splitext(input_path)[0]

        # Define rutas de salida para cada tabla.
        symbols_path = base + '.symbols'
        records_path = base + '.records'
        functions_path = base + '.functions'

        # En programas con flujo, exporta solo tipos de variables.
        usar_solo_tipos = self._has_flow or bool(self.functions)

        # Escribe la tabla de símbolos.
        with open(symbols_path, 'w', encoding='utf-8') as out_symbols:
            for name, (type_name, value) in self.symbols.items():
                if usar_solo_tipos:
                    out_symbols.write(f"{name}:{type_name}\n")
                else:
                    out_symbols.write(f"{name}:{type_name},{self._formatear_valor(value)}\n")

        # Escribe la tabla de registros.
        with open(records_path, 'w', encoding='utf-8') as out_records:
            for record_name, record_schema in self.records.items():
                campos = ','.join(f"{field_name}:{field_type}" for field_name, field_type in record_schema.items())
                out_records.write(f"{record_name}:[{campos}]\n")

        # Escribe la tabla de funciones.
        with open(functions_path, 'w', encoding='utf-8') as out_functions:
            for function_name, signatures in self.functions.items():
                for signature in signatures:
                    # Formatea los parámetros como nombre:tipo.
                    params = signature.get('params', [])
                    params_txt = ','.join(f"{param_name}:{param_type}" for param_type, param_name in params)
                    return_type = signature.get('return_type', 'void')
                    out_functions.write(f"{function_name}:[{params_txt}],{return_type}\n")

    def exportar_cuartetos(self, input_path):
        """Exporta los cuartetos generados a un fichero .quartets."""
        base = os.path.splitext(input_path)[0]
        quartets_path = base + '.quartets'

        with open(quartets_path, 'w', encoding='utf-8') as out_quartets:
            for operator, arg1, arg2, result in self.quartets:
                out_quartets.write(f"{operator},{arg1},{arg2},{result}\n")

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

    # Inicializa el ámbito y la firma de una función void.
    def p_inicio_funcion_void(self, p):
        '''inicio_funcion_void :'''
        # Obtiene el nombre de función y su lista de parámetros.
        func_name = p[-4]
        params = p[-2] if isinstance(p[-2], list) else []
        line = getattr(p.lexer, 'lineno', '?')

        # Marca que el programa contiene flujo de control o funciones.
        self._has_flow = True

        # Valida que los tipos de parámetros no tengan errores previos.
        if any(param_type == 'error' for param_type, _ in params):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: No se puede declarar la función '{func_name}' con parámetros de tipo inválido")
        else:
            # Registra la firma de la función void.
            self._registrar_firma_funcion(func_name, params, 'void', line)

        # Crea el ámbito local de parámetros de la función.
        func_current = {}
        for param_type, param_name in params:
            if param_name in func_current:
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: Parámetro '{param_name}' repetido en la función '{func_name}'")
            else:
                func_current[param_name] = (param_type, None)

        # Apila el ámbito de función y guarda su contexto activo.
        self.stack.append(func_current)
        self.current_function = {
            'name': func_name,
            'return_type': 'void',
            'has_return': False
        }

    # Cierra el ámbito de una función void.
    def p_fin_funcion_void(self, p):
        '''fin_funcion_void :'''
        # Elimina el ámbito local si existe.
        if len(self.stack) > 1:
            self.stack.pop()

        # Limpia la referencia a la función actual.
        self.current_function = None

    # Reconoce una declaración tipada global o una función con retorno tipado.
    def p_declaracion_o_funcion_tipada(self, p):
        '''declaracion_o_funcion_tipada : tipo ID marcar_declaracion_tipada resto_tipado_programa'''
        type_name, id_name, info = p[1], p[2], p[4]
        line = p.lineno(2)
        current = self.stack[-1]

        # Valida que el tipo declarado exista.
        if not self._es_tipo_valido(type_name):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: El tipo '{type_name}' no existe")
            self._decl_type = None
            self._decl_name = None
            self._decl_line = '?'
            return

        # Maneja el caso de declaración de función tipada.
        if info.get('kind') == 'function':
            # Comprueba que la función tipada tenga al menos un return válido.
            if not info.get('has_return', False):
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: La función '{id_name}' debe retornar un valor de tipo '{type_name}'")
            self._decl_type = None
            self._decl_name = None
            self._decl_line = '?'
            return

        # Maneja el caso de lista de variables tipadas.
        if info.get('kind') == 'decl_list':
            # Declara cada identificador en el ámbito actual.
            for name in [id_name] + info.get('ids', []):
                if name in current:
                    self.has_semantic_error = True
                    print(f"[ERROR SEMANTICO] Linea {line}: Variable '{name}' ya declarada en este ámbito")
                else:
                    default_value = self._valor_por_defecto(type_name)
                    current[name] = (type_name, default_value)

                    # Genera asignación por defecto para tipos básicos.
                    default_ref = self._valor_a_operando(default_value, type_name)
                    if default_ref is not None:
                        self._emit('ASSIGN', default_ref, '_', name)
            self._decl_type = None
            self._decl_name = None
            self._decl_line = '?'
            return

        # Maneja el caso de variable tipada con inicialización.
        if info.get('kind') != 'init':
            # Si no hay inicialización válida, solo limpia el estado temporal.
            self._decl_type = None
            self._decl_name = None
            self._decl_line = '?'
            return

        # Evita redeclarar una variable en el mismo ámbito.
        if id_name in current:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: Variable '{id_name}' ya declarada en este ámbito")
            self._decl_type = None
            self._decl_name = None
            self._decl_line = '?'
            return

        # Obtiene el tipo y valor de la expresión inicial.
        expr_type, expr_val, expr_ref = self._extraer_expr(info.get('expr'))

        # Comprueba compatibilidad de tipos para la asignación.
        if expr_type == 'error':
            can_assign = False
        elif expr_type == 'unknown':
            can_assign = True
        else:
            can_assign = self._auto_convert(expr_type, type_name)

        # Reporta error si la asignación no es compatible.
        if not can_assign:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: No se puede asignar tipo '{expr_type}' a '{id_name}' de tipo '{type_name}'")
            self._decl_type = None
            self._decl_name = None
            self._decl_line = '?'
            return

        # Conversión de valor si los tipos difieren pero son compatibles
        expr_val = self._convertir_valor_asignacion(expr_val, expr_type, type_name)

        # Guarda la variable declarada y limpia el estado temporal.
        current[id_name] = (type_name, expr_val)

        # Emite asignación en cuartetos cuando la expresión es representable.
        if expr_ref is None:
            expr_ref = self._valor_a_operando(expr_val, type_name)

        if expr_ref is not None:
            assign_ref = expr_ref
            if expr_type not in ('error', 'unknown'):
                assign_ref = self._asegurar_tipo_en_cuartetos(expr_ref, expr_type, type_name)
            self._emit('ASSIGN', assign_ref, '_', id_name)

        self._decl_type = None
        self._decl_name = None
        self._decl_line = '?'

    # Guarda el tipo y el nombre de la declaración tipada actual.
    def p_marcar_declaracion_tipada(self, p):
        '''marcar_declaracion_tipada :'''
        # Guarda datos de la declaración para reglas posteriores.
        self._decl_type = p[-2]
        self._decl_name = p[-1]
        self._decl_line = getattr(p.lexer, 'lineno', '?')

    # Desambigua si un elemento tipado es función o declaración de variable global.
    def p_resto_tipado_programa(self, p):
        '''resto_tipado_programa : LPAREN parametros_opt RPAREN inicio_funcion_tipada bloque fin_funcion_tipada
                                | ASSIGN expresion SEMICOLON
                                | resto_lista_ids SEMICOLON'''
        # Clasifica la declaración como función tipada.
        if len(p) == 7 and p.slice[1].type == 'LPAREN':
            p[0] = {'kind': 'function', 'has_return': p[6].get('has_return', False)}

        # Clasifica la declaración como inicialización.
        elif len(p) == 4:
            p[0] = {'kind': 'init', 'expr': p[2]}

        # Clasifica la declaración como lista de identificadores.
        else:
            p[0] = {'kind': 'decl_list', 'ids': p[1]}

    # Inicializa el ámbito y la firma de una función tipada.
    def p_inicio_funcion_tipada(self, p):
        '''inicio_funcion_tipada :'''
        # Obtiene tipo de retorno, nombre y parámetros de la función.
        return_type = self._decl_type
        func_name = self._decl_name
        params = p[-2] if isinstance(p[-2], list) else []
        line = self._decl_line

        # Marca que el programa contiene flujo de control o funciones.
        self._has_flow = True

        # Valida que los tipos de parámetros no tengan errores previos.
        if any(param_type == 'error' for param_type, _ in params):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: No se puede declarar la función '{func_name}' con parámetros de tipo inválido")
        else:
            # Registra la firma de la función tipada.
            self._registrar_firma_funcion(func_name, params, return_type, line)

        # Crea el ámbito local de parámetros de la función.
        func_current = {}
        for param_type, param_name in params:
            if param_name in func_current:
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: Parámetro '{param_name}' repetido en la función '{func_name}'")
            else:
                func_current[param_name] = (param_type, None)

        # Apila el ámbito de función y guarda su contexto activo.
        self.stack.append(func_current)
        self.current_function = {
            'name': func_name,
            'return_type': return_type,
            'has_return': False
        }

    # Cierra el ámbito de una función tipada y marca si tuvo return.
    def p_fin_funcion_tipada(self, p):
        '''fin_funcion_tipada :'''
        # Recupera si la función tuvo algún return.
        has_return = False
        if isinstance(self.current_function, dict):
            has_return = self.current_function.get('has_return', False)

        # Elimina el ámbito local si existe.
        if len(self.stack) > 1:
            self.stack.pop()

        # Limpia la referencia a la función actual.
        self.current_function = None

        # Devuelve información de retorno para reglas superiores.
        p[0] = {'has_return': has_return}

    # Reconoce la continuación de una lista de identificadores separada por comas.
    def p_resto_listas_ids(self, p):
        '''resto_lista_ids : lambda
                         | resto_lista_ids COMMA ID'''
        # Si la producción es vacía, no añade identificadores.
        if len(p) == 2:
            p[0] = []

        # Si hay coma e identificador, acumula en la lista.
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

    # Sentencia if dentro de una función void
    def p_sentencia_if_void(self, p):
        '''sentencia_if_void : IF LPAREN expresion RPAREN if_mark bloque_void else_void_opt if_end_mark'''
        # Marca que el programa tiene estructuras de control
        self._has_flow = True
        # Verifica que la condición del if sea de tipo boolean
        self._condicion_es_valida(p[3], p.lineno(1), 'if')

    # Reconoce la cláusula else opcional dentro de una función void.
    def p_else_void_opt(self, p):
        '''else_void_opt : lambda
                        | else_mark ELSE bloque_void'''
        pass

    # Sentencia while dentro de una función void
    def p_sentencia_while_void(self, p):
        '''sentencia_while_void : WHILE while_start LPAREN expresion RPAREN while_cond_mark entrar_bucle bloque_void salir_bucle while_end'''
        # Marca que el programa tiene estructuras de control
        self._has_flow = True
        # Verifica que la condición del while sea de tipo boolean
        self._condicion_es_valida(p[4], p.lineno(1), 'while')

    # Sentencia do-while dentro de una función void
    def p_sentencia_do_while_void(self, p):
        '''sentencia_do_while_void : DO do_start entrar_bucle bloque_void salir_bucle WHILE LPAREN expresion RPAREN SEMICOLON do_end'''
        # Marca que el programa tiene estructuras de control
        self._has_flow = True
        # Verifica que la condición del do-while sea de tipo boolean
        self._condicion_es_valida(p[8], p.lineno(6), 'do-while')

    # Sentencias simples válidas dentro de una función void
    def p_sentencia_simple_void(self, p):
        '''sentencia_simple_void : asignacion
                                | print_stmt
                                | BREAK
                                | expresion'''
        # Comprueba que break no aparezca fuera de un bucle
        if len(p) == 2 and p.slice[1].type == 'BREAK' and self.loop_depth <= 0:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {p.lineno(1)}: 'break' fuera de un bucle")
            return

        # Si el break es válido, genera salto a la etiqueta de fin de bucle.
        if len(p) == 2 and p.slice[1].type == 'BREAK' and self._loop_codegen_stack:
            end_label = self._loop_codegen_stack[-1].get('end')
            self._emit('JUMP', end_label, '_', '_')

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

    # Sentencia if general del lenguaje.
    def p_sentencia_if(self, p):
        '''sentencia_if : IF LPAREN expresion RPAREN if_mark bloque else_opt if_end_mark'''
        # Marca que el programa tiene estructuras de control
        self._has_flow = True
        # Verifica que la condición del if sea de tipo boolean
        self._condicion_es_valida(p[3], p.lineno(1), 'if')

    # Sentencia else opcional en un if general.
    def p_else_opt(self, p):
        '''else_opt : lambda
                   | else_mark ELSE bloque'''
        pass

    # Sentencia while general del lenguaje.
    def p_sentencia_while(self, p):
        '''sentencia_while : WHILE while_start LPAREN expresion RPAREN while_cond_mark entrar_bucle bloque salir_bucle while_end'''
        # Marca que el programa tiene estructuras de control
        self._has_flow = True
        # Verifica que la condición del while sea de tipo boolean
        self._condicion_es_valida(p[4], p.lineno(1), 'while')

    # Sentencia do-while general del lenguaje.
    def p_sentencia_do_while(self, p):
        '''sentencia_do_while : DO do_start entrar_bucle bloque salir_bucle WHILE LPAREN expresion RPAREN SEMICOLON do_end'''
        # Marca que el programa tiene estructuras de control
        self._has_flow = True
        # Verifica que la condición del do-while sea de tipo boolean
        self._condicion_es_valida(p[8], p.lineno(6), 'do-while')

    # Marca el inicio de un if y emite salto condicional al bloque else.
    def p_if_mark(self, p):
        '''if_mark :'''
        _, _, cond_ref = self._extraer_expr(p[-2])

        else_label = self._nueva_etiqueta()
        end_label = self._nueva_etiqueta()
        self._if_codegen_stack.append(
            {
                'else_label': else_label,
                'end_label': end_label,
                'has_else': False,
            }
        )

        if cond_ref is not None:
            self._emit('JUMPF', cond_ref, else_label, '_')

    # Marca el inicio del bloque else y cierra el bloque then.
    def p_else_mark(self, p):
        '''else_mark :'''
        if not self._if_codegen_stack:
            return

        ctx = self._if_codegen_stack[-1]
        self._emit('JUMP', ctx['end_label'], '_', '_')
        self._emit('LABEL', ctx['else_label'], '_', '_')
        ctx['has_else'] = True

    # Marca el final de una sentencia if con o sin else.
    def p_if_end_mark(self, p):
        '''if_end_mark :'''
        if not self._if_codegen_stack:
            return

        ctx = self._if_codegen_stack.pop()
        if ctx['has_else']:
            self._emit('LABEL', ctx['end_label'], '_', '_')
        else:
            self._emit('LABEL', ctx['else_label'], '_', '_')

    # Marca inicio de bucle while y emite etiqueta de entrada.
    def p_while_start(self, p):
        '''while_start :'''
        start_label = self._nueva_etiqueta()
        end_label = self._nueva_etiqueta()
        self._loop_codegen_stack.append({'start': start_label, 'end': end_label, 'kind': 'while'})
        self._emit('LABEL', start_label, '_', '_')

    # Evalúa condición de while y emite salto al final del bucle.
    def p_while_cond_mark(self, p):
        '''while_cond_mark :'''
        _, _, cond_ref = self._extraer_expr(p[-2])

        if not self._loop_codegen_stack:
            return

        end_label = self._loop_codegen_stack[-1].get('end')
        if cond_ref is not None:
            self._emit('JUMPF', cond_ref, end_label, '_')

    # Cierra bucle while con salto al inicio y etiqueta de salida.
    def p_while_end(self, p):
        '''while_end :'''
        if not self._loop_codegen_stack:
            return

        ctx = self._loop_codegen_stack.pop()
        self._emit('JUMP', ctx.get('start'), '_', '_')
        self._emit('LABEL', ctx.get('end'), '_', '_')

    # Marca inicio de bucle do-while y emite etiqueta del cuerpo.
    def p_do_start(self, p):
        '''do_start :'''
        start_label = self._nueva_etiqueta()
        end_label = self._nueva_etiqueta()
        self._loop_codegen_stack.append({'start': start_label, 'end': end_label, 'kind': 'do'})
        self._emit('LABEL', start_label, '_', '_')

    # Cierra bucle do-while con salto condicional y etiqueta final.
    def p_do_end(self, p):
        '''do_end :'''
        _, _, cond_ref = self._extraer_expr(p[-3])

        if not self._loop_codegen_stack:
            return

        ctx = self._loop_codegen_stack.pop()
        if cond_ref is not None:
            self._emit('JUMPT', cond_ref, ctx.get('start'), '_')
        self._emit('LABEL', ctx.get('end'), '_', '_')

    # Marcador que se ejecuta al entrar en un bucle para controlar el alcance de break.
    def p_entrar_bucle(self, p):
        '''entrar_bucle :'''
        # Incrementa el contador de bucles anidados
        self.loop_depth += 1

    # Marcador que se ejecuta al salir de un bucle para controlar el alcance de break.
    def p_salir_bucle(self, p):
        '''salir_bucle :'''
        # Decrementa el contador sin bajar de 0
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
        # Si es un break, valida que esté dentro de un bucle.
        if len(p) == 2 and p.slice[1].type == 'BREAK':
            # Reporta error cuando break aparece fuera de bucle.
            if self.loop_depth <= 0:
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {p.lineno(1)}: 'break' fuera de un bucle")
            elif self._loop_codegen_stack:
                # Salta al final del bucle más interno.
                end_label = self._loop_codegen_stack[-1].get('end')
                self._emit('JUMP', end_label, '_', '_')
            return

        # Si no es un return, no hay validaciones adicionales.
        if len(p) != 3 or p.slice[1].type != 'RETURN':
            return

        # Toma la línea del return para los mensajes de error.
        line = p.lineno(1)

        # Verifica que el return esté dentro de una función.
        if self.current_function is None:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: 'return' fuera de una función")
            return

        # Marca que existe al menos un return en la función (aunque su tipo falle).
        self.current_function['has_return'] = True

        # Obtiene el tipo de retorno esperado de la función activa.
        expected_type = self.current_function.get('return_type', 'void')

        # Recupera el tipo de la expresión retornada.
        expr_type, _ = ('error', None)
        if isinstance(p[2], tuple) and len(p[2]) >= 2:
            expr_type = p[2][0]

        # Decide si el tipo retornado es compatible con la función.
        if expr_type == 'error':
            can_return = False
        elif expr_type == 'unknown':
            can_return = True
        else:
            can_return = self._auto_convert(expr_type, expected_type)

        # Reporta error si el tipo de return no es válido.
        if not can_return:
            self.has_semantic_error = True
            func_name = self.current_function.get('name', '?')
            print(f"[ERROR SEMANTICO] Linea {line}: Return de tipo '{expr_type}' no compatible con función '{func_name}' de tipo '{expected_type}'")
            return

    # Reconoce declaraciones de variables simples o con inicialización.
    def p_declaracion_variable(self, p):
        '''declaracion_variable : tipo lista_ids
                               | tipo ID ASSIGN expresion'''
        # Obtiene tipo declarado, línea y ámbito actual.
        type_name = p[1]
        line = p.lineno(2)
        current = self.stack[-1]

        # Valida que el tipo declarado exista.
        if not self._es_tipo_valido(type_name):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: El tipo '{type_name}' no existe")
            return

        # Maneja una declaración múltiple como int a, b, c.
        if len(p) == 3:
            # Recorre todos los identificadores para declararlos.
            for name in p[2]:
                # Evita declarar dos veces en el mismo ámbito.
                if name in current:
                    self.has_semantic_error = True
                    print(f"[ERROR SEMANTICO] Linea {line}: Variable '{name}' ya declarada en este ámbito")
                else:
                    # Guarda la variable con su valor por defecto.
                    default_value = self._valor_por_defecto(type_name)
                    current[name] = (type_name, default_value)

                    # Genera asignación por defecto para tipos básicos.
                    default_ref = self._valor_a_operando(default_value, type_name)
                    if default_ref is not None:
                        self._emit('ASSIGN', default_ref, '_', name)
            return

        # Maneja una declaración con inicialización como int a = expr.
        id_name = p[2]

        # Extrae tipo y valor de la expresión inicial.
        expr_type, expr_val, expr_ref = self._extraer_expr(p[4])

        # Evita redeclarar la variable en el mismo ámbito.
        if id_name in current:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: Variable '{id_name}' ya declarada en este ámbito")
            return

        # Comprueba compatibilidad de tipos para la asignación inicial.
        if expr_type == 'error':
            can_assign = False
        elif expr_type == 'unknown':
            can_assign = True
        else:
            can_assign = self._auto_convert(expr_type, type_name)

        # Reporta error cuando los tipos no son compatibles.
        if not can_assign:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: No se puede asignar tipo '{expr_type}' a '{id_name}' de tipo '{type_name}'")
            return

        # Convierte el valor antes de guardarlo si hace falta.
        expr_val = self._convertir_valor_asignacion(expr_val, expr_type, type_name)

        # Guarda la variable con su tipo y valor final.
        current[id_name] = (type_name, expr_val)

        # Emite asignación en cuartetos cuando la expresión es representable.
        if expr_ref is None:
            expr_ref = self._valor_a_operando(expr_val, type_name)

        if expr_ref is not None:
            assign_ref = expr_ref
            if expr_type not in ('error', 'unknown'):
                assign_ref = self._asegurar_tipo_en_cuartetos(expr_ref, expr_type, type_name)
            self._emit('ASSIGN', assign_ref, '_', id_name)

    # Reconoce una lista de identificadores separada por comas.
    def p_lista_ids(self, p):
        '''lista_ids : ID
                    | lista_ids COMMA ID'''
        # Caso base con un solo identificador.
        if len(p) == 2:
            p[0] = [p[1]]

        # Caso recursivo que acumula identificadores.
        else:
            p[0] = p[1] + [p[3]]

    # Reconoce una asignación a una variable o acceso por punto.
    def p_asignacion(self, p):
        '''asignacion : acceso ASSIGN expresion'''
        # Toma acceso izquierdo y línea de asignación.
        left = p[1]
        line = p.lineno(2)

        # Valida que el acceso izquierdo tenga estructura válida.
        if not isinstance(left, dict):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: Lado izquierdo de asignación inválido")
            return

        # Valida que el acceso sea variable o campo.
        left_kind = left.get('kind')
        if left_kind not in ('var', 'field'):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: Lado izquierdo de asignación inválido")
            return

        # Obtiene nombre y tipo del lado izquierdo.
        id_name = left.get('name', '?')
        type_name = left.get('type', 'error')

        # Extrae tipo y valor de la expresión derecha.
        expr_type, expr_val, expr_ref = self._extraer_expr(p[3])

        # Comprueba compatibilidad de tipos para la asignación.
        if 'error' in (type_name, expr_type):
            can_assign = False
        elif 'unknown' in (type_name, expr_type):
            can_assign = True
        else:
            can_assign = self._auto_convert(expr_type, type_name)

        # Reporta error si no se puede asignar.
        if not can_assign:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: No se puede asignar tipo '{expr_type}' a '{id_name}' de tipo '{type_name}'")
            return

        # Convierte el valor cuando los tipos son compatibles pero distintos.
        expr_val = self._convertir_valor_asignacion(expr_val, expr_type, type_name)

        # Si el destino es una variable simple, actualiza y termina.
        if left_kind == 'var':
            self._actualizar_simbolo(id_name, expr_val)

            # Emite asignación para variables simples.
            if expr_ref is None:
                expr_ref = self._valor_a_operando(expr_val, type_name)

            if expr_ref is not None:
                assign_ref = expr_ref
                if expr_type not in ('error', 'unknown'):
                    assign_ref = self._asegurar_tipo_en_cuartetos(expr_ref, expr_type, type_name)
                self._emit('ASSIGN', assign_ref, '_', id_name)
            return

        # Si el destino es un campo, prepara la ruta de acceso.
        root_name = left.get('root')
        path = left.get('path', [])
        if not root_name or not path:
            return

        # Busca el símbolo raíz que contiene el registro.
        root_symbol = self._buscar_simbolo(root_name)
        if root_symbol is None:
            return

        # Obtiene el valor actual del símbolo raíz.
        _, root_value = root_symbol
        if root_value is None:
            return

        # Verifica que el valor raíz sea un registro accesible.
        if not isinstance(root_value, dict):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: No se puede acceder a campos sobre '{root_name}'")
            return

        # Recorre la ruta hasta el diccionario objetivo.
        target = root_value
        for field in path[:-1]:
            if not isinstance(target, dict):
                target = None
                break
            target = target.get(field)

        # Asigna el nuevo valor al campo final y actualiza el símbolo raíz.
        if isinstance(target, dict):
            target[path[-1]] = expr_val
            self._actualizar_simbolo(root_name, root_value)

    # Reconoce una llamada a la función del sistema print.
    def p_print_stmt(self, p):
        '''print_stmt : PRINT LPAREN argumentos_opt RPAREN'''
        # Obtiene argumentos y línea de la llamada a print.
        args = p[3] if isinstance(p[3], list) else []
        line = p.lineno(1)

        # Verifica que print reciba al menos un argumento.
        if len(args) == 0:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: 'print' requiere al menos un argumento")
            return

        # Revisa cada argumento para asegurar formato y tipo válidos.
        for arg in args:
            if not (isinstance(arg, tuple) and len(arg) >= 2):
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: Argumento inválido en 'print'")
                return

            # Rechaza argumentos que ya vengan marcados con error.
            arg_type, arg_value, arg_ref = self._extraer_expr(arg)
            if arg_type == 'error':
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: Argumento inválido en 'print'")
                return

            # Emite llamada print para argumentos representables.
            if arg_ref is None:
                arg_ref = self._valor_a_operando(arg_value, arg_type)
            if arg_ref is not None:
                self._emit('PRINT', arg_ref, '_', '_')

    # =======================================
    # REGISTROS Y FUNCIONES
    # =======================================

    # Reconoce una declaración global de registro.
    def p_declaracion_record(self, p):
        '''declaracion_record : RECORD ID LPAREN campos_record_opt RPAREN'''
        # Obtiene nombre del registro, campos y línea.
        record_name = p[2]
        raw_fields = p[4] if isinstance(p[4], list) else []
        line = p.lineno(2)

        # Evita redeclarar un registro con el mismo nombre.
        if record_name in self.records:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: El registro '{record_name}' ya fue declarado")
            return

        # Resuelve tipos heredados para campos sin tipo explícito.
        resolved_fields = []
        current_type = None

        # Recorre los campos crudos para completar tipos faltantes.
        for field_type, field_name in raw_fields:
            # Actualiza el tipo actual cuando viene explícito.
            if field_type is not None:
                current_type = field_type

            # Si no hay tipo acumulado, el campo es inválido.
            if current_type is None:
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: El campo '{field_name}' no tiene tipo definido")
                continue

            # Guarda el campo con su tipo ya resuelto.
            resolved_fields.append((current_type, field_name))

        # Prepara el esquema final del registro.
        record_schema = {}
        has_local_error = False

        # Valida duplicados y tipos de cada campo.
        for field_type, field_name in resolved_fields:
            # Detecta nombres de campo repetidos.
            if field_name in record_schema:
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: El campo '{field_name}' está repetido en el registro '{record_name}'")
                has_local_error = True
                continue

            # Verifica que el tipo del campo exista.
            if not self._es_tipo_valido(field_type):
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: El tipo '{field_type}' no existe para el campo '{field_name}'")
                has_local_error = True
                continue

            # Agrega el campo válido al esquema del registro.
            record_schema[field_name] = field_type

        # Guarda el registro solo si no hubo errores locales.
        if not has_local_error:
            self.records[record_name] = record_schema

    # Permite que la lista de campos de un registro sea vacía u opcional.
    def p_campos_record_opt(self, p):
        '''campos_record_opt : lambda
                            | campos_record'''
        # Si la producción es vacía, devuelve lista vacía.
        if len(p) == 2 and p.slice[1].type == 'lambda':
            p[0] = []

        # Si hay campos, propaga la lista construida.
        else:
            p[0] = p[1]

    # Construye la lista de campos de un registro.
    def p_campos_record(self, p):
        '''campos_record : campos_record COMMA campo_record_item
                     | campo_record_item'''
        # Caso base con un único campo.
        if len(p) == 2:
            p[0] = [p[1]]

        # Caso recursivo que acumula campos.
        else:
            p[0] = p[1] + [p[3]]

    # Reconoce un campo con tipo explícito en un registro.
    def p_campo_record_item_typed(self, p):
        '''campo_record_item : tipo ID'''
        # Devuelve el par tipo y nombre del campo.
        p[0] = (p[1], p[2])

    # Reconoce un campo sin tipo explícito en un registro.
    def p_campo_record_item_bare(self, p):
        '''campo_record_item : ID'''
        # Marca el tipo como pendiente para herencia posterior.
        p[0] = (None, p[1])

    # Permite que la lista de parámetros de una función sea vacía u opcional.
    def p_parametros_opt(self, p):
        '''parametros_opt : lambda
                         | parametros'''
        # Si la producción es vacía, no hay parámetros.
        if len(p) == 2 and p.slice[1].type == 'lambda':
            p[0] = []

        # Si hay parámetros, propaga la lista construida.
        else:
            p[0] = p[1]

    # Construye la lista de parámetros tipados de una función.
    def p_parametros(self, p):
        '''parametros : parametros COMMA parametro
                     | parametro'''
        # Caso base con un único parámetro.
        if len(p) == 2:
            p[0] = [p[1]]

        # Caso recursivo que acumula parámetros.
        else:
            p[0] = p[1] + [p[3]]

    # Reconoce un parámetro individual de una función.
    def p_parametro(self, p):
        '''parametro : tipo ID'''
        # Obtiene tipo, nombre y línea del parámetro.
        type_name, id_name = p[1], p[2]
        line = p.lineno(2)

        # Valida que el tipo del parámetro exista.
        if not self._es_tipo_valido(type_name):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: El tipo '{type_name}' no existe para el parámetro '{id_name}'")

            # Devuelve parámetro con error para continuar el análisis.
            p[0] = ('error', id_name)
            return

        # Devuelve el parámetro válido como par tipo y nombre.
        p[0] = (type_name, id_name)

    # Reconoce un tipo básico o el nombre de un registro definido por el usuario.
    def p_tipo(self, p):
        '''tipo : INT
                | FLOAT
                | CHAR
                | BOOLEAN
                | ID'''
        # Propaga el nombre del tipo reconocido por la gramática.
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
        # Obtiene tipo, valor y referencia de ambos operandos.
        left_type, left_value, left_ref = self._extraer_expr(p[1])
        right_type, right_value, right_ref = self._extraer_expr(p[3])

        # Obtiene operador y línea para mensajes de error.
        operator_type = p.slice[2].type
        line = getattr(p.slice[2], 'lineno', '?')

        # Mapea el operador al nombre de instrucción de cuarteto.
        op_quartet = self._operador_binario_a_cuarteto(operator_type)

        # Si hay error previo en algún operando, corta la evaluación.
        if 'error' in (left_type, right_type):
            p[0] = self._expr('error', None)
            return

        # Permite valores desconocidos para no bloquear análisis semántico.
        if 'unknown' in (left_type, right_type):
            p[0] = self._expr('unknown', None)
            return

        # Maneja operadores aritméticos.
        if operator_type in ('PLUS', 'MINUS', 'TIMES', 'DIVIDE'):
            # Valida que ambos operandos sean numéricos.
            if not (self._es_tipo_numerico(left_type) and self._es_tipo_numerico(right_type)):
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: Operación aritmética inválida entre '{left_type}' y '{right_type}'")
                p[0] = self._expr('error', None)
                return

            # Calcula el tipo común del resultado.
            result_type = self._tipo_numerico_comun(left_type, right_type)
            if operator_type in ('TIMES', 'DIVIDE') and result_type == 'char':
                result_type = 'int'

            # Evalúa valor en tiempo de análisis si hay literales concretos.
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

            # Emite cuarteto aritmético cuando ambos operandos son representables.
            result_ref = None
            if op_quartet and left_ref is not None and right_ref is not None:
                left_emit = self._asegurar_tipo_en_cuartetos(left_ref, left_type, result_type)
                right_emit = self._asegurar_tipo_en_cuartetos(right_ref, right_type, result_type)
                result_ref = self._nuevo_temporal()
                self._emit(op_quartet, left_emit, right_emit, result_ref)

            p[0] = self._expr(result_type, result_value, result_ref)
            return

        # Maneja operadores comparativos numéricos.
        if operator_type in ('GREATER', 'GREATER_EQUAL', 'LESS', 'LESS_EQUAL'):
            # Valida que ambos operandos sean numéricos.
            if not (self._es_tipo_numerico(left_type) and self._es_tipo_numerico(right_type)):
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: Operación comparativa inválida entre '{left_type}' y '{right_type}'")
                p[0] = self._expr('error', None)
                return

            # Evalúa valor en tiempo de análisis si hay literales concretos.
            result_value = None
            common_type = self._tipo_numerico_comun(left_type, right_type)
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

            # Emite cuarteto comparativo cuando ambos operandos son representables.
            result_ref = None
            if op_quartet and left_ref is not None and right_ref is not None:
                left_emit = self._asegurar_tipo_en_cuartetos(left_ref, left_type, common_type)
                right_emit = self._asegurar_tipo_en_cuartetos(right_ref, right_type, common_type)
                result_ref = self._nuevo_temporal()
                self._emit(op_quartet, left_emit, right_emit, result_ref)

            p[0] = self._expr('boolean', result_value, result_ref)
            return

        # Maneja comparación de igualdad.
        if operator_type == 'EQUAL':
            # Verifica compatibilidad de tipos para comparar.
            comparable = (
                left_type == right_type
                or self._auto_convert(left_type, right_type)
                or self._auto_convert(right_type, left_type)
            )
            if not comparable:
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: No se pueden comparar tipos '{left_type}' y '{right_type}' con '=='")
                p[0] = self._expr('error', None)
                return

            # Evalúa valor en tiempo de análisis si hay literales concretos.
            result_value = None
            if left_value is not None and right_value is not None:
                if self._es_tipo_numerico(left_type) and self._es_tipo_numerico(right_type):
                    _, l_val, r_val = self._normalizar_operandos_numericos(
                        left_type, left_value, right_type, right_value
                    )
                    result_value = (l_val == r_val)
                else:
                    result_value = (left_value == right_value)

            # Emite cuarteto de igualdad cuando ambos operandos son representables.
            result_ref = None
            if op_quartet and left_ref is not None and right_ref is not None:
                left_emit, right_emit = left_ref, right_ref
                if self._es_tipo_numerico(left_type) and self._es_tipo_numerico(right_type):
                    common_type = self._tipo_numerico_comun(left_type, right_type)
                    left_emit = self._asegurar_tipo_en_cuartetos(left_ref, left_type, common_type)
                    right_emit = self._asegurar_tipo_en_cuartetos(right_ref, right_type, common_type)
                result_ref = self._nuevo_temporal()
                self._emit(op_quartet, left_emit, right_emit, result_ref)

            p[0] = self._expr('boolean', result_value, result_ref)
            return

        # Maneja operadores lógicos booleanos.
        if operator_type in ('AND', 'OR'):
            # Valida que ambos operandos sean booleanos.
            if left_type != 'boolean' or right_type != 'boolean':
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: Operación lógica inválida entre '{left_type}' y '{right_type}'")
                p[0] = self._expr('error', None)
                return

            # Evalúa valor en tiempo de análisis si hay literales concretos.
            result_value = None
            if left_value is not None and right_value is not None:
                if operator_type == 'AND':
                    result_value = left_value and right_value
                else:
                    result_value = left_value or right_value

            # Emite cuarteto lógico cuando ambos operandos son representables.
            result_ref = None
            if op_quartet and left_ref is not None and right_ref is not None:
                result_ref = self._nuevo_temporal()
                self._emit(op_quartet, left_ref, right_ref, result_ref)

            p[0] = self._expr('boolean', result_value, result_ref)
            return

        # Si el operador no entra en ningún caso, marca error.
        p[0] = self._expr('error', None)
    
    # Operadores unarios del lenguaje (NOT, +, -).
    def p_expresion_unaria(self, p):
        '''expresion : NOT expresion
                    | MINUS expresion %prec UMINUS
                    | PLUS expresion %prec UPLUS'''
        # Extrae tipo, valor y referencia del operando.
        expr_type, expr_value, expr_ref = self._extraer_expr(p[2])

        # Obtiene operador y línea para mensajes de error.
        operator_type = p.slice[1].type
        line = getattr(p.slice[1], 'lineno', '?')
        op_quartet = self._operador_unario_a_cuarteto(operator_type)

        # Propaga errores o valores aún desconocidos.
        if expr_type in ('error', 'unknown'):
            p[0] = self._expr(expr_type, None)
            return

        # Maneja el operador lógico NOT.
        if operator_type == 'NOT':
            # Verifica que el operando sea booleano.
            if expr_type != 'boolean':
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: El operador '!' requiere boolean y recibió '{expr_type}'")
                p[0] = self._expr('error', None)
                return

            # Calcula valor en tiempo de análisis.
            result_value = None if expr_value is None else (not expr_value)

            # Emite cuarteto unario si hay referencia.
            result_ref = None
            if op_quartet and expr_ref is not None:
                result_ref = self._nuevo_temporal()
                self._emit(op_quartet, expr_ref, '_', result_ref)

            p[0] = self._expr('boolean', result_value, result_ref)
            return

        # Para + y -, valida que el tipo sea numérico.
        if not self._es_tipo_numerico(expr_type):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: El operador unario requiere tipo numérico y recibió '{expr_type}'")
            p[0] = self._expr('error', None)
            return

        # Calcula valor en tiempo de análisis.
        if expr_value is None or operator_type == 'PLUS':
            result_value = expr_value
        elif expr_type == 'char' and isinstance(expr_value, str) and len(expr_value) == 1:
            result_value = chr((-ord(expr_value)) % 256)
        else:
            result_value = -expr_value

        # Emite cuarteto unario si hay referencia.
        result_ref = None
        if op_quartet and expr_ref is not None:
            emit_ref = expr_ref

            # Normaliza char a int para operaciones unarias numéricas en cuartetos.
            if expr_type == 'char' and operator_type in ('PLUS', 'MINUS'):
                emit_ref = self._asegurar_tipo_en_cuartetos(expr_ref, 'char', 'int')

            result_ref = self._nuevo_temporal()
            self._emit(op_quartet, emit_ref, '_', result_ref)

        p[0] = self._expr(expr_type, result_value, result_ref)
    

    # Reduce una expresión al nivel de primario.
    def p_expresion_primaria(self, p):
        '''expresion : primario'''
        # Propaga el resultado del primario como expresión.
        p[0] = p[1]

    # Reconoce expresiones primarias del lenguaje.
    def p_primario(self, p):
        '''primario : literal
                   | acceso
                   | llamada
                   | LPAREN expresion RPAREN
                   | instanciacion'''
        # Caso sin paréntesis: literal, acceso, llamada o instanciación.
        if len(p) == 2:
            node = p[1]

            # Si ya viene tipado, lo conserva tal cual.
            if isinstance(node, tuple) and len(node) >= 2:
                node_type, node_value, node_ref = self._extraer_expr(node)
                p[0] = self._expr(node_type, node_value, node_ref)

            # Si viene como nodo de acceso, extrae tipo y valor.
            elif isinstance(node, dict):
                node_type = node.get('type', 'unknown')
                node_value = node.get('value')

                # Solo se genera referencia para accesos simples a variable.
                if node.get('kind') == 'var':
                    node_ref = node.get('name')
                else:
                    node_ref = None

                p[0] = self._expr(node_type, node_value, node_ref)
            else:
                # Si no se reconoce el formato, marca tipo desconocido.
                p[0] = self._expr('unknown', None)
        else:
            # Caso con paréntesis: propaga la expresión interna.
            p[0] = p[2]

    # Reconoce accesos a variables o a campos encadenados con punto.
    def p_acceso(self, p):
        '''acceso : ID
                  | acceso DOT ID'''
        # Caso base de acceso simple a variable.
        if len(p) == 2:
            var_name = p[1]

            # Busca la variable en la pila de ámbitos.
            symbol = self._buscar_simbolo(var_name)

            # Reporta error si la variable no existe.
            if symbol is None:
                self.has_semantic_error = True
                line = getattr(p.slice[1], 'lineno', '?')
                print(f"[ERROR SEMANTICO] Linea {line}: La variable '{var_name}' no ha sido declarada")
                p[0] = {'kind': 'invalid', 'name': var_name, 'type': 'error', 'value': None}
                return

            # Construye descriptor de acceso válido a variable.
            p[0] = {
                'kind': 'var',
                'name': var_name,
                'type': symbol[0],
                'value': symbol[1],
                'root': var_name,
                'path': []
            }
            return

        # Caso encadenado de acceso por punto.
        left_access = p[1]
        field_name = p[3]
        line = getattr(p.slice[3], 'lineno', '?')

        # Verifica que el acceso izquierdo tenga estructura válida.
        if not isinstance(left_access, dict):
            p[0] = {'kind': 'invalid', 'name': field_name, 'type': 'error', 'value': None}
            return

        # Verifica que el tipo izquierdo sea un registro conocido.
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

        # Verifica que el campo exista dentro del registro.
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

        # Obtiene tipo del campo y su valor actual si existe.
        field_type = self.records[left_type][field_name]
        field_value = None
        left_value = left_access.get('value')
        if isinstance(left_value, dict):
            field_value = left_value.get(field_name)

        # Construye la ruta acumulada del acceso encadenado.
        root_name = left_access.get('root', left_access.get('name', '?'))
        base_path = left_access.get('path', [])
        new_path = base_path + [field_name]

        # Devuelve descriptor de acceso válido a campo.
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
        # Obtiene nombre de función, argumentos y línea.
        func_name = p[1]
        args = p[3] if isinstance(p[3], list) else []
        line = p.lineno(1)

        # Impide recursión directa dentro del mismo cuerpo.
        if self.current_function is not None and func_name == self.current_function.get('name'):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: No se permite invocar '{func_name}' dentro de su propio cuerpo")
            p[0] = self._expr('error', None)
            return

        # Verifica que la función exista.
        if func_name not in self.functions:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: La función '{func_name}' no existe")
            p[0] = self._expr('error', None)
            return

        # Extrae tipos de los argumentos recibidos.
        arg_types = []
        for arg in args:
            if isinstance(arg, tuple) and len(arg) >= 2:
                arg_types.append(arg[0])
            else:
                arg_types.append('error')

        # Si algún argumento ya viene con error, corta la llamada.
        if 'error' in arg_types:
            p[0] = self._expr('error', None)
            return

        # Busca sobrecargas compatibles y su coste de conversión.
        candidates = []
        for signature in self.functions[func_name]:
            params = signature.get('params', [])
            if len(params) != len(arg_types):
                continue

            conversions = 0
            compatible = True
            for arg_type, (param_type, _) in zip(arg_types, params):
                # Sin conversión cuando tipos son iguales.
                if arg_type == param_type:
                    continue

                # Penaliza tipos desconocidos para romper empates.
                if arg_type == 'unknown':
                    conversions += 3
                    continue

                # Aplica coste de conversión si existe.
                conversion_cost = self._costo_conversion(arg_type, param_type)
                if conversion_cost is not None:
                    conversions += conversion_cost
                else:
                    # Marca firma incompatible si no hay conversión válida.
                    compatible = False
                    break

            # Guarda firmas compatibles con su coste total.
            if compatible:
                candidates.append((conversions, signature))

        # Si no hay candidatos compatibles, reporta error.
        if not candidates:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: No existe una sobrecarga compatible para '{func_name}'")
            p[0] = self._expr('error', None)
            return

        # Prioriza coincidencias exactas sin conversión.
        exact = [signature for conversions, signature in candidates if conversions == 0]
        if len(exact) == 1:
            selected = exact[0]
            return_type = selected.get('return_type', 'unknown')
            result_ref = None
            if return_type != 'void':
                result_ref = self._nuevo_temporal()
            self._emit('CALL', func_name, len(args), result_ref)
            p[0] = self._expr(return_type, None, result_ref)
            return

        # Si hay más de una coincidencia exacta, la llamada es ambigua.
        if len(exact) > 1:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: Llamada ambigua a '{func_name}'")
            p[0] = self._expr('error', None)
            return

        # Si no hay exacta, elige la de menor coste de conversión.
        min_conversions = min(conversions for conversions, _ in candidates)
        best = [signature for conversions, signature in candidates if conversions == min_conversions]

        # Si hay empate en mejor coste, también es ambigua.
        if len(best) != 1:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: Llamada ambigua a '{func_name}'")
            p[0] = self._expr('error', None)
            return

        # Devuelve el tipo de retorno de la sobrecarga seleccionada.
        selected = best[0]
        return_type = selected.get('return_type', 'unknown')
        result_ref = None
        if return_type != 'void':
            result_ref = self._nuevo_temporal()
        self._emit('CALL', func_name, len(args), result_ref)
        p[0] = self._expr(return_type, None, result_ref)

    # Reconoce la instanciación de registros mediante new.
    def p_instanciacion(self, p):
        '''instanciacion : NEW ID LPAREN argumentos_opt RPAREN'''
        # Obtiene nombre del registro, argumentos y línea.
        record_name = p[2]
        args = p[4] if isinstance(p[4], list) else []
        line = p.lineno(1)

        # Verifica que el tipo de registro exista.
        if record_name not in self.records:
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: El registro '{record_name}' no existe")
            p[0] = self._expr('error', None)
            return

        # Compara cantidad de argumentos con cantidad de campos.
        field_items = list(self.records[record_name].items())
        if len(args) != len(field_items):
            self.has_semantic_error = True
            print(f"[ERROR SEMANTICO] Linea {line}: La instanciación de '{record_name}' requiere {len(field_items)} argumentos y recibió {len(args)}")
            p[0] = self._expr('error', None)
            return

        # Inicializa la instancia y el estado de error local.
        instance = {'__record_type__': record_name}
        has_local_error = False

        # Recorre cada campo con su argumento correspondiente.
        for (field_name, field_type), arg in zip(field_items, args):
            # Extrae tipo y valor del argumento.
            arg_type, arg_value = ('error', None)
            if isinstance(arg, tuple) and len(arg) >= 2:
                arg_type, arg_value = arg[0], arg[1]

            # Si el argumento ya es erróneo, marca error local.
            if arg_type == 'error':
                has_local_error = True
                continue

            # Verifica compatibilidad entre argumento y tipo del campo.
            if arg_type != 'unknown' and not (arg_type == field_type or self._auto_convert(arg_type, field_type)):
                self.has_semantic_error = True
                print(f"[ERROR SEMANTICO] Linea {line}: El argumento para '{field_name}' no es compatible con tipo '{field_type}'")
                has_local_error = True
                continue

            # Convierte el valor cuando hace falta para ajustarlo al campo.
            if arg_value is not None and arg_type != field_type:
                arg_value = self._convertir_numero(arg_value, arg_type, field_type)

            # Asigna el valor convertido al campo de la instancia.
            instance[field_name] = arg_value

        # Si hubo errores locales, devuelve error de instanciación.
        if has_local_error:
            p[0] = self._expr('error', None)
            return

        # Devuelve instancia válida tipada con su nombre de registro.
        p[0] = self._expr(record_name, instance)

    # Permite que la lista de argumentos de una llamada sea vacía u opcional.
    def p_argumentos_opt(self, p):
        '''argumentos_opt : lambda
                         | argumentos'''
        # Si no hay argumentos, devuelve lista vacía.
        if len(p) == 2 and p.slice[1].type == 'lambda':
            p[0] = []

        # Si hay argumentos, propaga la lista construida.
        else:
            p[0] = p[1]

    # Construye la lista de argumentos de una llamada o instanciación.
    def p_argumentos(self, p):
        '''argumentos : argumentos COMMA expresion
                     | expresion'''
        # Caso base con un único argumento.
        if len(p) == 2:
            p[0] = [p[1]]

        # Caso recursivo que acumula argumentos.
        else:
            p[0] = p[1] + [p[3]]

    # Reconoce los literales básicos del lenguaje.
    def p_literal(self, p):
        '''literal : INT_VALUE
                  | FLOAT_VALUE
                  | CHAR_VALUE
                  | TRUE
                  | FALSE'''
        # Identifica el tipo de token literal reconocido.
        token_type = p.slice[1].type

        # Devuelve el literal tipado según su clase léxica.
        if token_type == 'INT_VALUE':
            p[0] = self._expr('int', p[1], self._valor_a_operando(p[1], 'int'))
        elif token_type == 'FLOAT_VALUE':
            p[0] = self._expr('float', p[1], self._valor_a_operando(p[1], 'float'))
        elif token_type == 'CHAR_VALUE':
            p[0] = self._expr('char', p[1], self._valor_a_operando(p[1], 'char'))
        else:
            p[0] = self._expr('boolean', p[1], self._valor_a_operando(p[1], 'boolean'))

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