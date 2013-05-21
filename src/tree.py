from error import Error, SymbolError, TypeCheckError
from type_checking import Environment
from type_checking import UNINSTANTIABLE_TYPES, NOT_NULLABLE_TYPES, UNINHERITABLE_TYPES

env = Environment()

class Node(object):
	TYPE = "node"
	TAB = '    '

	STRINGS = {
		"json": {
			"empty": "[]",
			"separator": ", ",
			"wrapper": "[%(children)s]",
			"parent": "{\"%(type)s\" : %(children)s}"
		},
		"parens": {
			"empty": "()",
			"separator": ",\n",
			"wrapper": "(\n%(children)s\n%(tab)s)",
			"parent": "%(tab)s%(type)s%(children)s"
		}
	}

	def __init__(self, children=[], token=None):
		self.children = children
		self.token = token

	def typeCheck(self):
		for child in self.children:
			child.typeCheck()

	def __getitem__(self, idx):
		return self.children[idx]

	def __str__(self):
		return self.pretty()

	def json_str(self, depth = 0):
		return self.pretty(depth, 'json')

	def pretty(self, depth = 0, style='parens'):
		texts = self.STRINGS[style]
		t = self.TAB*depth
		tinner = self.TAB*(depth+1)
		if len(self.children) == 0:
			children = texts['empty']
		else:
			children = texts['separator'].join([
				child.pretty(depth+1, style) 
					if isinstance(child, Node) 
					else self.TAB*(depth+1) + repr(child) for child in self.children
			])
			children = texts['wrapper'] % {'children':children, 'tab_inner': tinner, 'tab': t}
		out = texts['parent'] % {
				'type' : self.TYPE,
				'tab' : t,
				'tab_inner' : tinner,
				'children' : children
			}

		# Escape backslashes in JSON... and make sure to keep double quotes escaped for JSON.
		if depth == 0 and style == "json":
			import re
			regex = re.compile(r'\\(.)')
			out = regex.sub(lambda m: r'\\\"' if m.group(1) == '"' else r'\\' + m.group(1), out)

		return out
	
	def display(self):
		print str(self)

class Document(Node):
	TYPE = "document"

class Class(Node):
	TYPE = "class"
	def __init__(self, type, formals, options, body, token=None):
		self.type = type
		self.formals = formals
		self.options = options
		self.body = body
		self.superclass = options.type

		type.define(self.superclass)

		super(Class, self).__init__([type, formals, options, body], token=token)

class ClassBody(Node):
	TYPE = "classbody"

class ClassOpts(Node):
	TYPE = "classopts"

	def __init__(self, type, actuals, token=None):
		self.type = type
		self.actuals = actuals
		super(ClassOpts, self).__init__([type, actuals], token=token)

class List(Node):
	TYPE = "list"

class Native(Node):
	TYPE = "native"

class Formals(List):
	TYPE = "formals"

class Actuals(List):
	TYPE = "actuals"

class Block(Node):
	TYPE = "block"
	def __init__(self, value, contents = [], token=None):
		self.value = value
		self.contents = contents
		super(Block, self).__init__( contents + [value], token=token)

	def getType(self):
		return self.value.getType()

	def typeCheck(self):
		env.enterScope()
		for line in self.contents:
			line.typeCheck()
		val = self.value.typeCheck()
		env.exitScope()
		return val

class Expr(Node):
	TYPE = "expr"

class MatchExpr(Expr):
	TYPE = "match"

	def __init__(self, expr, cases, token=None):
		self.expr = expr
		self.cases = cases
		super(MatchExpr, self).__init__([expr] + cases, token=token)

	def getType(self):
		# Get the types of all of the cases...
		# Should we disclude nulls from this?  Hmm...
		types = [case.getType() for case in self.cases]

		# Join the types... my understanding is that this is to find a common parent class
		return env.typeJoin(*types)

	def typeCheck(self):
		types = []
		nulls = 0
		for case in self.cases:
			t = case.getType()

			if t.isNull():
				if nulls:
					raise TypeCheckError("More than one null case in match", self.token)
				else:
					nulls = 1
					continue

			for pt in types:
				if t.subsetOf(pt):
					raise TypeCheckError("Earlier case for type '%s' in match shadows type '%s'"
							% (pt, t), case.token
						)

			types.append(t)

		# Finally, compare the type of our match expression with all of the cases...
		etype = self.expr.getType()
		for t in types:
			if not etype.subsetOf(t) and not t.subsetOf(etype):
				raise TypeCheckError("Match expression of type '%s' is not compatible with case type '%s'"
					% (etype, t), self.token)

