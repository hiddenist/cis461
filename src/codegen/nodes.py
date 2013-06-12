import tree
from node_code_gen import NodeCodeGen
from type_checking.environment import env


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
  %(constructor_type)s,
  %(method_types)s
}

@._str.%(name)s = constant [%(len)s x i8] c"%(name)s\\00"
@.str.%(name)s = alias i8* bitcast ([%(len)s x i8]* @._str.%(name)s to i8*)

@%(name)s = global %%class_%(name)s {
  %%class_%(superclass)s* @%(superclass)s,
  i8* @.str.%(name)s,
  %(constructor_type)s @%(name)s._constructor,
  %(methods)s
}

%%obj_%(name)s = type {
  %%class_%(name)s* @%(name)s%(field_types)s
}
"""


    def methoddefstring(cls, name, args):
      # Add "this" argument

      args = [cls] + list(args)

      argstrs = []
      for ty in args:
        argstrs.append(OBJ_PTR % ty)

      ret = argstrs.pop()

      arg_names = ['%this'] + map(lambda i: "%%arg%d" % i, range(len(argstrs)-1))

      argstrs = map(lambda ty, n: "%s %s" % (ty, n), argstrs, arg_names)

      return "%s @%s.%s(%s)" % (ret, cls, name, ", ".join(argstrs))


    def methodtypestring(cls, args):
      # Add "this" argument

      args = [cls] + list(args)

      argstrs = []
      for ty in args:
        argstrs.append(OBJ_PTR % ty)

      ret = argstrs.pop()

      return "%s (%s)*" % (ret, ", ".join(argstrs))

    constructor_args = []
    for formal in self.node.formals.children:
      constructor_args.append(formal.type)

    constructor_args.append(cls)
    constructor_type = methodtypestring(cls, constructor_args)
      
    
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
      'constructor_type': constructor_type,
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
  store %%obj_%(class)s* %%this, %%obj_%(class)s** %%objstk
  %%isnull = icmp eq %%obj_%(class)s* %%this, null
  br i1 %%isnull, label %%allocate, label %%initialize
allocate: 
  %%space = call i8* @malloc(i32 %(malloc_bytes)d)
  %%newobj = bitcast i8* %%space to %%obj_%(class)s*
  %%cls_field = getelementptr inbounds %%obj_%(class)s* %%newobj, i32 0, i32 0
  store %%obj_%(class)s* %%newobj, %%obj_%(class)s** %%objstk
  store %%class_%(class)s* @%(class)s, %%class_%(class)s** %%cls_field
  br label %%initialize
initialize:
  %%ret = load %%obj_%(class)s** %%objstk
  ; Recursively call our superclass' constructor
  %%as_super = bitcast %%obj_%(class)s* %%ret to %%obj_%(superclass)s*
  call %%obj_%(superclass)s* @%(superclass)s._constructor(%%obj_%(superclass)s* %%as_super)

  ;;;; %(class)s class initialization ;;;;
  %(body)s

  ret %%obj_%(class)s* %%ret
}
"""
    constructor['def'] = methoddefstring(cls, '_constructor', constructor_args)

    var_map = {}
    # keeps track of information on variables used in this method
    varinfo = {
      'map': var_map, 
      'used': 0,
      'class': cls
    }
    for arg, formal in enumerate(self.node.formals.children):
      argname = "%%arg%d" % arg
      var_map[formal.id.static] = argname
      constructor['body'] += STORE_FIELD % {
        'temp': "%%%d" % varinfo['used'], 
        'class': cls, 
        'loc': formal.id.static + 1,
        'type': formal.type.name,
        'addr': argname
      }
      varinfo['used'] += 1

    defs = []
    for feature in self.node.body.children:
      if isinstance(feature, tree.Def):
        defs.append(feature)
      if isinstance(feature, tree.Block):
        pass
      if isinstance(feature, tree.VarInit):
        # Generate code for the expression...
        constructor['body'] += feature.value.codegen.generate(varinfo)
        result = varinfo['result']
        temp = "%%%d" % varinfo['used']
        print feature.id
        constructor['body'] += STORE_FIELD % {
          'temp': temp, 
          'class': cls, 
          'loc': feature.id.static + 1,
          'type': feature.type.name,
          'addr': result
        }
        var_map[feature.id.static] = temp
        varinfo['used'] += 1


    code += constr_form % constructor

    self.output(code)


class Block(NodeCodeGen):
  def generate(self, varinfo):
    code = ""
    for instr in self.node.children:
      code += instr.generate(varinfo)

    return code

class Integer(NodeCodeGen):
  def generate(self, varinfo):
    varinfo['result'] = "%%%d" % varinfo['used']
    varinfo['used'] += 1
    code = ("\n  %s = call %%obj_Int* @Int._constructor(%%obj_Int* null, i32 %d)" 
      % (varinfo['result'], self.node.value))

    return code

class ArithExpr(NodeCodeGen):
  def generate(self, method, varinfo):
    code = ""

    code += self.node.left.codegen.generate(varinfo)
    arg1 = varinfo['result']

    code += self.node.right.codegen.generate(varinfo)
    arg2 = varinfo['result']

    varinfo['result'] = "%%%d" % varinfo['used']
    varinfo['used'] += 1
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

class Identifier(NodeCodeGen):
  def generate(self, varinfo):
    if isinstance(self.node.static, int):
      temp = "%%%d" % varinfo['used']
      varinfo['used'] += 1
      varinfo['result'] = "%%%d" % varinfo['used']
      varinfo['used'] += 1
      return LOAD_FIELD % {
        'temp' : temp,
        'temp2' : varinfo['result'],
        'class' : varinfo['class'],
        'loc' : self.node.static + 1, # Easy to forget... but important.
        'type' : self.node.type
      }
    else:
      varinfo['result'] = varinfo['map'][self.node.static]
      return ""
