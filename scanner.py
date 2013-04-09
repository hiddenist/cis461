import ply.lex as lex

keywords = {
	'case': 'CASE',
	'class': 'CLASS',
	'def': 'DEF',
	'else': 'ELSE',
	'extends': 'EXTENDS',
	'if': 'IF',
	'match': 'MATCH',
	'native': 'NATIVE',
	'new': 'NEW',
	'null': 'NULL',
	'override': 'OVERRIDE',
	'super': 'SUPER',
	'this': 'THIS',
	'var': 'VAR',
	'while': 'WHILE'
}

reserved = ('abstract', 'catch', 'do', 'final', 'finally', 'for', 'forSome', 'implicit', 'import', 'lazy', 'object', 'package', 'private', 'protected', 'requires', 'return', 'sealed', 'throw', 'trait', 'try', 'type', 'val', 'with', 'yield')

tokens = (
	"EOF",
	"ID",
	"TYPE",
	"LPAREN",
	"LBRACE",
	"MINUS",
	"INTEGER",
	"STRING",
	"BOOLEAN",
	"NOT",
	"RPAREN",
	"COLON",
	"RBRACE",
	"SEMI",#
	"ASSIGN",
	"COMMA",
	"ARROW",
	"DOT",
	"LE",
	"LT",
	"EQUALS",
	"TIMES",
	"DIV",
	"PLUS",
) + tuple(keywords.values())

### Symbols ###
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_LBRACE = r'\{'
t_RBRACE = r'\}'
t_COLON = r':'
t_ASSIGN = r'='
t_EQUALS = r'=='
t_LE = r'<='
t_LT = r'<'
t_NOT = r'\!'
t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIV = r'/'
t_DOT = r'\.'
t_COMMA = r','
t_ARROW = r'=>'
t_SEMI = r';'

### Literals ###
def t_INTEGER(t):
	r'0|[1-9]\d*'
	try:
		t.value = int(t.value)
	except ValueError:
		print "Integer value too large %d" % t.value 
		# Does %d actually work if it's too big?
	return t

# Downsides of matching the entire string like this is that it's more difficult to return an error message for unterminated strings.  Presumably this can be fixed by using states instead.
def t_STRING(t): 
	r'"(?:[^"\n\r\\]|\\[0btnrf"\\])*"|(?s)"{3}(.*?)[^\]?"{3}'

	if t.value.startswith('"""'):
		t.value = t.value[3:-3]
	else:
		t.value = t.value[1:-1] # Remove quotes

	special = (
		(r'\0', '\0'),
		(r'\b', '\b'),
		(r'\t', '\t'),
		(r'\n', '\n'),
		(r'\r', '\r'),
		(r'\f', '\f'),
		(r'\"', '\"'),
		(r'\\', '\\'),
	)

	for seq, char in special:
		t.value = t.value.replace(seq, char)

	return t

def t_BOOLEAN(t):
	r'true|false'
	t.value = bool(t.value == "true")
	return t

### Identifiers ###
def t_ID(t): 
	r'[a-z]\w*'

	if t.value in reserved:
		print "Illegal reserved word used: %s" % t.value

	t.type = keywords.get(t.value, 'ID') # Check for keywords
	return t

t_TYPE = r'[A-Z]\w*'

## Ignored ###
def t_WHITESPACE(t):
	r'\s+'
	pass

def t_COMMENT(t):
	r'(?s)/\*.*?\*/'
	pass

def t_INLINECOMMENT(t):
	r'//.*'
	pass

### Special ###
def t_newline(t):
	r'(\n|\r|\r\n)'
	t.lexer.lineno += 1

def t_error(t):
	print "Illegal character '%s'" % t.value[0]
	t.lexer.skip(1)

lexer = lex.lex(debug = 1)

if __name__ == "__main__":
	lex.runmain()
