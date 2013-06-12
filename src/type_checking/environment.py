from error import SymbolError, UndefinedClassError
from settings import SYMBOL_DEBUG as DEBUG, SIMULATE_BASIC

class Environment(object):
  def __init__(self):
    # Keep track of classes which have had an error for being undefined.
    # Since class names have to be uppercase, it's impossible for a user to make a class with this name.
    self.undefined = set(["undefined"])

    # Keep track of the number of variables defined
    self.vars_defined = 0

    # Variables and their type, for each scope
    self.O = []

    # Methods and their parameter types
    self.M = {}

    # Classes and their superclasses
    self.C = {
      'Nothing': None,
      'Null' : None,
    }

    # Class attributes (types stores in O)
    self.Oc = {}

    # For all of the special types above, initialize with no parameters
    for c in self.C:
      self.Oc[c] = {}

    if SIMULATE_BASIC:
      self.C['Any'] = None
      self.C['Unit'] = 'Any'
      self.C['Int'] = 'Any'
      self.C['String'] = 'Any'
      self.C['Boolean'] = 'Any'
      self.C['ArrayAny'] = 'Any'
      self.C['IO'] = 'Any'
      self.C['Symbol'] = 'Any'
      
      for c in self.C:
        self.Oc[c] = {}
        self.M[c] = {}

      self.M.update({ 
        'Any': { 
          '_constructor' : ((), 0),
          'toString'     : (('String',), 1),
          'equals'       : (('Any', 'Boolean',), 2),
         },
        'IO': {
          '_constructor' : ((), 0),
          'abort'        : (('String', 'Nothing',), 1),
          'out'          : (('String', 'IO',), 2),
          'is_null'      : (('Any', 'Boolean',), 3),
          'out_any'      : (('Any', 'IO',), 4),
          'in'           : (('String',), 5),
          'symbol'       : (('String','Symbol',), 6),
          'symbol_name'  : (('Symbol','String',), 7),
        },
        'String': {
          '_constructor' : ((), 0),
          'length'       : (('Int',), 1),
          'charAt'       : (('Int', 'Int',), 2),
          'concat'       : (('String', 'String', 'String',), 3),
          'substring'    : (('Int', 'Int', 'String',), 4),
          'indexOf'      : (('String', 'Int',), 5),
        },
        'Symbol': { 
          '_constructor' : ((), 0),
          'hashCode'     : (('Int',), 1) 
        },
        'ArrayAny': {
          '_constructor' : (('Int',), 0),
          'length'       : (('Int',), 1),
          'resize'       : (('Int','ArrayAny',), 2),
          'get'          : (('Int', 'Any',), 3),
          'set'          : (('Int', 'Any', 'Any',), 4),
        }
      })

      self.Oc['Int']['value'] = ('Int', 0)
      self.Oc['Boolean']['value'] = ('Boolean', 0)
      self.Oc['String']['length'] = ('Int', 0)
      self.Oc['String']['str_field'] = ('String', 1)
      self.Oc['Symbol']['next'] = ('Symbol', 0)
      self.Oc['Symbol']['name'] = ('String', 1)
      self.Oc['Symbol']['hash'] = ('Int', 2)
      self.Oc['ArrayAny']['array_field'] = ('ArrayAny', 0)


  def enterClassScope(self, c):
    "Put all class attributes in scope"
    self.enterScope(self.Oc[c])
    self.enterScope({'this': (c, '%this'), 'super': (self.getSuperClass(c), '%super')})

  def exitClassScope(self, c):
    self.exitScope()
    self.exitScope()

  def enterScope(self, vs=None):
    if vs is None:
      vs = {}
    self.O.append(vs)

  def exitScope(self):
    self.O.pop()

  def defineAttr(self, c, v, T):
    try:
      self.hasAttr(c, v)
    except SymbolError, e:
      e.ignore()
      static = len(self.Oc[c])
      self.Oc[c][v] = (T, static)
    else:
      raise SymbolError("Class '%s' attribute named '%s'" % (c, v)
        + " is already defined (perhaps in a superclass)")

  def hasAttr(self, c, v):
    orig = c
    while c is not None:
      if c in self.C:
        if v in self.Oc[c]:
          return True
        c = self.getSuperClass(c)
      else:
        c = None
    raise SymbolError("Class '%s' has no attribute '%s'" % (c, v))

  def defineVar(self, v, T, static=""):
    # Get the current stack scope
    d = self.O[-1]
    if v in d:
      raise SymbolError("The variable '%s' was already defined in this scope." % v)
    else:
      self.vars_defined += 1
      if not static: static = "%%loc%d" % self.vars_defined
      d[v] = (T, static)

  def defineMethod(self, C, f, t):
    if f in self.M[C]:
      raise SymbolError("Method named '%s' already defined for class '%s'" % (f, C))

    self.M[C][f] = (t, len(self.M[C])) 

  def defineClass(self, c, S):
    if c in self.C:
      raise SymbolError("Class name '%s' is already defined")
    self.C[c] = S
    self.M[c] = {}
    self.Oc[c] = {}

  def getVar(self, v):
    for d in reversed(self.O):
      try:
        return d[v]
      except KeyError:
        continue
    raise SymbolError("Variable '%s' was not initialized" % v)

  def getVarType(self, v):
    return self.getVar(v)[0]

  def getVarStatic(self, v):
    return self.getVar(v)[1]

  def getMethod(self, C, f):
    if C in self.undefined:
      return (('undefined',), 0)

    s = C
    while s is not None:
      try:
        return self.M[s][f]
      except KeyError:
        s = self.getSuperClass(s)

    raise SymbolError("Class '%s' does not have a method '%s' defined" % (C, f))

  def getClassMethods(self, C):
    return self.M[C]

  def getClassVars(self, C):
    return self.Oc[C]

  def getMethodType(self, C, f):
    if C == "M": raise Exception("here")
    return self.getMethod(C, f)[0]

  def getMethodPos(self, C, f):
    return self.getMethod(C, f)[1]

  def getSuperClass(self, c):
    try:
      return self.C[c]
    except KeyError:
      if DEBUG: print "DEBUG: Undefined class:", type(c), self.C
      if c in self.undefined:
        return "undefined"
      else:
        raise UndefinedClassError("Type '%s' has not been defined" % c, c,  self)

  def checkClassHierarchy(self):
    checked = set()
    for cls in self.C:
      if cls in checked:
        continue

      family = set()
      while cls is not None:
          
        if cls in family:
          raise SymbolError("The class hierarchy is not a tree - class '%s' is its own ancestor"
            % cls)
        family.add(cls)
        checked.add(cls)
        try:
          # Ignore non-existing superclasses here because the classes will check that
          # and can output a more useful error message.
          cls = self.C[cls]
        except KeyError:
          break
  
  def combineInheritedValues(self):
    def memoize(fn):
      mem = {}
      def ret(*args):
        try:
          return mem[args]
        except KeyError:
          res = mem[args] = fn(*args)
          return res
      return ret

    @memoize 
    def combine(cls):
      spr = self.getSuperClass(cls)

      if spr is None:
        methods, attrs = {}, {}
      else:
        methods, attrs = combine(spr)

      # Overriding methods might be defined both in the superclass and subclass,
      # so keep track of duplicates and fix the numbering afterwards since we 
      # don't have time to restructure old code.

      holes = []
      minc = len(methods)
      for key,val in self.M[cls].iteritems():
        num = val[1]+minc

        # If this method already exists in the parent, assume its an override
        # and use the parents' position
        if key in methods:
          holes.append(num)
          num = methods[key][1]

        self.M[cls][key] = (val[0], num, cls)

      holes.sort()
      for hole in reversed(holes):
        for key, val in self.M[cls].iteritems():
          if val[1] > hole:
            self.M[cls][key] = (val[0], val[1]-1)

      # Finally, add all of the methods from the superclass that aren't yet
      # defined for the subclass
      for k,v in methods.iteritems():
        if k not in self.M[cls]:
          self.M[cls][k] = v
        

      ainc = len(attrs)
      for key,val in self.Oc[cls].iteritems():
        if key in attrs:
          SymbolError("Attribute %s of class '%s' already defined in superclass" 
            % (key, cls)).report()
        self.Oc[cls][key] = (val[0], val[1]+ainc)

      self.Oc[cls].update(attrs)

      return self.M[cls], self.Oc[cls]

    for key in self.C:
      combine(key)
      
      
    

env = Environment()
