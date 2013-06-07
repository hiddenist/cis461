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

del class_name
del obj_name
del cls
del obj


any_tostring_type = Type.function(string_obj_ptr, [any_obj_ptr])
any_equals_type = Type.function(boolean_obj_ptr, [any_obj_ptr, any_obj_ptr])
any_fn_ptrs = [Type.pointer(any_tostring_type), Type.pointer(any_equals_type)]
any_class.set_body([Type.pointer(Type.int(1))] + any_fn_ptrs)
any_obj.set_body([any_class_ptr])

def any_child_set_body(child_class, fns = []):
	child_class.set_body(any_fn_ptrs + fns)

io_abort_type = Type.function(Type.void(), [io_obj_ptr, string_obj_ptr])
io_out_type = Type.function(io_obj_ptr, [io_obj_ptr, string_obj_ptr])
io_isnull_type = Type.function(boolean_obj_ptr, [io_obj_ptr, io_obj_ptr])
io_outany_type = Type.function(any_obj_ptr, [io_obj_ptr, io_obj_ptr])
io_in_type = Type.function(string_obj_ptr, [io_obj_ptr])
io_symbol_type = Type.function(symbol_obj_ptr, [io_obj_ptr, string_obj_ptr])
io_symbolname_type = Type.function(string_obj_ptr, [io_obj_ptr, symbol_obj_ptr])

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


string_length_type = Type.function(int_obj_ptr, [string_obj_ptr])
string_concat_type = Type.function(string_obj_ptr, [string_obj_ptr, string_obj_ptr])
string_substring_type = Type.function(string_obj_ptr, [string_obj_ptr, int_obj_ptr, int_obj_ptr])
string_charat_type = Type.function(int_obj_ptr, [string_obj_ptr, int_obj_ptr])
string_indexof_type = Type.function(int_obj_ptr, [string_obj_ptr, string_obj_ptr])
any_child_set_body(string_class, [
	Type.pointer(string_length_type),
	Type.pointer(string_concat_type),
	Type.pointer(string_substring_type),
	Type.pointer(string_charat_type),
	Type.pointer(string_indexof_type),
])

# ASCII characters are 8 bit... what is Cool supposed to have?
char_type = Type.int(8)

# I should be able to make a variable length array like this... but we'll see
raw_str_type = Type.array(char_type,0) 
string_obj.set_body([string_class_ptr, int_obj_ptr, raw_str_type])

symbol_hashcode_type = Type.function(int_obj_ptr, [])
any_child_set_body(symbol_class, [
	Type.pointer(symbol_hashcode_type)
])
# Todo: What is the "next" field supposed to be?
symbol_obj.set_body([symbol_class_ptr, string_obj_ptr, int_obj_ptr])

arrayany_length_type = Type.function(int_obj_ptr, [])
arrayany_resize_type = Type.function(arrayany_obj_ptr, [int_obj_ptr])
arrayany_get_type = Type.function(any_obj_ptr, [int_obj_ptr])
arrayany_set_type = Type.function(any_obj_ptr, [int_obj_ptr, any_obj_ptr])
any_child_set_body(arrayany_class, [
	Type.pointer(arrayany_length_type),
	Type.pointer(arrayany_resize_type),
	Type.pointer(arrayany_get_type),
	Type.pointer(arrayany_set_type),
])

@variable
def abort():
	func = module.add_function(Type.function(Type.void(), []), "abort")
	return func

@variable
def any_tostring():
	func = module.add_function(any_tostring_type, "any_tostring")
	func.args[0].name = "this"
	bb = func.append_basic_block("entry")
	builder = Builder.new(bb)
	ret = builder.malloc(string_obj)
	# Could make a string like "Obj <class pointer>" for default tostring
	builder.ret(ret)
	return func

@variable
def any_equals():
	func = module.add_function(any_equals_type, "any_equals")
	func.args[0].name = "this"
	func.args[1].name = "o"
	bb = func.append_basic_block("entry")
	builder = Builder.new(bb)
	ret = builder.malloc(boolean_obj)
	builder.ret(ret)
	return func

@variable
def io_out():
	func = module.add_function(io_out_type, "io_out")
	func.args[0].name = "this"
	func.args[1].name = "arg"
	bb = func.append_basic_block("entry")
	builder = Builder.new(bb)
	builder.ret(func.args[0])
	return func


@variable
def io_abort():
	func = module.add_function(io_abort_type, "io_abort")
	func.args[0].name = "this"
	func.args[1].name = "msg"
	bb = func.append_basic_block("entry")
	builder = Builder.new(bb)
	builder.call(module.get_function_named("abort"), [])
	builder.ret_void()
	return func

@variable
def io_isnull():
	func = module.add_function(io_isnull_type, "io_isnull")
	func.args[0].name = "this"
	func.args[1].name = "obj"
	bb = func.append_basic_block("entry")
	builder = Builder.new(bb)
	ret = builder.malloc(boolean_obj)
	builder.ret(ret)
	return func


addr = {}
for ty in built_in_types:
	class_name = '%s_class' % ty
	struct = Type.struct(globals()[class_name].elements)
	addr[ty] = module.add_global_variable(struct, ty)

addr["any"].initializer = Constant.struct([
	Constant.null(Type.pointer(Type.int(1))),
	Constant.null(Type.pointer(any_tostring_type)),
	any_equals
])

addr["io"].initializer = Constant.struct([
	addr["any"],
	any_tostring,
	any_equals,
	io_abort,
	io_out,
	io_isnull,
	Constant.null(Type.pointer(io_outany_type)),
	Constant.null(Type.pointer(io_in_type)),
	Constant.null(Type.pointer(io_symbol_type)),
	Constant.null(Type.pointer(io_symbolname_type)),
])

@variable
def main():
	func = module.add_function(Type.function(Type.void(), []), "main")
	bb = func.append_basic_block("entry")
	builder = Builder.new(bb)
	
	builder.ret_void()
	return func


print module

module.verify()
