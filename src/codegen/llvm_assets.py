from llvm.core import *

# A decorator which turns a no-argument function into a variable using its return method.
# The decorated class is not callable.  This is just useful for block-scope variables.
def variable(fn):
	return fn()


# The LLVM module, which holds all the IR code.
module = Module.new("Cool2013")

# The LLVM instruction builder. Created whenever a new function is entered.
builder = None

# A dictionary that keeps track of which values are defined in the current scope
# and what their LLVM representation is.
named_values = {}


# Struct for object - contains reference to class, class vars
# Struct for class - reference to super, class methods

built_in_types = ('any','io','unit','int','boolean','string','symbol','arrayany')

for ty in built_in_types:
	class_name = '%s_class' % ty
	obj_name = '%s_obj' % ty
	cls = globals()[class_name] = Type.opaque(class_name)
	globals()[class_name + "_ptr"] = Type.pointer(cls)
	obj = globals()[obj_name] = Type.opaque(obj_name)
	globals()[obj_name + "_ptr"] = Type.pointer(obj)
	module.add_global_variable(cls, class_name)

del class_name
del obj_name
del built_in_types
del cls
del obj



any_tostring_type = Type.function(string_obj_ptr, [])
any_equals_type = Type.function(boolean_obj_ptr, [any_obj_ptr])
any_fn_ptrs = [Type.pointer(any_tostring_type), Type.pointer(any_equals_type)]
any_class.set_body([Type.void()] + any_fn_ptrs)
any_obj.set_body([any_class_ptr])

def any_child_set_body(child_class, fns = []):
	child_class.set_body([any_class_ptr] + any_fn_ptrs + fns)

io_abort_type = Type.function(Type.void(), [string_obj_ptr])
io_out_type = Type.function(any_obj_ptr, [string_obj_ptr])
io_isnull_type = Type.function(boolean_obj_ptr, [io_obj_ptr])
io_outany_type = Type.function(any_obj_ptr, [io_obj_ptr])
io_in_type = Type.function(string_obj_ptr, [])
io_symbol_type = Type.function(symbol_obj_ptr, [string_obj_ptr])
io_symbolname_type = Type.function(string_obj_ptr, [symbol_obj_ptr])

any_child_set_body(
	io_class, [
		Type.pointer(io_abort_type), 
		Type.pointer(io_out_type), 
		Type.pointer(io_isnull_type),
		Type.pointer(io_outany_type),
		Type.pointer(io_in_type), 
		Type.pointer(io_symbol_type), 
		Type.pointer(io_symbolname_type)
	]
)

io_obj.set_body([io_class_ptr])

any_child_set_body(unit_class)
unit_obj.set_body([unit_class_ptr])

any_child_set_body(int_class)
int_obj.set_body([int_class_ptr, int_obj_ptr, Type.int(32)])

any_child_set_body(boolean_class)
boolean_obj.set_body([boolean_class_ptr, Type.int(1)])


string_length_type = Type.function(int_obj_ptr, [])
string_concat_type = Type.function(string_obj_ptr, [string_obj_ptr])
string_substring_type = Type.function(string_obj_ptr, [int_obj_ptr, int_obj_ptr])
string_charat_type = Type.function(int_obj_ptr, [int_obj_ptr])
string_indexof_type = Type.function(int_obj_ptr, [string_obj_ptr])
any_child_set_body(string_class, [
	Type.pointer(string_length_type),
	Type.pointer(string_concat_type),
	Type.pointer(string_substring_type),
	Type.pointer(string_charat_type),
	Type.pointer(string_indexof_type),
])

# ASCII characters are 8 bit... what is Cool supposed to have?
string_obj.set_body([string_class_ptr, int_obj_ptr, Type.pointer(Type.int(8))])



module.verify()
print module
