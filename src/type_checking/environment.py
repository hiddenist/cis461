from error import SymbolError
from settings import SYMBOL_DEBUG as DEBUG, SIMULATE_BASIC

class Environment(object):
	def __init__(self):
		# Variables and their type, for each scope
		self.O = []

		# Methods and their parameter types
		self.M = {}

		# Classes and their superclasses
		self.C = {
			'Nothing': None,
			'Null' : None,
		}

		# Class attributes (types stores in O)
		self.Oc = {}

		# For all of the special types above, initialize with no parameters
		for c in self.C:
			self.Oc[c] = {}

		if SIMULATE_BASIC:
			self.C['Any'] = None
			self.C['Unit'] = 'Any'
			self.C['Int'] = 'Any'
			self.C['String'] = 'Any'
			self.C['Boolean'] = 'Any'
			self.C['ArrayAny'] = 'Any'
			self.C['IO'] = 'Any'
			self.C['Symbol'] = 'Any'
			
			for c in self.C:
				self.Oc[c] = {}

			self.M = { 
				('Any', 'toString') : ('String',),
				('Any', 'equals') : ('Any', 'Boolean',),
				('IO', 'abort') : ('String', 'Nothing',),
				('IO', 'out') : ('String', 'IO',),
				('IO', 'is_null') : ('Any', 'Boolean',),
				('IO', 'out_any') : ('Any', 'IO',),
				('IO', 'in') : ('String',),
				('IO', 'symbol') : ('String','Symbol',),
				('IO', 'symbol_name') : ('Symbol','String',),
				('String', 'length') : ('Int',),
				('String', 'charAt') : ('Int', 'Int',),
				('String', 'concat') : ('String', 'String', 'String',),
				('String', 'substring') : ('Int', 'Int', 'String',),
				('String', 'indexOf') : ('String', 'Int',),
				('Symbol', 'hashCode'): ('Int',),
				('ArrayAny', 'length') : ('Int',),
				('ArrayAny', 'resize') : ('Int','ArrayAny',),
				('ArrayAny', 'get') : ('Int', 'Any',),
				('ArrayAny', 'set') : ('Int', 'Any', 'Any',),
			}

			self.Oc['Int']['value'] = 'Int'
			self.Oc['Boolean']['value'] = 'Boolean'
			self.Oc['String']['length'] = 'Int'
			self.Oc['String']['str_field'] = 'String'
			self.Oc['Symbol']['next'] = 'Symbol'
			self.Oc['Symbol']['name'] = 'String'
			self.Oc['Symbol']['hash'] = 'Int'
			self.Oc['ArrayAny']['array_field'] = 'ArrayAny'


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

	def checkClassHierarchy(self):
		checked = set()
		for cls in self.C:
			if cls in checked:
				continue

			family = set()
			while cls is not None:
					
				if cls in family:
					raise SymbolError("The class hierarchy is not a tree - class '%s' is its own ancestor"
						% cls)
				family.add(cls)
				checked.add(cls)
				try:
					# Ignore non-existing superclasses here because the classes will check that
					# and can output a more useful error message.
					cls = self.C[cls]
				except KeyError:
					break

env = Environment()
