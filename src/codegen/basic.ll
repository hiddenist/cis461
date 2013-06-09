; ModuleID = 'basic.cool'

target triple = "i386-pc-linux-gnu"

; Usually I see these at the bottom of LLVM programs.  Why?
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
  %obj_Any*     ()*                     @Any._constructor,
  %obj_String*  (%obj_Any*)*            @Any.toString,
  %obj_Boolean* (%obj_Any*, %obj_Any*)* @Any.equals 
}

define %obj_Any* @Any._constructor(%obj_Any* %obj) {
  %isnull = icmp eq %obj_Any* %obj, null
  br i1 %isnull, label %allocate, label %initialize
allocate: 
  %space = call i8* @malloc(i32 4)
  %obj = bitcast i8* %space to %obj_Any*
  %cls_field = getelementptr inbounds %obj_Any* %obj, i32 0, i32 0
  store %class_Any @Any, %class_Any** %cls_field
initialize:
  ; if Any had a superclass, this is where we would recursively call its constructor
  ret %obj_Any* %obj
}

; let's just use c-style strings to make c functions easier
@.Any_str = constant [4 x i8] c"Any\00" 
define %obj_String* @Any.toString(%obj_Any* %this) {
  %str_rep = getelementptr [3 x i8]* @.Any_str, i32 0, i64 0
  %obj = call %obj_String* @String._constructor(%obj_String* null, i8* %str)
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
  %obj_String*  (%obj_Any*, %obj_Any*)*,            ; toString
  %obj_Boolean* (%obj_Any*, %obj_Any*, %obj_Any*)*, ; equals
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
  br i1 %isnull, label %allocate, label %initialize
allocate: 
  %space = call i8* @malloc(i32 4)
  %obj = bitcast i8* %space to %obj_IO*
  %cls_field = getelementptr inbounds %obj_IO* %obj, i32 0, i32 0
  store %class_IO @IO, %class_IO** %cls_field
initialize:
  ; Recursively call our superclass' constructor
  %as_any = bitcast %obj_IO* %obj to %obj_Any*
  call %obj_Any* @Any._constructor(%obj_Any* %as_any)
  
  ret %obj_IO* %obj
}

define void @IO.abort(%obj_IO* %this, %obj_String* %msg) noreturn nounwind {
  call void @abort() noreturn nounwind
}

define %obj_IO* @IO.out(%obj_IO* %this returned, %obj_String* %str) {
  ; Get str_field from the String %str
  %str_ptr_loc = getelementptr %obj_String* %str, i32 0, i32 3
  %str_ptr = load i8** %str_ptr_loc
  
  call i32 @puts(i8* %str_ptr)
  
  ret %obj_IO* %this
}

; Unit doesn't actually have a constructor or destructor defined
; we just use a global (defined below) for the single instance
%class_Unit = type {
  %class_Any*,
  %obj_Unit*    (%obj_Unit*)*,          ; _constructor
  %obj_String*  (%obj_Any*)*,           ; toString
  %obj_Boolean* (%obj_Any*, %obj_Any*)* ; equals
}
%obj_Unit = type { %class_Any* }

@Unit = global %class_Unit {
  %class_Any*                           @Any,
  %obj_Unit*    (%obj_Unit*)*           null,
  %obj_Unit*    (%obj_Unit*)*           null,
  %obj_String*  (%obj_Any*)*            @Any.toString,
  %obj_Boolean* (%obj_Any*, %obj_Any*)* @Any.equals
}
; Since there is only one instance of unit, it can be a global.
@Unit_obj = global %obj_Unit { %class_Any* @Any }


%class_Int = type { 
  %class_Any*,
  %obj_Int*     (%obj_Int*, i32)*,       ; _constructor
  %obj_String*  (%obj_Int*)*,            ; toString
  %obj_Boolean* (%obj_Int*, %obj_Any*)*, ; equals
  %obj_Int*     (%obj_Int*, %obj_Int*)*, ; _add
  %obj_Int*     (%obj_Int*, %obj_Int*)*, ; _sub
  %obj_Int*     (%obj_Int*, %obj_Int*)*, ; _mul
  %obj_Int*     (%obj_Int*, %obj_Int*)*, ; _div
  %obj_Int*     (%obj_Int*, %obj_Int*)*, ; _neg
  %obj_Boolean* (%obj_Int*, %obj_Int*)*, ; _lt
  %obj_Boolean* (%obj_Int*, %obj_Int*)*  ; _le
}
%obj_Int = type { 
  %class_Int*,
  i32* ; value
}

@Int = global { 
  %class_Any*                           @Any,
  %obj_Int*     (%obj_Int*, i32)*       @Int._constructor,
  %obj_String*  (%obj_Int*)*            @Int.toString,
  %obj_Boolean* (%obj_Int*, %obj_Any*)* @Int.equals,
  %obj_Int*     (%obj_Int*, %obj_Int*)* @Int._add,
  %obj_Int*     (%obj_Int*, %obj_Int*)* @Int._sub,
  %obj_Int*     (%obj_Int*, %obj_Int*)* @Int._mul,
  %obj_Int*     (%obj_Int*, %obj_Int*)* @Int._div,
  %obj_Int*     (%obj_Int*, %obj_Int*)* @Int._neg,
  %obj_Boolean* (%obj_Int*, %obj_Int*)* @Int._lt,
  %obj_Boolean* (%obj_Int*, %obj_Int*)* @Int._le
}

