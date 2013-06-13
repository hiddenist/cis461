; Usually I see these at the bottom of LLVM programs.  Why not the top?

declare noalias i8* @malloc(i32) nounwind
declare void @exit(i32) noreturn nounwind
declare i32 @puts(i8*)
declare i32 @putchar(i8)
declare i32 @sprintf(i8*, i8*, ...)

declare i32 @strlen(i8*) nounwind readonly
declare i32 @strcmp(i8*, i8*) nounwind readonly
declare i8* @strcat(i8*, i8*)
declare i8* @strcpy(i8*, i8*)
declare i8* @strstr(i8*, i8*)

declare i8* @io_in(i8*, i32)

%obj_Nothing = type { }

%class_Any = type { 
  %class_Any*,
  i8*,
  %obj_Any*     (%obj_Any*)*,           ; _constructor
  %obj_String*  (%obj_Any*)*,           ; _toString
  %obj_Boolean* (%obj_Any*, %obj_Any*)* ; equals
}
%obj_Any = type { %class_Any* }

; Is there an easier way to do this?
@._str.Any = constant [4 x i8] c"Any\00"
@.str.Any = alias i8* bitcast ([4 x i8]* @._str.Any to i8*)

@Any = global %class_Any { 
  %class_Any*                           null,
  i8*                                   @.str.Any,
  %obj_Any*     (%obj_Any*)*            @Any._constructor,
  %obj_String*  (%obj_Any*)*            @Any.toString,
  %obj_Boolean* (%obj_Any*, %obj_Any*)* @Any.equals 
}

define %obj_Any* @Any._constructor(%obj_Any* %obj) {
  %isnull = icmp eq %obj_Any* %obj, null
  %objstk = alloca %obj_Any*
  store %obj_Any* %obj, %obj_Any** %objstk
  br i1 %isnull, label %allocate, label %initialize
allocate: 
  %space = call i8* @malloc(i32 4)
  %newobj = bitcast i8* %space to %obj_Any*
  %cls_field = getelementptr inbounds %obj_Any* %newobj, i32 0, i32 0
  store %obj_Any* %newobj, %obj_Any** %objstk
  store %class_Any* @Any, %class_Any** %cls_field
  br label %initialize
initialize:
  ; if Any had a superclass, this is where we would recursively call its constructor
  %ret = load %obj_Any** %objstk
  ret %obj_Any* %ret
}

; let's just use c-style strings to make c functions easier
@.Any_str_format = constant [11 x i8] c"<%s at %d>\00" 
define %obj_String* @Any.toString(%obj_Any* %this) {
  %format = getelementptr [11 x i8]* @.Any_str_format, i32 0, i32 0
  %buffer = alloca i8, i32 200 ; hopefully this is a reasonable buffer size

  %clsp = getelementptr %obj_Any* %this, i32 0, i32 0
  %cls = load %class_Any** %clsp
  %clsstr = getelementptr %class_Any* %cls, i32 0, i32 1
  %strp = load i8** %clsstr

  call i32 (i8*, i8*, ...)* @sprintf(i8* %buffer, i8* %format, i8* %strp, %obj_Any* %this)
  %str = call %obj_String* @String._constructor(%obj_String* null, i8* %buffer)
  ret %obj_String* %str
}

define %obj_Boolean* @Any.equals(%obj_Any* %this, %obj_Any* %that) {
  ; The base equals just checks if these are pointers to the same object.
  %eq = icmp eq %obj_Any* %this, %that 
  %bool = call %obj_Boolean* @Boolean._constructor(%obj_Boolean* null, i1 %eq)
  ret %obj_Boolean* %bool
}


%class_Unit = type {
  %class_Any*,
  i8*,
  %obj_Unit* (%obj_Unit*)*,              ; _constructor
  %obj_String*  (%obj_Unit*)*,           ; toString
  %obj_Boolean* (%obj_Unit*, %obj_Any*)* ; equals
}

%obj_Unit = type { %class_Unit* }

