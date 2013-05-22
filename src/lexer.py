import ply.lex as lex
from error import *
from settings import LEX_DEBUG as DEBUG

# Keyword tokens
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

# "Extended Cool" reserved words
reserved = ('abstract', 'catch', 'do', 'final', 'finally', 'for', 'forSome', 'implicit', 'import', 'lazy', 'object', 'package', 'private', 'protected', 'requires', 'return', 'sealed', 'throw', 'trait', 'try', 'type', 'val', 'with', 'yield')

# Literal tokens must be a single character
literals = ('(', ')', '{', '}', ':', '=', '<', '!', '+', '-', '*', '/', '.', ',', ';')

# Other tokens
tokens = (
	"ID",
	"TYPE",
	"INTEGER",
	"STRING",
	"BOOLEAN",
	"ARROW",
	"LE",
	"EQUALS",
) + tuple(keywords.values())

# Possible lexing states
states = (
	('string', 'exclusive'),
	('longstring', 'exclusive'),
	('comment', 'exclusive')
)

# Decorator to count newlines on tokens which might match them.
def allows_linebreaks(f):
	def decorator(t):
		t.lexer.lineno += t.value.count('\n')
		return f(t)

	# PLY uses the function doc as part of functionality, so we need to transfer that with the decorator.
	decorator.__doc__ = f.__doc__

	return decorator


# Token rules

### Symbols ###
t_ARROW = r'=>'
t_EQUALS = r'=='
t_LE = r'<='


### Count newlines ###
@allows_linebreaks
def t_newline(t):
	r'\n+' # We won't encounter \r or \r\n since we'll be opening files with the U tag (or otherwise preprocessing the text so that \n is the only kind of newline)

if (DEBUG):
	def t_illegal_newline(t):
		r'\r' # ... or if it does, display a warning when in debug
		raise LexError("DEBUG WARNING: Input contains carriage returns!", t)


### Literals ###
def t_INTEGER(t):
	r'0|[1-9]\d*'
	try:
		t.value = int(t.value)
	except ValueError:
		raise LexError("Integer value too large %d" % t.value, t)
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

	# We can't raise an error and return a token, so store the error in the token for the driver to display
	if t.value in reserved:
		t.error = LexError("Illegal reserved word used: '%s'" % t.value, t)
	
	return t

t_TYPE = r'[A-Z]\w*'


## Ignored ###
def t_WHITESPACE(t):
	r'[ \t]+'
	# Not newlines, so we don't have to call the newline counter every time we encounter whitespace (that's often!)
	# Also, 
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
	t.error = LexError("Unterminated string: Encountered newline", t)
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
	raise LexError("Illegal character in %s: %s" % (t.lexer.lexstate, repr(t.value[0])), t)


### Error state ###
def t_INITIAL_comment_error(t):
	t.lexer.skip(1)
	raise LexError("Illegal character: %s " % repr(t.value[0]), t)

lexer = lex.lex(debug=DEBUG)

# Modify the lexer's token method to handle errors, since yacc takes over the role of our driver and calls this.
def error_handling_token(get_token):
	def new_fn(*args, **kwargs):
		token = get_token(*args, **kwargs)
		if hasattr(token, 'error'):
			token.error.display()
		return token
	return new_fn

lexer.token = error_handling_token(lexer.token)
