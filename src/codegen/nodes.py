import tree
from node_code_gen import NodeCodeGen
from type_checking.environment import env
from error import SymbolError


string_constants = 0

OBJ_PTR = "%%obj_%s*"

GET_FIELD_ADDR = "\n  %(temp)s = getelementptr %%obj_%(class)s* %%ret, i32 0, i32 %(loc)d"
STORE_FIELD = (
  GET_FIELD_ADDR + 
  "\n  store %%obj_%(type)s* %(addr)s, %%obj_%(type)s** %(temp)s"
)
LOAD_FIELD = (
  GET_FIELD_ADDR + 
  "\n  %(temp2)s = load %%obj_%(type)s** %(temp)s"
)

def bitcast_if_necessary(varinfo, expected, got, loc):
  if expected == got:
    return loc, ""
  temp = get_next_temp(varinfo)
  code = "\n  %s = bitcast %%obj_%s* %s to %%obj_%s*" % (temp, got, loc, expected)
  return temp, code

def get_next_temp(varinfo):
  temp = "%%%d" % varinfo['used']
  varinfo['used'] += 1
  return temp

def add_string_constant(varinfo, string):
  if 'strings' not in varinfo:
    varinfo['strings'] = {}

  if string not in varinfo['strings']:
    global string_constants
    constant_name = "@.str%d" % string_constants
    varinfo['strings'][string] = constant_name
    string_constants += 1

  return varinfo['strings'][string]

def string_const_code(varinfo):
  code = ""
  if 'strings' in varinfo and len(varinfo['strings']):
    for string, const in varinfo['strings'].iteritems():
      code += '\n%s = constant [%d x i8] c"%s\\00"' % (const, len(string)+1, string)
  return code

def methodtypestrs(cls, args):
  # Add "this" argument
  args = [cls] + list(args)
  argstrs = []

  for ty in args:
    argstrs.append(OBJ_PTR % ty)

  ret = argstrs.pop()
  return ret, argstrs


def methodcallstring(cls, name, argtypes, args):
  ret, argstrs = methodtypestrs(cls, argtypes)
  argstrs = map(lambda ty, n: "%s %s" % (ty, n), argstrs, args)
  return "%s %s(%s)" % (ret, name, ", ".join(argstrs))


def methoddefstring(cls, name, argtypes, this="%this"):
  arg_names = [this] + map(lambda i: "%%arg%d" % i, range(len(argtypes)-1))
  return methodcallstring(cls, "@%s.%s" % (cls, name), argtypes, arg_names) 


def methodtypestring(cls, argtypes):
  ret, argstrs = methodtypestrs(cls, argtypes)
  return "%s (%s)*" % (ret, ", ".join(argstrs))





class Document(NodeCodeGen):
  def generate(self):
    for child in self.node.children:
      child.codegen.generate()

    code = """
define void @llvm_main() {
  call %obj_Main* @Main._constructor(%obj_Main* null)
  ret void
}
"""

    self.output(code)

