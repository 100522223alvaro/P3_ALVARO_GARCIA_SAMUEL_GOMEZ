import ply.yacc as yacc
from lexer import LexerClass

class ParserClass:
    symbols = {}
    default_types = {
        'int':0,
        'float':0.0,
        'bool':False
    }
    
    tokens = LexerClass.tokens
    
    precedence = (
        ("left","PLUS","MINUS"),
        ("right","UPLUS","UMINUS")
    )
    
    def __init__(self):
        self.parser = yacc.yacc(module=self)
        self.lexer = LexerClass().lexer
        
    start = 'program'
    
    def p_program(self,p):
        '''program : program sentence SEMICOLON
                    | sentence SEMICOLON'''
        print('program')
    
    def p_sentence(self, p):
        '''sentence : expression 
                    | declaration
                    | assign'''
        print('sentence')
        
        
    def p_binary_expression(self, p):
        '''expression : expression PLUS expression
                      | expression MINUS expression'''
        operator, expression_1, expression_2 = p[2], p[1], p[3]
        if expression_1[0] == 'bool' or expression_2[0] == 'bool':
            print("ERROR SEMTANTICO: No se puede operar con booleanos")
            exit()
        
        out_type = expression_1[0]
        if expression_1[0] != expression_2[0]:
            out_type = 'float'
        if operator == "-":
            p[0] = (out_type,expression_1[1]-expression_2[1])
        elif operator == "+":
            p[0] = (out_type,expression_1[1]+expression_2[1])
            
        print("binary_expression")
    
    def p_unary_expression(self, p):
        '''expression : PLUS expression %prec UMINUS
                      | MINUS expression %prec UPLUS'''
        operator, expression = p[1], p[2]
        if expression[0] == 'bool':
            print("ERROR SEMTANTICO: No se puede operar con booleanos")
            exit()
        if operator == "-":
            p[0] = (expression[0],-expression[1])
        elif operator == "+":
            p[0] = expression
        print("unary_expression")
        
    # ----------------- Expr terminales ------------------
    def p_literal_int_expression(self,p):
        '''expression : INT_VALUE'''
        p[0] = ('int', p[1])
        print("literal_int_expression: ",p[0])
    
    def p_literal_float_expression(self,p):
        '''expression : FLOAT_VALUE'''
        p[0] = ('float', p[1])
        print("literal_float_expression: ",p[0])
    
    def p_literal_bool_expression(self,p):
        '''expression : TRUE
                      | FALSE'''
        p[0] = ('bool', p[1])
        print("literal_bool_expression: ",p[0])
    
    def p_literal_id_expression(self,p):
        '''expression : ID'''
        if p[1] not in self.symbols:
            print("ERROR SEMTANTICO: ", p[1], " no ha sido declarada previamente")
            exit()
        p[0] = self.symbols[p[1]]
        print("literal_id_expression: ",p[0])
    
    # ----------------------------------------------------
    
    def p_declaration(self, p):
        '''declaration : VAR ID COLON type'''
        if p[2] in self.symbols:
            print("ERROR SEMTANTICO: ", p[2], " Ya ha sido declarada")
            exit()
        self.symbols[p[2]] = (p[4],self.default_types[p[4]])
        print(f"declaracion de {p[2]} a tipo {p[4]}")
    
    def p_assign(self, p):
        '''assign : ID ASSIGN expression'''
        id_name,expression = p[1],p[3]
        if id_name not in self.symbols:
            print("ERROR SEMTANTICO: ", id_name, " no ha sido declarada previamente")
            exit()
        symbol = self.symbols[id_name]
        if symbol[0] != expression[0]:
            print("ERROR SEMTANTICO: ", id_name, "no es del tipo", expression[0])
            exit()
        # print("simbolo y expresion:", symbol[1], expression[1])
        self.symbols[id_name] = expression
        print(f"asignacion de '{id_name}' a {expression[1]}")
    
    def p_type(self,p):
        '''type : FLOAT
                | INT
                | BOOL'''
        p[0] = p[1]
        print("type")
    
    def p_error(self,p):
        print(f"Error sintactico con {p}")
    
    def test(self,data:str):
        self.parser.parse(data)
    
    def parse_file(self,path):
        if not path:
            path = "input"
        try:
            with open(path,"r") as file:
                self.parser.parse(file.read())
        except FileNotFoundError:
            print("ERROR: Fichero no encontrado")
        except Exception as e:
            print("ERROR: error inesperado:", e)
        print(self.symbols)