@._str.Unit = constant [5 x i8] c"Unit\00"
@.str.Unit = alias i8* bitcast ([5 x i8]* @._str.Unit to i8*)
@Unit = global %class_Unit {
  %class_Any*                            @Any,
  i8*                                    @.str.Unit,
  %obj_Unit* (%obj_Unit*)*               null,
  %obj_String*  (%obj_Unit*)*            @Unit.toString,           
  %obj_Boolean* (%obj_Unit*, %obj_Any*)* @Unit.equals
}

@the_Unit = global %obj_Unit { %class_Unit* @Unit }

@Unit.toString = alias 
  %obj_String* (%obj_Unit*)* bitcast (                  
  %obj_String* (%obj_Any*)* @Any.toString to 
  %obj_String* (%obj_Unit*)*
)

@Unit.equals = alias 
  %obj_Boolean* (%obj_Unit*, %obj_Any*)* bitcast (                  
  %obj_Boolean* (%obj_Any*, %obj_Any*)* @Any.equals to 
  %obj_Boolean* (%obj_Unit*, %obj_Any*)* 
)


%class_Boolean = type { 
  %class_Any*,
  i8*,
  %obj_Boolean* (%obj_Boolean*, i1)*,       ; _constructor
  %obj_String*  (%obj_Boolean*)*,           ; toString
  %obj_Boolean* (%obj_Boolean*, %obj_Any*)* ; equals
}
%obj_Boolean = type { 
  %class_Boolean*,
  i1* ; value
}


@._str.Boolean = constant [8 x i8] c"Boolean\00"
@.str.Boolean = alias i8* bitcast ([8 x i8]* @._str.Boolean to i8*)
@Boolean = global %class_Boolean {
  %class_Any*                               @Any,
  i8*                                       @.str.Boolean,
  %obj_Boolean* (%obj_Boolean*, i1)*        @Boolean._constructor,
  %obj_String*  (%obj_Boolean*)*            @Boolean.toString,
  %obj_Boolean* (%obj_Boolean*, %obj_Any*)* @Boolean.equals
}

define i1 @.get_bool_val(%obj_Boolean* %bool) {
  %bpp = getelementptr %obj_Boolean* %bool, i32 0, i32 1
  %bp = load i1** %bpp
  %val = load i1* %bp
  ret i1 %val
}

define %obj_Boolean* @Boolean._constructor(%obj_Boolean* %obj, i1 %val) {
  %objstk = alloca %obj_Boolean*
  store %obj_Boolean* %obj, %obj_Boolean** %objstk
  %isnull = icmp eq %obj_Boolean* %obj, null
  br i1 %isnull, label %allocate, label %initialize
allocate: 
  %space = call i8* @malloc(i32 8)
  %newobj = bitcast i8* %space to %obj_Boolean*
  %cls_field = getelementptr inbounds %obj_Boolean* %newobj, i32 0, i32 0
  store %obj_Boolean* %newobj, %obj_Boolean** %objstk
  store %class_Boolean* @Boolean, %class_Boolean** %cls_field
  br label %initialize
initialize:
  %ret = load %obj_Boolean** %objstk
  ; Recursively call our superclass' constructor
  %as_any = bitcast %obj_Boolean* %ret to %obj_Any*
  call %obj_Any* @Any._constructor(%obj_Any* %as_any)
  
  ;;;; Boolean initialization ;;;;
  
  ; create heap space for the bool value
  %t1 = call i8* @malloc(i32 1) 
  ; wasted bits, since malloc can't allocate less than one bit - interestingly, it might be more 
  ; efficient on some architectures to allocate a full 32 bits for a boolean.
  %bp = bitcast i8* %t1 to i1*
  store i1 %val, i1* %bp

  ; store the bool pointer to the value field
  %valfield = getelementptr %obj_Boolean* %ret, i32 0, i32 1
  store i1* %bp, i1** %valfield

  ret %obj_Boolean* %ret
}