class Class(NodeCodeGen):
  def generate(self):
    cls = self.node.type.name

    code = ""

    form = """
%%class_%(name)s = type {
  %%class_%(superclass)s*,
  i8*,
  %(method_types)s
}

@._str.%(name)s = constant [%(len)s x i8] c"%(name)s\\00"
@.str.%(name)s = alias i8* bitcast ([%(len)s x i8]* @._str.%(name)s to i8*)

@%(name)s = global %%class_%(name)s {
  %%class_%(superclass)s* @%(superclass)s,
  i8* @.str.%(name)s,
  %(methods)s
}

%%obj_%(name)s = type {
  %%class_%(name)s* @%(name)s%(field_types)s
}
"""
    
    m = env.getClassMethods(cls)

    alias_strs = []
    alias_form = ("\n@%(class)s.%(method)s = alias %(type)s bitcast "+
      "(%(supertype)s @%(super)s.%(method)s to %(type)s)\n")

    method_consts = [None]*len(m)
    method_types = list(method_consts)
    methods = {}
    for name, (args, pos, inherited_from) in m.iteritems(): 
      typestr = methodtypestring(cls, args)
      method_types[pos] = typestr
      method_consts[pos] = "%s %s" % (typestr, "@%s.%s" % (cls, name))
      methods[name] = typestr

      if inherited_from != cls:
        supertypestr = methodtypestring(inherited_from, args)
        alias_strs.append(alias_form % {
          'class': cls,
          'method': name,
          'type' : typestr,
          'super' : inherited_from,
          'supertype' : supertypestr
        })


    v = env.getClassVars(cls)
    fields = [None]*len(v)
    for name, (ty, pos) in v.iteritems():
      fields[pos] = ",\n  " + (OBJ_PTR % ty)

    code += form % { 
      'name': cls, 
      'len': len(cls)+1,
      'superclass' : self.node.superclass.name,
      'method_types': ",\n  ".join(method_types),
      'methods': ",\n  ".join(method_consts),
      'field_types' : "".join(fields)
    }

    for alias in alias_strs:
      code += alias

    # Constructor...


    constructor = {
      'body': "",
      'class': cls,
      'superclass': self.node.superclass.name,
      'malloc_bytes': (len(fields)+1)*4
    }
    constr_form = """
define %(def)s {
  %%objstk = alloca %%obj_%(class)s*
  store %%obj_%(class)s* %%child, %%obj_%(class)s** %%objstk
  %%isnull = icmp eq %%obj_%(class)s* %%child, null
  br i1 %%isnull, label %%allocate, label %%initialize
allocate: 
  %%space = call i8* @malloc(i32 %(malloc_bytes)d)
  %%newobj = bitcast i8* %%space to %%obj_%(class)s*
  %%cls_field = getelementptr inbounds %%obj_%(class)s* %%newobj, i32 0, i32 0
  store %%obj_%(class)s* %%newobj, %%obj_%(class)s** %%objstk
  store %%class_%(class)s* @%(class)s, %%class_%(class)s** %%cls_field
  br label %%initialize
initialize:
  %%this = load %%obj_%(class)s** %%objstk
  ; Recursively call our superclass' constructor
  %%as_super = bitcast %%obj_%(class)s* %%this to %%obj_%(superclass)s*
  call %%obj_%(superclass)s* @%(superclass)s._constructor(%%obj_%(superclass)s* %%as_super)

  ;;;; %(class)s class initialization ;;;;
  %(body)s

  ret %%obj_%(class)s* %%this
}
"""
    args = env.getMethodType(cls, "_constructor")
    constructor['def'] = methoddefstring(cls, '_constructor', args, '%child')

    varinfo = {
      'used': 0,
      'class': cls
    }
    for arg, formal in enumerate(self.node.formals.children):
      argname = "%%arg%d" % arg
      constructor['body'] += STORE_FIELD % {
        'temp': get_next_temp(varinfo), 
        'class': cls, 
        'loc': formal.id.static + 1,
        'type': formal.type.name,
        'addr': argname
      }

    defs = []
    for feature in self.node.body.children:
      if isinstance(feature, tree.Def):
        defs.append(feature)
      if isinstance(feature, tree.Block):
        constructor['body'] += feature.codegen.generate(varinfo)
      if isinstance(feature, tree.VarInit):
        # Generate code for the expression...
        constructor['body'] += feature.value.codegen.generate(varinfo)
        result = varinfo['result']
        temp = get_next_temp(varinfo)
        constructor['body'] += STORE_FIELD % {
          'temp': temp, 
          'class': cls, 
          'loc': feature.id.static + 1,
          'type': feature.type.name,
          'addr': result
        }

    code += string_const_code(varinfo)
    code += constr_form % constructor

    for method in defs:
      code += method.codegen.generate(cls)

    self.output(code)

class Def(NodeCodeGen):
  def generate(self, cls):
    # keeps track of information on variables used in this method
    
    name = self.node.id.name
    rtype = self.node.type.name
    args = env.getMethodType(cls, name)

    varinfo = {
      'used': 0,
      'class': cls
    }

    body = "\n\ndefine %s {" % methoddefstring(cls, name, args)

    body += self.node.value.codegen.generate(varinfo)

    ret, c = bitcast_if_necessary(varinfo, rtype, varinfo['result_type'], varinfo['result'])
    body += c

    body += "\n  ret %%obj_%s* %s" % (rtype, ret)
    body += "\n}"
    
    code = string_const_code(varinfo)
    code += body

    return code

class Block(NodeCodeGen):
  def generate(self, varinfo):
    code = "\n\n  ;;; block ;;;"
    for instr in self.node.children:
      if hasattr(instr, 'codegen'):
        code += instr.codegen.generate(varinfo)
      else:
        code += "\n  ; No codegen for %s " % type(instr)
    code += "\n  ;;; endblock ;;;\n"

    return code
    

