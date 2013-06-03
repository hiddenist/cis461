def NodeCodeGen(object):
	def __init__(self, node):
		self.node = node
		self.token = node.token

	def generate(self):
		if hasattr(self.node, 'children'):
			for child in self.node.children:
				if hasattr(child, 'codegen'):
					child.codegen.generate()
