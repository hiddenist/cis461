class Node(object):
	def __init__(self, *children):
		self.children = children

class Expr(Node):
	pass

class IfExpr(Expr):
	def __init__(self, cond, true, false):
		self.cond = cond
		self.true = true
		self.false = false
		super(IfExpr, self).__init__(cond, true, false)

class WhileExpr(Expr):
	def __init__(self, cond, control):
		self.cond = cond
		self.control = control
		super(WhileExpr, self).__init__(cond, control)

class DotExpr(Expr):
	def __init__(self, actuals, id, prop):
		self.actuals = actuals
		self.id = id
		self.prop = prop
		super(IfExpr, self).__init__(actuals, id, prop)

class BinaryExpr(Expr):
	def __init__(self, lhs, rhs):
		self.lhs = lhs
		selg.rhs = rhs
		super(BinaryExpr, self).__init__(lhs, rhs)

class UnaryExpr(Expr):
	def __init__(self, arg):
		self.arg = arg
		super(UnaryExpr, self).__init__(arg)

class LTExpr(BinaryExpr):
	pass

class LTEExpr(BinaryExpr):
	pass

class EqExpr(BinaryExpr):
	pass

class AddExpr(BinaryExpr):
	pass

class SubExpr(BinaryExpr):
	pass

class MultExpr(BinaryExpr):
	pass

class DivExpr(BinaryExpr):
	pass
	
class NotExpr(UnaryExpr):
	pass

class NegExpr(UnaryExpr):
	pass
