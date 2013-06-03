import sys
from settings import *

USAGE = """usage: %s <INPUT FILE> (<OUTPUT FORMAT>)

  By default, the output format is JSON.  "Parens" may also be used for an 
  indented, parenthesized-style format.
""" % sys.argv[0]

	

if __name__ == "__main__":
	from lexer import tokens, reserved, lexer as lex
	from parser import yacc
	from error import *
	from type_checking import TypeChecker
	from code_gen import CodeGen

	verbose = True # should probably make this a command-line arg

	def errorExit():
		for e in Error.elist:
			e.display()
		sys.exit("Failed with %d error%s." % (Error.errors, '' if Error.errors == 1 else 's'))

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
		if verbose: print "--- Beginning parsing ---"
		tree = yacc.parse(text, lexer=lex, debug=PARSE_DEBUG)

		if Error.errors:
			errorExit()
			
		if verbose: print "--- Beginning type checking ---"
		TypeChecker(tree).check()

		if Error.errors:
			errorExit()

		CodeGen(tree).generate()

		if verbose: print "--- Beginning code generation ---"
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


	sys.stderr.write(
		"Completed with %d error%s.\n" % (
			Error.errors, 
			'' if Error.errors == 1 else 's'
		)
	)




