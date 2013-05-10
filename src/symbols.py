from error import TypeCheckError

class SymbolTable(object):
	def __init__(self):
		O = [{}]
		M = {}

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
		raise TypeCheckError("Variable '%s' was not initialized" % v)

	def getMethod(self, C, f):
		try:
			return self.M[(C, f)]
		except KeyError:
			raise TypeCheckError("Method '%s.%s' is not defined" % (C, f))

	def insertVar(self, v, T):
		self.O[-1][v] = T

	def insertMethod(self, C, f, t):
		self.M[(C, f)] = t
