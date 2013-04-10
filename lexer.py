import ply.lex as lex
from error import *

DEBUG = False

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

literals = ('(', ')', '{', '}', ':', '=', '<', '!', '+', '-', '*', '/', '.', ',', ';')

tokens = (
	"EOF",
	"ID",
	"TYPE",
	"INTEGER",
	"STRING",
	"BOOLEAN",
	"ARROW",
	"LE",
	"EQUALS",
) + tuple(keywords.values())

states = (
	('string', 'exclusive'),
	('longstring', 'exclusive'),
	('comment', 'exclusive')
)

### Symbols ###
t_ARROW = r'=>'
t_EQUALS = r'=='
t_LE = r'<='

def allows_linebreaks(f):
	def decorator(t):
		t.lexer.lineno += t.value.count('\n')
		return f(t)

	decorator.__doc__ = f.__doc__
	return decorator

### Count newlines ###
@allows_linebreaks
def t_newline(t):
	r'\n+'

### Literals ###
def t_INTEGER(t):
	r'0|[1-9]\d*'
	try:
		t.value = int(t.value)
	except ValueError:
		raise TokenError("Integer value too large %d" % t.value, t)
		# Does %d actually work if it's too big?
	return t

def t_BOOLEAN(t):
	r'true|false'
	t.value = bool(t.value == "true")
	return t

### Identifiers ###
def t_ID(t): 
	r'[a-z]\w*'


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


### States ###
def t_begincomment(t):
	r'/\*'
	t.lexer.push_state('comment')
	t.lexer.comment_start = t
	pass

def t_comment_end(t):
	r'\*/'
	t.lexer.pop_state()
	pass

@allows_linebreaks
def t_comment_content(t):
	r'(?:[^*]|\*[^/])+'
	pass

### Strings ###
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

def t_beginlongstring(t):
	r'"""'
	t.lexer.push_state('longstring')
	t.lexer.string_start = t
	pass

def t_longstring_escapedquote(t):
	r'\\"'

def t_longstring_end(t):
	r'"""'
	t.lexer.pop_state()
	t.value = replace_escape_sequences(t.lexer.lexdata[t.lexer.string_start.lexpos+3:t.lexer.lexpos-3])
	t.type = "STRING"
	t.lexpos = t.lexer.string_start.lexpos
	return t

@allows_linebreaks
def t_longstring_stringdata(t):
	r'"{1,2}|[^"]*[^\\"]'

def t_beginstring(t):
	r'"'
	t.lexer.push_state('string')
	t.lexer.string_start = t
	pass

def t_string_stringdata(t):
	r'(?:[^"\n\\]|\\[0btnrf"\\])+'

@allows_linebreaks
def t_string_linebreak(t):
	r'\n'
	t.error = TokenError("Unterminated string: Encountered newline", t)
	return t_string_end(t)

def t_string_end(t):
	r'"'
	t.lexer.pop_state()
	t.value = replace_escape_sequences(t.lexer.lexdata[t.lexer.string_start.lexpos+1:t.lexer.lexpos-1])
	t.type = "STRING"
	t.lexpos = t.lexer.string_start.lexpos
	return t

def t_string_longstring_error(t):
	t.lexer.skip(1)
	raise TokenError("Illegal character in %s: %s" % (t.lexer.lexstate, repr(t.value[0])), t)


### Error state ###
def t_INITIAL_comment_error(t):
	t.lexer.skip(1)
	print t.lexer.lexstate
	raise TokenError("Illegal character: %s " % repr(t.value[0]), t)

lexer = lex.lex(debug = DEBUG)
