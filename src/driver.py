import sys
from settings import *

USAGE = """
usage: coolc <INPUT FILE> (<OUTPUT FILE>)

  Takes a Cool file as input, and creates an executable.

  If no output file is specified, this will use the name of the Cool file 
  without the extension.
"""

  

if __name__ == "__main__":
  from lexer import tokens, reserved, lexer as lex
  from parser import yacc
  from error import *
  from type_checking import TypeChecker
  from codegen import CodeGen

  import os
  import subprocess
  import re

  verbose = True # should probably make this a command-line arg

  def errorExit():
    for e in Error.elist:
      e.display()
    sys.exit("Failed with %d error%s." % (Error.errors, '' if Error.errors == 1 else 's'))

  if len(sys.argv) not in (2, 3):
    sys.exit(USAGE)

  filename = sys.argv[1]

  try:
    outfile = sys.argv[2].lower()
  except IndexError:  
    outfile = os.path.basename(filename).split('.')[0]


  if os.path.exists(outfile):
    yes = ('yes','y','Y','')
    no = ('no','n','N')
    override = raw_input("The file %s already exists.  Overwrite? [Y/n]: "%outfile)
    while override not in yes + no:
      override = raw_input("Please specify yes or no: ")

    if override in no:
      sys.exit("Aborting compilation")


  print "outputting to", outfile

  try:
    f = open(filename,'U')
  except IOError, e:
    sys.exit(e)

  text = f.read()
  f.close()

  Error.filename = filename
  Error.input = text

  srcpath = os.path.dirname(os.path.abspath(__file__))

  try:
    if verbose: print "--- Beginning lexing/parsing ---"
    tree = yacc.parse(
      text, 
      lexer=lex, 
      debug=PARSE_DEBUG
    )

    if Error.errors:
      errorExit()

    #print tree.pretty(style=style)
      
    if verbose: print "--- Beginning type checking ---"
    TypeChecker(tree).check()

    if Error.errors:
      errorExit()

    if verbose: print "--- Beginning code generation ---"
    code = CodeGen(tree).generate()

    build_path = os.path.join(srcpath, "codegen/build")

    with open(os.path.join(build_path, "basic.ll")) as f:
      core_code = f.read()

    blankfile = os.path.join(build_path, "blank.c")

    cmd = [CLANG_PATH, blankfile, "-S", "-emit-llvm", "-o" "-"]

    try:
      llvm_headers = subprocess.check_output(cmd)
    except OSError:
      sys.exit("ERROR: The clang executable cannot be found. "
        +"Please update the CLANG_PATH setting in the setting.py file.")
    
    llvm_headers = re.sub(r"(; ModuleID =).*", r"\1 '%s'", llvm_headers) % filename
    
    complete_llvm = "\n".join([llvm_headers, core_code, code])

    if WRITE_LLVM_FILE:
      with open(outfile + ".ll", "w") as f:
        f.write(complete_llvm)

    c_driver = os.path.join(build_path, "driver.c")
    cmd = [CLANG_PATH, c_driver, '-x', 'ir', '-', '-o', outfile]
    pipe = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    outdata, errdata = pipe.communicate(complete_llvm)
    pipe.wait()

    print "File output as %s" % outfile


  except TooManyErrors:
    errorExit()
  except Error, e:
    e.display()
    errorExit()


  state = lex.lexstate
  if state in ('comment', 'string', 'longstring'):
    token = None
    if state == 'comment': token = lex.comment_start
    if state in ('longstring', 'string'): token = lex.string_start
    TokenError("\nUnterminated %s: Encountered EOF\n" % (state), token).display()


  sys.stderr.write(
    "Completed with %d error%s.\n" % (
      Error.errors, 
      '' if Error.errors == 1 else 's'
    )
  )