@.true_str = constant [ 5 x i8 ] c"true\00"
@.false_str = constant [ 6 x i8 ] c"false\00"
define %obj_String* @Boolean.toString(%obj_Boolean* %this) {
  %str = alloca i8*
  %val = call i1 @.get_bool_val(%obj_Boolean* %this)
  br i1 %val, label %if, label %else
if:
  %true = getelementptr [5 x i8]* @.true_str, i32 0, i32 0
  store i8* %true, i8** %str
  br label %fi
else:
  %false = getelementptr [6 x i8]* @.false_str, i32 0, i32 0
  store i8* %false, i8** %str
  br label %fi
fi:
  %str_rep = load i8** %str
  %obj = call %obj_String* @String._constructor(%obj_String* null, i8* %str_rep)
  ret %obj_String* %obj
}

define %obj_Boolean* @Boolean.equals(%obj_Boolean* %this, %obj_Any* %that) {
  %typep = getelementptr %obj_Any* %that, i32 0, i32 0
  %type = load %class_Any** %typep
  %bcls = bitcast %class_Boolean* @Boolean to %class_Any*
  %ib = icmp eq %class_Any* %type, %bcls
  %res = alloca i1
  store i1 %ib, i1* %res
  br i1 %ib, label %isbool, label %return

isbool:
  %that_bool = bitcast %obj_Any* %that to %obj_Boolean*
  %thisv = call i1 @.get_bool_val(%obj_Boolean* %this)
  %thatv = call i1 @.get_bool_val(%obj_Boolean* %that_bool)

  %eq = icmp eq i1 %thisv, %thatv
  store i1 %eq, i1* %res

  br label %return
return:

  %val = load i1* %res
  %bool = call %obj_Boolean* @Boolean._constructor(%obj_Boolean* null, i1 %val)
  ret %obj_Boolean* %bool
}


%class_Int = type { 
  %class_Any*,
  i8*,
  %obj_Int*     (%obj_Int*, i32)*,      ; _constructor
  %obj_String*  (%obj_Int*)*,           ; toString
  %obj_Boolean* (%obj_Int*, %obj_Any*)* ; equals
}
%obj_Int = type { 
  %class_Int*,
  i32* ; value
}

@._str.Int = constant [4 x i8] c"Int\00"
@.str.Int = alias i8* bitcast ([4 x i8]* @._str.Int to i8*)
@Int = global %class_Int { 
  %class_Any*                            @Any,
  i8*                                    @.str.Int,
  %obj_Int*      (%obj_Int*, i32)*       @Int._constructor,
  %obj_String*   (%obj_Int*)*            @Int.toString,
  %obj_Boolean*  (%obj_Int*, %obj_Any*)* @Int.equals
}

define %obj_Int* @Int._constructor(%obj_Int* %obj, i32 %val) {
  %isnull = icmp eq %obj_Int* %obj, null
  %objstk = alloca %obj_Int*
  store %obj_Int* %obj, %obj_Int** %objstk
  br i1 %isnull, label %allocate, label %initialize
allocate: 
  %space = call i8* @malloc(i32 8)
  %newobj = bitcast i8* %space to %obj_Int*
  %cls_field = getelementptr inbounds %obj_Int* %newobj, i32 0, i32 0
  store %obj_Int* %newobj, %obj_Int** %objstk
  store %class_Int* @Int, %class_Int** %cls_field
  br label %initialize
initialize:
  %ret = load %obj_Int** %objstk
  ; Recursively call our superclass' constructor
  %as_any = bitcast %obj_Int* %ret to %obj_Any*
  call %obj_Any* @Any._constructor(%obj_Any* %as_any)
  
  ;;;; Int initialization ;;;;
  
  ; create heap space for the integer value
  %t1 = call i8* @malloc(i32 4)
  %intp = bitcast i8* %t1 to i32*
  store i32 %val, i32* %intp

  ; store the integer pointer to the value field
  %valfield = getelementptr %obj_Int* %ret, i32 0, i32 1
  store i32* %intp, i32** %valfield

  ret %obj_Int* %ret
}

