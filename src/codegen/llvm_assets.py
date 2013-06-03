# The LLVM module, which holds all the IR code.
llvm_module = Module.new("Cool2013")

# The LLVM instruction builder. Created whenever a new function is entered.
llvm_builder = None

# A dictionary that keeps track of which values are defined in the current scope
# and what their LLVM representation is.
named_values = ()

