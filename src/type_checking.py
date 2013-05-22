from error import SymbolError
from settings import SYMBOL_DEBUG as DEBUG


UNINSTANTIABLE_TYPES = ('Any', 'Int', 'Unit', 'Boolean', 'Symbol')
NOT_NULLABLE_TYPES = ('Nothing', 'Boolean', 'Int', 'Unit')
UNINHERITABLE_TYPES = ('Null', 'Nothing')

class Environment(object):
	def __init__(self):
		# Variables and their type, for each scope
		self.O = []

		# Methods and their parameter types
		self.M = {}

		# Classes and their superclasses
		self.C = { # built-in types (for now?):
			'Any': None,
			'String' : 'Any',
			'Int' : 'Any',
			'Boolean' : 'Any',
			'Null' : None,
			'Nothing': None,
		}

		# Class attributes (types stores in O)
		self.Oc = {}

		# For all of the built in types, initialize no params
		for c in self.C:
			self.Oc[c] = []

	def enterScope(self):
		self.O.append({})

	def exitScope(self):
		self.O.pop()

	def defineAttr(self, c, v):
		try:
			self.hasAttr(c, v)
		except SymbolError, e:
			e.ignore()
			self.Oc[c].append(v)
		else:
			raise SymbolError("Class '%s' attribute named '%s'" % (c, v)
				+ "is already defined (perhaps in a superclass)")

	def hasAttr(self, c, v):
		orig = c
		while c is not None:
			if v in self.Oc[c]:
				return True
			c = self.getSuperClass(c)
		raise SymbolError("Class '%s' has no attribute '%s'" % (c, v))

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
		self.Oc[c] = []

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
