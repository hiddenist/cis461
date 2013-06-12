; ModuleID = 'basic.cool'

target triple = "i386-pc-linux-gnu"

; Usually I see these at the bottom of LLVM programs.  Why not the top?
declare noalias i8* @malloc(i32) nounwind
declare i32 @puts(i8*)
declare i32 @putchar(i8)
declare i32 @sprintf(i8*, i8*, ...)
declare i32 @strlen(i8*) nounwind readonly

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
  %obj_String*  (%obj_Boolean*)*,           @Boolean.toString
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
  %obj_Int*     (%obj_Int*, i32)*,    ; _constructor
  %obj_String*  (%obj_Int*)*          ; toString
}
%obj_Int = type { 
  %class_Int*,
  i32* ; value
}

@._str.Int = constant [4 x i8] c"Int\00"
@.str.Int = alias i8* bitcast ([4 x i8]* @._str.Int to i8*)
@Int = global %class_Int { 
  %class_Any*                           @Any,
  i8*                                   @.str.Int,
  %obj_Int*     (%obj_Int*, i32)*       @Int._constructor,
  %obj_String*     (%obj_Int*)*         @Int.toString
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


%class_String = type { 
  %class_Any*,
  i8*,
  %obj_String*  (%obj_String*, i8*)*                                ; _constructor
}
%obj_String = type { 
  %class_String*,
  %obj_Int*, ; length
  i8*        ; str_field
}

@._str.String = constant [7 x i8] c"String\00"
@.str.String = alias i8* bitcast ([7 x i8]* @._str.String to i8*)
@String = global %class_String {
  %class_Any*                                         @Any,
  i8*                                                 @.str.String,
  %obj_String*  (%obj_String*, i8*)*                  @String._constructor
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

%class_IO = type { 
  %class_Any*,
  i8*,
  %obj_IO*      (%obj_IO*)*,                        ; _constructor
  %obj_String*  (%obj_IO*)*,                        ; toString
  %obj_IO*      (%obj_IO*, %obj_String*)*           ; out
}
%obj_IO = type { %class_IO* }

@._str.IO = constant [3 x i8] c"IO\00"
@.str.IO = alias i8* bitcast ([3 x i8]* @._str.IO to i8*)
@IO = global %class_IO { 
  %class_Any*                             @Any,
  i8*                                     @.str.IO,
  %obj_IO*      (%obj_IO*)*               @IO._constructor,
  %obj_String*  (%obj_IO*)*               @IO.toString,
  %obj_IO*      (%obj_IO*, %obj_String*)* @IO.out
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


define %obj_IO* @IO.out(%obj_IO* %this, %obj_String* %str) {  
  %cstr_ptr = getelementptr inbounds %obj_String* %str, i32 0, i32 2
  %cstr = load i8** %cstr_ptr
  call i32 @puts(i8* %cstr)
  
  ret %obj_IO* %this
}

define i32 @llvm_main() {
  %1 = call %obj_Boolean* @Boolean._constructor(%obj_Boolean* null, i1 0)
  %2 = call %obj_Int* @Int._constructor(%obj_Int* null, i32 0)
  %3 = bitcast %obj_Int* %2 to %obj_Any*
  %obj = call %obj_Boolean* @Boolean.equals(%obj_Boolean* %1, %obj_Any* %3)

  %as_any = bitcast %obj_Boolean* %obj to %obj_Any*
  ;%as_any = call %obj_Any* @Any._constructor(%obj_Any* null)
  
  ; Call the "toString" method
  %cls_loc = getelementptr %obj_Any* %as_any, i32 0, i32 0
  %cls = load %class_Any** %cls_loc
  %tostr_loc = getelementptr %class_Any* %cls, i32 0, i32 3
  %tostr = load %obj_String* (%obj_Any*)** %tostr_loc
  %str = call %obj_String* %tostr(%obj_Any* %as_any)

  ; Output result to stdout
  %io = call %obj_IO* @IO._constructor(%obj_IO* null)
  %iocls_loc = getelementptr %obj_IO* %io, i32 0, i32 0
  %iocls = load %class_IO** %iocls_loc
  %out_loc = getelementptr %class_IO* %iocls, i32 0, i32 4
  %out = load %obj_IO* (%obj_IO*, %obj_String*)** %out_loc
  call %obj_IO* %out(%obj_IO* %io, %obj_String* %str)
  ret i32 0
}
