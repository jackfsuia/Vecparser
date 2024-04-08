import re
from pymatlabparser.matlab_lexer import MatlabLexer
from sly.lex import Token 

class Variable:
##"vasdsd(dwa,sd,aww)"
    def __init__(self,token_list:list[Token], index:list[str]=None, is_constant=False ) -> None:

        self.token_list=token_list
        self.index = index
        self.is_constant = is_constant
        if index==[]:
            self.is_constant = True

    def start_parsing(self):

        if self.index != None:#if has index, dont parses
            return self
        
        elif len(self.token_list)==1:
            self.is_constant = True
            self.index=[]
            return self

        elif self.is_atom:
            self.index = self.atom_index
            self.token_list = [self.token_list[0]]
            return self
        
        else :#composite
            self= expression_parser(self)

        return self

    @property
    def name(self):
        name=''
        for token in self.token_list:
            name+=token.value
        return name
  
    
    @property
    def is_atom(self):

        if self.token_list[0].type=='NAME' and self.token_list[1].value == '(' and self.token_list[-1].value == ')':
            r_paren = 0
            for token in self.token_list:
                # right parens can be more than 1
                if token.value=='(':
                    r_paren+=1
            if r_paren == 1:
                return True
        return False
    
    @property
    def atom_index(self):
        index = []
        for token in self.token_list[2:]:
            if token.type == 'NAME':
                index.append(token.value)
        return index
    
    def __str__(self):
        return self.name


def expand(x:Variable, target_order:list[str]=None,)->Variable:
    if x.is_constant:
        return x
    if len(x.index) == len(target_order):
        return x
    len_of_original=len(x.index)
    idx_max = []
    for target_idx in target_order:
        if target_idx not in x.index:
            idx_max.append(loop_bounds[target_idx])
            x.index.append(target_idx)

    fake_x='x'
    result = f"repmat({fake_x}"+',1'*len_of_original
    for im in idx_max:
        result += f",{im}"
    result += ")"
    tokens = MatlabLexer().tokenize(result)
    token_list=[token for token in tokens]
    x.token_list=token_list[0:2]+x.token_list+token_list[3:]
    return x


def permute(x:Variable, target_order:list[str]=None)->Variable:
    if x.is_constant:
        return x
    idx = x.index  ## ['n','m','k'...]
    if len(idx) != len(target_order):
        raise Exception("permute failed: len(idx) != len(order)")
    if idx == target_order:
        return x
    pos_dict = dict(zip(idx, list(range(1,len(idx)+1))))
    pos = []
    for target_pos in target_order:
        pos.append(pos_dict[target_pos])
    # print out
        
    fake_x='x'
    result = f"permute({fake_x},["
    for p in pos:
        result += f"{p},"
    result = result[:-1] + "])"
    tokens = MatlabLexer().tokenize(result)
    token_list=[token for token in tokens]
    x.token_list=token_list[0:2]+x.token_list+token_list[3:]
    x.index=target_order
    return x


MIDDLE_OPERATORS={'+':5,'-':5,'*':10,'/':10,'.*':10,'./':10,'^':11,'>=':3,'=':3,'<=':3,'==':3,'<':3,'>':3,'&':2,'|':1,'&&':0,'||':-1,'~=':3}
LEFT_OPERATORS={'f':13,'-':5,'(':-2}
VECTORIZED_OPERATORS={'*':'.*','/':'./','^':'.^','+':'+','-':'-','>=':'>=','=':'=','<=':'<=','=':'=','==':'==','<':'<','>':'>','&':'&','|':'|','&&':'&','||':'|','~=':'~='}


# RIGHT_OPERATORS=['^']
def apply_operator(operator:Token, *args:Variable)->Variable:
    
    def binary_extend_list(x:Variable,op:Token,y:Variable)->list[Token]:
        op.value=VECTORIZED_OPERATORS[op.value]
        x.token_list.append(op)
        return x.token_list+y.token_list  
    def unary_extend_list(op:Token,x:Variable)->list[Token]:
        if op.value in VECTORIZED_OPERATORS:
            op.value=VECTORIZED_OPERATORS[op.value]
        x.token_list.insert(0, op)
        return x.token_list  

    if operator.value in MIDDLE_OPERATORS and len(args) == 2:
        if operator.value == '=':#differentiate between cvx and matlab
            index=args[0].index
        else:
            index =list(set.union(*[set(x.index) for x in args]))
        result_variables=[permute(expand(x, index),index) for x in args]
        return Variable(binary_extend_list(result_variables[0], operator, result_variables[1]), index=index)

    if operator.value in LEFT_OPERATORS and len(args) == 1:#left op
        index=args[0].index
        result_variables=[permute(expand(x, index),index) for x in args]
        return Variable(unary_extend_list(operator, result_variables[0]), index=index)
    
    if operator.type == 'NAME' and len(args) == 1: #left functional
        index=args[0].index
        result_variables=[permute(expand(x, index),index) for x in args]
        return Variable(unary_extend_list(operator, result_variables[0]), index=index)

    return None


