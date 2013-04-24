import sys
from lexer import tokens, reserved, lexer as lex
from parser import yacc
from error import *


USAGE = "usage: %s [INPUT_FILE]" % sys.argv[0]

if __name__ == "__main__":
	if len(sys.argv) != 2:
		sys.exit(USAGE)

	filename = sys.argv[1]

	try:
		f = open(filename,'U')
	except IOError, e:
		sys.exit(e)

	text = f.read()
	f.close()

	Error.filename = filename
	Error.input = text

	try:
		yacc.parse(text, lexer=lex)
	except TokenError, e:
		e.display()

	state = lex.lexstate
	if state in ('comment', 'string', 'longstring'):
		token = None
		if state == 'comment': token = lex.comment_start
		if state in ('longstring', 'string'): token = lex.string_start
		TokenError("\nUnterminated %s: Encountered EOF\n" % (state), token).display()
		sys.stderr

	print "Parsed program with %d error%s." % (Error.errors, '' if Error.errors == 1 else 's')



