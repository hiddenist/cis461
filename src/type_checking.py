from error import SymbolError
from settings import SYMBOL_DEBUG as DEBUG


UNINSTANTIABLE_TYPES = ('Any', 'Int', 'Unit', 'Boolean', 'Symbol')
NOT_NULLABLE_TYPES = ('Nothing', 'Boolean', 'Int', 'Unit')
UNINHERITABLE_TYPES = ('Null', 'Nothing')

class Environment(object):
	def __init__(self):
		self.O = [{}]
		self.M = {}
		self.C = {
			'Any': None,
			'String' : 'Any',
			'Int' : 'Any',
			'Boolean' : 'Any',
			'Null' : None,
			'Nothing': None,
		}

	def enterScope(self):
		self.O.append({})

	def exitScope(self):
		self.O.pop()

	def defineVar(self, v, T):
		# Get the current stack scope
		d = self.O[-1]
		if v in d:
			raise SymbolError("The variable '%s' was already defined in this scope." % v)
		else:
			d[v] = T

	def defineMethod(self, C, f, t):
		self.M[(C, f)] = t

	def defineClass(self, c, S):
		if c in self.C:
			raise SymbolError("Class name '%s' is already defined")
		self.C[c] = S

	def getVar(self, v):
		for d in reversed(self.O):
			try:
				return d[v]
			except KeyError:
				continue
		raise SymbolError("Variable '%s' was not initialized" % v)

	def getMethod(self, C, f):
		try:
			return self.M[(C, f)]
		except KeyError:
			raise SymbolError("Class '%s' does not have a method '%s' defined" % (C, f))

	def getSuperClass(self, c):
		try:
			return self.C[c]
		except KeyError:
			if DEBUG: print type(c), self.C
			raise SymbolError("Type '%s' has not been defined" % c)