class Call(NodeCodeGen):
  def generate(self, varinfo):
    super_call = False
    code = ""
    if isinstance(self.node.method, tree.Dot):
      code += self.node.method.parent.codegen.generate(varinfo)
      obj = varinfo['result']
      cls = self.node.method.parent.type
      name = self.node.method.child.name
    elif isinstance(self.node, tree.Super):
      code += "\n  ; Super call!"
      obj = get_next_temp(varinfo)
      cls = varinfo['class']
      supercls = env.getSuperClass(cls)
      super_call = True
      name = self.node.method.name
      code += "\n  %s = typecast %%obj_%s* to %%obj_%s*" % (obj, cls, supercls)
    else:
      obj = "%this"
      cls = varinfo['class']
      name = self.node.method.name

    code = "\n\n  ; Calling %s.%s" % (supercls if super_call else cls, name)


    m = env.getMethod(cls, name)
    loc = m[1] + 2
    
    args = [obj]
    for actual,argtype in zip(self.node.actuals.children, m[0]):
      code += actual.codegen.generate(varinfo)
      ref, c = bitcast_if_necessary(varinfo, argtype, varinfo['result_type'], varinfo['result'])
      code += c
      args.append(ref)

    temp = get_next_temp(varinfo)
    code += "\n  %s = getelementptr %%obj_%s* %s, i32 0, i32 0" % (temp, cls, obj) 

    temp2 = get_next_temp(varinfo)
    code += "\n  %s = load %%class_%s** %s" % (temp2, cls, temp)

    if super_call:
      temp2p1 = get_next_temp(varinfo)
      code += "\n  %s = getelementptr %%class_%s* %s, i32 0, i32 0" % (temp2p1, cls, temp2)

      temp2p2 = get_next_temp(varinfo)
      code += "\n  %s = load %%class_%s** %s" % (temp2p2, supercls, temp2p1)

      temp2 = temp2p2
      cls = supercls

    temp3 = get_next_temp(varinfo)
    code += "\n  %s = getelementptr %%class_%s* %s, i32 0, i32 %d" % (temp3, cls, temp2, loc)

    temp4 = get_next_temp(varinfo)
    code += "\n  %s = load %s* %s" % (temp4, methodtypestring(cls, m[0]), temp3)

    temp5 = get_next_temp(varinfo)
    code += "\n  %s = call %s" % (temp5, methodcallstring(cls, temp4, m[0], args))

    code += "\n"
    return code

class Super(Call):
  def generate(self, varinfo):
    return super(Super, self).generate(varinfo)

class Boolean(NodeCodeGen):
  def generate(self, varinfo):
    varinfo['result'] = get_next_temp(varinfo)
    varinfo['result_type'] = "Boolean"
    code = ("\n  %s = call %%obj_Boolean* @Boolean._constructor(%%obj_Boolean* null, i1 %d)" 
      % (varinfo['result'], int(self.node.value)))
    return code

class Integer(NodeCodeGen):
  def generate(self, varinfo):
    varinfo['result'] = get_next_temp(varinfo)
    varinfo['result_type'] = "Int"
    code = ("\n  %s = call %%obj_Int* @Int._constructor(%%obj_Int* null, i32 %d)" 
      % (varinfo['result'], self.node.value))
    return code

class String(NodeCodeGen):
  def generate(self, varinfo):
    code = ""
    const = add_string_constant(varinfo, self.node.value)
    const_type = "[%d x i8]*" % (len(self.node.value)+1)
    temp = get_next_temp(varinfo)
    code += "\n  %s = getelementptr %s %s, i32 0, i32 0" % (temp, const_type, const)
    temp2 = get_next_temp(varinfo)
    code += "\n  %s = typecast %s %s to i8*" % (temp2, const_type, temp)
    varinfo['result'] = get_next_temp(varinfo)
    varinfo['result_type'] = "String"
    code += ("\n  %s = call %%obj_String* @String._constructor(%%obj_Int* null, i8* %s)" 
      % (varinfo['result'], temp2))
    return code

class Unit(NodeCodeGen):
  def generate(self, varinfo):
    varinfo['result_type'] = "Unit"
    varinfo['result'] = '@the_Unit'
    return ""

class This(NodeCodeGen):
  def generate(self, varinfo):
    varinfo['result_type'] = varinfo['cls']
    varinfo['result'] = "%this"
    return ""


class IfExpr(NodeCodeGen):
  def generate(self, varinfo):
    code = ""
    code += self.node.cond.codegen.generate(varinfo)
    cond = varinfo['result']
    bv = get_next_temp(varinfo)
    
    code += "\n  %s = call i1 @.get_bool_val(%%obj_Boolean* %s)" % (bv, cond)

    ty = "%%obj_%s*" % self.node.type
    ralloc = get_next_temp(varinfo)
    code += "\n  %s = alloca %%obj_%s*" % (ralloc, ty)

    labeltrue = get_next_temp(varinfo)
    labelfalse = get_next_temp(varinfo)
    labelfi = get_next_temp(varinfo)

    code += "\n  br i1 %s, label %s, label %s" % (bv, labeltrue, labelfalse)
    code += "\n; <label>:%s" % labeltrue

    code += self.node.true.codegen.generate(varinfo)

    code += "\n  store %s %s, %s* %s" % (ty, varinfo['result'], ty, ralloc)
    code += "\n  br label %s" % labelfi
    code += "\n; <label>:%s" % labelfalse
    
    code += self.node.false.codegen.generate(varinfo)

    code += "\n  store %s %s, %s* %s" % (ty, varinfo['result'], ty, ralloc)
    code += "\n  br label %s" % labelfi
    code += "\n; <label>:%s" % labelfi

    res = get_next_temp(varinfo)
    code += "\n  %s = load %s %s" % (res, ty, ralloc)

    varinfo['result'] = res
    varinfo['result_type'] = self.node.type

    return code


