# Compilador Lava

Proyecto académico de la asignatura **Procesadores del Lenguaje** centrado en la construcción de un front-end de compilador para el lenguaje **Lava**. La implementación incluye análisis léxico, análisis sintáctico, análisis semántico y generación de código intermedio en formato de cuartetos.

El objetivo del proyecto es validar programas escritos en Lava, detectar errores sintácticos y semánticos, construir las tablas internas del compilador y exportar una representación intermedia útil para fases posteriores de compilación.

## Autores

- Álvaro García González
- Samuel Gómez Fernández

## Tecnologías utilizadas

- **Python 3**
- **PLY** (`ply.lex` y `ply.yacc`)
- Gramáticas LALR
- Tablas de símbolos
- Análisis semántico
- Generación de código intermedio mediante cuartetos

## Funcionalidades principales

### Analizador léxico

El fichero `lexer.py` define el analizador léxico del lenguaje Lava. Reconoce:

- Palabras reservadas: `int`, `float`, `char`, `boolean`, `void`, `return`, `if`, `else`, `do`, `while`, `print`, `new`, `record`, `break`, `true` y `false`.
- Identificadores.
- Literales enteros en decimal, binario, octal y hexadecimal.
- Literales `float`, incluyendo notación científica.
- Literales `char`, incluyendo secuencias de escape.
- Operadores aritméticos, lógicos y comparativos.
- Comentarios de una línea (`//`) y multilínea (`/* ... */`).
- Posición de cada token: línea, columna inicial y columna final.

Además, el compilador puede ejecutarse en modo léxico para generar un fichero `.token` con el flujo de tokens reconocido.

### Analizador sintáctico

El fichero `parser.py` implementa la gramática del lenguaje Lava con PLY. El parser reconoce:

- Declaraciones de variables.
- Asignaciones.
- Expresiones aritméticas, lógicas y comparativas.
- Precedencia y asociatividad de operadores.
- Bloques de código.
- Sentencias `if`, `if-else`, `while` y `do-while`.
- Sentencias `break`, `return` y `print`.
- Definición e instanciación de registros (`record` y `new`).
- Acceso a campos simples y anidados.
- Declaración y llamada a funciones.
- Funciones `void` y funciones tipadas.
- Sobrecarga de funciones por tipo y número de parámetros.

### Analizador semántico

El análisis semántico está integrado en el parser y valida, entre otros aspectos:

- Uso de variables declaradas.
- Redeclaraciones en el mismo ámbito.
- Compatibilidad de tipos en asignaciones.
- Conversión automática permitida entre `char`, `int` y `float`.
- Condiciones booleanas en estructuras de control.
- Uso correcto de `break` dentro de bucles.
- Uso correcto de `return` según el tipo de la función.
- Existencia y compatibilidad de registros.
- Acceso correcto a campos de registros.
- Existencia de funciones.
- Resolución de sobrecarga mediante coste mínimo de conversión.

Para gestionar el alcance léxico, el parser utiliza una pila de ámbitos. El ámbito global almacena las variables globales y, al entrar en una función, se crea un ámbito local con sus parámetros y variables internas.

### Generación de código intermedio

Como parte opcional de la práctica, el proyecto genera código intermedio en formato de cuartetos. Cada instrucción tiene la forma:

```text
OPERADOR,ARG1,ARG2,RESULT
```

Ejemplo:

```text
ADD,a1,a2,@T15
ASSIGN,@T15,_,areaTotal
JUMPF,cuad1,@L1,_
PRINT,a1,_,_
```

El generador emite instrucciones para:

- Asignaciones: `ASSIGN`
- Operaciones aritméticas: `ADD`, `SUB`, `MUL`, `DIV`
- Comparaciones: `GT`, `GTE`, `LT`, `LTE`, `EQ`
- Operaciones lógicas: `AND`, `OR`, `NOT`
- Operadores unarios: `UMINUS`, `UPLUS`
- Conversiones: `CHAR_TO_INT`, `INT_TO_FLOAT`
- Control de flujo: `JUMPF`, `JUMPT`, `JUMP`, `LABEL`
- Impresión: `PRINT`
- Llamadas a función: `CALL`

Los temporales siguen la convención `@T1`, `@T2`, etc. Las etiquetas siguen la convención `@L1`, `@L2`, etc.

## Estructura del repositorio

```text
.
|-- lexer.py
|-- parser.py
|-- main.py
|-- P3_memoria.pdf
`-- pruebas
    |-- input
    |   |-- 01_tipos_y_literales.lava
    |   |-- 02_expresiones_y_conversiones.lava
    |   |-- 03_control_flujo.lava
    |   |-- 04_registros.lava
    |   |-- 05_registros_anidados.lava
    |   |-- 06_funciones.lava
    |   |-- 07_sobrecarga.lava
    |   |-- 08_integracion.lava
    |   `-- 09_casos_limite.lava
    `-- output
        |-- functions
        |-- quartets
        |-- records
        `-- symbols
```

