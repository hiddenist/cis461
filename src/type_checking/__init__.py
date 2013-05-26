import tree
from node_checker import NodeChecker
import node_checkers

checker_classes = node_checkers.__dict__

class TypeChecker(object):
	def __init__(self, tree):
		"Create the correct kind of typechecking node for this class"
		self.root = tree
		self.pass1_checkers = []
		self.set_checkers(tree)

	def set_checkers(self, tree):
		"Recursively define the type checker for every node in the tree"
		has_checker = TypeChecker.set_checker(tree)

		if has_checker and hasattr(tree.checker, 'pass1'):
			self.pass1_checkers.append(tree.checker)

		if hasattr(tree, 'children'):
			for child in tree.children:
				self.set_checkers(child)

	@staticmethod
	def set_checker(node):
		if isinstance(node, tree.Node):
			name = node.__class__.__name__
			if name in checker_classes:
				checker = checker_classes[name]
				if issubclass(checker, NodeChecker):
					node.checker = checker(node)
					return True
		return False

	def pass1(self):
		for checker in self.pass1_checkers:
			checker.pass1()

	def check(self):
		self.pass1()
		self.root.checker.check()

	
