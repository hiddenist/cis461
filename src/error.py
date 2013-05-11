import sys
import settings

class Error(Exception):
	errors = 0
	MAX_ERRORS = settings.MAX_ERRORS
	def __init__(self, string):
		super(Error, self).__init__(string)
		Error.errors += 1
		self.errorno = Error.errors

	def display(self):
		sys.stderr.write(str(self) + '\n')

	def ignore(self):
		"Remove this error from the error count"
		Error.errors -= 1
		self.errorno = None
		
class TokenError(Error):
	def __init__(self, string, token=None):
		super(TokenError, self).__init__(string)
		self.setToken(token)

	def setToken(self, token):
		self.token = token
		if hasattr(token, 'lineno') and hasattr(token, 'lexpos'):
			self.lineno = token.lineno
			self.lexpos = token.lexpos
		else:
			self.lineno = None
			self.lexpos = None

	def display(self):
		sys.stderr.write("\n(%d) Error encountered" % self.errorno)
		if self.token is not None and self.lineno and self.lexpos:
			col, line, displaycol = self.line_info()
			sys.stderr.write(" (%s: line %d col %d):\n" % (Error.filename, self.lineno, col))
			sys.stderr.write(line)
			sys.stderr.write('\n'+(' '*(displaycol-1))+'^\n')
		else:
			sys.stderr.write(': ')
		sys.stderr.write(str(self))
		sys.stderr.write('\n\n')

	@staticmethod
	def find_column(lexpos):
		if not lexpos:
			return 0
		last_cr = Error.input.rfind('\n',0,lexpos)
		column = (lexpos - last_cr)
		return column

	def line_info(self):
		next_cr = Error.input.find('\n',self.lexpos)
		if next_cr < 0:
			next_cr = len(input)
		
		column = self.find_column(self.lexpos)
		displaycolumn = column

		# Limit lines to a maximum of 80 characters - 40 before the column, 40 after.
		# Append an ellipsis if truncation is performed.

		ellipsis = '...'
		max_pad = 40

		startline = self.lexpos - max_pad if column > max_pad else self.lexpos - column
		endline = self.lexpos + max_pad if (next_cr - self.lexpos) > max_pad else next_cr

		line = Error.input[startline+1:endline].replace('\t',' ')

		if column > max_pad: 
			line = ellipsis + line[len(ellipsis):]
			displaycolumn = max_pad

		if endline != next_cr: line = line[:-len(ellipsis)] + ellipsis

		return (column, line, displaycolumn)

class TypeCheckError(TokenError):
	pass

class SymbolError(TokenError):
	pass
