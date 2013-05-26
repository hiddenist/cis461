UNINSTANTIABLE_TYPES = ('Any', 'Int', 'Unit', 'Boolean', 'Symbol')
NOT_NULLABLE_TYPES = ('Nothing', 'Boolean', 'Int', 'Unit')
UNINHERITABLE_TYPES = ('Unit', 'Int', 'String', 'Boolean', 'ArrayAny', 
	'Symbol', 'Null', 'Nothing')

class NodeChecker(object):
	def __init__(self, node):
		self.node = node
		self.token = node.token

	def getType(self):
		pass

	def pass1(self): 
		pass

	def check(self): 
		pass
	