class Case(Node):
	TYPE = "case"
	def __init__(self, id, type, block, token=None):
		self.id = id
		self.type = type
		self.block = block
		super(Case, self).__init__([id, type, block], token=token)

	def getType(self):
		return self.type
	
	def typeCheck(self):
		env.enterScope()
		self.id.define(shadow=True)
		self.block.typeCheck()
		env.exitScope()

class IfExpr(Expr):
	TYPE = "if"
	def __init__(self, cond, true, false, token=None):
		self.cond = cond
		self.true = true
		self.false = false
		super(IfExpr, self).__init__([cond, true, false], token=token)

class WhileExpr(Expr):
	TYPE = "while"
	def __init__(self, cond, control, token=None):
		self.cond = cond
		self.control = control
		super(WhileExpr, self).__init__([cond, control], token=token)

	def getType(self):
		return Type("Unit")

	def typeCheck(self):
		super(WhileExpr, self).typeCheck()
		if not self.cond.getType().isType("Boolean"):
			raise TypeCheckError("Loop condition must be a boolean")
		pass

class Dot(Node):
	TYPE = "dot"
	def __init__(self, parent, child, token=None):
		self.parent = parent
		self.child = child
		super(Dot, self).__init__([parent, child], token=token)

	def getType(self):
		print "Uninitialized"
		return Type("Null")

class BinaryExpr(Expr):
	def __init__(self, left, right, token=None):
		self.left = left
		self.right = right
		super(BinaryExpr, self).__init__([left, right], token=token)

class UnaryExpr(Expr):
	def __init__(self, arg, token=None):
		self.arg = arg
		super(UnaryExpr, self).__init__([arg], token=token)

class AssignExpr(BinaryExpr):
	TYPE = "assign"

	def getType(self):
		return Type("Unit")

	def typeCheck(self):
		super(AssignExpr, self).typeCheck()

		ltype = self.left.getType()
		rtype = self.right.getType()

		if not rtype.subsetOf(ltype):
			raise TypeCheckError("Type '%s' can not be assigned to variable of type '%s'" 
				% (rtype, ltype))

class CompExpr(BinaryExpr):
	def getType(self):
		return Type("Boolean")

class IntCompExpr(CompExpr):
	def typeCheck(self):
		super(IntCompExpr, self).typeCheck()

		ltype = self.left.getType()
		rtype = self.right.getType()

		if not ltype.isType("Int") or not rtype.isType("Int"):
			raise TypeCheckError("Cannot compare '%s' to '%s'; both must be Int" 
				% (ltype, rtype), self.token)

		

class LTExpr(IntCompExpr):
	TYPE = "lt"

class LEExpr(IntCompExpr):
	TYPE = "le"

class EqExpr(CompExpr):
	TYPE = "equals"

class ArithExpr(BinaryExpr):
	def getType(self):
		return Type("Int")

	def typeCheck(self):
		ltype = self.left.getType()
		rtype = self.right.getType()
		if not ltype.isType("Int") or not rtype.isType("Int"):
			raise TypeCheckError("Cannot apply arithmetic operation to types '%s' and '%s'; both must be Int" 
				% (ltype, rtype), self.token)

class AddExpr(ArithExpr):
	TYPE = "add"

class SubExpr(ArithExpr):
	TYPE = "subtract"

class MultExpr(ArithExpr):
	TYPE = "multiply"

class DivExpr(ArithExpr):
	TYPE = "divide"
	
class NotExpr(UnaryExpr):
	TYPE = "not"

class NegExpr(UnaryExpr):
	TYPE = "negative"

class Primary(Node):
	TYPE = "primary"

class Call(Primary):
	TYPE = "call"
	def __init__(self, type, actuals, token=None):
		self.type = type
		self.actuals = actuals
		super(Call, self).__init__([type, actuals], token=token)

class Super(Call):
	TYPE = "super"

class NullaryPrimary(Primary):
	def __init__(self, token=None):
		super(NullaryPrimary, self).__init__(token=token)

class Null(NullaryPrimary):
	TYPE = "null"
	def getType(self):
		return Type("Null")

class This(NullaryPrimary):
	TYPE = "this"