define i32 @.get_int_val(%obj_Int* %int) {
  %ipp = getelementptr %obj_Int* %int, i32 0, i32 1
  %ip = load i32** %ipp
  %val = load i32* %ip
  ret i32 %val
}

@.sprintf_format = constant [3 x i8] c"%d\00" 

define %obj_String* @Int.toString(%obj_Int* %this) {
  %format = getelementptr [3 x i8]* @.sprintf_format, i32 0, i32 0
  ; biggest 32 bit int is 10 chars, and maybe a -, plus null char, 
  ; and some extra just in case I've forgotten something (it's just stack space)
  %buffer = alloca i8, i32 16
  %val = call i32 @.get_int_val(%obj_Int* %this)
  call i32 (i8*, i8*, ...)* @sprintf(i8* %buffer, i8* %format , i32 %val)
  %str = call %obj_String* @String._constructor(%obj_String* null, i8* %buffer)
  ret %obj_String* %str
} 

define %obj_Boolean* @Int.equals(%obj_Int* %this, %obj_Any* %that) {
  %typep = getelementptr %obj_Any* %that, i32 0, i32 0
  %type = load %class_Any** %typep
  %bcls = bitcast %class_Int* @Int to %class_Any*
  %ib = icmp eq %class_Any* %type, %bcls
  %res = alloca i1
  store i1 %ib, i1* %res
  br i1 %ib, label %isint, label %return

isint:
  %that_int = bitcast %obj_Any* %that to %obj_Int*
  %thisv = call i32 @.get_int_val(%obj_Int* %this)
  %thatv = call i32 @.get_int_val(%obj_Int* %that_int)

  %eq = icmp eq i32 %thisv, %thatv
  store i1 %eq, i1* %res

  br label %return
return:

  %val = load i1* %res
  %bool = call %obj_Boolean* @Boolean._constructor(%obj_Boolean* null, i1 %val)
  ret %obj_Boolean* %bool
}

define %obj_Int* @Int._add(%obj_Int* %this, %obj_Int* %that) {
  %lhs = call i32 @.get_int_val(%obj_Int* %this)
  %rhs = call i32 @.get_int_val(%obj_Int* %that)
  %val = add i32 %lhs, %rhs
  %newInt = call %obj_Int* @Int._constructor(%obj_Int* null, i32 %val)
  ret %obj_Int* %newInt
}

define %obj_Int* @Int._sub(%obj_Int* %this, %obj_Int* %that) {
  %lhs = call i32 @.get_int_val(%obj_Int* %this)
  %rhs = call i32 @.get_int_val(%obj_Int* %that)
  %val = sub i32 %lhs, %rhs
  %newInt = call %obj_Int* @Int._constructor(%obj_Int* null, i32 %val)
  ret %obj_Int* %newInt
}

define %obj_Int* @Int._mul(%obj_Int* %this, %obj_Int* %that) {
  %lhs = call i32 @.get_int_val(%obj_Int* %this)
  %rhs = call i32 @.get_int_val(%obj_Int* %that)
  %val = mul i32 %lhs, %rhs
  %newInt = call %obj_Int* @Int._constructor(%obj_Int* null, i32 %val)
  ret %obj_Int* %newInt
}

define %obj_Int* @Int._div(%obj_Int* %this, %obj_Int* %that) {
  %lhs = call i32 @.get_int_val(%obj_Int* %this)
  %rhs = call i32 @.get_int_val(%obj_Int* %that)
  %val = sdiv i32 %lhs, %rhs
  %newInt = call %obj_Int* @Int._constructor(%obj_Int* null, i32 %val)
  ret %obj_Int* %newInt
}

define %obj_Boolean* @Int._lt(%obj_Int* %this, %obj_Int* %that) {
  %lhs = call i32 @.get_int_val(%obj_Int* %this)
  %rhs = call i32 @.get_int_val(%obj_Int* %that)
  %val = icmp slt i32 %lhs, %rhs
  %bool = call %obj_Boolean* @Boolean._constructor(%obj_Boolean* null, i1 %val)
  ret %obj_Boolean* %bool
}

