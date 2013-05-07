import sys
from lexer import tokens, reserved, lexer as lex
from parser import yacc
from error import *


USAGE = """usage: %s <INPUT FILE> (<OUTPUT FORMAT>)

  By default, the output format is JSON.  "Parens" may also be used for an 
  indented, parenthesized-style format.
""" % sys.argv[0]

if __name__ == "__main__":
	if len(sys.argv) not in (2, 3):
		sys.exit(USAGE)

	filename = sys.argv[1]

	try:
		style = sys.argv[2].lower()
	except IndexError:	
		style = 'json'

	try:
		f = open(filename,'U')
	except IOError, e:
		sys.exit(e)

	text = f.read()
	f.close()

	Error.filename = filename
	Error.input = text

	try:
		tree = yacc.parse(text, lexer=lex)
		print tree.pretty(0, style)
	except TokenError, e:
		e.display()
		sys.exit("Failed with %d error%s." % (Error.errors, '' if Error.errors == 1 else 's'))

	state = lex.lexstate
	if state in ('comment', 'string', 'longstring'):
		token = None
		if state == 'comment': token = lex.comment_start
		if state in ('longstring', 'string'): token = lex.string_start
		TokenError("\nUnterminated %s: Encountered EOF\n" % (state), token).display()
		sys.stderr


	print "Parsing complete. Encountered %d error%s." % (
		Error.errors, '' if Error.errors == 1 else 's'
	)




