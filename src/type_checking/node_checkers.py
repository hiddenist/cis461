from node_checker import *
from error import TypeCheckError, SymbolError
from settings import DEBUG
import tree
from environment import env

# Each of the class names in this file should correspond to a class in the tree.py file

class Document(NodeChecker):
	def check(self):
		for child in self.node.children:
			child.check()

class Class(NodeChecker): 
	def pass1(self):
		# Define the class
		self.node.type.checker.define(self.node.superclass)

		# Define each of the methods
		for feature in self.node.body.children:
			if isinstance(feature, tree.Def):
				feature.checker.define(self.node.type.name)

	def check(self):
		if not isinstance(self.node.superclass, tree.Native):
			self.node.superclass.check()

		env.enterClassScope(self.node.type.name)

		for formal in self.node.formals.children:
			formal.id.checker.attrDefine(self.node.type, formal.type)

		for feature in self.node.body.children:
			if isinstance(feature, tree.VarInit):
				feature.id.checker.attrDefine(self.node.type, feature.type)
			else:
				feature.check()

		env.exitClassScope(self.node.type.name)

class Formals(NodeChecker):
	def getType(self):
		return [f.getType() for f in self.node.children]

class Block(NodeChecker):
	def getType(self):
		if not hasattr(self, 'type'):
			self.check()
		return self.type

	def check(self):
		env.enterScope()
		for line in self.node.contents:
			line.check()
		self.node.value.check()
		self.type = self.node.value.getType()
		env.exitScope()


class MatchExpr(NodeChecker):
	def getType(self):
		# Get the types of all of the cases...
		# Should we disclude nulls from this?  Hmm...
		types = [case.getType() for case in self.node.cases]
		t = Type.typeJoin(*types)

		# Join the types... my understanding is that this is to find a common parent class
		return t

	def check(self):
		types = []
		nulls = 0
		for case in self.node.cases:
			t = case.type.getType()

			if t.isNull():
				if nulls:
					TypeCheckError("More than one null case in match", self.token).report()
				else:
					nulls = 1
					continue

			for pt in types:
				if t.subsetOf(pt):
					TypeCheckError("Earlier case for type '%s' in match shadows type '%s'"
							% (pt, t), case.token).report()

			types.append(t)

		# Finally, compare the type of our match expression with all of the cases...
		etype = self.node.expr.getType()
		for t in types:
			if not etype.subsetOf(t) and not t.subsetOf(etype):
				TypeCheckError("Match expression of type '%s' is not compatible with case type '%s'"
					% (etype, t), self.token).report()
	

class Case(NodeChecker):
	def getType(self):
		return self.node.block.getType()
	
	def check(self):
		env.enterScope()
		self.node.id.checker.define(self.node.type, shadow=True)
		self.node.block.check()
		env.exitScope()


class IfExpr(NodeChecker):
	def getType(self):
		return Type.typeJoin(self.node.true.getType(), self.node.false.getType())

	def check(self):
		self.node.cond.check()
		self.node.true.check()
		self.node.false.check()
		if not self.node.cond.getType().isType("Boolean"):
			TypeCheckError("If condition must be a boolean", self.node.cond.token).report()


class WhileExpr(NodeChecker):
	def getType(self):
		return Type("Unit")

	def check(self):
		self.node.cond.check()
		self.node.control.check()
		if not self.node.cond.getType().isType("Boolean"):
			TypeCheckError("Loop condition must be a boolean", self.cond.token).report()


class Dot(NodeChecker):
	def getType(self):
		print "Todo: dot type check"
		return Type("Null")


class AssignExpr(NodeChecker):
	def getType(self):
		return Type("Unit")

	def check(self):
		self.node.left.check()
		self.node.left.check()
		ltype = self.node.left.getType()
		rtype = self.node.right.getType()

		if not rtype.subsetOf(ltype):
			TypeCheckError("Type '%s' can not be assigned to variable of type '%s'" 
				% (rtype, ltype)).report()

class CompExpr(NodeChecker):
	def getType(self):
		return Type("Boolean")

class IntCompExpr(CompExpr):
	def check(self):
		self.node.left.check()
		self.node.right.check()
		ltype = self.node.left.getType()
		rtype = self.node.right.getType()

		invalid = None
		if not ltype.isType("Int"):
			invalid = self.node.left
		elif not rtype.isType("Int"):
			invalue = self.node.right

		if invalid:
			TypeCheckError("Cannot compare '%s' to '%s'; both must be Int" 
				% (ltype, rtype), invalid.token).report()

