import ply.yacc as yacc
from lexer import tokens
from parse_tree import *


# This one should be first in the parsing file to make it the "base" rule
def p_program(p):
	"""
	program : classdecl program
	           | classdecl 
	"""

def p_error(p):
	print "Parsing syntax error"

def p_empty(p):
	'empty :'
	pass


def p_classdecl(p):
	"classdecl : CLASS TYPE varformals classopts classbody"

def p_classopts(p):
	"""
	classopts : empty
		| EXTENDS NATIVE
		| EXTENDS TYPE actuals
	"""

def p_varformals(p):
	"""
	varformals : '(' empty ')'
		|'(' var_list ')'
	"""

def p_var_list(p):
	"var_list : VAR ID ':' TYPE var_list_tail"

def p_var_list_fail(p):
	"""
	var_list_tail : empty
		| ',' var_list
	"""


def p_classbody(p):
	"classbody : '{' features '}'"

def p_features(p):
	"""
	features : empty
		| feature features
	"""

def p_feature(p):
	"""
	feature : opt_override DEF ID formals ':' TYPE '=' expr_native ';'
		| VAR ID '=' NATIVE
		| VAR ID ':' TYPE '=' expr
		| '{' block '}' ';'
	"""

def p_expr_native(p):
	"expr_native = expr | NATIVE"

def p_opt_override(p):
	"opt_override : empty | OVERRIDE"


def p_formals(p):
	"""
	formals : '(' ')'
		| '(' formals_list ')'
	"""

def p_formals_list(p):
	"formals_list : ID ':' TYPE formals_list_tail"

def p_formals_list_tail(p):
	"""
	formals_list_tail : empty 
		| ',' formals_list
	"""

def p_actuals(p):
	"""
	actuals : '(' ')' 
		| '(' exprlist ')'
	"""

def p_expr_list(p):
	"expr_list : expr expr_list_tail"

def p_expr_list_tail(p):
	"""
	expr_list_tail : empty
		| ',' expr_list
	"""

def p_block(p):
	"""
	block : empty
		| expr
		| expr ';' expr
		| VAR ID ':' TYPE '=' expr ';' expr
	"""

def p_primary(p):
	"""
	primary : SUPER '.' ID actuals
		| NEW TYPE actuals
		| '{' block '}'
		| '(' expr ')'
		| null
		| '(' ')'
		| ID
		| INTEGER
		| STRING
		| BOOLEAN
		| THIS
	"""

def p_cases(p):
	"""
	cases : '{' case ID ':' TYPE '=>' block '}'
		| '{' case NULL '=>' block '}'
	"""

def p_expr_primary(p):
	"expr : primary"
	p[0] = p[1]

def p_expr_assign(p):
	"expr : ID '=' expr"

def p_expr_control(p):
	"expr : control"
	p[0] = p[1]

def p_control_if(p):
	"control : IF '(' expr ')' ELSE control"
	p[0] = IfExpr(p[3], p[5], p[7])

def p_control_while(p):
	"control : WHILE '(' expr ')' control"
	p[0] = WhileExpr(p[3], p[5])

def p_match(p):
	"match : cases MATCH"

def p_control_match(p):
	"control : match"
	p[0] = p[1]

def p_match_comparison(p):
	"match : comparison"
	p[0] = p[1]

def p_comparison_lt(p):
	"comparison : comparison < equiv"
	p[0] = LTExpr(p[1], p[3])

def p_comparison_lte(p):
	"comparison : comparison <= equiv"
	p[0] = LTEExpr(p[1], p[3])

def p_comparison_equiv(p):
	"comparison : equiv"
	p[0] = p[1]

def p_equiv(p):
	"equiv : equiv '==' sum"
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
	"dot : actuals ID '.' dot"
	p[0] = DotExpr(p[1], p[2], p[4])

def p_dot_primary(p):
	"dot : primary"
	p[0] = p[1]