## Instalación

Clona el repositorio e instala la dependencia principal:

```bash
pip install ply
```

Opcionalmente, puedes crear un entorno virtual:

```bash
python -m venv venv
source venv/bin/activate
pip install ply
```

En Windows:

```powershell
python -m venv venv
.\venv\Scripts\activate
pip install ply
```

## Uso

### Ejecutar el compilador completo

```bash
python main.py pruebas/input/08_integracion.lava
```

Si el programa es válido, se generan ficheros con la misma base que el archivo de entrada:

- `.symbols`: tabla de símbolos.
- `.records`: tabla de registros.
- `.functions`: tabla de funciones.
- `.quartets`: código intermedio.

### Ejecutar solo el analizador léxico

```bash
python main.py --token pruebas/input/01_tipos_y_literales.lava
```

Este modo genera un fichero `.token` con el listado de tokens reconocidos.

## Ejemplo de programa Lava

```c
record Vec2(float x, y);
record Rectangulo(Vec2 origen, Vec2 esquina);

float area(float a, float b) {
    return a * b;
}

Rectangulo r = new Rectangulo(new Vec2(0.0, 0.0), new Vec2(4.0, 4.0));
float resultado = area(3.0, 5.0);
print(resultado);
```

## Ficheros de salida

### Tabla de símbolos

Ejemplo de salida `.symbols`:

```text
decimal:int,495
fPunto:float,3.14
cLetra:char,a
bVerdad:boolean,true
```

### Tabla de registros

Ejemplo de salida `.records`:

```text
Vec2:[x:float,y:float]
Segmento:[inicio:Vec2,fin:Vec2]
Triangulo:[a:Vec2,b:Vec2,c:Vec2]
```

### Tabla de funciones

Ejemplo de salida `.functions`:

```text
calcular:[x:float],float
calcular:[x:int],int
combinar:[a:int,b:float],float
combinar:[a:float,b:float],float
```

### Código intermedio

Ejemplo de salida `.quartets`:

```text
CALL,area,2,@T23
ASSIGN,@T23,_,aEscalar
PRINT,aEscalar,_,_
```

## Batería de pruebas

El directorio `pruebas/input` contiene nueve programas `.lava` diseñados para cubrir las principales características del lenguaje:

| Fichero | Cobertura principal |
| --- | --- |
| `01_tipos_y_literales.lava` | Tipos primitivos, literales y declaraciones múltiples |
| `02_expresiones_y_conversiones.lava` | Operadores, precedencia y conversiones automáticas |
| `03_control_flujo.lava` | `if`, `if-else`, `while`, `do-while` y `break` |
| `04_registros.lava` | Registros simples, campos y valores por defecto |
| `05_registros_anidados.lava` | Registros anidados y acceso encadenado |
| `06_funciones.lava` | Funciones tipadas, funciones `void`, parámetros y llamadas |
| `07_sobrecarga.lava` | Sobrecarga por aridad y por tipo |
| `08_integracion.lava` | Integración de registros, funciones, control de flujo y sobrecarga |
| `09_casos_limite.lava` | Comentarios, paréntesis anidados y casos límite del lexer |

Las salidas esperadas se incluyen en `pruebas/output`, separadas por tipo de artefacto.

## Decisiones de diseño destacadas

- **Parser y semántica integrados**: las acciones semánticas se ejecutan durante la reducción de reglas gramaticales.
- **Pila de ámbitos**: permite distinguir variables globales, parámetros y variables locales.
- **Representación interna de expresiones**: cada expresión se representa como `(tipo, valor, referencia)`, combinando información semántica y de generación de código.
- **Conversión automática controlada**: se permiten conversiones `char -> int`, `int -> float` y `char -> float`.
- **Resolución de sobrecarga por coste**: se priorizan coincidencias exactas y, si no existen, la firma con menor coste de conversión.
- **Cuartetos integrados en el análisis**: las instrucciones intermedias se generan al mismo tiempo que se valida semánticamente el programa.

## Estado del proyecto

El proyecto implementa un front-end completo para Lava dentro del alcance de la práctica:

- Analizador léxico funcional.
- Parser con gramática completa.
- Validaciones semánticas.
- Tablas semánticas exportables.
- Generación de código intermedio.
- Batería de pruebas con salidas esperadas.

Este repositorio muestra competencias en diseño de compiladores, gramáticas formales, análisis semántico, estructuras de datos para lenguajes de programación y generación de representaciones intermedias.
