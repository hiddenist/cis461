from tree_linker import TreeLinker
from node_checker import NodeChecker
import nodes


class TypeChecker(TreeLinker):
	NODE_CLASSES = nodes.__dict__
	NODE_SUPERCLASS = NodeChecker
	LINK_NAME = 'checker'

	def check(self):
		self.tree.checker.pass1()
		self.tree.checker.check()

	
