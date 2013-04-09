import ply.lex as lex

tokens = (
	"EOF",
	"ID",
	"LPAREN",
	"LBRACE",
	"NULL",
	"SUPER",
	"NEW",
	"MINUS",
	"INTEGER",
	"STRING",
	"BOOLEAN",
	"THIS",
	"IF",
	"WHILE",
	"NOT",
	"RPAREN",
	"TYPE",
	"COLON",
	"VAR",
	"RBRACE",
	"SEMI",
	"ASSIGN",
	"CASE",
	"DEF",
	"NATIVE",
	"COMMA",
	"ARROW",
	"DOT",
	"CLASS",
	"ELSE",
	"EXTENDS",
	"OVERRIDE",
	"LE",
	"LT",
	"EQUALS",
	"TIMES",
	"DIV",
	"PLUS",
	"MATCH"
)


def CoolLexer:
	t_EOF = r''
	t_ID = r'[a-z]\w*'
	t_LPAREN = r'\('
	t_LBRACE = r'\{'
	t_NULL = r'null'
	t_SUPER = r'super'
	t_NEW = r'new'
	t_MINUS = r'-'

	def t_INTEGER(t):
		r'[1-9]\d*'
		try:
			t.value = int(t.value)
		except ValueError:
			print "Integer value too large %d" % t.value 
			# Does %d actually work if it's too big?
		return t

	def t_STRING(t): 
		r"""(?xm)
			(?:
				"
					(?:[^"\n\r\\]
						| \\0
						| \\b
						| \\t
						| \\n
						| \\r
						| \\f
						| \"
						| \\\\
					)*
					\\0
					\\b
					\\t
				"
			) | (?:
				"{3}
					.*
				"{3}
			)
		"""

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
		t.value = t.value == "true"
		return t

	t_THIS = r'this'
	t_IF = r'if'
	t_WHILE = r'while'
	t_NOT = r'not'
	t_RPAREN = r'\)'
	t_TYPE = r'[A-Z]\w*'
	t_COLON = r':'
	t_VAR = r'var'
	t_RBRACE = r'\}'
	t_SEMI = r';'
	t_ASSIGN = r'='
	t_CASE = r'case'
	t_DEF = r'def'
	t_NATIVE = r'native'
	t_COMMA = r','
	t_ARROW = r'=>'
	t_DOT = r'\.'
	t_CLASS = r'class'
	t_ELSE = r'else'
	t_EXTENDS = r'extends'
	t_OVERRIDE = r'override'
	t_LE = r'<='
	t_LT = r'<'
	t_EQUALS = r'=='
	t_TIMES = r'\*'
	t_DIV = r'/'
	t_PLUS = r'\+'
	t_MATCH = r'match'

	t_ignore = r"""(?x)
			//.*$
		|	/\* (?:[^*]|*[^/]?)* \*/
		| \s+
	"""

	def t_newline(t):
		r'(\n|\r|\r\n)'
		t.lexer.lineno += 1

	def t_error(t):
		print "Illegal character '%s'" % t.value[0]
		t.lexer.skip(1)

	return lex.lex()