define %obj_Boolean* @Int._le(%obj_Int* %this, %obj_Int* %that) {
  %lhs = call i32 @.get_int_val(%obj_Int* %this)
  %rhs = call i32 @.get_int_val(%obj_Int* %that)
  %val = icmp sle i32 %lhs, %rhs
  %bool = call %obj_Boolean* @Boolean._constructor(%obj_Boolean* null, i1 %val)
  ret %obj_Boolean* %bool
}

%class_String = type { 
  %class_Any*,
  i8*,
  %obj_String*  (%obj_String*, i8*)*,                  ; _constructor
  %obj_String*  (%obj_String*)*,                       ; toString
  %obj_Boolean* (%obj_String*, %obj_Any*)*,            ; equals
  %obj_Int*     (%obj_String*)*,                       ; length
  %obj_String*  (%obj_String*, %obj_String*)*,         ; concat
  %obj_String*  (%obj_String*, %obj_Int*, %obj_Int*)*, ; substring
  %obj_Int*     (%obj_String*, %obj_Int*)*,            ; charAt
  %obj_Int*     (%obj_String*, %obj_String*)*          ; indexOf
}
%obj_String = type { 
  %class_String*,
  %obj_Int*, ; length
  i8*        ; str_field
}

@._str.String = constant [7 x i8] c"String\00"
@.str.String = alias i8* bitcast ([7 x i8]* @._str.String to i8*)
@String = global %class_String {
  %class_Any*                                          @Any,
  i8*                                                  @.str.String,
  %obj_String*  (%obj_String*, i8*)*                   @String._constructor,
  %obj_String*  (%obj_String*)*                        @String.toString,
  %obj_Boolean* (%obj_String*, %obj_Any*)*             @String.equals,
  %obj_Int*     (%obj_String*)*                        @String.length,
  %obj_String*  (%obj_String*, %obj_String*)*          @String.concat,
  %obj_String*  (%obj_String*, %obj_Int*, %obj_Int*)*  @String.substring,
  %obj_Int*     (%obj_String*, %obj_Int*)*             @String.charAt,
  %obj_Int*     (%obj_String*, %obj_String*)*          @String.indexOf
}

define %obj_String* @String._constructor(%obj_String* %obj, i8* %str) {
  %isnull = icmp eq %obj_String* %obj, null
  %objstk = alloca %obj_String*
  store %obj_String* %obj, %obj_String** %objstk
  br i1 %isnull, label %allocate, label %initialize
allocate: 
  %space = call i8* @malloc(i32 12)
  %newobj = bitcast i8* %space to %obj_String*
  %cls_field = getelementptr inbounds %obj_String* %newobj, i32 0, i32 0
  store %obj_String* %newobj, %obj_String** %objstk
  store %class_String* @String, %class_String** %cls_field
  br label %initialize
initialize:
  %ret = load %obj_String** %objstk
  
  ; Recursively call our superclass' constructor
  %as_any = bitcast %obj_String* %ret to %obj_Any*
  call %obj_Any* @Any._constructor(%obj_Any* %as_any)
  
  ;;;; String initialization ;;;;

  ; Get the length of the string
  %len = call i32 @strlen(i8* %str) nounwind readonly

  ; Create an Int of that length
  %int = call %obj_Int* @Int._constructor(%obj_Int* null, i32 %len)

  ; Store the Int in the length field
  %lenfield = getelementptr %obj_String* %ret, i32 0, i32 1
  store %obj_Int* %int, %obj_Int** %lenfield
  
  ; Allocate space on the heap for the string
  %bytes = add i32 %len, 1
  %strp = call i8* @malloc(i32 %bytes)
  ; Already returns a char*, no bitcast necessary

  ; Copy the string into this new space...
  ; Following loop code should be functionally equivalent to something like this:
  ;
  ; int i = 0;
  ; do {
  ;   new_str[i] = str[i];
  ; } while (str[i++] != '\0'); 
  ;
  ; Turns out I could just use c's strcpy for this, but oh well

  %ip = alloca i32
  store i32 0, i32* %ip
  br label %loopbegin
loopbegin:
  %i = load i32* %ip

  %orig = getelementptr i8* %str, i32 %i
  %new = getelementptr i8* %strp, i32 %i
  %chr = load i8* %orig
  store i8 %chr, i8* %new

  %inc = add nsw i32 %i, 1
  store i32 %inc, i32* %ip
  %is_null_char = icmp eq i8 %chr, 0
  br i1 %is_null_char, label %loopend, label %loopbegin
loopend:
  
  ; Store the new string pointer in the str_field field
  %strfield = getelementptr %obj_String* %ret, i32 0, i32 2
  store i8* %strp, i8** %strfield

  ret %obj_String* %ret
}