## input parser
def extract_loop_bounds(input_string):

    matchs = re.findall(r'for (\w+)=(\d+):(\w+)', input_string, re.MULTILINE)
    num_dict={}
    if matchs:    
        for n_end in matchs:
            num_dict[n_end[0]]=n_end[2] 
        return num_dict
    else:
        raise Exception("no loop bound")

def extract_expressions(input_block):
    result=[]
    for line in input_block:
        matchs = re.findall(r'.+=.+;', line.replace(" ",""), re.MULTILINE)
        result.append(matchs[0][:-1])
    return result

def extract_condition(block):
    match = re.search(r'[^\w]*if ',block[0])
    if match:
        return block[0][match.end():]
    return None

def expression_parser(variable)->Variable:
    
    def expression_parens(token_list:list[Token])->dict[int,int]:
        lis=[]
        end_index={}
        for i, tok in enumerate(token_list):
            if tok.type=='LPAREN':
                lis.append(i)
            elif tok.type=='RPAREN':
                end_index[lis.pop()] = i
        return end_index
    

    def double_lexer(token_list:list[Token]):
        #the returned list only saves two types of things: operators , variables
        end_index= expression_parens(token_list)
        lis=[]
        i=0
        while(i<len(token_list)):
            
            first_token = token_list[i]
           
            if first_token.type=='NAME' and (i+1)<len(token_list) and token_list[i+1].type == 'LPAREN':
                if token_list[i+2].value in loop_bounds: # whether it is a array
                    v=Variable(token_list[i:end_index[i+1]+1]).start_parsing()
                    lis.append(v)
                    i=end_index[i+1]+1
                    continue
                else:
                    lis.append(first_token)
                    i=i+1
                    continue

            elif first_token.type=='NAME' and first_token.value in loop_bounds: 
                temp = first_token.value
                first_token.value=f'(1:{loop_bounds[first_token.value]})\''
                v=Variable([first_token], index=[temp]).start_parsing()
                lis.append(v)
                i=i+1
                continue

            elif first_token.type == 'NAME' and first_token.value == cached_condition_name:
                v=Variable([first_token], index = cached_condition_index).start_parsing()
                lis.append(v)
                i=i+1
                continue                

            elif first_token.type=='NAME' or  first_token.type=='NUMBER':

                v=Variable([first_token]).start_parsing()
                lis.append(v)
                i=i+1
                continue

            elif first_token.type != 'LPAREN' and first_token.type != 'RPAREN': #运算符
                lis.append(first_token)
                i=i+1
                continue

            elif first_token.type == 'LPAREN' or first_token.type == 'RPAREN':

                lis.append(first_token)
                i=i+1
                continue
        return lis
    
    def parse_symbols(symbols):


        def use_one_operator_from_stack(symbols):
            right_value=symbols.pop()
            op = symbols.pop()#operator
            if op.value in LEFT_OPERATORS and op.value not in MIDDLE_OPERATORS:#become unary op
                symbols.append(apply_operator(op, right_value))
            elif op.value in LEFT_OPERATORS and op.value in MIDDLE_OPERATORS and (symbols == [] or (type(symbols[-1]).__name__ == 'Token' and symbols[-1].value == "(") or (type(symbols[-1]).__name__ == 'Token' and symbols[-1].value in MIDDLE_OPERATORS)):#become unary op
                symbols.append(apply_operator(op, right_value))
            elif op.type=='NAME':# function/unary op
                symbols.append(apply_operator(op, right_value))
            else: #become biary op
                left_value = symbols.pop()
                symbols.append(apply_operator(op, left_value, right_value))

        def priority( token:Token ):
            if token.value in MIDDLE_OPERATORS:
                return MIDDLE_OPERATORS[token.value]
            elif token.value in LEFT_OPERATORS:
                return LEFT_OPERATORS[token.value]
            elif token.type == 'NAME':
                return LEFT_OPERATORS['f']
            else:
                raise Exception(f'no priority for {token.value}')
            
        def is_symbol_operator(symbol, str):
            if type(symbol).__name__ == 'Token' and symbol.value == str:
                return True
            else:
                return False

        # 当前操作数和操作符栈
        result_symbols = []

        for symbol in symbols:
            if type(symbol).__name__ == 'Token'  and symbol.value not in "()":  # 如果是操作符
                while len(result_symbols)>=2 and not is_symbol_operator(result_symbols[-1], '(') and type(result_symbols[-2]).__name__ == 'Token' and priority(result_symbols[-2]) >= priority(symbol):

                    use_one_operator_from_stack(result_symbols)

                result_symbols.append(symbol)

            elif is_symbol_operator(symbol, '('):
                result_symbols.append(symbol)
            elif is_symbol_operator(symbol, ')'):

                while len(result_symbols)>=2:
                    if is_symbol_operator(result_symbols[-2], '('):
                        variable = result_symbols.pop()
                        left_paren=result_symbols.pop()
                        break
                    else:
                        use_one_operator_from_stack(result_symbols)

                variable.token_list=[left_paren]+ variable.token_list +[symbol]
                result_symbols.append(variable)

            else:  # 如果是数值
                result_symbols.append(symbol)

        # 处理剩余的操作符
        
        while len(result_symbols)>=2:
            use_one_operator_from_stack(result_symbols)


        return result_symbols[0]
    
    symbols = double_lexer(variable.token_list)

    result_variable = parse_symbols(symbols)

    return result_variable