class Unit(NullaryPrimary):
	TYPE = "unit"
	def getType():
		return Type("Unit")

class UnaryPrimary(Primary):
	def __init__(self, value, token=None):
		self.value = value
		super(UnaryPrimary, self).__init__([value], token=token)

class Symbol(Node):
	def __init__(self, name, token=None):
		self.name = name
		super(Symbol, self).__init__([name], token=token)

	def pretty(self, depth=0, style="parens"):
		if style == "parens":
			return '%s%s("%s")' % (self.TAB*depth, self.TYPE, self.name)
		elif style == "json":
			return '{"%s":"%s"}' % (self.TYPE, self.name)

		return super(Literal, self).pretty(depth, style)

	def typeCheck(self):
		pass

class Identifier(Symbol):
	TYPE = "id"

	def getType(self):
		return Type(env.getVar(self.name))

	def define(self, type, shadow=False):
		if not shadow:
			try:
				env.getVar(self.name)
			except SymbolError, e:
				e.ignore()
			else:
				raise SymbolError("The variable '%s' is already defined and may not shadow." % self.id, 
					self.token)

		env.defineVar(self.name, type.name)

class Literal(UnaryPrimary):
	def rep(self):
		return repr(self.value)

	def getType(self):
		return Type(self.CLASSTYPE)

	def pretty(self, depth=0, style="parens"):
		if style == "parens":
			return self.TAB*depth + repr(self.value)
		elif style == "json":
			return self.rep()

		return super(Literal, self).pretty(depth, style)

	def typeCheck(self):
		pass

class Integer(Literal):
	TYPE = "integer"
	CLASSTYPE = "Int"

class Boolean(Literal):
	TYPE = "boolean"
	CLASSTYPE = "Boolean"

	def rep(self):
		return "true" if self.value else "false"

class String(Literal):
	TYPE = "string"
	CLASSTYPE = "String"

	def rep(self):
		# All just to print a double quoted raw string
		return '"%s"' % repr(self.value).replace('"', r'\"').replace(r"\'", "'")[1:-1]

class Formal(Node):
	TYPE = "formal"
	def __init__(self, id, type, token=None):
		self.id = id
		self.type = type
		super(Formal, self).__init__([id, type], token=token)

	def typeCheck(self):
		self.id.define(self.type)

class Actual(Node):
	TYPE = "actual"

class Type(Symbol):
	TYPE = "type"

	def __str__(self):
		return self.name

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
		return Type(env.getSuperClass(self.name))

	def define(self, superclass):
		if superclass in UNINHERITABLE_TYPES:
			raise TypeCheckError("Class '%s' may not extend type '%s'" % (self.name, superclass), self.token)
		try:
			env.defineClass(self.name, superclass.name)
		except SymbolError, e:
			e.setToken(self.token)
			raise e

	def typeCheck(self):
		try:
			env.getSuperClass(self.name)
		except SymbolError, e:
			e.setToken(self.token)
			raise e

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

class Constructor(Node):
	TYPE = "constructor"
	def __init__(self, type, actuals, token=None):
		# Type check rule for new disallows the following types
		if type in UNINSTANTIABLE_TYPES:
			raise TypeCheckError("Objects of type '%s' are uninstantiable.")
		self.type = type
		self.actuals = actuals
		super(Constructor, self).__init__([type, actuals], token=token)

class Feature(Node):
	TYPE = "feature"

class Def(Feature):
	TYPE = "def"
	def __init__(self, override, id, formals, type, value, token=None):
		self.override = override
		self.id = id
		self.formals = formals
		self.type = type
		self.value = value
		if override:
			super(Def, self).__init__([Override(), id, formals, type, value], token=token)
		else:
			super(Def, self).__init__([id, formals, type, value], token=token)

class Override(Node):
	Type = "override"

class VarInit(Feature):
	TYPE = "init"
	def __init__(self, id, type, value, token=None):
		self.id = id
		self.type = type
		self.value = value
		self.local = False
		super(VarInit, self).__init__([id, type, value], token=token)

	def setLocal(self):
		self.local = True
		return self

	def getType(self):
		return Type(self.type)
	
	def typeCheck(self):
		super(VarInit, self).typeCheck()

		valuetype = self.value.getType()
		if not valuetype.subsetOf(self.type):
			raise TypeCheckError("Value of type '%s' can't be assigned to variable of type '%s'"
				% (valuetype, self.type), self.token)

		self.id.define(self.type)
