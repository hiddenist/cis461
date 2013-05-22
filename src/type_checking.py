from error import SymbolError
from settings import SYMBOL_DEBUG as DEBUG


UNINSTANTIABLE_TYPES = ('Any', 'Int', 'Unit', 'Boolean', 'Symbol')
NOT_NULLABLE_TYPES = ('Nothing', 'Boolean', 'Int', 'Unit')
UNINHERITABLE_TYPES = ('Unit', 'Int', 'String', 'Boolean', 'ArrayAny', 
	'Symbol', 'Null', 'Nothing')

class Environment(object):
	def __init__(self):
		# Variables and their type, for each scope
		self.O = []

		# Methods and their parameter types
		self.M = {
			('String', 'charAt') : ('Int', 'Int'),
			('String', 'concat') : ('String', 'String', 'String'),
			('Any', 'toString') : ('String',),
			('IO', 'out') : ('String', 'IO')
		}

		# Classes and their superclasses
		self.C = { # built-in types (for now?):
			'Any': None,
			'Unit' : 'Any',
			'Int' : 'Any',
			'String' : 'Any',
			'Boolean' : 'Any',
			'ArrayAny' : 'Any',
			'IO' : 'Any',
			'Symbol' : 'Any',
			'Null' : None,
			'Nothing': None,
		}

		# Class attributes (types stores in O)
		self.Oc = {}

		# For all of the built in types, initialize no params
		for c in self.C:
			self.Oc[c] = {}

	def enterClassScope(self, c):
		"Put all class attributes in scope"

		# Create a scope hierarchy for each superclass' attributes
		parent = self.getSuperClass(c)
		while parent is not None:
			if parent in self.C:
				self.enterScope(self.Oc[parent])
				parent = self.getSuperClass(parent)
			else:
				parent = None

		self.enterScope({'this': c, 'super': self.getSuperClass(c)})

	def exitClassScope(self, c):
		# Exit class' scope:
		self.exitScope()
		# Exit attribute scopes:
		parent = self.getSuperClass(c)
		while parent is not None:
			self.exitScope()
			parent = self.getSuperClass(parent)

	def enterScope(self, vs=None):
		if vs is None:
			vs = {}
		self.O.append(vs)

	def exitScope(self):
		self.O.pop()

	def defineAttr(self, c, v, T):
		try:
			self.hasAttr(c, v)
		except SymbolError, e:
			e.ignore()
			self.Oc[c][v] = T
			self.defineVar(v, T)
		else:
			raise SymbolError("Class '%s' attribute named '%s'" % (c, v)
				+ " is already defined (perhaps in a superclass)")

	def hasAttr(self, c, v):
		orig = c
		while c is not None:
			if c in self.C:
				if v in self.Oc[c]:
					return True
				c = self.getSuperClass(c)
			else:
				c = None
		raise SymbolError("Class '%s' has no attribute '%s'" % (c, v))

	def defineVar(self, v, T):
		# Get the current stack scope
		d = self.O[-1]
		if v in d:
			raise SymbolError("The variable '%s' was already defined in this scope." % v)
		else:
			d[v] = T

	def defineMethod(self, C, f, t):
		if (C, f) in self.M:
			raise SymbolError("Method named '%s' already defined for class '%s'" % (f, C))

		self.M[(C, f)] = t

	def defineClass(self, c, S):
		if c in self.C:
			raise SymbolError("Class name '%s' is already defined")
		self.C[c] = S
		self.Oc[c] = {}

	def getVar(self, v):
		for d in reversed(self.O):
			try:
				return d[v]
			except KeyError:
				continue
		raise SymbolError("Variable '%s' was not initialized" % v)

	def getMethod(self, C, f):
		s = C
		while s is not None:
			try:
				return self.M[(s, f)]
			except KeyError:
				s = self.getSuperClass(s)
			
		raise SymbolError("Class '%s' does not have a method '%s' defined" % (C, f))

	def getSuperClass(self, c):
		try:
			return self.C[c]
		except KeyError:
			if DEBUG: print type(c), self.C
			raise SymbolError("Type '%s' has not been defined" % c)