define %obj_Int* @Int._constructor(%obj_Int* %obj, i32 %val) {
  %isnull = icmp eq %obj_Int* %obj, null
  br i1 %isnull, label %allocate, label %initialize
allocate: 
  %space = call i8* @malloc(i32 8)

  ; do I need to store this on the stack ever?
  %obj = bitcast i8* %space to %obj_Int*

  %cls_field = getelementptr inbounds %obj_Int* %obj, i32 0, i32 0
  store %class_Int @Int, %class_Int** %cls_field
initialize:
  ; Recursively call our superclass' constructor
  %as_any = bitcast %obj_Int* %obj to %obj_Any*
  call %obj_Any* @Any._constructor(%obj_Any* %as_any)
  
  ;;;; Int initialization ;;;;
  
  ; create heap space for the integer value
  %space = call i8* @malloc(i32 4)
  %intp = bitcast i8* %space to i32*
  store i32 %val, i32* %intp

  ; store the integer pointer to the value field
  %valfield = getelementptr %obj_Int* %obj, i32 0, i32 3
  store i32* %intp, i32** %valfield

  ret %obj_Int* %obj
}


%class_Boolean = type { 
  %class_Any*,
  %obj_Boolean* (%obj_Boolean*, i1)*,       ; _constructor
  %obj_String*  (%obj_Boolean*)*,           ; toString
  %obj_Boolean* (%obj_Boolean*, %obj_Any*)* ; equals
}
%obj_Boolean = type { 
  %class_Boolean*,
  i1 ; value
}

@Boolean = global {
  %class_Any*                               @Any,
  %obj_Boolean* (%obj_Boolean*, i1)*        @Boolean._constructor,
  %obj_String*  (%obj_Boolean*)*            @Boolean.toString,
  %obj_Boolean* (%obj_Boolean*, %obj_Any*)* @Boolean.equals
}


%class_String = type { 
  %class_Any*,
  %obj_String*  (i8*)*,                                ; _constructor
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

@String = global {
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
  br i1 %isnull, label %allocate, label %initialize
allocate: 
  %space = call i8* @malloc(i32 12)

  ; do I need to store this on the stack ever?
  %obj = bitcast i8* %space to %obj_String*

  %cls_field = getelementptr inbounds %obj_String* %obj, i32 0, i32 0
  store %class_String @String, %class_String** %cls_field
initialize:
  ; Recursively call our superclass' constructor
  %as_any = bitcast %obj_String* %obj to %obj_Any*
  call %obj_Any* @Any._constructor(%obj_Any* %as_any)
  
  ;;;; String initialization ;;;;

  ; Get the length of the string
  %len = call i32 @strlen(i8* %str) nounwind readonly

  ; Create an Int of that length
  %int = call %obj_Int* @Int._constructor(%obj_Int* null, i32 %len)

  ; Store the Int in the length field
  %lenfield = getelementptr %obj_String* %obj, i32 0, i32 2
  store %obj_Int* %int, %obj_Int** %lenfield
  
  ; Allocate space on the heap for the string
  %bytes = add i32 %len, 1
  %strp = call i8* @malloc(i32 %bytes)

  ; Copy the string into this new space
  ; todo: yeah... in a second
  
  ; Store the new string pointer in the str_field field
  %strfield = getelementptr %obj_String* %obj, i32 0, i32 3
  store i8* %strp, i8** %strfield

  
  ret %obj_String* %obj
}

%class_Symbol = type { 
  %class_Any*,
  %obj_Symbol*  (%obj_Symbol*)*,         ; _constructor
  %obj_String*  (%obj_Symbol*)*,         ; toString
  %obj_Boolean* (%obj_Any*, %obj_Any*)*, ; equals
  %obj_Int*     (%obj_Symbol)*           ; hashCode
}
%obj_Symbol = type { 
  %class_Symbol*,
  %obj_Symbol*,  ; next
  %obj_String*,  ; name
  %obj_Int*      ; hash
}

@Symbol = global { 
  %class_Any*                                @Any,
  %obj_Symbol*  (%obj_Symbol*, %obj_String)* @Symbol._constructor,
  %obj_String*  (%obj_Symbol*)*              @Symbol.toString,
  %obj_Boolean* (%obj_Any*, %obj_Any*)*      @Any.equals,
  %obj_Int*     (%obj_Symbol)*               @Symbol.hashCode
}

%class_ArrayAny = type {
  %class_Any*,
  %obj_ArrayAny* (%obj_ArrayAny*, %obj_Int*)*,           ; _constructor
  %obj_String*   (%obj_Any*)*,                           ; toString
  %obj_Boolean*  (%obj_Any*)*,                           ; equals
  %obj_Int*      (%obj_ArrayAny*)*,                      ; length
  %obj_ArrayAny* (%obj_ArrayAny*, %obj_Int*)*,           ; resize 
  %obj_Any       (%obj_ArrayAny*, %obj_Int*)*,           ; get
  %obj_Any       (%obj_ArrayAny*, %obj_Int*, %obj_Any*)* ; set
}
%obj_ArrayAny = type {
  %class_ArrayAny*,
  %obj_Int*,      ; length
  [0 x %obj_Any*] ; array_field
}

@ArrayAny = global {
  %class_Any*                                            @Any,
  %obj_ArrayAny* (%obj_ArrayAny*, %obj_Int*)*            @ArrayAny._constructor,
  %obj_String*   (%obj_Any*)*                            @Any.toString,
  %obj_Boolean*  (%obj_Any*)*                            @Any.equals,
  %obj_Int*      (%obj_ArrayAny*)*                       @ArrayAny.length,
  %obj_ArrayAny* (%obj_ArrayAny*, %obj_Int*)*            @ArrayAny.resize,
  %obj_Any       (%obj_ArrayAny*, %obj_Int*)*            @ArrayAny.get,
  %obj_Any       (%obj_ArrayAny*, %obj_Int*, %obj_Any*)* @ArrayAny.set
}

define void @main() {
entry:
  ret void
}