define %obj_String* @String.toString(%obj_String* %this) {
  ret %obj_String* %this
}

define %obj_Boolean* @String.equals(%obj_String* %this, %obj_Any* %that) {
  %typep = getelementptr %obj_Any* %that, i32 0, i32 0
  %type = load %class_Any** %typep
  %bcls = bitcast %class_String* @String to %class_Any*
  %ib = icmp eq %class_Any* %type, %bcls
  %res = alloca i1
  store i1 %ib, i1* %res
  br i1 %ib, label %isstr, label %return

isstr:
  %that_str = bitcast %obj_Any* %that to %obj_String*

  %s1p = getelementptr %obj_String* %this, i32 0, i32 2
  %s1 = load i8** %s1p

  %s2p = getelementptr %obj_String* %that_str, i32 0, i32 2
  %s2 = load i8** %s2p

  %cmp = call i32 @strcmp(i8* %s1, i8* %s2)
  %eq = icmp eq i32 %cmp, 0

  store i1 %eq, i1* %res
  br label %return
return:

  %val = load i1* %res
  %bool = call %obj_Boolean* @Boolean._constructor(%obj_Boolean* null, i1 %val)
  ret %obj_Boolean* %bool
}


define %obj_Int* @String.length(%obj_String* %this) {
  %field = getelementptr %obj_String* %this, i32 0, i32 1
  %len = load %obj_Int** %field
  ret %obj_Int* %len
}


define %obj_String* @String.concat(%obj_String* %this, %obj_String* %that) {

  %l1i = call %obj_Int* @String.length(%obj_String* %this)
  %l1 = call i32 @.get_int_val(%obj_Int* %l1i)
  %l2i = call %obj_Int* @String.length(%obj_String* %that)
  %l2 = call i32 @.get_int_val(%obj_Int* %l2i)

  %newlen = add i32 %l1, %l2
  %1 = add i32 %newlen, 1 ; plus null byte
  %stacksp = alloca i8, i32 %1

  %s1p = getelementptr %obj_String* %this, i32 0, i32 2
  %s1 = load i8** %s1p
  %s2p = getelementptr %obj_String* %that, i32 0, i32 2
  %s2 = load i8** %s2p

  call i8* @strcpy(i8* %stacksp, i8* %s1)
  call i8* @strcat(i8* %stacksp, i8* %s2)

  %new = call %obj_String* @String._constructor(%obj_String* null, i8* %stacksp)
  ret %obj_String* %new

}


define %obj_String* @String.substring(%obj_String* %this, %obj_Int* %start, %obj_Int* %end) {

  ; todo: How do I generate a runtime error? 
  ; Right now, bad things will happen if you use out of bounds arguments.  Meh.
  
  ; Copy the string into stack space
  %len = call %obj_Int* @String.length(%obj_String* %this)
  %i = call i32 @.get_int_val(%obj_Int* %len)
  %1 = add i32 %i, 1
  %stacksp = alloca i8, i32 %1
  
  %strp = getelementptr %obj_String* %this, i32 0, i32 2
  %str = load i8** %strp

  call i8* @strcpy(i8* %stacksp, i8* %str)

  ; insert a null char at the end index
  %to = call i32 @.get_int_val(%obj_Int* %end)
  %endp = getelementptr i8* %stacksp, i32 %to
  store i8 0, i8* %endp

  ; get a pointer to the start index and pass it to the string constructor
  %from = call i32 @.get_int_val(%obj_Int* %start)
  %startp = getelementptr i8* %stacksp, i32 %from

  %new = call %obj_String* @String._constructor(%obj_String* null, i8* %startp)
  ret %obj_String* %new
}


