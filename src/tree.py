class Node(object):
	TYPE = "node"
	TAB = '    '
	def __init__(self, *children):
		print "Creating '%s' with args" % self.TYPE, map(lambda x: x.TYPE if hasattr(x, 'TYPE') else x, children)
		self.children = children

	def __str__(self):
		return self.pretty()

	def pretty(self, depth = 0):
		t = self.TAB*depth
		if len(self.children) == 0:
			children = '()'
		else:
			children = ',\n'.join([child.pretty(depth+1) if isinstance(child, Node) else self.TAB*(depth+1) + repr(child) for child in self.children])
			children = ' (\n%s\n%s)' % (children, t)
		return "%(tab)s%(type)s%(children)s" % {
			'type' : self.TYPE,
			'tab' : t,
			'children' : children
		}
	
	def display(self):
		print str(self)

class Document(Node):
	TYPE = "document"

class Class(Node):
	TYPE = "class"

class Block(Node):
	Type = "block"
	def __init__(self, value = None, contents = ()):
		self.value = value
		self.contents = contents
		super(Block, self).__init__(value, *contents)

class Expr(Node):
	TYPE = "expr"

class MatchExpr(Expr):
	TYPE = "match"
	def __init__(self, e, cases):
		self.e = e
		self.cases = cases
		super(MatchExpr, self).__init__(e, cases)
	

class IfExpr(Expr):
	TYPE = "if"
	def __init__(self, cond, true, false):
		self.cond = cond
		self.true = true
		self.false = false
		super(IfExpr, self).__init__(cond, true, false)

class WhileExpr(Expr):
	TYPE = "while"
	def __init__(self, cond, control):
		self.cond = cond
		self.control = control
		super(WhileExpr, self).__init__(cond, control)

class DotExpr(Expr):
	TYPE = "dot"
	def __init__(self, this, id, actuals):
		self.this = this
		self.id = id
		self.actuals = actuals
		super(DotExpr, self).__init__(this, id, actuals)

class BinaryExpr(Expr):
	def __init__(self, left, right):
		self.left = left
		self.right = right
		super(BinaryExpr, self).__init__(left, right)

class UnaryExpr(Expr):
	def __init__(self, arg):
		self.arg = arg
		super(UnaryExpr, self).__init__(arg)

class AssignExpr(BinaryExpr):
	TYPE = "assign"

class LTExpr(BinaryExpr):
	TYPE = "lt"

class LEExpr(BinaryExpr):
	TYPE = "le"

class EqExpr(BinaryExpr):
	TYPE = "equals"

class AddExpr(BinaryExpr):
	TYPE = "add"

class SubExpr(BinaryExpr):
	TYPE = "subtract"

class MultExpr(BinaryExpr):
	TYPE = "multiply"

class DivExpr(BinaryExpr):
	TYPE = "divide"
	
class NotExpr(UnaryExpr):
	TYPE = "not"

class NegExpr(UnaryExpr):
	TYPE = "negation"


class Primary(Node):
	TYPE = "primary"

class Call(Primary):
	TYPE = "call"
	def __init__(self, type, actuals):
		self.type = type
		self.actuals = actuals
		super(Call, self).__init__(type, actuals)

class Super(Call):
	TYPE = "super"

class NullaryPrimary(Primary):
	pass

class Null(NullaryPrimary):
	TYPE = "null"

class This(NullaryPrimary):
	TYPE = "this"

class Unit(NullaryPrimary):
	TYPE = "unit"

class UnaryPrimary(Primary):
	def __init__(self, value):
		self.value = value
		super(UnaryPrimary, self).__init__(value)


class Symbol(Node):
	def __init__(self, name):
		self.name = name
		super(Symbol, self).__init__(name)

	def pretty(self, depth=0):
		return "%s%s('%s')" % (self.TAB*depth, self.TYPE, self.name)

class Identifier(Symbol):
	TYPE = "id"

class Literal(UnaryPrimary):
	def pretty(self, depth=0):
		return self.TAB*depth + repr(self.value)

class Integer(Literal):
	TYPE = "integer"

class Boolean(Literal):
	TYPE = "boolean"

class String(Literal):
	TYPE = "string"


class VarFormals(Node):
	TYPE = "varformals"

class Formals(Node):
	TYPE = "formals"

class Formal(Node):
	TYPE = "formal"

class Actuals(Node):
	TYPE = "actuals"

class Actual(Node):
	TYPE = "actual"

class Type(Symbol):
	TYPE = "type"
	def __init__(self, name):
		self.name = name
		super(Type, self).__init__(name)

class Feature(Node):
	TYPE = "feature"

class Def(Feature):
	TYPE = "def"
	def __init__(self, override, id, formals, type, value):
		self.override = override
		self.id = id
		self.formals = formals
		self.type = type
		self.value = value
		super(Def, self).__init__(override, id, formals, type, value)

class ClassBody(Node):
	TYPE = "classbody"

class ClassOpts(Node):
	TYPE = "classopts"

class VarInit(Feature):
	TYPE = "init"
	def __init__(self, i, type, value):
		self.id = id
		self.type = type
		self.value = value
		super(VarInit, self).__init__(id, type, value)

