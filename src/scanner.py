import sys
from lexer import tokens, reserved, lexer as lex
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

	lex.input(text)
	largest_token = max([len(s) for s in tokens])
	template = "{0:{width}}  {1:4}  {2:4}  {3}"
	print template.format('token','line','char','value', width=largest_token)

	while True:
		try:
			token = lex.token()
		except TokenError, e:
			e.display()
			continue

		if not token: break # EOF

		if hasattr(token, 'error'):
			token.error.display()

		print template.format(token.type, token.lineno, TokenError.find_column(token.lexpos), token.value, width=largest_token)

	# Report errors about unfinished states when encountering EOF
	# Short strings don't seem to be able to trigger this, since EOF is counted as a newline - but my intuition says that it might still be possible, so I'll leave it here.
	state = lex.lexstate
	if state in ('comment', 'string', 'longstring'):
		token = None
		if state == 'comment': token = lex.comment_start
		if state in ('longstring', 'string'): token = lex.string_start
		TokenError("\nUnterminated %s: Encountered EOF\n" % (state), token).display()
		sys.stderr