define %obj_Int* @String.charAt(%obj_String* %this, %obj_Int* %pos) {
  %strp = getelementptr %obj_String* %this, i32 0, i32 2
  %str = load i8** %strp
  %i = call i32 @.get_int_val(%obj_Int* %pos)
  %atpos = getelementptr i8* %str, i32 %i

  %chr = load i8* %atpos
  %a = alloca i32

  %ac = bitcast i32* %a to i8*
  store i8 %chr, i8* %ac

  %ord = load i32* %a

  %int = call %obj_Int* @Int._constructor(%obj_Int* null, i32 %ord)
  ret %obj_Int* %int
}


define %obj_Int* @String.indexOf(%obj_String* %this, %obj_String* %sub) {
  
  %s1p = getelementptr %obj_String* %this, i32 0, i32 2
  %s1 = load i8** %s1p
  %s2p = getelementptr %obj_String* %sub, i32 0, i32 2
  %s2 = load i8** %s2p
  
  %pos = call i8* @strstr(i8* %s1, i8* %s2)

  ; strstr returns a pointer to the substring location (or null), not an index
  ; So, use -1 if its null, or calculate the difference between pointers for the index

  %res = alloca i32
  %isnull = icmp eq i8* %pos, null

  br i1 %isnull, label %nomatch, label %match

nomatch:
  store i32 -1, i32* %res
  br label %return

match:
  ; This will truncate the pointer on 64 bit systems
  ; I think that's okay, since the strings shouldn't be too far apart, right?
  %startp = ptrtoint i8* %s1 to i32
  %subp = ptrtoint i8* %pos to i32

  %diff = sub i32 %subp, %startp
  store i32 %diff, i32* %res

  br label %return
return:

  %i = load i32* %res
  %int = call %obj_Int* @Int._constructor(%obj_Int* null, i32 %i)
  ret %obj_Int* %int
}


%class_IO = type { 
  %class_Any*,
  i8*,
  %obj_IO*      (%obj_IO*)*,               ; _constructor
  %obj_String*  (%obj_IO*)*,               ; toString
  %obj_Boolean* (%obj_IO*, %obj_Any*)*,    ; equals
  %obj_Nothing* (%obj_IO*, %obj_String*)*, ; abort
  %obj_IO*      (%obj_IO*, %obj_String*)*, ; out
  %obj_Boolean* (%obj_IO*, %obj_Any*)*,    ; isNull
  %obj_IO*      (%obj_IO*, %obj_Any*)*     ; out_any
}
%obj_IO = type { %class_IO* }

@._str.IO = constant [3 x i8] c"IO\00"
@.str.IO = alias i8* bitcast ([3 x i8]* @._str.IO to i8*)
@IO = global %class_IO { 
  %class_Any*                             @Any,
  i8*                                     @.str.IO,
  %obj_IO*      (%obj_IO*)*               @IO._constructor,
  %obj_String*  (%obj_IO*)*               @IO.toString,
  %obj_Boolean* (%obj_IO*, %obj_Any*)*    @IO.equals,
  %obj_Nothing* (%obj_IO*, %obj_String*)* @IO.abort,
  %obj_IO*      (%obj_IO*, %obj_String*)* @IO.out,
  %obj_Boolean* (%obj_IO*, %obj_Any*)*    @IO.is_null,
  %obj_IO*      (%obj_IO*, %obj_Any*)*    @IO.out_any
  ; in
  ; symbol
  ; symbol_name
}