def lhs_rhs_for_cvx(expression):
    lis = []
    i=0
    start = 0
    while i< len(expression):
        if expression[i]=='(':
            lis.append(expression[i])
        elif expression[i:i+2] == '==' or expression[i:i+2] == '>=' or expression[i:i+2] == '<=':
            if not lis:
                start = i
                break
            i+=2
            continue
        elif expression[i]==')':
            lis.pop()
        i+=1

    return expression[start:start+2], expression[:start], expression[start+2:]
            
def add_condition(expression, condition):

    a =  re.search(r'[^=<>]=[^=<>]',expression)
    if a : #matlab
        lhs,rhs = expression[:a.start()+1], expression[a.end()-1:]
        conditinal_expression =f'{lhs}=({condition})*({rhs}) + (1-({condition}))*{lhs}'
    else: #cvx to be done...
        op, lhs, rhs  = lhs_rhs_for_cvx(expression)
        conditinal_expression =f'0{op}(-({lhs})+({rhs}))*({condition})'

    return conditinal_expression

input_string=""

with open('loop_editor.m', 'r') as file:
    content = file.read()
    
    pattern = r'for .*\nend'
    match = re.search(pattern, content, re.DOTALL)

    if match:
        input_string = match.group(0)
        print('\n---------------------------The extracted original for-loop is:----------------------------------')
        print(input_string)
    else:
        raise Exception("No for-loop found.")    

print("-----------------------------vectorized by Vecparser as----------------------------------------\n")
new_content="\n\n%-------------------------vectorized by Vecparser as-----------------------\n\n"


loop_bounds = extract_loop_bounds(input_string)


line_list=input_string.splitlines()

def vectorize_one_block(input_block):
    global cached_condition_name
    global cached_condition_index
    global new_content
    cached_condition_name=None

    condition=extract_condition(input_block)
    if condition:
        cached_condition_name='cached_condition_for_this'
        tokens = MatlabLexer().tokenize(condition)
        condition_v = Variable([to for to in tokens]).start_parsing()
        print(f'{cached_condition_name}=({condition_v.name});')
        new_content+=f'{cached_condition_name}=({condition_v.name});\n\n'
        cached_condition_index = condition_v.index

    if condition:
        expressions = extract_expressions(input_block[1:])
    else:
        expressions = extract_expressions(input_block)

    for expression in expressions:
        conditional_expression=None
        if condition:
            conditional_expression = add_condition(expression, cached_condition_name)
        else:
            conditional_expression = expression
        tokens = MatlabLexer().tokenize(conditional_expression)
        parser_result= Variable([to for to in tokens]).start_parsing()
        print(parser_result, end="")
        print(';')
        new_content+=f'{parser_result.name};\n\n'

def clear_line_stack(line_stack):
    while line_stack:
        if len(line_stack) == 1:
            return line_stack.pop()
        line_stack.pop()
    return None

line_stack=[]
cached_condition_name=None
cached_condition_index=None

for i,line in enumerate(line_list):
    if ';' in line:
        line_stack.append(i)
    elif re.search(r'[^\w]*if ',line):
        if line_stack:
            bottom= clear_line_stack(line_stack)
            if bottom:
                vectorize_one_block(line_list[bottom:i])
        line_stack.append(i)
    elif re.search(r'[^\w]*end[^\w]*',line):
        if line_stack:
            bottom = clear_line_stack(line_stack)
            if bottom:
                vectorize_one_block(line_list[bottom:i])



print("\n---------Those results have been writen to the file \"loop_editor.m\", please refresh it.---------")
new_content+="%-----Please clear this file each time before you write a new loop on------"
with open('loop_editor.m', "a") as target_file:
    target_file.write(new_content)
