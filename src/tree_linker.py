from tree import Node

class TreeLinker(object):
	NODE_CLASSES = {}
	NODE_SUPERCLASS = object
	LINK_NAME = 'linked_node'
	TREE_NODE = Node

	def __init__(self, tree):
		self.tree = tree
		self.link_nodes(tree)

	@classmethod
	def link_nodes(cls, tree):
		cls.link_node(tree)

		if hasattr(tree, 'children'):
			for child in tree.children:
				cls.link_nodes(child)

	@classmethod
	def link_node(cls, node):
		if isinstance(node, cls.TREE_NODE):
			name = node.__class__.__name__
			if name in cls.NODE_CLASSES:
				linked = cls.NODE_CLASSES[name]
				if issubclass(linked, cls.NODE_SUPERCLASS):
					setattr(node, cls.LINK_NAME, linked(node))
					return True
		return False
