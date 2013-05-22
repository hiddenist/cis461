import sys
from settings import *

USAGE = """usage: %s <INPUT FILE> (<OUTPUT FORMAT>)

  By default, the output format is JSON.  "Parens" may also be used for an 
  indented, parenthesized-style format.
""" % sys.argv[0]

def errorExit(errors):
	sys.exit("Failed with %d error%s." % (errors, '' if errors == 1 else 's'))
	

if __name__ == "__main__":
	from lexer import tokens, reserved, lexer as lex
	from parser import yacc
	from error import *

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
		if DEBUG: print "--- Beginning parsing ---"
		tree = yacc.parse(text, lexer=lex, debug=PARSE_DEBUG)
		print tree.pretty(0, style)

		if Error.errors:
			errorExit()
			
		if DEBUG: print "--- Beginning type checking ---"
		tree.typeCheck()
	except TooManyErrors:
		errorExit()
	except Error, e:
		e.display()
		errorExit()

	state = lex.lexstate
	if state in ('comment', 'string', 'longstring'):
		token = None
		if state == 'comment': token = lex.comment_start
		if state in ('longstring', 'string'): token = lex.string_start
		TokenError("\nUnterminated %s: Encountered EOF\n" % (state), token).display()


	if Error.errors > 0:
		sys.stderr.write(
			"Completed with %d error%s.\n" % (
				Error.errors, 
				'' if Error.errors == 1 else 's'
			)
		)




