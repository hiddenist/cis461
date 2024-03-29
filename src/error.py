import sys
import settings

class TooManyErrors(Exception):
	pass

class Error(Exception):
	errors = 0
	elist = []
	MAX_ERRORS = settings.MAX_ERRORS
	def __init__(self, string):
		super(Error, self).__init__(string)
		Error.errors += 1
		self.errorno = Error.errors

		if settings.DEBUG: Error.elist.append(self)

	def display(self):
		sys.stderr.write(str(self) + '\n')

	def report(self):
		"Displays an error, but also raises another error when the max errors have been exceeded"
		self.display()
		if Error.errors >= Error.MAX_ERRORS:
			raise TooManyErrors()

	def ignore(self):
		"Remove this error from the error count"
		Error.errors -= 1
		self.errorno = -1
		if settings.DEBUG: Error.elist.remove(self)
		
class NotImplemented(Error):
  pass

class TokenError(Error):
	def __init__(self, string, token=None):
		super(TokenError, self).__init__(string)
		self.setToken(token)

	def setToken(self, token):
		self.token = token

		if self.token is not None:
			self.token.displayedError = False

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

	def report(self):
		# Ignore multiple errors on the same token...
		if self.token is not None and self.token.displayedError:
			self.ignore()
		else:
			super(TokenError, self).report()
			if self.token is not None:
				self.token.displayedError = True

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

class LexError(TokenError):
	pass

class TypeCheckError(TokenError):
	pass

class SymbolError(TokenError):
	pass

class UndefinedClassError(SymbolError):
	def __init__(self, string, cls, env):
		super(UndefinedClassError, self).__init__(string)
		self.cls = cls
		self.env = env
	
	def report(self):
		super(UndefinedClassError, self).report()
		self.env.undefined.add(self.cls)
