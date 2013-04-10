import ply.lex as lex

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
		raise ScannerError("Integer value too large %d" % t.value, t)
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
	t.lexer.comment_start = t.lexer.lexpos
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
	t.lexer.string_start = t.lexer.lexpos-3
	pass

def t_longstring_escapedquote(t):
	r'\\"'

def t_longstring_end(t):
	r'"""'
	t.lexer.pop_state()
	t.value = replace_escape_sequences(t.lexer.lexdata[t.lexer.string_start+3:t.lexer.lexpos-3])
	t.type = "STRING"
	t.lexpos = t.lexer.string_start
	return t

@allows_linebreaks
def t_longstring_stringdata(t):
	r'"{1,2}|[^"]*[^\\"]'

def t_beginstring(t):
	r'"'
	t.lexer.push_state('string')
	t.lexer.string_start = t.lexer.lexpos
	pass

def t_string_stringdata(t):
	r'(?:[^"\n\\]|\\[0btnrf"\\])+'

@allows_linebreaks
def t_string_linebreak(t):
	r'\n'
	t.error = ScannerError("Missing end quote on string", t)
	return t_string_end(t)

def t_string_end(t):
	r'"'
	t.lexer.pop_state()
	t.value = replace_escape_sequences(t.lexer.lexdata[t.lexer.string_start:t.lexer.lexpos-1])
	t.type = "STRING"
	t.lexpos = t.lexer.string_start
	return t

def t_string_longstring_error(t):
	t.lexer.skip(1)
	raise ScannerError("Illegal character in %s: %s" % (t.lexer.lexstate, repr(t.value[0])), t)


### Error state ###
def t_INITIAL_comment_error(t):
	t.lexer.skip(1)
	print t.lexer.lexstate
	raise ScannerError("Illegal character: %s " % repr(t.value[0]), t)

lexer = lex.lex(debug = DEBUG)

class ScannerError(Exception):
	def __init__(self, string, token=None):
		super(ScannerError, self).__init__(string)
		if token is not None:
			self.line = token.lineno
			self.pos = token.lexpos
		else:
			self.line = 0
			self.pos = 0

# Compute column and grab the associated line - this needs organization
def find_column(input,lexpos):
	last_cr = input.rfind('\n',0,lexpos)
	next_cr = input.find('\n',lexpos)

	if next_cr < 0:
		next_cr = len(input)
	
	column = (lexpos - last_cr)

	# Limit lines to a maximum of 80 characters - 40 before the column, 40 after.  Append an ellipsis if truncation is performed.
	ellipsis = '...'
	max_pad = 40

	startline = lexpos - max_pad if (lexpos - last_cr) > max_pad else last_cr
	endline = lexpos + max_pad if (next_cr - lexpos) > max_pad else next_cr

	displaycolumn = column - (startline - last_cr)

	line = input[startline+1:endline].replace('\t',' ')

	if startline != last_cr: 
		line = ellipsis + line[len(ellipsis):]
		displaycolumn += len(ellipsis)

	if endline != next_cr: line = line[:-len(ellipsis)] + ellipsis

	return (column, line, displaycolumn)

if __name__ == "__main__":
	import sys

	filename = sys.argv[1]

	f = open(filename,'U')
	text = f.read()
	f.close()

	lexer.input(text)
	largest_token = max([len(s) for s in tokens])
	template = "{0:{width}}  {1:4}  {2:4}  {3}"
	print template.format('token','line','char','value', width=largest_token)
	while True:
		try:
			token = lex.token()
		except ScannerError, e:
			# Todo: Error class
			col, line, displaycol = find_column(text, e.pos)
			sys.stderr.write("\nScanner Error (%s: line %d col %d):\n" % (filename, e.line, col))
			sys.stderr.write(line)
			sys.stderr.write('\n'+(' '*(displaycol-1))+'^\n')
			sys.stderr.write(e)
			sys.stderr.write('\n')
			continue

		if not token: break

		if token.type == 'ID' and token.value in reserved:
			col, line, displaycol = find_column(text, token.lexpos)
			sys.stderr.write("\nScanner Error (%s: line %d col %d):\n" % (filename, token.lineno, col))
			sys.stderr.write(line)
			sys.stderr.write('\n'+(' '*(displaycol-1))+'^\n')
			sys.stderr.write("Illegal reserved word used: '%s'\n\n" % token.value)

		if hasattr(token, 'error'):
			col, line, displaycol = find_column(text, token.lexpos)
			sys.stderr.write("\nScanner Error (%s: line %d col %d):\n" % (filename, token.lineno, col))
			sys.stderr.write(line)
			sys.stderr.write('\n'+(' '*(displaycol-1))+'^\n')
			sys.stderr.write(token.error)
			sys.stderr.write('\n')

		col, _, _ = find_column(text, token.lexpos)
		print template.format(token.type, token.lineno, col, token.value, width=largest_token)
	
	if lexer.lexstate in ("comment", 'string', 'longstring'):
		col, _, _ = find_column(text, lexer.lexpos)
		sys.stderr.write("\nUnexpected EOF: Unterminated %s (%s: line %d col %d)\n" % (lexer.lexstate, filename, lexer.lineno, col))