define %obj_IO* @IO._constructor(%obj_IO* %obj) {
  %isnull = icmp eq %obj_IO* %obj, null
  %objstk = alloca %obj_IO*
  store %obj_IO* %obj, %obj_IO** %objstk
  br i1 %isnull, label %allocate, label %initialize
allocate: 
  %space = call i8* @malloc(i32 4)
  %newobj = bitcast i8* %space to %obj_IO*
  %cls_field = getelementptr inbounds %obj_IO* %newobj, i32 0, i32 0
  store %obj_IO* %newobj, %obj_IO** %objstk
  store %class_IO* @IO, %class_IO** %cls_field
  br label %initialize
initialize:
  %ret = load %obj_IO** %objstk
  
  ; Recursively call our superclass' constructor
  %as_any = bitcast %obj_IO* %ret to %obj_Any*
  call %obj_Any* @Any._constructor(%obj_Any* %as_any)
  
  ret %obj_IO* %ret
}

@IO.toString = alias 
  %obj_String* (%obj_IO*)* bitcast (                  
  %obj_String* (%obj_Any*)* @Any.toString to 
  %obj_String* (%obj_IO*)*
)

@IO.equals = alias 
  %obj_Boolean* (%obj_IO*, %obj_Any*)* bitcast (                  
  %obj_Boolean* (%obj_Any*, %obj_Any*)* @Any.equals to 
  %obj_Boolean* (%obj_IO*, %obj_Any*)* 
)


define %obj_Nothing* @IO.abort(%obj_IO* %this, %obj_String* %msg) {

  ; Call the static IO out, since the spec doesn't say this calls abort (just that it 
  ; prints a message), and the standard abort just prints the string
  call %obj_IO* @IO.out(%obj_IO* %this, %obj_String* %msg)

  call void @exit(i32 0) noreturn nounwind
  ret %obj_Nothing* null
}

define %obj_IO* @IO.out(%obj_IO* %this, %obj_String* %str) {  
  %cstr_ptr = getelementptr inbounds %obj_String* %str, i32 0, i32 2
  %cstr = load i8** %cstr_ptr
  call i32 @puts(i8* %cstr)
  
  ret %obj_IO* %this
}

define %obj_Boolean* @IO.is_null(%obj_IO* %this, %obj_Any* %obj) {
  %res = icmp eq %obj_Any* %obj, null
  %bool = call %obj_Boolean* @Boolean._constructor(%obj_Boolean* null, i1 %res)
  ret %obj_Boolean* %bool
}

@.str.null = constant [5 x i8] c"null\00"
define %obj_IO* @IO.out_any(%obj_IO* %this, %obj_Any* %arg) {

  %iocls_loc = getelementptr %obj_IO* %this, i32 0, i32 0
  %iocls = load %class_IO** %iocls_loc
  %out_loc = getelementptr %class_IO* %iocls, i32 0, i32 6
  %out = load %obj_IO* (%obj_IO*, %obj_String*)** %out_loc

  %null = icmp eq %obj_Any* %arg, null
  br i1 %null, label %outnull, label %outobj
outnull:
  %ns = getelementptr [5 x i8]* @.str.null, i32 0, i32 0
  %nullstr = call %obj_String* @String._constructor(%obj_String* null, i8* %ns)
  call %obj_IO* %out(%obj_IO* %this, %obj_String* %nullstr)
  
  br label %return
outobj:
  %cls_loc = getelementptr %obj_Any* %arg, i32 0, i32 0
  %cls = load %class_Any** %cls_loc
  %tostr_loc = getelementptr %class_Any* %cls, i32 0, i32 3
  %tostr = load %obj_String* (%obj_Any*)** %tostr_loc
  %str = call %obj_String* %tostr(%obj_Any* %arg)
  call %obj_IO* %out(%obj_IO* %this, %obj_String* %str)
  
  br label %return
return:

  ret %obj_IO* %this
}

define %obj_String* @IO.in(%obj_IO* %this) {
  %buf = alloca i8, i32 1024
  call i8* @io_in(i8* %buf, i32 1024)
  %str = call %obj_String* @String._constructor(%obj_String* null, i8* %buf)
  ret %obj_String* %str
}