class LTExpr(IntCompExpr): pass
class LEExpr(IntCompExpr): pass
class EqExpr(CompExpr): pass

class ArithExpr(NodeChecker):
	def getType(self):
		return Type("Int")

	def check(self):
		self.node.left.check()
		self.node.right.check()
		ltype = self.node.left.getType()
		rtype = self.node.right.getType()

		invalid = None

		if not ltype.isType("Int"):
			invalid = self.node.left
		elif not rtype.isType("Int"):
			invalid = self.node.right

		if invalid:
			TypeCheckError("Cannot apply arithmetic operation to types "
				+ "'%s' and '%s';" % (ltype, rtype)
				+ " both must be Int" , invalid.token).report()

class AddExpr(ArithExpr): pass
class SubExpr(ArithExpr): pass
class MultExpr(ArithExpr): pass
class DivExpr(ArithExpr): pass

class NotExpr(NodeChecker):
	def getType(self):
		return Type("Boolean")

	def check(self):
		self.node.arg.check()
		if not self.node.arg.getType().isType("Boolean"):
			TypeCheckError("'Not' operator may only be used with argument of type 'Boolean'", 
				self.token).report()


class NegExpr(NodeChecker):
	def getType(self):
		return Type("Int")

	def check(self):
		self.node.arg.check()
		if not self.node.arg.getType().isType("Int"):
			TypeCheckError("Negation operator may only be used with argument of type 'Int'", 
				self.token).report()

class Call(NodeChecker):
	def getMethod(self):
		if isinstance(self.node.method, tree.Identifier):
			c = env.getVar('this')
			n = self.node.method.name
		elif isinstance(self.node.method, tree.Dot):
			c = self.node.method.parent.getType().name
			n = self.node.method.child.name
		else:
			print "What else can a method call be made of?"

		try:
			return c, n, env.getMethod(c, n)
		except SymbolError, e:
			e.setToken(self.token)
			e.report()
			return None, None, ['Nothing']

	def getType(self):
		return Type(self.getMethod()[-1][-1])

	def check(self):
		c, m, args = self.getMethod()
		ret, args = args[-1], args[:-1]
		if len(self.node.actuals.children) != len(args):
			TypeCheckError("Method '%s' of class '%s' requires %d arguments; received %d"
				% (m, c, len(args), len(self.node.actuals.children)), self.token).report()
		else:
			for i, actual in enumerate(self.node.actuals.children):
				if not actual.getType().subsetOf(args[i]):
					TypeCheckError("Provided argument does not match type in method definition;"
						+ " '%s' is not compatible with '%s'" 
						% (actual.getType().name, args[i]), actual.token).report()

class Super(Call):
	def getMethod(self):
		c = env.getVar('super')
		n = self.node.method.name
		return c, n, env.getMethod(c, n)

class Null(NodeChecker):
	def getType(self):
		return Type("Null")

class This(NodeChecker):
	def getType(self):
		return Type(env.getVar('this'))

class Unit(NodeChecker):
	def getType(self):
		return Type("Unit")

class Integer(NodeChecker):
	def getType(self):
		return Type("Int")

class Boolean(NodeChecker):
	def getType(self):
		return Type("Boolean")

class String(NodeChecker):
	def getType(self):
		return Type("String")

class Formal(NodeChecker):
	def getType(self):
		return self.node.type.getType()

class Constructor(NodeChecker):
	def check(self):
		if self.node.type.name in UNINSTANTIABLE_TYPES:
			TypeCheckError("Objects of type '%s' are uninstantiable", self.token).report()

	def getType(self):
		return self.node.type.getType()

class VarInit(NodeChecker):
	def getType(self):
		return self.node.type.getType()
	
	def check(self):
		self.node.value.check()
		valuetype = self.node.value.getType()
		if not valuetype.subsetOf(self.getType()):
			TypeCheckError("Value of type '%s' can't be assigned to variable of type '%s'"
				% (valuetype, self.getType()), self.token).report()

		self.node.id.checker.define(self.getType())

