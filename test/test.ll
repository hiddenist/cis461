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
  %obj_Any*     (%obj_Any*)*,           ; _constructor
  %obj_String*  (%obj_Any*)*            ; _toString
}
%obj_Any = type { %class_Any* }

@Any = global %class_Any { 
  %class_Any*                           null,
  %obj_Any*     (%obj_Any*)*            @Any._constructor,
  %obj_String*  (%obj_Any*)*            @Any.toString
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


%class_Int = type { 
  %class_Any*,
  %obj_Int*     (%obj_Int*, i32)*,    ; _constructor
  %obj_String*  (%obj_Int*)*          ; toString
}
%obj_Int = type { 
  %class_Int*,
  i32* ; value
}

@Int = global %class_Int { 
  %class_Any*                           @Any,
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

@.sprintf_format = constant [3 x i8] c"%d\00" 
define %obj_String* @Int.toString(%obj_Int* %this) {
	%format = getelementptr [3 x i8]* @.sprintf_format, i32 0, i32 0
	; biggest 32 bit int is 10 chars, and maybe a -, plus null char, 
	; and some extra just in case I've forgotten something (it's just stack space)
	%buffer = alloca i8, i32 16
	%valpp = getelementptr %obj_Int* %this, i32 0, i32 1
	%valp = load i32** %valpp
	%val = load i32* %valp
	call i32 (i8*, i8*, ...)* @sprintf(i8* %buffer, i8* %format , i32 %val)
	%str = call %obj_String* @String._constructor(%obj_String* null, i8* %buffer)
	ret %obj_String* %str
} 

%class_String = type { 
  %class_Any*,
  %obj_String*  (%obj_String*, i8*)*                                ; _constructor
}
%obj_String = type { 
  %class_String*,
  %obj_Int*, ; length
  i8*        ; str_field
}

@String = global %class_String {
  %class_Any*                                         @Any,
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
  %obj_IO*      (%obj_IO*)*,                        ; _constructor
  %obj_String*  (%obj_IO*)*,                        ; toString
  %obj_IO*      (%obj_IO*, %obj_String*)*           ; out
}
%obj_IO = type { %class_IO* }

@IO = global %class_IO { 
  %class_Any*                             @Any,
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
  %int = call %obj_Int* @Int._constructor(%obj_Int* null, i32 42) 
  
  ; Call the "toString" method
  %cls_loc = getelementptr %obj_Int* %int, i32 0, i32 0
  %cls = load %class_Int** %cls_loc
  %tostr_loc = getelementptr %class_Int* %cls, i32 0, i32 2
  %tostr = load %obj_String* (%obj_Int*)** %tostr_loc
  %str = call %obj_String* %tostr(%obj_Int* %int)

  ; Output result to stdout
  %io = call %obj_IO* @IO._constructor(%obj_IO* null)
  %iocls_loc = getelementptr %obj_IO* %io, i32 0, i32 0
  %iocls = load %class_IO** %iocls_loc
  %out_loc = getelementptr %class_IO* %iocls, i32 0, i32 3
  %out = load %obj_IO* (%obj_IO*, %obj_String*)** %out_loc
  call %obj_IO* %out(%obj_IO* %io, %obj_String* %str)
  ret i32 0
}
