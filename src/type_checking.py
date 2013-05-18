from error import SymbolError
from settings import SYMBOL_DEBUG as DEBUG

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
			raise SymbolError("Class '%s' does not have a method '%s'" % (C, f))

	def insertVar(self, v, T):
		self.O[-1][v] = T

	def insertMethod(self, C, f, t):
		self.M[(C, f)] = t

	def insertClass(self, c, S):
		if c in self.C:
			raise SymbolError("Class name '%s' is already defined")
		self.C[c] = S

	def getClass(self, c):
		try:
			return self.C[c]
		except KeyError:
			if DEBUG: print type(c), self.C
			raise SymbolError("Type '%s' does not exist" % c)