class ArithExpr(NodeCodeGen):
  def generate(self, method, varinfo):
    code = ""

    code += self.node.left.codegen.generate(varinfo)
    arg1 = varinfo['result']

    code += self.node.right.codegen.generate(varinfo)
    arg2 = varinfo['result']

    varinfo['result'] = get_next_temp(varinfo)
    varinfo['result_type'] = "Int"
    code += ("\n  %s = call %%obj_Int* @Int._%s(%%obj_Int* %s, %%obj_Int* %s)" % 
      (varinfo['result'], method, arg1, arg2))
    return code

class AddExpr(ArithExpr): 
  def generate(self, varinfo):
    return super(AddExpr, self).generate('add', varinfo)

class SubExpr(ArithExpr): 
  def generate(self, varinfo):
    return super(SubExpr, self).generate('sub', varinfo)

class MultExpr(ArithExpr): 
  def generate(self, varinfo):
    return super(MultExpr, self).generate('mul', varinfo)

class DivExpr(ArithExpr): 
  def generate(self, varinfo):
    return super(DivExpr, self).generate('div', varinfo)

class LTExpr(ArithExpr): 
  def generate(self, varinfo):
    return super(DivExpr, self).generate('lt', varinfo)

class LEExpr(ArithExpr): 
  def generate(self, varinfo):
    return super(DivExpr, self).generate('le', varinfo)

class Identifier(NodeCodeGen):
  def generate(self, varinfo):
    try:
      varinfo['result_type'] = self.node.type
    except:
      raise SymbolError("ahhh", self.node.token)
    if isinstance(self.node.static, int):
      temp = get_next_temp(varinfo)
      varinfo['result'] = get_next_temp(varinfo)
      return LOAD_FIELD % {
        'temp' : temp,
        'temp2' : varinfo['result'],
        'class' : varinfo['class'],
        'loc' : self.node.static + 1, # Easy to forget... but important.
        'type' : self.node.type
      }
    else:
      temp = varinfo['result'] = get_next_temp(varinfo)
      return "\n  %s = load %%obj_%s** %s" % (temp, self.node.type, self.node.static)

def _assign_var(varinfo, ty, assign, static):
    code = assign.codegen.generate(varinfo)
    rty = varinfo['result_type']
    store = varinfo['result']

    if rty != ty:
      temp = get_next_temp(varinfo)
      code += "\n  %s = bitcast %%obj_%s* %s to %%obj_%s*" % (temp, rty, store, ty)
      store = temp

    code += "\n  store %%obj_%s* %s, %%obj_%s** %s" % (ty, store, ty, static)
    return code
  
class VarInit(NodeCodeGen):
  def generate(self, varinfo):
    ty = self.node.type.name
    var = self.node.id.static
    code = "\n  %s = alloca %%obj_%s*" % (var, ty)

    code += _assign_var(varinfo, ty, self.node.value, var)

    varinfo['result'] = None
    varinfo['result_type'] = None
    return code

class AssignExpr(NodeCodeGen):
  def generate(self, varinfo):
    var = self.node.left.static
    ty = self.node.left.type

    code = _assign_var(varinfo, ty, self.node.right, var)

    varinfo['result'] = '@the_Unit'
    varinfo['result_type'] = "Unit"
    return code

class Constructor(NodeCodeGen):
  def generate(self, varinfo):
    cls = self.node.type.name
    code = "\n  ; Calling %s._constructor" %cls

    name = "@%s.%s" % (cls, "_constructor")
    argtypes = env.getMethodType(cls, "_constructor")

    args = ['null']
    for actual,argtype in zip(self.node.actuals.children, argtypes):
      code += actual.codegen.generate(varinfo)
      ref, c = bitcast_if_necessary(varinfo, argtype, varinfo['result_type'], varinfo['result'])
      code += c
      args.append(ref)

    varinfo['result'] = get_next_temp(varinfo)
    varinfo['result_type'] = cls

    code += "\n  %s = call %s" % (varinfo['result'], methodcallstring(cls, name, argtypes, args))

    return code
    
