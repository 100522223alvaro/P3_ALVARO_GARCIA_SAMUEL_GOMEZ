Tenemos que terminar esta práctica. 

- tienes el enunciado en @Práctica-_-Lava-Procesadores-del-Lenguaje-v3.txt

- tienes lo que llevamos de memoria en @P3_memoria.md

## Nos falta hacer, según mi compañero: 

Instrucciones para la Batería de Pruebas y Memoria (Práctica de Procesadores)
Contexto General:
El código final del proyecto ya está subido al repositorio. El objetivo de esta tarea es diseñar una batería de pruebas exhaustiva para el lenguaje .lava, organizar correctamente los ficheros generados y redactar la documentación correspondiente para la memoria.

1. Estructura de Directorios Requerida (ya he creado las carpetas)

Crea exactamente la siguiente jerarquía de carpetas en el proyecto para mantener el orden de las pruebas:

Plaintext
/pruebas
├── /input
└── /output
    ├── /records
    ├── /functions
    ├── /symbols
    └── /quatests
2. Generación y Ejecución de Pruebas

Diseño de Inputs: Crea diferentes archivos de entrada (.lava) diseñados para probar a la perfección todas las funcionalidades, rutas y posibles casos límite del código. Guarda todos estos archivos en la carpeta /pruebas/input.

Ejecución de Código: Ejecuta el archivo main utilizando cada uno de los inputs generados.

Nota importante: No es necesario crear ningún script de automatización (como bash o Makefiles) para ejecutar las pruebas.

3. Organización de Resultados (Outputs)
Por cada ejecución de un archivo .lava, el programa generará 4 ficheros de salida. Debes encargarte de guardar y clasificar cada uno en su subcarpeta correspondiente dentro de /pruebas/output/:

Los ficheros de registros ➔ /records

Los ficheros de funciones ➔ /functions

Los ficheros de tabla de símbolos ➔ /symbols

Los ficheros de cuádruplas/tests ➔ /quatests

4. Documentación (Memoria)
Una vez generados, ejecutados y organizados los tests, redacta una explicación clara y detallada de la batería de pruebas realizada. Debes justificar qué casos se han probado y cómo demuestran que el código funciona correctamente, dejándolo listo para incluir en la memoria final de la práctica.

