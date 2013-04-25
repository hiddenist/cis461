import ply.yacc as yacc
from lexer import tokens
from tree import *
from error import *


# Starting grammar rule goes first in the file
def p_program(p):
	"""
	program : classdecl program
	           | classdecl 
	"""
	p[0] = Document(*p[1:])
	p[0].display()


def p_error(p):
	# If we don't want to fail on an error, we could display this here instead of raising
	err = TokenError("Syntax error: unexpected token", p)
	if Error.errors < Error.MAX_ERRORS:
		err.display()
		yacc.errok() # Ignore the error, discard the token, and continue trying to parse
	else:
		raise err

def p_empty(p):
	'empty :'
	pass


def p_classdecl(p):
	"classdecl : CLASS type varformals classopts classbody"
	p[0] = Class(*p[2:])

def p_classopts(p):
	"""
	classopts : empty
		| EXTENDS NATIVE
		| EXTENDS type actuals
	"""

	if len(p) > 2:
		p[0] = ClassOpts(*p[2:])
	else:
		pass

def p_type(p):
	"type : TYPE"
	p[0] = Type(p[1])

def p_varformals_empty(p):
	"varformals : '(' ')'"
	p[0] = VarFormals()

def p_varformals(p):
	"varformals : '(' var_list ')'"
	p[0] = VarFormals(*p[2])

def p_var_list(p):
	"var_list : VAR id ':' type var_list_tail"
	p[0] = (Formal(p[2], p[4]),) + p[5]

def p_var_list_tail(p):
	"""
	var_list_tail : empty
		| ',' var_list
	"""
	if len(p) == 2:
		p[0] = ()
	else:
		p[0] = p[2]


def p_classbody(p):
	"classbody : '{' features '}'"
	p[0] = ClassBody(*p[2])


def p_features_empty(p):
	"features : empty"
	p[0] = ()

def p_features(p):
	"features : feature features"
	p[0] = (p[1],) + p[2]

def p_var_init(p):
	"var_init : VAR id ':' type '=' expr"
	p[0] = VarInit(p[2], p[4], p[6])

def p_feature_var(p):
	"""
	feature : var_init ';'
		| VAR id '=' NATIVE ';'
	"""
	if len(p) == 2:
		p[0] = p[1]
	else:
		p[0] = VarInit(p[2], p[4], p[4])

def p_feature_block(p):
	"feature : '{' block '}' ';'"
	p[0] = p[2]

def p_feature_def(p):
	"feature : opt_override DEF id formals ':' type '=' expr_native ';'"
	p[0] = Def(p[1], p[3], p[4], p[6], p[8])

def p_expr_native(p):
	"""
	expr_native : expr 
		| NATIVE
	"""
	p[0] = p[1]

def p_opt_override_empty(p):
	"opt_override : empty"
	p[0] = False

def p_opt_override(p):
	"opt_override :  OVERRIDE"
	p[0] = True


def p_formals_empty(p):
	"formals : '(' ')'"
	p[0] = Formals()

def p_formals(p):
	"formals : '(' formal_list ')'"
	p[0] = Formals(*p[2])

def p_formal_list(p):
	"formal_list : id ':' type formal_list_tail"
	p[0] = (Formal(p[1], p[3]),) + p[4]

def p_formal_list_tail(p):
	"""formal_list_tail : ',' formal_list
		| empty
	"""
	if len(p) == 2:
		p[0] = ()
	else:
		p[0] = p[2]

def p_actuals_empty(p):
	"actuals : '(' ')' "
	p[0] = Actuals()

def p_actuals(p):
	"actuals : '(' exprlist ')'"
	p[0] = Actuals(*p[2])

def p_exprlist(p):
	"exprlist : expr exprlist_tail"
	p[0] = (p[1],) + p[2]

def p_exprlist_tail_empty(p):
	"exprlist_tail : empty"
	p[0] = ()

def p_exprlist_tail(p):
	"exprlist_tail : ',' exprlist"
	p[0] = p[2]

def p_block(p):
	"""
	block : empty
		| block_contents expr
	"""
	if len(p) == 2:
		p[0] = Block()
	else:
		p[2] = Block(p[2], p[1])
	