class Def(NodeChecker):
	def define(self, c):
		self.c = c
		# Just define it - don't type check since we can't yet anyways
		args = tuple(f.name for f in self.node.formals.getType())
		try:
			env.defineMethod(c, self.node.id.name, args + (self.node.type.name,))
		except SymbolError, e:
			e.setToken(self.token)
			e.report()

	def getType(self):
		return self.node.type.getType()

	def check(self):
		if isinstance(self.node.value, tree.Native):
			return

		args = tuple(f.name for f in self.node.formals.getType())
		try:
			super_method = env.getMethod(env.getSuperClass(self.c), self.node.id.name)
			if self.node.override:
				sargs = super_method[:-1]
				if len(args) != len(sargs):
						TypeCheckError("Overriding method does not have the same number of arguments as "
							+ "overridden method", self.token).report()
				else: 
					for arg, sarg in zip(args, sargs):
						if arg != sarg:
							TypeCheckError("Overriding method argument types do not match overridden method "
								+"types", self.token).report()
							break
				
				if not self.getType().subsetOf(super_method[-1]):
					TypeCheckError("Overriding method type is not compatible with overridden method type",
						self.node.type.token).report()
			else:
				TypeCheckError("Overriding method must use override keyword", self.token).report()
		except SymbolError, e:
			if self.node.override:
				TypeCheckError("Method is set to override, but does not exist in ancestor classes", 
					self.token).report()
			else:
				e.ignore()

		env.enterScope()
		
		for formal in self.node.formals.children:
			formal.id.checker.define(formal.type.getType(), shadow=True)

		self.node.type.check()

		self.node.value.check()

		t = self.node.value.getType()
		if t is None or not t.subsetOf(self.getType()):
			TypeCheckError("Method result '%s' does not match method return type '%s'" % (t, self.getType()), 
				self.node.type.token).report()

		env.exitScope()

class Identifier(NodeChecker):
	def getType(self):
		try:
			return Type(env.getVar(self.node.name))
		except SymbolError, e:
			e.setToken(self.token)
			e.report()

	def attrDefine(self, attrClass, attrType):
		try:
			env.defineAttr(attrClass.name, self.node.name, attrType.name)
		except SymbolError, e:
			e.setToken(self.token)
			e.report()

	def check(self):
		self.getType()

	def define(self, idType, shadow=False):
		if not shadow:
			try:
				env.getVar(self.node.name)
			except SymbolError, e:
				e.ignore()
			else:
				e = SymbolError("The variable '%s' is already defined and may not shadow" % self.node.name,
					self.token)
				e.report()
				return

		try:
			env.defineVar(self.node.name, idType.name)
		except SymbolError, e:
			e.setToken(self.token)
			e.report()

class Type(NodeChecker):
	def __str__(self):
		return str(self.name)

	def __init__(self, name):
		if isinstance(name, tree.Type):
			super(Type, self).__init__(name)
			self.name = self.node.name
		elif isinstance(name, str):
			self.name = name
		else:
			raise Exception("Type must take a tree node or string as an argument")

	def getType(self):
		return self

	@staticmethod
	def typeJoin(*types):
		""" 
			Find the common ancestor in a list of types.
			Returns None if no such ancestor exists.
		"""
		if len(types) == 0:
			return None

		if len(types) == 1:
			return types[0]

		# Let's just compare the entire list to the last class in the list.
		# For match statements, the last class should be the most general.
		# However, if we choose a null case, choose the second to last.

		# If this type join is used for more than just match statements, I really need to rethink this.

		types = list(types)
		s = types.pop()
		if s.isNull():
			s, _ = types.pop(), types.append(s) 

		found = False
		while s is not None:
			violated = False

			for t in types:
				if not t.subsetOf(s):
					violated = True
					break

			if violated:
				s = s.parent()
			else:
				return s

		return None

	def isNull(self):
		return self.name == 'Null'

	def parent(self):
		s = env.getSuperClass(self.name)
		if s is None:
			return Type("Nothing")
		return Type(s)

	def define(self, superclass):
		if superclass.name in UNINHERITABLE_TYPES:
			TypeCheckError("Class '%s' may not extend type '%s'" 
				% (self.name, superclass), self.token).report()
		try:
			if isinstance(superclass, tree.Native):
				env.defineClass(self.name, None)
			else:
				env.defineClass(self.name, superclass.name)
		except SymbolError, e:
			e.setToken(self.token)
			e.report()

	def typeCheck(self):
		try:
			env.getSuperClass(self.name)
		except SymbolError, e:
			e.setToken(self.token)
			e.report()

	def isType(self, t):
		if isinstance(t, Type):
			t = t.name
		return self.name == t 

	def subsetOf(self, t):
		"Checks compatibility between types"
		# Null can be any type except for a few specified, built-in types
		if self.isNull():
			if isinstance(t, Type):
				t = t.name
			return t not in NOT_NULLABLE_TYPES

		c = self.name
		# Check if this class or any of its ancestors match the provided type
		while c is not None:
			c = Type(c)
			if c.isType(t):
				return True
			c = env.getSuperClass(c.name)

		return False
	
