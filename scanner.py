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
	"SEMI",
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

states = (
	('string', 'exclusive'),
	('longstring', 'exclusive'),
	('comment', 'exclusive')
)

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

# Compute column. 
#     input is the input text string
#     token is a token instance
def find_column(input,token):
	last_cr = input.rfind('\n',0,token.lexpos)
	if last_cr < 0:
		last_cr = 0
	column = (token.lexpos - last_cr) + 1
	return column

def replace_escape_sequences(s):
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
		s = s.replace(seq, char)
	
	return s

def t_LONGSTRING(t):
	r'(?s)"{3}(?:.*?[^\\])?"{3}'
	t.value = replace_sequences(t.value[3:-3])
	t.type = "STRING"
	return t

# Downsides of matching the entire string like this is that it's more difficult to return an error message for unterminated strings.  Presumably this can be fixed by using states instead.
def t_STRING(t): 
	r'"(?:[^"\n\r\\]|\\[0btnrf"\\])*"'
	t.value = replace_sequences(t.value[1:-1])
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

def t_INLINECOMMENT(t):
	r'//.*'
	pass

### Maintain state ###
def t_ANY_newline(t):
	r'(?:\r\n|\n|\r)+'
	t.value = t.value.replace('\r\n','\n')
	t.lexer.lineno += len(t.value)/2

### Start conditions ###
def t_begincomment(t):
	r'/\*'
	t.lexer.push_state('comment')
	pass

def t_comment_end(t):
	r'(?s).*?\*/'
	t.lexer.pop_state()
	pass


def t_beginlongstring(t):
	r'"""'
	t.lexer.push_state('longstring')
	t.lexer.string_start = t.lexer.lexpos
	pass

def t_longstring_stringdata(t):
	r'"{1,2}|\\"|[^"]+'

def t_longstring_end(t):
	r'"""'
	t.lexer.pop_state()
	t.value = replace_escape_sequences(t.lexer.lexdata[t.lexer.code_start:t.lexer.lexpos+1])
	t.type = "STRING"
	return t

def t_beginstring(t):
	r'"'
	t.lexer.push_state('string')
	t.lexer.string_start = t.lexer.lexpos
	pass

def t_string_stringdata(t):
	r'(?:[^"\n\r\\]|\\[0btnrf"\\])+'

def t_string_end(t):
	r'"'
	t.lexer.pop_state()
	t.value = replace_escape_sequences(t.lexer.lexdata[t.lexer.code_start:t.lexer.lexpos+1])
	t.type = "STRING"
	return t

def t_string_error(t):
	print "Illegal character in string: '%s'" % t.value[0]
	pass


### Error state ###
def t_ANY_error(t):
	print "Illegal character '%s'" % t.value[0]
	t.lexer.skip(1)

lexer = lex.lex(debug = 1)

if __name__ == "__main__":
	lex.runmain()

	#import sys
	# get file input
	#filename = sys.argv[1]

	# get tokens until there is nore more input
