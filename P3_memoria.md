# 

# **![][image1]**

## Universidad Carlos III

## Curso Procesadores del Lenguaje 25/26-2C

## Analizador Semántico

# **MEMORIA P3**

Grupo: **80**  
Autores:

**Álvaro García González \- 100522223@alumnos.uc3m.es**  
**Samuel Gómez Fernández \- 100522224@alumnos.uc3m.es**

**Índice**

[**1\. Introducción	3**](#introducción)

[**1.1. Parte Opcional: Generación de Código Intermedio	3**](#parte-opcional:-generación-de-código-intermedio)

[**2\. Arquitectura de la Solución	4**](#arquitectura-de-la-solución)

[2.1. Descripción General de parser.py	4](#descripción-general-de-parser.py)

[2.2. Descripción General de main.py	4](#descripción-general-de-main.py)

[2.3. Variables e Indicadores de Estado	4](#variables-e-indicadores-de-estado)

[**3\. Diseño de la Solución	5**](#diseño-de-la-solución)

[3.1. Definición Formal de la Gramática	5](#definición-formal-de-la-gramática)

[3.2. Tabla de Símbolos	8](#tabla-de-símbolos)

[3.2.1. Tabla de Variables	9](#tabla-de-variables)

[3.2.2. Tabla de Registros	9](#tabla-de-registros)

[3.2.3. Tabla de Funciones	9](#tabla-de-funciones)

[3.3. Pila de Ámbitos	9](#pila-de-ámbitos)

[3.4. Representación Interna de Expresiones	9](#representación-interna-de-expresiones)

[3.5. Métodos Auxiliares del parser	10](#métodos-auxiliares-del-parser)

[3.5.1. Gestión de la Tabla de Símbolos	10](#gestión-de-la-tabla-de-símbolos)

[3.5.2. Comprobación y Conversión de Tipos	10](#comprobación-y-conversión-de-tipos)

[3.5.3. Validación Semántica	11](#validación-semántica)

[3.5.4. Exportación de Tablas Semánticas	11](#exportación-de-tablas-semánticas)

[3.5.5. Utilidades Específicas de cuartetos	11](#utilidades-específicas-de-cuartetos)

[3.6. Comprobaciones Semánticas Implementadas	12](#comprobaciones-semánticas-implementadas)

[3.6.1. Controles Semánticos de Declaraciones y Asignaciones	12](#controles-semánticos-de-declaraciones-y-asignaciones)

[3.6.1.1. Declaración de Variables	12](#declaración-de-variables)

[3.6.1.2. Asignación de Variables	13](#asignación-de-variables)

[3.6.1.3. Validación de print	13](#validación-de-print)

[3.6.2. Controles Semánticos de Expresiones	13](#controles-semánticos-de-expresiones)

[3.6.2.1. Operaciones aritméticas	13](#operaciones-aritméticas)

[3.6.2.2. Operaciones Comparativas	14](#operaciones-comparativas)

[3.6.2.3. Operaciones Lógicas	14](#operaciones-lógicas)

[3.6.2.4. Operadores Unarios	14](#operadores-unarios)

[3.6.3. Controles Semánticos de Registros	15](#controles-semánticos-de-registros)

[3.6.3.1. Declaración de Registros	15](#declaración-de-registros)

[3.6.3.2. Instanciación con new	15](#instanciación-con-new)

[3.6.3.3. Acceso a Campos	16](#acceso-a-campos)

[3.6.4. Controles Semánticos de Funciones	16](#controles-semánticos-de-funciones)

[3.6.4.1. Declaración y Sobrecarga	16](#declaración-y-sobrecarga)

[3.6.4.2. Invocación y Resolución de Sobrecarga	17](#invocación-y-resolución-de-sobrecarga)

[3.6.4.3. Validación de return	17](#validación-de-return)

[3.6.5. Controles Semánticos de Control de Flujo	18](#controles-semánticos-de-control-de-flujo)

[3.6.5.1. Condiciones en if, while y do-while	18](#condiciones-en-if,-while-y-do-while)

[3.6.5.2. Validación de break	18](#validación-de-break)

[3.7. Gestión de Errores Semánticos	19](#gestión-de-errores-semánticos)

[**3.8. Diseño Parte Opcional	20**](#diseño-parte-opcional)

[3.8.1. Formato Fichero .quartets	20](#formato-fichero-.quartets)

[3.8.2. Cobertura de Instrucciones	20](#cobertura-de-instrucciones)

[3.8.3. Marcadores de Producción para Control de Flujo	20](#marcadores-de-producción-para-control-de-flujo)

[**4\. Batería de Pruebas	21**](#batería-de-pruebas)

[**5\. Conclusiones	21**](#conclusiones)

[**ANEXO. Declaración de Uso de Inteligencia Artificial	22**](#anexo.-declaración-de-uso-de-inteligencia-artificial)

1. # **Introducción** {#introducción}

El presente documento constituye la memoria técnica de la tercera fase (P3) del proyecto de compilación de la asignatura. Esta fase final se centra en el diseño, implementación y validación de un **analizador semántico** integrado en el parser del lenguaje de programación Lava, construido sobre el analizador sintáctico y léxico desarrollado en las entregas anteriores y siguiendo estrictamente la especificación del enunciado.

El propósito de la práctica es triple. En primer lugar, **extender la gramática formal ya existente con acciones semánticas** capaces de detectar y reportar errores de tipo, redeclaración de variables, uso incorrecto de sentencias de control y validación de firmas de funciones. En segundo lugar, **implementar las estructuras de datos necesarias para dar soporte a dicho análisis**: una tabla de variables, una tabla de registros, una tabla de funciones y una pila de ámbitos que modela correctamente el alcance léxico del lenguaje, todo ello mediante la librería *ply.yacc*. 

1. ## **Parte Opcional: Generación de Código Intermedio** {#parte-opcional:-generación-de-código-intermedio}

En esta entrega se ha implementado adicionalmente la **parte opcional** de la práctica: la **generación de código intermedio en formato de cuartetos** (ficheros *.quartets*). Esta funcionalidad se integró directamente en ***parser.py***, aprovechando el flujo semántico ya existente, de modo que cada regla gramatical, una vez validada semánticamente, emite los cuartetos correspondientes. La exportación del fichero *.quartets* se realiza en ***main.py*** tras una ejecución semántica exitosa. 

Esta memoria detalla las decisiones de diseño adoptadas, justificando técnicamente cada elección realizada y las conclusiones obtenidas. El objetivo es **proporcionar una documentación clara que facilite la comprensión del código implementado.**

2. # **Arquitectura de la Solución** {#arquitectura-de-la-solución}

La solución final se apoya sobre tres piezas: 

* ***lexer.py***, responsable del análisis léxico.  
* ***parser.py***, que concentra la gramática, las acciones semánticas y la generación de cuartetos.  
* ***main.py***, que actúa como punto de entrada, selecciona el modo de ejecución y exporta los artefactos generados. 

  1. ## **Descripción General de parser.py** {#descripción-general-de-parser.py}

***parser.py*** implementa la clase **ParserClass**, que actúa como analizador sintáctico, semántico y generador de código intermedio del lenguaje Lava. Su funcionamiento: recibe el flujo de tokens producido por **LexerClass**, aplica las reglas de producción de la gramática y, de forma simultánea, ejecuta las acciones semánticas asociadas a cada regla. Al finalizar el análisis, exporta los resultados a tres ficheros de salida *.symbols, .records y .functions* que reflejan el estado final de las tablas semánticas;  y *.quartets* (código intermedio).

2. ## **Descripción General de main.py** {#descripción-general-de-main.py}

***main.py*** representa la ejecución del compilador. Tras invocar el parser, comprueba si existen errores sintácticos o semánticos. Si no los hay, exporta las tablas semánticas mediante **exportar\_tablas\_semanticas(entrada)** y, adicionalmente, exporta el código intermedio mediante **exportar\_cuartetos(entrada)**. 

3. ## **Variables e Indicadores de Estado**  {#variables-e-indicadores-de-estado}

El constructor **\_\_init\_\_** inicializa un conjunto de variables que controlan el estado del análisis a lo largo de toda la ejecución del parser:

**Estado semántico:** 

* ***has\_syntax\_error*****:** indica si se ha producido algún error sintáctico durante el análisis.  
* ***has\_semantic\_error*****:** indica si se ha producido algún error semántico.  
* ***current\_function*****:** almacena el contexto de la función que se está analizando en cada momento, incluyendo su nombre, tipo de retorno y si ya se ha encontrado un *return* válido.  
* ***loop\_depth*****:** contador de bucles anidados activos, utilizado para validar el uso correcto de *break*.  
* **\_has\_flow:** marca si el programa contiene estructuras de control o funciones, lo que determina el formato de exportación de la tabla de variables.  
* ***\_decl\_type, \_decl\_name, \_decl\_line*****:** variables auxiliares que almacenan temporalmente los datos de la declaración que se está procesando, necesarias para comunicar información entre reglas de producción no adyacentes.


**Estado de generación de cuartetos:** 

* ***self.quartets*****:** lista de tuplas (*operador, arg1, arg2, resultado*) que actúa como buffer de cuartetos emitidos.   
* ***self.\_temp\_counter:*** contador entero para generar nombres de temporales (*@T1, @T2, ...*).   
* ***self.\_label\_counter:*** contador entero para generar nombres de etiquetas (*@L1, @L2, ...*).   
* ***self.\_if\_codegen\_stack:*** pila de diccionarios con el contexto de cada *if/else* activo (etiquetas *else\_label, end\_label* y flag *has\_else*).   
* ***self.\_loop\_codegen\_stack:*** pila de diccionarios con el contexto de cada bucle activo (etiquetas *start, end* y campo *kind* con valor *while* o *do*). 


Todo estos estados se reinician en **\_reiniciar\_estado\_semantico()**, que limpia tanto las tablas semánticas como el estado de generación de cuartetos.

Asimismo, la clase **ParserClass()** define el elemento estático **DEFAULT\_TYPES:** diccionario que asocia cada tipo básico del lenguaje con su valor por defecto. Se utiliza para inicializar variables declaradas sin valor explícito.

3. # **Diseño de la Solución** {#diseño-de-la-solución}

   1. ## **Definición Formal de la Gramática** {#definición-formal-de-la-gramática}

A continuación se presenta la **gramática** completa del lenguaje Lava en notación **BNF**. Debe tenerse en cuenta que algunos no terminales auxiliares como *\<if\_mark\>, \<while\_start\>* o *\<inicio\_funcion\_tipada\>* no introducen nuevas construcciones del lenguaje, sino que actúan como marcadores internos para ejecutar acciones semánticas y de generación de código intermedio durante el parseo. 

```shell
// Gramática
programa         ::= elementos_opt

elementos_opt    ::= λ | elementos

elementos        ::= elementos elemento | elemento

elemento         ::= SEMICOLON
                   | declaracion_funcion_void
                   | declaracion_o_funcion_tipada
                   | declaracion_record SEMICOLON
                   | sentencia_bloque
                   | sentencia_simple SEMICOLON

// Declaraciones globales y funciones
declaracion_funcion_void ::=	VOID ID LPAREN parametros_opt RPAREN
    				inicio_funcion_void bloque_void fin_funcion_void
declaracion_o_funcion_tipada ::=  tipo ID marcar_declaracion_tipada resto_tipado_programa

resto_tipado_programa ::=
      LPAREN parametros_opt RPAREN inicio_funcion_tipada bloque fin_funcion_tipada
    | ASSIGN expresion SEMICOLON
    | resto_lista_ids SEMICOLON

resto_lista_ids  ::= λ | resto_lista_ids COMMA ID

// Bloques y control de flujo en funciones void
bloque_void      ::= LBRACE elementos_bloque_void_opt RBRACE

elementos_bloque_void_opt ::= λ | elementos_bloque_void

elementos_bloque_void ::= elementos_bloque_void elemento_bloque_void
    			   | elemento_bloque_void

elemento_bloque_void ::= SEMICOLON | sentencia_bloque_void
    			| declaracion_variable SEMICOLON
    			| sentencia_simple_void SEMICOLON

sentencia_bloque_void ::= bloque_void | sentencia_if_void | sentencia_while_void
    			  | sentencia_do_while_void

sentencia_if_void ::= IF LPAREN expresion RPAREN
    			if_mark bloque_void else_void_opt if_end_mark

else_void_opt    ::= λ | else_mark ELSE bloque_void

sentencia_while_void ::=
    WHILE while_start LPAREN expresion RPAREN
    while_cond_mark entrar_bucle bloque_void salir_bucle while_end

sentencia_do_while_void ::=
    DO do_start entrar_bucle bloque_void salir_bucle
    WHILE LPAREN expresion RPAREN SEMICOLON do_end

sentencia_simple_void ::= asignacion | print_stmt | BREAK | expresion

// Bloques y control de flujo general
bloque           ::= LBRACE elementos_bloque_opt RBRACE

elementos_bloque_opt ::= λ | elementos_bloque

elementos_bloque ::= elementos_bloque elemento_bloque | elemento_bloque

elemento_bloque  ::= SEMICOLON | sentencia_bloque | declaracion_variable SEMICOLON
    		     | sentencia_simple SEMICOLON

sentencia_bloque ::= bloque | sentencia_if | sentencia_while | sentencia_do_while
sentencia_if     ::= IF LPAREN expresion RPAREN if_mark bloque else_opt if_end_mark

else_opt         ::= λ | else_mark ELSE bloque
sentencia_while  ::=
    WHILE while_start LPAREN expresion RPAREN
    while_cond_mark entrar_bucle bloque salir_bucle while_end

sentencia_do_while ::=
    DO do_start entrar_bucle bloque salir_bucle
    WHILE LPAREN expresion RPAREN SEMICOLON do_end

// Sentencias simples y declaraciones
sentencia_simple ::= asignacion | print_stmt | BREAK | RETURN expresion | expresion

declaracion_variable ::= tipo lista_ids | tipo ID ASSIGN expresion

lista_ids        ::= ID | lista_ids COMMA ID

asignacion       ::= acceso ASSIGN expresion

print_stmt       ::= PRINT LPAREN argumentos_opt RPAREN

// Registros parámetros y tipos
declaracion_record ::= RECORD ID LPAREN campos_record_opt RPAREN

campos_record_opt ::= λ | campos_record

campos_record    ::= campos_record COMMA campo_record_item | campo_record_item

campo_record_item ::= tipo ID | ID

parametros_opt   ::= λ | parametros

parametros       ::= parametros COMMA parametro | parametro

parametro        ::= tipo ID

tipo             ::= INT | FLOAT | CHAR | BOOLEAN | ID

// Expresiones
expresion        ::= expresion OR expresion
                   | expresion AND expresion
                   | expresion EQUAL expresion
                   | expresion GREATER expresion
                   | expresion GREATER_EQUAL expresion
                   | expresion LESS expresion
                   | expresion LESS_EQUAL expresion
                   | expresion PLUS expresion
                   | expresion MINUS expresion
                   | expresion TIMES expresion
                   | expresion DIVIDE expresion
                   | NOT expresion
                   | MINUS expresion
                   | PLUS expresion
                   | primario

primario         ::= literal | acceso | llamada | LPAREN expresion RPAREN | instanciacion

acceso           ::= ID | acceso DOT ID

llamada          ::= ID LPAREN argumentos_opt RPAREN

instanciacion    ::= NEW ID LPAREN argumentos_opt RPAREN

argumentos_opt   ::= λ | argumentos

argumentos       ::= argumentos COMMA expresion | expresion

literal          ::= INT_VALUE | FLOAT_VALUE | CHAR_VALUE | TRUE | FALSE

// Marcadores auxiliares
-- Marcadores de codegen (producen λ):
if_mark          ::= λ
else_mark        ::= λ
if_end_mark      ::= λ
while_start      ::= λ
while_cond_mark  ::= λ
while_end        ::= λ
do_start         ::= λ
do_end           ::= λ
entrar_bucle     ::= λ
salir_bucle      ::= λ

-- Marcadores semánticos (producen λ):
inicio_funcion_void    ::= λ
fin_funcion_void       ::= λ
inicio_funcion_tipada  ::= λ
fin_funcion_tipada     ::= λ
marcar_declaracion_tipada ::= λ

// Producción vacía
λ                ::= <empty>
```

2. ## **Tabla de Símbolos** {#tabla-de-símbolos}

La tabla de símbolos es la estructura central del análisis semántico. Se implementa mediante tres diccionarios Python independientes, cada uno con una responsabilidad bien delimitada. Todos ellos se inicializan en **\_\_init\_\_**.

1. ### **Tabla de Variables** {#tabla-de-variables}

Almacenada en ***self.symbols***, recoge todas las variables de tipo básico declaradas en el ámbito global del programa. Cada entrada sigue la estructura *nombre → (tipo, valor)*, donde el valor puede ser un literal concreto o el valor por defecto del tipo si la variable se declaró sin inicialización.

2. ### **Tabla de Registros** {#tabla-de-registros}

Almacenada en ***self.records***, registra todos los tipos compuestos declarados con la palabra reservada record. Cada entrada sigue la estructura *nombre\_registro → {nombre\_campo → tipo\_campo}*, preservando el orden de declaración de los campos.

3. ### **Tabla de Funciones** {#tabla-de-funciones}

Almacenada en ***self.functions***, gestiona todas las funciones declaradas en el programa y da soporte a la sobrecarga. La estructura es *nombre\_función → \[lista de firmas\]*, donde cada firma es un diccionario con dos campos: ***params*** (lista de pares *(tipo, nombre)*) y ***return\_type*** (tipo de retorno, incluyendo *void*).

3. ## **Pila de Ámbitos** {#pila-de-ámbitos}

La pila de ámbitos, implementada en ***self.stack***, modela el alcance léxico del lenguaje. Se trata de una lista de diccionarios donde cada elemento representa un ámbito activo: el primero (*self.stack\[0\]*) corresponde siempre al ámbito global (*self.symbols*), y cada nueva función empujada mediante *self.stack.append()* añade un ámbito local en la cima.

Cuando el parser entra en el cuerpo de una función, crea un nuevo diccionario con los parámetros de esa función como entradas iniciales y lo apila. Al salir de la función (**p\_fin\_funcion\_void***,* **p\_fin\_funcion\_tipada**), ese diccionario se elimina con *self.stack.pop()*. Este mecanismo garantiza que las **variables locales no colisionen con las globales** y que dejen de existir al salir de su ámbito.

```py
self.stack = [self.symbols]
```

4. ## **Representación Interna de Expresiones** {#representación-interna-de-expresiones}

Con la introducción de la generación de código intermedio, la representación interna de todas las expresiones pasó de ser una tupla de longitud exacta 2 *(tipo, valor)* a una tupla de longitud 3 ***(tipo, valor, ref)***:

* ***tipo*** recoge el tipo semántico inferido.   
* ***valor*** almacena el valor calculado cuando puede conocerse en tiempo de análisis.   
* ***ref*** representa el operando que se usará directamente en los cuartetos (un literal serializado, el nombre de una variable o un temporal *@Tn*).


Para construir y descomponer estas expresiones de forma uniforme se introdujeron dos métodos auxiliares que se explicaran con detalle en el siguiente apartado: **\_expr** y **\_extraer\_expr**.

5. ## **Métodos Auxiliares del parser** {#métodos-auxiliares-del-parser}

   1. ### **Gestión de la Tabla de Símbolos** {#gestión-de-la-tabla-de-símbolos}

Estos métodos operan directamente sobre la pila de ámbitos (*self.stack*) para localizar y modificar variables ya declaradas:

* **\_buscar\_simbolo(name):** recorre la pila de ámbitos de más interno a más externo y devuelve la entrada correspondiente al nombre buscado, o *None* si no existe. Este orden de recorrido garantiza que las variables locales tienen precedencia sobre las globales.  
* **\_actualizar\_simbolo(name, value):** localiza el símbolo en la pila siguiendo el mismo criterio de proximidad y actualiza su valor manteniendo el tipo original. Devuelve *True* si la actualización fue exitosa o *False* si el símbolo no existe.


  2. ### **Comprobación y Conversión de Tipos** {#comprobación-y-conversión-de-tipos}

Este es el grupo más extenso de métodos auxiliares. Su función es determinar la compatibilidad entre tipos y realizar las conversiones necesarias durante el análisis:

* **\_es\_tipo\_valido(type\_name):** comprueba si un nombre de tipo corresponde a un tipo básico del lenguaje o a un registro previamente declarado.  
* **\_es\_tipo\_numerico(type\_name):** determina si un tipo es numérico, considerando como tales *char, int y float*.  
* **\_auto\_convert(source\_type, target\_type):** indica si existe una conversión implícita permitida entre dos tipos. Las conversiones válidas son c*har → int, char → float e int → float*, siguiendo una jerarquía de promoción numérica.  
* **\_costo\_conversion(source\_type, target\_type):** asigna un coste numérico a cada conversión posible (*char → int: 1, int → float: 1, char → float: 2*), utilizado para resolver la sobrecarga de funciones eligiendo la firma con menor coste total de conversión.  
* **\_tipo\_numerico\_comun(left\_type, right\_type):** determina el tipo resultante de operar dos operandos numéricos, aplicando la regla de promoción: *float* tiene mayor prioridad que *int*, e int mayor que *char*.  
* **\_convertir\_numero(value, source\_type, target\_type):** convierte un valor numérico concreto al tipo objetivo. Gestiona casos especiales como el char vacío (tratado como cero) y la conversión de caracteres mediante *ord()*.  
* **\_normalizar\_operandos\_numericos(left\_type, left\_value, right\_type, right\_value):** combina **\_tipo\_numerico\_comun** y **\_convertir\_numero** para llevar ambos operandos de una expresión binaria al mismo tipo antes de evaluarla.  
* **\_convertir\_valor\_asignacion(value, source\_type, target\_type):** aplica la conversión de valor específicamente en el contexto de una asignación, normalizando primero los char a su valor numérico entero cuando es necesario.  
* **\_valor\_por\_defecto(type\_name, visited):** genera el valor inicial de una variable recién declarada. Para tipos básicos consulta *DEFAULT\_TYPES*; para registros construye recursivamente un diccionario con el valor por defecto de cada campo. El parámetro opcional *visited* evita recursión infinita en registros con referencias cíclicas.


  3. ### **Validación Semántica** {#validación-semántica}

Estos métodos encapsulan comprobaciones semánticas concretas que se invocan desde múltiples reglas de producción:

* \_**condicion\_es\_valida(expr, line, contexto):** verifica que la expresión usada como condición en un *if, while* o *do-while* sea de **tipo boolean**. De forma excepcional, también admite el tipo *unknown* para no interrumpir el análisis cuando el tipo de una expresión no ha podido resolverse completamente todavía. Si el tipo es incompatible, registra el error semántico con el número de línea y el nombre de la estructura de control afectada.  
* **\_registrar\_firma\_funcion(func\_name, params, return\_type, line):** añade una nueva firma a la tabla de funciones, comprobando previamente que no exista ya una firma idéntica para el mismo nombre. Si la firma está duplicada, reporta un error semántico. Este mecanismo es el que permite la **sobrecarga de funciones**.


  4. ### **Exportación de Tablas Semánticas** {#exportación-de-tablas-semánticas}

Una vez completado el análisis, el parser puede volcar los resultados a disco mediante dos métodos:

* **\_formatear\_valor(value):** convierte un valor Python al formato textual esperado en los ficheros de salida. Los booleanos se escriben como *true/false*, los registros como *{campo:valor,...}* y el resto como su representación en cadena directa.  
* **exportar\_tablas\_semanticas(input\_path):** genera los tres ficheros de salida a partir del nombre del fichero de entrada analizado: *.symbols* con las variables globales, *.records* con los registros declarados y *.functions* con todas las firmas de funciones registradas. Cuando el programa contiene funciones o estructuras de control (*\_has\_flow* o *self.functions*), la tabla de símbolos exporta únicamente el tipo de cada variable, omitiendo el valor.

  5. ### **Utilidades Específicas de cuartetos** {#utilidades-específicas-de-cuartetos}

* **\_expr(type\_name, value, ref=None):** construye la representación *(tipo, valor, ref)*. Si *ref* no se proporciona, intenta inferirlo a partir del valor mediante **\_valor\_a\_operando**.  
* **\_extraer\_expr(expr):** descompone cualquier expresión (de longitud 2 o 3\) en sus tres componentes *(tipo, valor, ref)*, garantizando compatibilidad hacia atrás.   
* **\_nuevo\_temporal** y **\_nueva\_etiqueta**, que generan nombres *@Tn* y *@Ln*.   
* **\_normalizar\_operando\_cuarteto(operand):** convierte un operando al formato texto usado en *.quartets* (*\_* para *None*, *true/false* para booleanos, y *str(operand)* para el resto).   
* **\_emit(operator, arg1, arg2, result):** registra un cuarteto en el buffer *self.quartets*, normalizando todos sus campos.   
* **\_valor\_a\_operando(value, value\_type=None):** convierte valores semánticos concretos al formato de operando de cuarteto. Los *char* se serializan con comillas simples y con escape de *\\* y *'*.  
* **\_asegurar\_tipo\_en\_cuartetos(ref, source\_type, target\_type):** inserta cuartetos de conversión explícita de tipo cuando los operandos requieren promoción: *CHAR\_TO\_INT*, *INT\_TO\_FLOAT* o la cadena *CHAR\_TO\_INT \+ INT\_TO\_FLOAT* para *char → float*. Devuelve la referencia al temporal resultante.   
* **\_operador\_binario\_a\_cuarteto(operator\_type):** mapea los tokens de operador binario de la gramática a sus opcodes de cuarteto (*PLUS → ADD, MINUS → SUB, TIMES → MUL, DIVIDE → DIV, GREATER → GT, GREATER\_EQUAL → GTE, LESS → LT, LESS\_EQUAL → LTE, EQUAL → EQ, AND → AND, OR → OR)*.   
* **\_operador\_unario\_a\_cuarteto(operator\_type):** mapea los tokens de operador unario a sus opcodes (*NOT → NOT, MINUS → UMINUS, PLUS → UPLUS*).   
* **exportar\_cuartetos(input\_path):** serializa self.quartets al fichero *.quartets*, escribiendo una línea por cuarteto con el formato *OPERADOR,ARG1,ARG2,RESULT*. 

  6. ## **Comprobaciones Semánticas Implementadas** {#comprobaciones-semánticas-implementadas}

     1. ### **Controles Semánticos de Declaraciones y Asignaciones** {#controles-semánticos-de-declaraciones-y-asignaciones}

        1. #### **Declaración de Variables** {#declaración-de-variables}

Las funciones implicadas son **p\_declaracion\_variable** (dentro de bloques y funciones) y **p\_declaracion\_o\_funcion\_tipada** (en el ámbito global, donde se desambigua si es una declaración o una función).

El parser distingue dos formas de declaración: la declaración simple o múltiple sin asignación (*int a, b, c;*) y la declaración con inicialización (*int a \= 5;*). En ambos casos se realizan las siguientes comprobaciones:

* **Se verifica que el tipo declarado sea válido**, es decir, que sea un tipo básico del lenguaje (int, float, char, boolean) o un registro previamente definido (mediante **\_es\_tipo\_valido**).  
* **Se comprueba que el nombre de la variable no exista ya en el ámbito actual**. Si la variable ya fue declarada, se reporta un error de re-declaración.  
* **En el caso de declaración sin inicialización, la variable se registra con su valor por defecto según el tipo:** 0 para *int*, 0.0 para *float*, '' para *char* y false para *boolean*. Para variables de tipo registro, se construye recursivamente un valor por defecto con los valores por defecto de cada campo.  
* **La declaración múltiple con asignación no está permitida** (*float a, b \= 5*; sería un error sintáctico).

Además, si en una declaración se usa una variable no declarada dentro de la expresión de inicialización (por ejemplo *int x \= x \+ x;*), se detecta error semántico porque el acceso a x falla al no existir aún en el ámbito.

2. #### **Asignación de Variables** {#asignación-de-variables}

La función implicada es **p\_asignacion**, que acepta tanto variables simples como accesos encadenados con punto (a.campo). El lado izquierdo es validado como un acceso de tipo *var* o *field*; cualquier otro tipo de expresión en la parte izquierda se rechaza como inválido.

Una vez **identificados los tipos del lado izquierdo y del lado derecho**, se llama a **\_auto\_convert** para determinar si la asignación es compatible. Si los tipos son iguales, se acepta directamente; si son compatibles por conversión implícita, se convierte el valor mediante **\_convertir\_valor\_asignacion** antes de guardarlo. Si los tipos son incompatibles, se reporta el error semántico.

3. #### **Validación de *print*** {#validación-de-print}

La función implicada es **p\_print\_stmt**. La sentencia *print* se trata como una función especial del sistema. Al procesarla se comprueba:

* **Que se proporcione al menos un argumento**. Si la llamada no tiene argumentos, se reporta un error semántico.  
* **Que cada argumento sea una expresión válida con un tipo reconocido**. Si algún argumento tiene tipo *error*, se reporta un error semántico.

  2. ### **Controles Semánticos de Expresiones** {#controles-semánticos-de-expresiones}

     1. #### **Operaciones aritméticas** {#operaciones-aritméticas}

La función implicada es **p\_expresion\_binaria**, en la rama de los operadores ***PLUS, MINUS, TIMES*** y ***DIVIDE***.

Los operadores ***\+, \-, \**** y ***/*** requieren que ambos operandos sean de **tipo numérico** (*char, int o float*). Si alguno de los operandos es de tipo *boolean* o de tipo *registro*, se reporta un error semántico. El tipo resultante se determina mediante **\_tipo\_numerico\_comun**, que aplica la regla de promoción: *float \> int \> char*.

Existe un caso especial para ***\**** y ***/***: si el tipo común resultaría ser char, se promociona a int para evitar desbordamientos. 

```py
if operator_type in ('TIMES', 'DIVIDE') and result_type == 'char':
      result_type = 'int'
```

Cuando ambos operandos tienen valor concreto en tiempo de análisis, el parser evalúa la operación directamente, propagando el resultado. La división entre cero produce *None* como valor, evitando excepciones en tiempo de compilación.

2. #### **Operaciones Comparativas** {#operaciones-comparativas}

La función implicada es **p\_expresion\_binaria**, en la rama de los operadores ***GREATER, GREATER\_EQUAL, LESS, LESS\_EQUAL*** y ***EQUAL***.

Los operadores ***\>, \>=, \<*** y ***\<=*** exigen que ambos operandos sean numéricos, y devuelven siempre boolean. Para evaluarlos, ambos operandos se normalizan al mismo tipo numérico común mediante **\_normalizar\_operandos\_numericos**. 

El operador ***\==*** es más permisivo: acepta tipos iguales o tipos compatibles por conversión en alguna de las dos direcciones. Cuando ambos operandos son numéricos, también se normalizan al mismo tipo numérico común antes de comparar; en los demás casos comparables, la igualdad se evalúa directamente sobre los valores.

3. #### **Operaciones Lógicas** {#operaciones-lógicas}

La función implicada es **p\_expresion\_binaria**, en la rama de los operadores ***AND*** y ***OR***.

Los operadores ***&&*** (AND) y ***||*** (OR) requieren que ambos operandos sean estrictamente de **tipo boolean**. No se admite ninguna conversión automática: un *int* o *char* no pueden usarse directamente como booleanos. Si alguno de los operandos no es *boolean*, se reporta un error semántico. El resultado es siempre *boolean*.

4. #### **Operadores Unarios** {#operadores-unarios}

La función implicada es **p\_expresion\_unaria**.

El operador ***\!*** (NOT) requiere un operando de **tipo boolean** y devuelve también *boolean*. Los operadores unarios ***\+*** y ***\-*** requieren un operando **numérico** (*char, int* o *float*). En el caso de ***\+***, el valor se propaga sin cambios; en el caso de ***\-***, se aplica la negación correspondiente al tipo del operando.

Internamente, el parser trabaja con expresiones tipadas que contienen al menos el tipo y el valor calculado, pudiendo incorporar información auxiliar adicional. A partir de esa representación, **p\_expresion\_unaria** extrae el tipo del operando y valida si el operador aplicado es compatible con él.

Si el operando tiene **tipo boolean**, solo se admite el operador ***\!***. Si el operando tiene **tipo numérico**, se admiten ***\+*** y ***\-***. Cuando el operando es de **tipo char** y se aplica la negación unaria, esta se realiza mediante una inversión modular sobre el código ASCII: *chr((-ord(c)) % 256\)*.

```py
# En char aplica negación modular sobre el código ASCII.
elif expr_type == 'char' and isinstance(expr_value, str) and len(expr_value) == 1:
    result_value = ('char', chr((-ord(expr_value)) % 256))
```

Si el operando tiene un **tipo no compatible** con el operador utilizado, se reporta el correspondiente error semántico y se devuelve una expresión marcada con tipo *error*, evitando así la propagación de falsos positivos en comprobaciones posteriores.

3. ### **Controles Semánticos de Registros** {#controles-semánticos-de-registros}

   1. #### **Declaración de Registros** {#declaración-de-registros}

La función implicada es **p\_declaracion\_record**.

Cuando se procesa una declaración *record*, se realizan las siguientes comprobaciones:

* **Se verifica que no exista ya un registro con el mismo nombre**. Si existe, se reporta un error de re-declaración.  
* **Se comprueba que el tipo de cada campo sea válido:** un tipo básico o un registro previamente declarado.  
* **Se verifica que no haya campos con el mismo nombre dentro del mismo registro**.  
* **Se soporta la multi-declaración de campos con el mismo tipo** *(record Point(float x1, x2);*), donde los campos que no indican tipo explícito heredan el tipo del campo anterior. Esta resolución se realiza mediante las funciones **p\_campo\_record\_item\_typed** y **p\_campo\_record\_item\_bare**.


```py
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
```

  2. #### **Instanciación con *new*** {#instanciación-con-new}

La función implicada es **p\_instanciacion**.

Al procesar una instanciación (*new NombreRegistro(args)*), se comprueba:

* **Que el registro referenciado exista en la tabla de registros**.  
* **Que el número de argumentos proporcionados coincida con el número de campos del registro**.  
* **Que el tipo de cada argumento sea compatible con el tipo del campo correspondiente**, aplicando conversiones automáticas cuando sea posible (**\_auto\_convert**).

Si todas las comprobaciones son correctas, se construye un diccionario con los valores de cada campo, que representa la instancia del registro.

3. #### **Acceso a Campos** {#acceso-a-campos}

La función implicada es **p\_acceso**.

El acceso a campos de registros mediante el operador punto (***.***) se resuelve de forma encadenada, soportando accesos anidados como *linea.a.x1*. En cada nivel de acceso se comprueba:

* **Que el tipo del lado izquierdo sea un registro existente.**  
* **Que el campo referenciado exista en la definición de ese registro**.

Si alguna comprobación falla, el acceso se marca como inválido y se propaga el tipo *error* para que las expresiones que lo contengan puedan ser evaluadas correctamente. Para cada acceso válido, se almacena la ruta completa de campos desde la variable raíz, lo que permite posteriormente realizar asignaciones a campos anidados.

4. ###  **Controles Semánticos de Funciones** {#controles-semánticos-de-funciones}

   1. #### **Declaración y Sobrecarga** {#declaración-y-sobrecarga}

Las funciones implicadas son **p\_declaracion\_funcion\_void**, **p\_inicio\_funcion\_void** y **p\_fin\_funcion\_void** para funciones *void*.  
**p\_declaracion\_o\_funcion\_tipada**, **p\_inicio\_funcion\_tipada** y **p\_fin\_funcion\_tipada** para funciones con retorno tipado.  
La validación de tipos de los parámetros se realiza en **p\_parametro**.   
La desambiguación entre declaración de variable y función en el ámbito global se gestiona mediante **p\_marcar\_declaracion\_tipada** y **p\_resto\_tipado\_programa**.

Al declarar una función, las reglas **p\_inicio\_funcion\_void** y **p\_inicio\_funcion\_tipada** comprueban que ningún parámetro tenga un tipo inválido. A continuación invocan ***\_registrar\_firma\_funcion***, que busca en *self.functions* si ya existe una entrada con el mismo nombre y la misma lista de tipos de parámetros: si es así, se emite un error semántico por firma duplicada; en caso contrario, se añade como una nueva sobrecarga válida. 

Después de registrar la firma, se crea un nuevo ámbito local con los parámetros como entradas iniciales y se apila en *self.stack*. En este paso también se comprueba que no haya parámetros repetidos dentro de la misma función. Al salir de la función, **p\_fin\_funcion\_void** y **p\_fin\_funcion\_tipada** desapilan el ámbito local y limpian *self.current\_function*.

El lenguaje Lava permite así varias funciones con el mismo nombre siempre que difieran en número o tipo de parámetros. La recursión directa no está permitida, pero esta restricción no se debe a que la firma no exista todavía, sino a una comprobación explícita realizada en **p\_llamada**: si una función intenta invocarse a sí misma mientras su cuerpo se está analizando, se reporta un error semántico.

2. #### **Invocación y Resolución de Sobrecarga** {#invocación-y-resolución-de-sobrecarga}

La función implicada es **p\_llamada**.

Cuando se invoca una función, el parser realiza un proceso de resolución en varios pasos:

* **Se verifica que la función exista en la tabla de funciones** y que no se esté invocando desde su propio cuerpo (la recursión directa no está permitida).  
* **Se buscan todas las firmas con el mismo nombre cuyo número de parámetros coincida con el número de argumentos proporcionados.**  
* **Para cada firma candidata, se calcula el coste total de conversión** sumando el coste individual de cada argumento. Si un argumento no es convertible al tipo del parámetro correspondiente, esa firma se descarta.  
* **Se da prioridad a la firma con coincidencia exacta** (coste 0). Si no existe, se selecciona la firma con menor coste total de conversión.  
* **Si hay empate entre varias firmas** (ya sea por coincidencia exacta múltiple o por mismo coste mínimo), **se reporta un error de llamada ambigua**.


  3. #### **Validación de *return*** {#validación-de-return}

La función implicada es **p\_sentencia\_simple**, en la rama del token ***RETURN***, **p\_fin\_funcion\_tipada** y **p\_declaracion\_o\_funcion\_tipada**.

La regla **p\_sentencia\_simple** procesa las sentencias *return expr* en los contextos donde el lenguaje permite retorno. Cuando aparece un return, se comprueba en primer lugar que esté dentro de una función; si aparece fuera de cualquier función, se reporta un error semántico.

Si el return pertenece a una función con retorno tipado, se valida que el tipo de la expresión retornada sea compatible con el tipo declarado de la función, aplicando conversiones automáticas cuando sea necesario. Además, cada return correcto marca la función actual con el indicador *has\_return*.

La comprobación de que una función tipada contenga al menos un return no se resuelve en la propia sentencia, sino al finalizar el análisis de la función: **p\_fin\_funcion\_tipada** devuelve si se ha encontrado algún retorno y **p\_declaracion\_o\_funcion\_tipada** emite un error semántico si la función declarada exige valor de retorno y no se ha detectado ninguno.

En las funciones *void*, el uso de *return* con expresión no se trata aquí como un caso semántico adicional, ya que la gramática de los bloques void no admite ese tipo de sentencia.

5. ### **Controles Semánticos de Control de Flujo** {#controles-semánticos-de-control-de-flujo}

   1. #### **Condiciones en *if, while* y *do-while*** {#condiciones-en-if,-while-y-do-while}

Las funciones implicadas son **p\_sentencia\_if**, **p\_sentencia\_while** y **p\_sentencia\_do\_while** para el ámbito general.  
**p\_sentencia\_if\_void**, **p\_sentencia\_while\_void** y **p\_sentencia\_do\_while\_void** dentro de funciones *void*.

Las tres estructuras de control de flujo requieren que la expresión usada como condición sea de **tipo boolean**. No se admiten conversiones automáticas en este contexto: una expresión numérica como *5 / 7* no es válida como condición, aunque su valor sea distinto de cero. Si el tipo de la condición no es *boolean*, se reporta un error semántico indicando la estructura afectada y el tipo recibido.

Esta validación se centraliza en el método **\_condicion\_es\_valida:** 

```py
def _condicion_es_valida(self, expr, line, contexto):
    expr_type = 'error'
    if isinstance(expr, tuple) and len(expr) >= 2:
        expr_type = expr[0]

    if expr_type == 'boolean' or expr_type == 'unknown':
        return True

    if expr_type != 'error':
        self.has_semantic_error = True
        print(f"[ERROR SEMANTICO] Linea {line}: La condición de '{contexto}' "
              f"debe ser de tipo 'boolean' y recibió '{expr_type}'")
    return False
```

2. #### **Validación de *break*** {#validación-de-break}

Las funciones implicadas son **p\_sentencia\_simple** y **p\_sentencia\_simple\_void**, en la rama del token ***BREAK***.   
El control del nivel de anidamiento se realiza mediante **p\_entrar\_bucle** y **p\_salir\_bucle**.

La sentencia *break* solo es válida dentro del cuerpo de un bucle (*while* o *do-while*). Para controlar esto, el parser mantiene un contador *loop\_depth* que se incrementa al entrar en un bucle y se decrementa al salir. Si se encuentra un *break* con *loop\_depth* igual a cero, se reporta un error semántico. Este mecanismo permite el uso correcto de *break* dentro de bucles anidados y dentro de bloques *if* contenidos en un bucle.

Se destaca el siguiente fragmento de **p\_sentencia\_simple** que representa lo explicado**:** 

```py
if len(p) == 2 and p.slice[1].type == 'BREAK' and self.loop_depth <= 0: 
self.has_semantic_error = True 
print(f"[ERROR SEMANTICO] Linea {p.lineno(1)}: 'break' fuera de un bucle")
```

7. ## **Gestión de Errores Semánticos** {#gestión-de-errores-semánticos}

Cada vez que el parser detecta una violación semántica, activa el flag ***has\_semantic\_error*** e imprime un mensaje descriptivo por consola indicando el número de línea y la naturaleza del error. En lugar de detener inmediatamente la ejecución, el analizador intenta continuar el procesamiento del resto del programa siempre que la estructura sintáctica lo permita, devolviendo expresiones marcadas como *error* o finalizando únicamente la acción semántica de la regla afectada. De este modo, es posible acumular varios errores en una misma ejecución y ofrecer una salida de diagnóstico más completa.

*Fragmento representativo basado en la función **p\_declaracion\_o\_funcion\_tipada*****:**

```py
self.has_semantic_error = True
print(f"[ERROR SEMANTICO] Linea {line}: No se puede asignar tipo '{expr_type}' "
      f"a '{id_name}' de tipo '{type_name}'")
return
```

El flag ***has\_semantic\_error*** permite que el módulo ***main.py*** determine el resultado final del proceso sin necesidad de capturar excepciones específicas del análisis: si al terminar el parseo se ha detectado algún error sintáctico o semántico, el programa finaliza con código de salida 1; en caso contrario, exporta las tablas semánticas y, en esta versión final, también el fichero de cuartetos asociado al código intermedio.

Adicionalmente, el tipo especial ***unknown*** se utiliza como mecanismo de tolerancia semántica en aquellos puntos donde no conviene rechazar de forma prematura una construcción cuyo tipo no ha podido resolverse completamente. Así, en lugar de propagar automáticamente un *error*, ciertas reglas permiten continuar el análisis con *unknown*, reduciendo la aparición de falsos positivos encadenados y haciendo el comportamiento del analizador más robusto frente a errores parciales previos.

8. ## **Diseño Parte Opcional** {#diseño-parte-opcional}

   1. ### **Formato Fichero .quartets** {#formato-fichero-.quartets}

La salida intermedia se escribe en un fichero con la misma base que el programa fuente y extensión *.quartets*. Cada línea contiene exactamente cuatro campos separados por comas: ***OPERADOR,ARG1,ARG2,RESULT***   
Cuando un operador no usa alguno de los campos, se escribe ***\_***. Los booleanos se serializan como *true* y *false*, los caracteres se representan entre comillas simples escapando los casos necesarios y los temporales y etiquetas siguen la convención *@T1, @T2, ... y @L1, @L2, ...* 

2. ### **Cobertura de Instrucciones** {#cobertura-de-instrucciones}

La implementación genera cuartetos para:

* asignaciones a variables simples (**ASSIGN**).   
* operaciones binarias aritméticas (**ADD, SUB, MUL, DIV**).  
*  comparaciones (**GT, GTE, LT, LTE, EQ**).  
* operaciones lógicas (**AND, OR**).   
* operadores unarios (**NOT, UMINUS, UPLUS**).   
* conversiones explícitas (**CHAR\_TO\_INT, INT\_TO\_FLOAT**).   
* control de flujo (**JUMPF, JUMPT, JUMP, LABEL**).  
* impresión (**PRINT**).  
* invocaciones a función (**CALL**). 


  3. ### **Marcadores de Producción para Control de Flujo** {#marcadores-de-producción-para-control-de-flujo}

Para poder emitir cuartetos de salto y etiquetas en los puntos exactos del análisis, se introduce un conjunto de reglas de producción vacías llamadas marcadores. Estas reglas no consumen ningún token ni tienen semántica propia: su único propósito es ejecutar acciones de codegen en momentos precisos dentro de la reducción LALR. Las producciones de las sentencias de control existentes se amplían para incluirlos.

**p\_if\_mark** se inserta en la gramática justo después de haber evaluado la condición del *if* y antes de entrar en el bloque *then*. En ese momento ya se dispone de la referencia de la condición, por lo que la función la extrae con **\_extraer\_expr**, genera dos nuevas etiquetas (*else\_label* y *end\_label*), las apila en ***\_if\_codegen\_stack*** y emite el salto condicional **JUMPF** hacia la etiqueta del else. Si no existe rama *else*, ese salto apuntará directamente al final del *if*.

**p\_else\_mark** y **p\_if\_end\_mark** trabajan en pareja para cerrar la estructura del *if*. **p\_else\_mark** se activa al inicio de la rama *else*: emite un salto incondicional **JUMP** al final del if para cerrar la rama *then*, y a continuación coloca la etiqueta **LABEL** del *else*. **p\_if\_end\_mark** se activa al terminar toda la sentencia *if*: si hubo else, emite la etiqueta de fin *end\_label*; si no hubo else, emite la etiqueta *else\_label* como punto de convergencia, ya que en ese caso ambas etiquetas son equivalentes. Ambas funciones consultan y modifican el contexto almacenado en ***\_if\_codegen\_stack***.

**p\_while\_start** y **p\_while\_end** flanquean el bucle *while*. **p\_while\_start** se reduce antes de evaluar la condición: genera *start\_label* y *end\_label*, apila el contexto en ***\_loop\_codegen\_stack*** y emite la etiqueta de entrada **LABEL** *start\_label*. Esto garantiza que el salto de retorno al final del cuerpo tenga siempre un destino correcto. **p\_while\_end** se reduce tras ejecutar el cuerpo: desapila el contexto, emite el salto incondicional **JUMP** de vuelta a *start\_label* y coloca la etiqueta de salida **LABEL** *end\_label*. Existe además **p\_while\_cond\_mark**, que se inserta entre la condición y el cuerpo y emite el salto condicional **JUMPF** hacia *end\_label* en caso de que la condición sea falsa.

**p\_do\_start** y **p\_do\_end** cumplen la misma función para el bucle *do-while*, con la diferencia de que la condición se evalúa al final. *p\_do\_start* se reduce al inicio, antes del cuerpo: genera las etiquetas y emite **LABEL** start\_label. **p\_do\_end** se reduce después de evaluar la condición de cierre: extrae su referencia, emite un **JUMPT** de retorno al inicio si la condición es verdadera y coloca la etiqueta de salida **LABEL** *end\_label*.

4. # **Batería de Pruebas** {#batería-de-pruebas}

## Objetivo

Se han diseñado nueve ficheros de entrada `.lava` que ejercen de forma exhaustiva todas las funcionalidades implementadas en el compilador: tipos primitivos, literales en múltiples notaciones, expresiones con conversiones automáticas, estructuras de control, registros simples y anidados, funciones tipadas y `void`, sobrecarga de funciones y casos límite del lexer. Todos los ficheros compilan sin errores, lo que garantiza que cada ejecución produce los cuatro ficheros de salida exigidos.

## Estructura de directorios

```
/pruebas
├── /input          ← ficheros .lava de entrada
└── /output
    ├── /records    ← ficheros .records de cada ejecución
    ├── /functions  ← ficheros .functions de cada ejecución
    ├── /symbols    ← ficheros .symbols de cada ejecución
    └── /quatests   ← ficheros .quartets de cada ejecución
```

Para ejecutar una prueba manualmente:

```
python main.py pruebas/input/XX_<nombre>.lava
```

Los cuatro ficheros de salida se generan junto al fichero de entrada (mismo directorio y mismo nombre base).

## Tabla de cobertura

| Fichero | Funcionalidades probadas | `.records` | `.functions` |
|---------|--------------------------|-----------|-------------|
| `01_tipos_y_literales.lava` | 4 tipos primitivos; enteros dec/bin/oct/hex; float con punto y notación científica; `true`/`false`; multi-declaración; declaración + inicialización; `print` de cada tipo | vacío | vacío |
| `02_expresiones_y_conversiones.lava` | `+ - * /` binarios; unarios `- + !`; comparativos; lógicos `&& \|\| !`; conversiones `char→int`, `char→float`, `int→float`; `==` permisivo; precedencia y paréntesis | vacío | vacío |
| `03_control_flujo.lava` | `if` simple; `if-else`; `if` anidado; `while`; `do-while`; `break` en `while` y `do-while`; condición compuesta | vacío | vacío |
| `04_registros.lava` | `record` con tipos explícitos; herencia de tipo entre campos consecutivos; `new`; acceso a campo; asignación a campo; record sin inicializar (valores por defecto); tipos mixtos | **lleno** | vacío |
| `05_registros_anidados.lava` | Registro con campo de tipo registro; acceso encadenado `a.b.c`; asignación a campo anidado; `new` anidado como argumento de otro `new` | **lleno** | vacío |
| `06_funciones.lava` | Funciones tipadas con `return`; funciones `void`; múltiples parámetros; variables locales; llamada como expresión y como sentencia; `print` dentro de función; función con `while` interno | vacío | **lleno** |
| `07_sobrecarga.lava` | Sobrecarga por tipo (`int` vs `float`); sobrecarga por aridad; resolución exacta; resolución por coste mínimo (`char→int` < `char→float`) | vacío | **lleno** |
| `08_integracion.lava` | Registros anidados + funciones con parámetro de tipo registro + `while`/`do-while` + `if-else` + sobrecarga | **lleno** | **lleno** |
| `09_casos_limite.lava` | Comentarios `//` y `/* */` multilínea; `;` múltiples entre sentencias; paréntesis profundamente anidados; distintos valores `char` ASCII; `if` con condición compuesta | vacío | vacío |

## Análisis de resultados

### Ficheros `.symbols`

Los tests **01, 02, 04, 05 y 09** no contienen estructuras de control ni definiciones de función, por lo que el compilador exporta la tabla de símbolos en formato `nombre:tipo,valor`. Por ejemplo, `01_tipos_y_literales.symbols` refleja los cuatro enteros con valor `495` (todas las notaciones dec/bin/oct/hex encodifican el mismo número), los flotantes con su valor decimal final y las variables sin inicializar con el valor por defecto de su tipo (`0`, `0.0`, `''`, `false`).

Los tests **03, 06, 07 y 08** contienen control de flujo y/o funciones, por lo que los símbolos se exportan solo con tipo (`nombre:tipo`), ya que sus valores no son deterministas en tiempo de compilación.

### Ficheros `.records`

Solo los tests que declaran `record` generan ficheros no vacíos:

- **04** muestra cuatro registros (`Punto`, `Eje`, `Mezcla`, `Stats`) con la herencia de tipo resuelta. `Eje:[x1:float,x2:float]` confirma que `x2` hereda el tipo `float` de `x1`.
- **05** muestra registros con campos de tipo registro: `Segmento:[inicio:Vec2,fin:Vec2]`, verificando que los tipos compuestos se serializan correctamente en la tabla.
- **08** combina registros anidados con funciones que los reciben como parámetro: `Rectangulo:[origen:Vec2,esquina:Vec2]`.

### Ficheros `.functions`

Solo los tests con definiciones de función generan ficheros no vacíos:

- **06** registra las 7 firmas distintas con sus parámetros y tipo de retorno, incluyendo `factorial:[n:int],int`.
- **07** registra las 7 variantes de las tres funciones sobrecargadas (`calcular`, `imprimir`, `combinar`), validando que la tabla acumula todas las firmas por nombre. Por ejemplo: `calcular:[x:float],float` y `calcular:[x:int],int` coexisten.
- **08** valida que las dos sobrecargas de `area` coexisten: `area:[r:Rectangulo],float` y `area:[a:float,b:float],float`.

### Ficheros `.quartets`

- **02** genera instrucciones `CHAR_TO_INT` e `INT_TO_FLOAT` para las conversiones automáticas, confirmando que el compilador emite las instrucciones de conversión explícitas en el código intermedio.
- **03** genera `JUMPF`, `JUMP` y `LABEL` para los `if`/`else` y `while`, y `JUMPT` con `LABEL` para el `do-while`, confirmando la generación correcta de saltos condicionales e incondicionales y el uso de etiquetas `@L#`.
- **06** genera instrucciones `CALL` para cada invocación de función, validando la interacción entre el análisis semántico y la generación de código intermedio.
- **07** valida la resolución de sobrecarga a nivel de cuartetos: la llamada `calcular('A')` produce `CHAR_TO_INT` pero no `INT_TO_FLOAT`, confirmando que se eligió la versión `int` (coste 1) frente a la `float` (coste 2).
- **08** combina todas las instrucciones anteriores en un programa realista: `ASSIGN`, `ADD`, `MUL`, `JUMPF`, `LABEL`, `JUMP`, `JUMPT`, `CALL` y conversiones de tipo aparecen en el mismo fichero, ejerciendo la interacción entre todas las features.
- **09** confirma que las instrucciones `PRINT` se emiten también en presencia de expresiones con paréntesis profundamente anidados, validando que la precedencia no rompe la generación de cuartetos.

## Conclusión

Los nueve tests demuestran que el compilador procesa correctamente todo el espectro del lenguaje Lava. Cada fichero está diseñado para ser mínimo pero exhaustivo dentro de su área: ningún test duplica el trabajo de otro y, en conjunto, cubren todas las reglas semánticas, todos los operadores, todas las conversiones automáticas y toda la variedad de instrucciones de código intermedio definidas en el enunciado. El test de integración (08) valida además que las features interaccionan correctamente entre sí sin introducir regresiones.

5. # **Conclusiones** {#conclusiones}

La práctica se ha completado cumpliendo los objetivos previstos de la tercera entrega: se ha implementado un **analizador semántico** integrado en el parser de Lava, capaz de detectar y reportar errores de tipo, redeclaración de variables, uso incorrecto de sentencias de control y validación de firmas de funciones. Además, se ha desarrollado la **parte opcional de generación de código intermedio**, incorporando la emisión de cuartetos dentro del propio analizador sintáctico-semántico.

Entre las **decisiones de diseño adoptadas**, destaca la **gestión de la pila de ámbitos** mediante una lista de diccionarios apilables, lo que permite modelar correctamente el alcance léxico del lenguaje y separar de forma natural variables globales y locales. También resulta especialmente relevante la **ampliación de la representación interna de las expresiones** a la forma **(tipo, valor, ref)**, ya que permite combinar en una misma estructura la información necesaria para el análisis semántico y para la generación de cuartetos.

En cuanto a la **resolución de sobrecarga**, la selección de firma basada en el coste mínimo de conversión permite un comportamiento coherente con el enunciado: se priorizan siempre las coincidencias exactas y solo en su ausencia se consideran conversiones automáticas compatibles.

La validación se ha realizado mediante una **batería de pruebas** de nueve ficheros `.lava`, detallada en la sección correspondiente, que cubre de forma sistemática todos los tipos primitivos, los operadores y sus conversiones automáticas, las estructuras de control, los registros simples y anidados, las funciones con y sin sobrecarga, y casos límite del lexer.

En conjunto, el compilador de Lava queda en un estado final completo y coherente: no sólo verifica la corrección semántica de los programas, sino que además genera una representación intermedia en forma de cuartetos, lo que refuerza el carácter integral de la solución desarrollada.

# **ANEXO. Declaración de Uso de Inteligencia Artificial** {#anexo.-declaración-de-uso-de-inteligencia-artificial}

Durante el desarrollo de esta práctica, se emplearon herramientas de IA generativa exclusivamente como apoyo técnico. El diseño, la implementación del código fuente y la toma de decisiones recaen íntegramente en los estudiantes.

**Uso de Perplexity AI**  
Perplexity AI se empleó como herramienta de consulta y apoyo en los siguientes ámbitos:

* **Diseño de acciones semánticas:** consulta de estrategias para integrar la lógica semántica dentro de las reglas de producción de PLY sin introducir conflictos LALR ni efectos secundarios indeseados.  
* **Gestión de ámbitos y pila de contextos:** apoyo para definir el modelo de pila de ámbitos más adecuado para el alcance léxico del lenguaje Lava, incluyendo la creación y destrucción de ámbitos en la entrada y salida de funciones.  
* **Resolución de sobrecarga de funciones:** consulta sobre estrategias de resolución de sobrecarga basadas en coste de conversión, para determinar qué firma seleccionar cuando múltiples candidatas son compatibles con los argumentos de una llamada.  
* **Apoyo en la batería de pruebas:** ayuda en la elaboración de casos de prueba variados que cubrieran los casos límite adecuados.

**Uso de Claude Opus 4.6**  
Se empleó para la revisión del código, detección de inconsistencias y como apoyo directo en la implementación de funcionalidades avanzadas:

* **Corrección en \_convertir\_numero:** se añadió una comprobación previa para capturar el caso de char vacío ('') antes de invocar *ord()*, evitando un error en tiempo de ejecución por longitud inválida.  
* **Herencia de tipo en campos de registro:** se habilitó la herencia de tipo entre campos consecutivos de un registro (por ejemplo, *record Point(float x1, x2)*), de modo que **campo\_record\_item** acepta tanto tipo *ID* como *ID* solo, y **p\_declaracion\_record** resuelve los tipos *None* con el último tipo explícito visto en la lista.  
* **Implementación de la parte opcional (Generación de código intermedio):** La IA asistió en el diseño e integración de la fase de generación de código intermedio mediante cuartetos. Ayudó a estructurar la emisión de estas instrucciones (operador, operandos y resultado) directamente dentro del analizador sintáctico-semántico, facilitando la correcta gestión de temporales, etiquetas y saltos de control de flujo.


**Verificación y Responsabilidad**  
Las respuestas de ambas herramientas se utilizaron únicamente como referencia. Toda sugerencia fue sometida a revisión crítica, análisis frente a las especificaciones del lenguaje Lava y validación funcional. El uso de IA no ha sustituido el proceso de aprendizaje, y los estudiantes pueden explicar y defender todas las decisiones de código adoptadas.

[image1]: <data:image/png;base64,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>