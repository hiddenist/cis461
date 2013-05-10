from error import SymbolError

class SymbolTable(object):
	def __init__(self):
		self.O = [{}]
		self.M = {}
		self.C = {'Any': None}

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
			raise SymbolError("Method '%s.%s' is not defined" % (C, f))

	def insertVar(self, v, T):
		self.O[-1][v] = T

	def insertMethod(self, C, f, t):
		self.M[(C, f)] = t

	def insertClass(self, c, S):
		if c in self.C:
			raise SymbolError("Class name '%s' is already defined") 
		self.C[c] = S

	def getClass(self, c):
		return self.C[c]
