from tree_linker import TreeLinker
from node_code_gen import NodeCodeGen
import nodes

class CodeGen(TreeLinker):
  NODE_CLASSES = nodes.__dict__
  NODE_SUPERCLASS = NodeCodeGen
  LINK_NAME = 'codegen'

  def generate(self):
    return self.tree.codegen.generate()