def p_block_contents(p):
	"""
	block_contents : block_instr ';' 
		       | block_contents block_instr ';'
	"""
	if len(p) == 3:
		p[0] = (p[1],)
	else:
		p[0] = p[1] + (p[2],)
		
		

def p_block_instr(p):
	"""
		block_instr : var_init
			| expr
	"""
	p[0] = p[1]

def p_block_expr(p):
	"block : expr"
	p[0] = p[1]

# Is this correct? Or should a block have its own node..?
def p_primary_block(p):
	"primary : '{' block '}'"
	p[0] = p[2]

def p_primary_pexpr(p):
	"primary : '(' expr ')'"
	p[0] = p[2]

def p_primary_super(p):
	"primary : SUPER '.' id actuals"
	p[0] = Super(p[3], p[4])

def p_primary_call(p):
	"primary : id actuals"
	p[0] = Call(p[1], p[2])

def p_primary_constructor(p):
	"primary : NEW type actuals"
	p[0] = Constructor(p[2], p[3])

def p_primary_this(p):
	"primary : THIS"
	p[0] = This()

def p_primary_null(p):
	"primary : NULL"
	p[0] = Null()

def p_primary_unit(p):
	"primary : '(' ')'"
	p[0] = Unit()

def p_primary_int(p):
	"primary : INTEGER"
	p[0] = Integer(p[1])

def p_primary_bool(p):
	"primary : BOOLEAN"
	p[0] = Boolean(p[1])

def p_primary_str(p):
	"primary : STRING"
	p[0] = String(p[1])

def p_primary_id(p):
	"primary : id"
	p[0] = p[1]

def p_id(p):
	"id : ID"
	p[0] = Identifier(p[1])

def p_cases(p):
	"""
	cases : '{' CASE id ':' type ARROW block '}'
		| '{' CASE NULL ARROW block '}'
	"""

def p_expr_assign(p):
	"expr : id '=' expr"
	p[0] = AssignExpr(p[1], p[3])

def p_expr_control(p):
	"expr : control"
	p[0] = p[1]

def p_control_if(p):
	"control : IF '(' expr ')' expr ELSE expr"
	p[0] = IfExpr(p[3], p[5], p[7])

def p_control_while(p):
	"control : WHILE '(' expr ')' control"
	p[0] = WhileExpr(p[3], p[5])

def p_control_match(p):
	"control : match"
	p[0] = p[1]

def p_match(p):
	"match : match MATCH cases"
	p[0] = MatchExpr(p[1], p[3])

def p_match_comparison(p):
	"match : comparison"
	p[0] = p[1]

def p_comparison_lt(p):
	"comparison : comparison '<' equiv"
	p[0] = LTExpr(p[1], p[3])

def p_comparison_le(p):
	"comparison : comparison LE equiv"
	p[0] = LEExpr(p[1], p[3])

def p_comparison_equiv(p):
	"comparison : equiv"
	p[0] = p[1]

def p_equiv(p):
	"equiv : equiv EQUALS sum"
	p[0] = EqExpr(p[1], p[2])

def p_equiv_sum(p):
	"equiv : sum"
	p[0] = p[1]

def p_sum_plus(p):
	"sum : sum '+' product"
	p[0] = AddExpr(p[1], p[3])

def p_sum_minus(p):
	"sum : sum '-' product"
	p[0] = SubExpr(p[1], p[3])

def p_sum_product(p):
	"sum : product"
	p[0] = p[1]

def p_product_times(p):
	"product : product '*' negation"
	p[0] = MultExpr(p[1], p[3])

def p_product_div(p):
	"product : product '/' negation"
	p[0] = DivExpr(p[1], p[3])

def p_product_negation(p):
	"product : negation"
	p[0] = p[1]

def p_negation_not(p):
	"negation : '!' negation"
	p[0] = NotExpr(p[0])

def p_negation_neg(p):
	"negation : '-' negation"
	p[0] = NegExpr(p[0])

def p_negation_dot(p):
	"negation : dot"
	p[0] = p[1]

def p_dot_access(p):
	"dot : dot '.' id actuals"
	p[0] = DotExpr(p[1], p[3], p[4])

def p_dot_primary(p):
	"dot : primary"
	p[0] = p[1]

yacc.yacc(debug=1)
