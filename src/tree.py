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

	def __init__(self, *children):
		self.children = children

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
			children = texts['separator'].join([child.pretty(depth+1, style) if isinstance(child, Node) else self.TAB*(depth+1) + repr(child) for child in self.children])
			children = texts['wrapper'] % {'children':children, 'tab_inner': tinner, 'tab': t}
		return  texts['parent'] % {
				'type' : self.TYPE,
				'tab' : t,
				'tab_inner' : tinner,
				'children' : children
			}
	
	def display(self):
		print str(self)

class Document(Node):
	TYPE = "document"

class Class(Node):
	TYPE = "class"
	def __init__(self, type, formals, options, body):
		self.type = type
		self.formals = formals
		self.options = options
		self.body = body
		if options is None:
			super(Class, self).__init__(type, formals, body)
		else:
			super(Class, self).__init__(type, formals, options, body)

class List(Node):
	TYPE = "list"

class Native(Node):
	TYPE = "native"

class Formals(List):
	TYPE = "formals"

class Actuals(List):
	TYPE = "actuals"

class Block(Node):
	Type = "block"
	def __init__(self, value = None, contents = []):
		self.value = value
		self.contents = contents
		super(Block, self).__init__(value, *contents)

class Expr(Node):
	TYPE = "expr"

class MatchExpr(Expr):
	TYPE = "match"
	def __init__(self, expr, cases):
		self.expr = expr
		self.cases = cases
		super(MatchExpr, self).__init__(expr, *cases)

class Case(Node):
	TYPE = "case"
	def __init__(self, id, type, block):
		self.id = id
		self.type = type
		self.block = block
		super(Case, self).__init__(id, type, block)

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
	TYPE = "negative"

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

	def pretty(self, depth=0, style="parens"):
		if style == "parens":
			return '%s%s("%s")' % (self.TAB*depth, self.TYPE, self.name)
		elif style == "json":
			return '{"%s":"%s"}' % (self.TYPE, self.name)

		return super(Literal, self).pretty(depth, style)

class Identifier(Symbol):
	TYPE = "id"

class Literal(UnaryPrimary):
	def rep(self):
		return repr(self.value)

	def pretty(self, depth=0, style="parens"):
		if style == "parens":
			return self.TAB*depth + repr(self.value)
		elif style == "json":
			return '%s' % self.rep()

		return super(Literal, self).pretty(depth, style)

class Integer(Literal):
	TYPE = "integer"

class Boolean(Literal):
	TYPE = "boolean"

	def rep(self):
		return "true" if self.value else "false"

class String(Literal):
	TYPE = "string"

	def rep(self):
		# All just to print a double quoted raw string
		return '"%s"' % repr(self.value).replace('"', r'\"').replace(r"\'", "'")[1:-1]

class Formal(Node):
	TYPE = "formal"

class Actual(Node):
	TYPE = "actual"

class Type(Symbol):
	TYPE = "type"

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
		if override:
			super(Def, self).__init__(Override(), id, formals, type, value)
		else:
			super(Def, self).__init__(id, formals, type, value)

class Override(Node):
	Type = "override"
	def __init__(self):
		super(Override, self).__init__()

class ClassBody(Node):
	TYPE = "classbody"

class ClassOpts(Node):
	TYPE = "classopts"

class VarInit(Feature):
	TYPE = "init"
	def __init__(self, id, type, value):
		self.id = id
		self.type = type
		self.value = value
		super(VarInit, self).__init__(id, type, value)

