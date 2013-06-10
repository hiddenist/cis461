; ModuleID = 'basic.cool'

target triple = "i386-pc-linux-gnu"

; Usually I see these at the bottom of LLVM programs.  Why not the top?
declare noalias i8* @malloc(i32) nounwind
declare void @abort() noreturn nounwind
declare i32 @puts(i8*)
declare i8* @gets(i8*)
declare i32 @strlen(i8*) nounwind readonly

%class_Any = type { 
  %class_Any*,
  %obj_Any*     (%obj_Any*)*,           ; _constructor
  %obj_String*  (%obj_Any*)*,           ; toString
  %obj_Boolean* (%obj_Any*, %obj_Any*)* ; equals
}
%obj_Any = type { %class_Any* }

@Any = global %class_Any { 
  %class_Any*                           null,
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
@.Any_str = constant [4 x i8] c"Any\00" 
define %obj_String* @Any.toString(%obj_Any* %this) {
  %str_rep = getelementptr [4 x i8]* @.Any_str, i32 0, i32 0
  %obj = call %obj_String* @String._constructor(%obj_String* null, i8* %str_rep)
  ret %obj_String* %obj
}

define %obj_Boolean* @Any.equals(%obj_Any* %this, %obj_Any* %other) {
  ; The base equals just checks if these are pointers to the same object.
  %eq = icmp eq %obj_Any* %this, %that 
  %bool = call %obj_Boolean* @Boolean._constructor(%obj_Boolean* null, i1 %eq)
  ret %obj_Boolean* %bool
}

%class_IO = type { 
  %class_Any*,
  %obj_IO*      (%obj_IO*)*,                        ; _constructor
  %obj_String*  (%obj_Any*)*,                       ; toString
  %obj_Boolean* (%obj_Any*, %obj_Any*)*,            ; equals
  void          (%obj_IO*, %obj_String*)*,          ; abort
  %obj_IO*      (%obj_IO*, %obj_String*)*,          ; out
  %obj_Boolean* (%obj_IO*, %obj_IO*)*,              ; is_null
  %obj_Any*     (%obj_IO*, %obj_IO*)*,              ; out_any
  %obj_String*  (%obj_IO*)*,                        ; in
  %obj_Symbol*  (%obj_IO*, %obj_String*)*,          ; symbol
  %obj_String*  (%obj_IO*, %obj_Symbol*)*           ; symbol_name
}
%obj_IO = type { %class_IO* }

@IO = global %class_IO { 
  %class_Any*                             @Any,
  %obj_IO*      (%obj_IO*)*               @IO._constructor,
  %obj_String*  (%obj_Any*)*              @Any.toString,
  %obj_Boolean* (%obj_Any*, %obj_Any*)*   @Any.equals,
  void          (%obj_IO*, %obj_String*)* @IO.abort,
  %obj_IO*      (%obj_IO*, %obj_String*)* @IO.out,
  %obj_Boolean* (%obj_IO*, %obj_IO*)*     @IO.is_null,
  %obj_Any*     (%obj_IO*, %obj_IO*)*     @IO.out_any,
  %obj_String*  (%obj_IO*)*               @IO.in,
  %obj_Symbol*  (%obj_IO*, %obj_String*)* @IO.symbol,
  %obj_String*  (%obj_IO*, %obj_Symbol*)* @IO.symbol_name
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

define void @IO.abort(%obj_IO* %this, %obj_String* %msg) noreturn nounwind {
  call void @abort() noreturn nounwind
}

define %obj_IO* @IO.out(%obj_IO* %this returned, %obj_String* %str) {
  ; Get str_field from the String %str
  %cstr_ptr = getelementptr %obj_String* %str, i32 0, i32 2
  %cstr = load i8** %cstr_ptr
  
  call i32 @puts(i8* %cstr)
  
  ret %obj_IO* %this
}


%class_Unit = type {
  %class_Any*,
  %obj_Unit*    (%obj_Unit*)*,          ; _constructor
  %obj_String*  (%obj_Any*)*,           ; toString
  %obj_Boolean* (%obj_Any*, %obj_Any*)* ; equals
}
%obj_Unit = type { %class_Unit* }

@Unit = global %class_Unit {
  %class_Any*                            @Any,
  %obj_Unit*    (%obj_Unit*)*            null, ; No constructor - only one instance.
  %obj_String*  (%obj_Unit*)*            @Unit.toString,
  %obj_Boolean* (%obj_Unit*, %obj_Any*)* @Unit.equals
}
; Since there is only one instance of unit, it can be a global.
@the_Unit = global %obj_Unit { %class_Unit* @Unit }


%class_Int = type { 
  %class_Any*,
  %obj_Int*     (%obj_Int*, i32)*,       ; _constructor
  %obj_String*  (%obj_Int*)*,            ; toString
  %obj_Boolean* (%obj_Int*, %obj_Any*)*, ; equals
  %obj_Boolean* (%obj_Int*, %obj_Int*)*, ; _lt
  %obj_Boolean* (%obj_Int*, %obj_Int*)*  ; _le
  %obj_Int*     (%obj_Int*, %obj_Int*)*, ; _add
  %obj_Int*     (%obj_Int*, %obj_Int*)*, ; _sub
  %obj_Int*     (%obj_Int*, %obj_Int*)*, ; _mul
  %obj_Int*     (%obj_Int*, %obj_Int*)*, ; _div
  %obj_Int*     (%obj_Int*, %obj_Int*)*, ; _neg
}
%obj_Int = type { 
  %class_Int*,
  i32* ; value
}

@Int = global %class_Int { 
  %class_Any*                           @Any,
  %obj_Int*     (%obj_Int*, i32)*       @Int._constructor,
  %obj_String*  (%obj_Int*)*            @Int.toString,
  %obj_Boolean* (%obj_Int*, %obj_Any*)* @Int.equals,
  %obj_Boolean* (%obj_Int*, %obj_Int*)* @Int._lt,
  %obj_Boolean* (%obj_Int*, %obj_Int*)* @Int._le
  %obj_Int*     (%obj_Int*, %obj_Int*)* @Int._add,
  %obj_Int*     (%obj_Int*, %obj_Int*)* @Int._sub,
  %obj_Int*     (%obj_Int*, %obj_Int*)* @Int._mul,
  %obj_Int*     (%obj_Int*, %obj_Int*)* @Int._div,
  %obj_Int*     (%obj_Int*, %obj_Int*)* @Int._neg,
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

define %obj_Boolean* @Int.equals(%obj_Int* %this, %obj_Int* %that) {
  %lhs = call i32 @.get_int_val(%obj_Int* %this)
  %rhs = call i32 @.get_int_val(%obj_Int* %that)
  %eq = icmp eq i32 %lhs, %rhs
  %bool = call %obj_Boolean* @Boolean._constructor(%obj_Boolean* null, i1 %eq)
  ret %obj_Boolean* %bool
}

define %obj_Boolean* @Int._lt(%obj_Int* %this, %obj_Int* %that) {
  %lhs = call i32 @.get_int_val(%obj_Int* %this)
  %rhs = call i32 @.get_int_val(%obj_Int* %that)
  %eq = icmp slt i32 %lhs, %rhs
  %bool = call %obj_Boolean* @Boolean._constructor(%obj_Boolean* null, i1 %eq)
  ret %obj_Boolean* %bool
}

define %obj_Boolean* @Int._le(%obj_Int* %this, %obj_Int* %that) {
  %lhs = call i32 @.get_int_val(%obj_Int* %this)
  %rhs = call i32 @.get_int_val(%obj_Int* %that)
  %eq = icmp sle i32 %lhs, %rhs
  %bool = call %obj_Boolean* @Boolean._constructor(%obj_Boolean* null, i1 %eq)
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



%class_Boolean = type { 
  %class_Any*,
  %obj_Boolean* (%obj_Boolean*, i1)*,       ; _constructor
  %obj_String*  (%obj_Boolean*)*,           ; toString
  %obj_Boolean* (%obj_Boolean*, %obj_Any*)* ; equals
}
%obj_Boolean = type { 
  %class_Boolean*,
  i1* ; value
}

@Boolean = global %class_Boolean {
  %class_Any*                               @Any,
  %obj_Boolean* (%obj_Boolean*, i1)*        @Boolean._constructor,
  %obj_String*  (%obj_Boolean*)*            @Boolean.toString,
  %obj_Boolean* (%obj_Boolean*, %obj_Any*)* @Boolean.equals
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

@.true_str = constant [ 5 x i8 ] c"true\00";
@.false_str = constant [ 6 x i8 ] c"false\00";
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



%class_String = type { 
  %class_Any*,
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

@String = global %class_String {
  %class_Any*                                         @Any,
  %obj_String*  (%obj_String*, i8*)*                  @String._constructor,
  %obj_String*  (%obj_String*)*                       @String.toString,
  %obj_Boolean* (%obj_String*, %obj_Any*)*            @String.equals,
  %obj_Int*     (%obj_String*)*                       @String.length,
  %obj_String*  (%obj_String*, %obj_String*)*         @String.concat,
  %obj_String*  (%obj_String*, %obj_Int*, %obj_Int*)* @String.substring,
  %obj_Int*     (%obj_String*, %obj_Int*)*            @String.charAt,
  %obj_Int*     (%obj_String*, %obj_String*)*         @String.indexOf
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

%class_Symbol = type { 
  %class_Any*,
  %obj_Symbol*  (%obj_Symbol*, %obj_String*)*, ; _constructor
  %obj_String*  (%obj_Symbol*)*,               ; toString
  %obj_Boolean* (%obj_Symbol*, %obj_Any*)*,    ; equals
  %obj_Int*     (%obj_Symbol)*                 ; hashCode
}
%obj_Symbol = type { 
  %class_Symbol*,
  %obj_Symbol*,  ; next
  %obj_String*,  ; name
  %obj_Int*      ; hash
}

@Symbol = global %class_Symbol { 
  %class_Any*                                 @Any,
  %obj_Symbol*  (%obj_Symbol*, %obj_String*)* @Symbol._constructor,
  %obj_String*  (%obj_Symbol*)*               @Symbol.toString,
  %obj_Boolean* (%obj_Symbol*, %obj_Any*)*    @Symbol.equals,
  %obj_Int*     (%obj_Symbol)*                @Symbol.hashCode
}

%class_ArrayAny = type {
  %class_Any*,
  %obj_ArrayAny* (%obj_ArrayAny*, %obj_Int*)*,            ; _constructor
  %obj_String*   (%obj_ArrayAny*)*,                       ; toString
  %obj_Boolean*  (%obj_ArrayAny*)*,                       ; equals
  %obj_Int*      (%obj_ArrayAny*)*,                       ; length
  %obj_ArrayAny* (%obj_ArrayAny*, %obj_Int*)*,            ; resize 
  %obj_Any*      (%obj_ArrayAny*, %obj_Int*)*,            ; get
  %obj_Any*      (%obj_ArrayAny*, %obj_Int*, %obj_Any*)*  ; set
}
%obj_ArrayAny = type {
  %class_ArrayAny*,
  %obj_Int*,      ; length
  [0 x %obj_Any*]* ; array_field
}

@ArrayAny = global %class_ArrayAny {
  %class_Any*                                             @Any,
  %obj_ArrayAny* (%obj_ArrayAny*, %obj_Int*)*             @ArrayAny._constructor,
  %obj_String*   (%obj_ArrayAny*)*                        @ArrayAny.toString,
  %obj_Boolean*  (%obj_ArrayAny*)*                        @ArrayAny.equals,
  %obj_Int*      (%obj_ArrayAny*)*                        @ArrayAny.length,
  %obj_ArrayAny* (%obj_ArrayAny*, %obj_Int*)*             @ArrayAny.resize,
  %obj_Any*      (%obj_ArrayAny*, %obj_Int*)*             @ArrayAny.get,
  %obj_Any*      (%obj_ArrayAny*, %obj_Int*, %obj_Any*)*  @ArrayAny.set
}

define void @main() {
entry:
  ret void
}
