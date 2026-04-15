#!/usr/bin/env python3
# -*- coding: utf-8 -*-
 
import sys
import os
from lexer import LexerClass
from parser import ParserClass

def generar_fichero_token(entrada: str, data: str):
    """Genera el fichero .token ejecutando solo el lexer."""
    # Construye el nombre del fichero de salida a partir del .lava de entrada.
    output_entrada = os.path.splitext(entrada)[0] + ".token"

    # Crea una instancia del lexer y le pasa el contenido a analizar.
    lexer_obj = LexerClass()
    lexer_obj.input(data)

    try:
        # Abre el fichero de salida en modo escritura.
        with open(output_entrada, 'w', encoding='utf-8') as out:
            # Escribe la cabecera exigida en la práctica.
            out.write("// { TIPO, VALOR, LÍNEA, COLUMNA-INICIO, COLUMNA-FIN }\n")

            # Consume tokens hasta que el lexer no devuelva más.
            while True:
                tok = lexer_obj.lexer.token()
                if not tok:
                    break

                # Usa el valor original del token si existe; si no, usa tok.value.
                original = getattr(tok, 'original', tok.value)

                # Recupera columnas precalculadas si el lexer las guardó.
                # Si no existen, calcula la columna inicial a partir de lexpos.
                col_inicial = getattr(
                    tok,
                    'col_start',
                    lexer_obj.find_column(data, tok.lexpos)
                )

                # Recupera la columna final si ya está almacenada.
                # Si no, la estima como columna inicial + longitud del lexema.
                col_final = getattr(
                    tok,
                    'col_end',
                    col_inicial + len(str(original))
                )

                # Escribe una línea por token con el formato de salida adecuado.
                out.write(
                    f"{tok.type}, {original}, {tok.lineno}, "
                    f"{col_inicial}, {col_final}\n"
                )

    except OSError as e:
        # Error al crear o escribir el fichero .token.
        print(f"Error al escribir el archivo '{output_entrada}': {e}", file=sys.stderr)
        sys.exit(1)

def main():
    """Lee el fichero de entrada y ejecuta lexer o parser según el modo."""
    
    # 1) Validar argumentos
    if len(sys.argv) not in (2, 3):
        print("Uso: python main.py <nombre_fichero.lava>")
        print("Uso: python main.py --token <nombre_fichero.lava>")
        sys.exit(1)

    # Por defecto, se ejecuta el parser.
    modo_token = False

    # 2) Si hay 3 argumentos: validar que el modo sea correcto y extraer el nombre del fichero.
    if len(sys.argv) == 3:
        # Se valida que el modo sea --token o -token, y se extrae el nombre del fichero.
        if sys.argv[1] in ('--token', '-token'):
            modo_token = True
            entrada = sys.argv[2]
        else:
            print("Uso: python main.py --token <nombre_fichero.lava>")
            sys.exit(1)
    else:
        entrada = sys.argv[1]
    
    # 3) Validar que el fichero existe 
    if not os.path.exists(entrada):
        print(f"Error: El archivo '{entrada}' no existe o no es un fichero.")
        sys.exit(1)
    
    # 4) Validar que el fichero tiene extensión .lava
    if not entrada.endswith('.lava'):
        print(f"Error: El archivo debe tener extensión .lava")
        sys.exit(1)
    
    # 5) Leer el contenido del fichero
    try:
        with open(entrada, 'r', encoding='utf-8') as f:
            data = f.read()
    except OSError as e:
        print(f"Error al leer el archivo '{entrada}': {e}")
        sys.exit(1)

    # 6) Modo lexer: generar el fichero .token y salir
    if modo_token:
        generar_fichero_token(entrada, data)
        return

    # 7) Inicializar el parser y analizar
    try:
        parser = ParserClass()
        parser.parse(data)

        # Si el parser ha marcado que hubo error sintáctico, termina con código de error.
        if parser.has_syntax_error:
            sys.exit(1)

    except Exception as e:
        # Captura errores inesperados al crear o ejecutar el parser.
        print(f"Error al inicializar el parser: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    # Punto de entrada del programa
    main()
