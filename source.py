import io
import sys
import os
import pprint

pp = pprint.PrettyPrinter(4,compact=True,sort_dicts=False)
istack = bytearray()
scopeStack = [istack]
nbracketStack = []
blockstack = []
varList = []
varStack = [varList]


# -- SETTINGS --

# Stack Options:
BEFORE_STACK_BUFFER_INITIALISATION = True
'''
Not specifically required but you absolutely should use it if you plan to use chars (as well as boolians) as your first variables
'''
AFTER_STACK_CLEANUP = True
# 

# Debug:
ADDITIONAL_DEBUG_SETTINGS = True

LINE_LEN_REF_MAX_B = 8
#MEMORY_CAPACITY = 640000
#STRING_SIZE_BYTE_LIMIT = 4800

# ---------------











class vptr:
    def __init__(self,start=0,size=0) -> None:
        self.start = start
        self.size = size
    start: int
    size: int
#print(varList)
def varExists(cVars,name: str):
    #print(cVars)
    for v in cVars:
        if name == v["name"]:
            return True
    return False

def pushVar(cVars,name: str, ptr: vptr):
    if ADDITIONAL_DEBUG_SETTINGS:
        assert not varExists(cVars,name), f"Error: Attempting to allocate the same variable twice ({name})(check naming)\nVars: {cVars}"
        cVars.append({
            "name":name,
            "ptr":ptr
        })    
    else:
        cVars.append({
            "name":name,
            "ptr":ptr
        })
def freeByName(name: str):
    global istack
    b = getVarByName(name)
    free(b["ptr"])
    del varList[b["varListAt"]]
    

def free(cScope:bytearray,ptr: vptr): 
    cScope = cScope[:ptr.start] + cScope[ptr.start+ptr.size:]
    del ptr
    return cScope
def alloc(cScope: bytearray,size: int,value:int=0):
    optr = vptr()
    #print(size)
    #print(istack)
    #print(len(istack))
    optr.start = len(cScope)
    
    #print(optr.start)
    optr.size = size
    for i in range(size):
        istack.append(value)
    return optr
    
def getChunk(size: int, value: int = 0):
    out = bytearray()
    for i in range(size):
        out.append(value)
    return out
    
def grabLine(f):
    buffer = ""
    cPos = f.tell()
    # print("--- grabLine ---")
    # print(f"cPos: {cPos}")
    f.seek(0,2)
    EOF = f.tell()
    #print(EOF)
    #f.seek(0,0)
    #print(f"File: \" {f.read()} \"")
    #f.flush()
    f.seek(cPos,0)
    # print(f"f.tell(): {f.tell()}")
    c = ""
    while c != ";":
        c = ""
        c = f.read(1).decode("utf-8")
        if f.tell() > EOF:
            f.flush()
        # print(c,end="")
        #print(f"Position: {f.tell()}, Character: '{c}'")
        
        assert f.tell() < EOF, "OOPS: Something has gone terribly wrong! Check your syntax, you probably missed a ; "
        buffer += c
    # print(f"\nf.tell(): {f.tell()}")
    # print("------------------")
    
    #f.seek(1,1)
    return buffer[:len(buffer)-1]
def grabWords(f):
    f.seek(0,2)
    EOF = f.tell()
    f.seek(0,0)
    c = ""
    word = ""
    lines = []
    lcount = 0
    index = 0
    tindex = 0 
    while f.tell() < EOF:
        c = f.read(1).decode("utf-8")
        if c == ";":
            if word != "":
                if word == "{":
                    assert False, f"Error: Invalid syntax at char {f.tell()} Line: {lcount} Word: {tindex}"
                elif word == "}":
                    assert False, f"Error: Invalid syntax at char {f.tell()} Line: {lcount} Word: {tindex}"
                elif word == "(":
                    nbracketStack.append(tindex)
                    lines.append({
                        "word":word,
                        "index":index,
                        "line":lcount,
                        "end":0
                    })
                elif word == ")":
                    assert len(nbracketStack) > 0, f"Error: Closing bracket used but block was never opened At: Char: {f.tell()-1} Line: {lcount} Word: {tindex}"
                    sIndex = nbracketStack.pop()
                    lines[sIndex]["end"] = tindex
                    lines.append({    
                        "word":word,
                        "index":index,
                        "line":lcount,
                        "start":sIndex
                    })
                else:
                    lines.append({    
                        "word":word,
                        "index":index,
                        "line":lcount
                    })
                tindex += 1
            index = 0
            lcount += 1
        elif c.isspace():
            if word != "":
                if word == "{":
                    blockstack.append(tindex)
                    lines.append({    
                        "word":word,
                        "index":index,
                        "line":lcount,
                        "end":0
                    })
                elif word == "}":
                    assert len(blockstack) > 0, f"Error: Closing bracket used but block was never opened At: Char: {f.tell()-1} Line: {lcount} Word: {tindex}"
                    sIndex = blockstack.pop()
                    lines[sIndex]["end"] = tindex
                    lines.append({    
                        "word":word,
                        "index":index,
                        "line":lcount,
                        "start":sIndex
                    })
                elif word == "(":
                    nbracketStack.append(tindex)
                    lines.append({
                        "word":word,
                        "index":index,
                        "line":lcount,
                        "end":0
                    })
                elif word == ")":
                    assert len(nbracketStack) > 0, f"Error: Closing bracket used but block was never opened At: Char: {f.tell()-1} Line: {lcount} Word: {tindex}"
                    sIndex = nbracketStack.pop()
                    lines[sIndex]["end"] = tindex
                    lines.append({    
                        "word":word,
                        "index":index,
                        "line":lcount,
                        "start":sIndex
                    })
                else:
                    lines.append({    
                        "word":word,
                        "index":index,
                        "line":lcount
                    })
                index += 1
                tindex += 1
                word = ""
        else:
            word += c
    return lines

            
        
def getVarByName(cVars,name: str):
    for index,i in enumerate(cVars):
        #print(f"In var: at {index}: {i}")
        if i["name"] == name:
            i["varListAt"] = index
            return i
    assert False, f"Variable name: {name} not found in scope!"
def getValueByName_b(cScope,cVars,name: str):
    t = getVarByName(cVars,name)
    #print(name)
    return cScope[t["ptr"].start : t["ptr"].start+t["ptr"].size]
def getValueInStack(ptr: vptr,stack: bytearray):
    return stack[:ptr.start]+stack[ptr.start+ptr.size:]
def calcOp(val1,val2,op):
    match op:
        case "+":
            return val1 + val2
        case "-":
            return val1 - val2
        case "*":
            return val1 * val2
        case "/":
            return val1 / val2
    assert False, "Undefined Number/string operator"
def getClosing(line: list,position) -> int:
    if line[position] == "(":
        c = position + 1
        
        while line[c] != ")":
            if line[c] == "(":
                c = getClosing(line,c)
            c += 1
        return c
# def calcLine(line: list, position):
#     for index, word in enumerate(line[position+1:getClosing(line,position)-1]):
#         if word == "+" or word == "-" or word == "*" or word == "/":
#             calcOp()
def computeSim(cVars,cStack,words,offset=0) -> int:
    oWordsResults = []
    oIndex = 0
    result = 0
    if type(words) == dict:
        if words["word"].isnumeric():
            #print("GETTING NUMBER?")
            return (int(words["word"]),0)
        else:
            #print("GETTING VARIABLE FROM STACK!")
            return (int.from_bytes(getValueByName_b(cStack,cVars,words["word"]),"little"),0)
    else:
        index = 0
        while index < len(words):
            wordInfo = words[index]   
            if wordInfo["word"] == "(":
                assert wordInfo["end"]-offset > 0, f"Error: Bracket opened but never closed at {wordInfo['line']}"
                (result,s) = computeSim(cVars,cStack,words[index+1:wordInfo["end"]-offset])
                oWordsResults.append({
                    "word":str(result),
                })
                oIndex += 1 + s
            elif wordInfo["word"] == ")":
                pass
            # -------------------------------
            # boolean operations
            # -------------------------------
            elif wordInfo["word"] == "==":
                a = oWordsResults.pop()["word"]
                if words[index+1]["word"] == "(":
                    (b,s) = computeSim(cVars,cStack,words[index+1:words[index+1]["end"]-1])
                    s -= 2
                else:
                    if words[index+1]["word"].isnumeric():
                        b = int(words[index+1]["word"])
                    else:
                        b = int.from_bytes(getValueByName_b(cStack,cVars,words[index+1]["word"]),"little")
                    s = 0
                if a.isnumeric():
                    a = int(a)
                else:
                    a = int.from_bytes(getValueByName_b(cStack,cVars,a))
                oWordsResults.append({"word":str(int(a==b))})
                index += 1 + s
            elif wordInfo["word"] == "<":
                # a = oWordsResults.pop()["word"]
                # (b,s) = computeSim(cVars,cStack,words[index+1:])
                # if a.isnumeric():
                #     a = int(a)
                # else:
                #     a = int.from_bytes(getValueByName_b(cStack,cVars,a))
                # if a < b:
                #     oWordsResults.append({"word":"1"})
                # else:
                #     oWordsResults.append({"word":"0"})
                # oIndex += 1 + s
                a = oWordsResults.pop()["word"]
                if words[index+1]["word"] == "(":
                    (b,s) = computeSim(cVars,cStack,words[index+1:words[index+1]["end"]-1])
                    s -= 2
                else:
                    if words[index+1]["word"].isnumeric():
                        b = int(words[index+1]["word"])
                    else:
                        b = int.from_bytes(getValueByName_b(cStack,cVars,words[index+1]["word"]),"little")
                    s = 0
                if a.isnumeric():
                    a = int(a)
                else:
                    a = int.from_bytes(getValueByName_b(cStack,cVars,a))
                oWordsResults.append({"word":str(int(a<b))})
                index += 1 + s
            elif wordInfo["word"] == ">":
                # a = oWordsResults.pop()["word"]
                # (b,s) = computeSim(cVars,cStack,words[index+1:])
                # if a.isnumeric():
                #     a = int(a)
                # else:
                #     a = int.from_bytes(getValueByName_b(cStack,cVars,a))
                # if a > b:
                #     oWordsResults.append({"word":"1"})
                # else:
                #     oWordsResults.append({"word":"0"})
                # oIndex += 1 + s
                a = oWordsResults.pop()["word"]
                if words[index+1]["word"] == "(":
                    (b,s) = computeSim(cVars,cStack,words[index+1:words[index+1]["end"]-1])
                    s -= 2
                else:
                    if words[index+1]["word"].isnumeric():
                        b = int(words[index+1]["word"])
                    else:
                        b = int.from_bytes(getValueByName_b(cStack,cVars,words[index+1]["word"]),"little")
                    s = 0
                if a.isnumeric():
                    a = int(a)
                else:
                    a = int.from_bytes(getValueByName_b(cStack,cVars,a))
                oWordsResults.append({"word":str(int(a>b))})
                index += 1 + s
            elif wordInfo["word"] == "<=":
                # a = oWordsResults.pop()["word"]
                # (b,s) = computeSim(cVars,cStack,words[index+1:])
                # if a.isnumeric():
                #     a = int(a)
                # else:
                #     a = int.from_bytes(getValueByName_b(cStack,cVars,a))
                # if a <= b:
                #     oWordsResults.append({"word":"1"})
                # else:
                #     oWordsResults.append({"word":"0"})
                # oIndex += 1 + s
                a = oWordsResults.pop()["word"]
                if words[index+1]["word"] == "(":
                    (b,s) = computeSim(cVars,cStack,words[index+1:words[index+1]["end"]-1])
                    s -= 2
                else:
                    if words[index+1]["word"].isnumeric():
                        b = int(words[index+1]["word"])
                    else:
                        b = int.from_bytes(getValueByName_b(cStack,cVars,words[index+1]["word"]),"little")
                    s = 0
                if a.isnumeric():
                    a = int(a)
                else:
                    a = int.from_bytes(getValueByName_b(cStack,cVars,a))
                oWordsResults.append({"word":str(int(a<=b))})
                index += 1 + s
            elif wordInfo["word"] == ">=":
                # a = oWordsResults.pop()["word"]
                # (b,s) = computeSim(cVars,cStack,words[index+1:])
                # if a.isnumeric():
                #     a = int(a)
                # else:
                #     a = int.from_bytes(getValueByName_b(cStack,cVars,a))
                # if a >= b:
                #     oWordsResults.append({"word":"1"})
                # else:
                #     oWordsResults.append({"word":"0"})
                # oIndex += 1 + s
                a = oWordsResults.pop()["word"]
                if words[index+1]["word"] == "(":
                    (b,s) = computeSim(cVars,cStack,words[index+1:words[index+1]["end"]-1])
                    s -= 2
                else:
                    if words[index+1]["word"].isnumeric():
                        b = int(words[index+1]["word"])
                    else:
                        b = int.from_bytes(getValueByName_b(cStack,cVars,words[index+1]["word"]),"little")
                    s = 0
                if a.isnumeric():
                    a = int(a)
                else:
                    a = int.from_bytes(getValueByName_b(cStack,cVars,a))
                oWordsResults.append({"word":str(int(a>=b))})
                index += 1 + s
            # ---------------------   
            # arithmetic operations
            # ---------------------
            elif wordInfo["word"] == "+":
                a = oWordsResults.pop()["word"]
                (b,s) = computeSim(cVars,cStack,words[index+1:])
                if a.isnumeric():
                    a = int(a)
                else:
                    a = int.from_bytes(getValueByName_b(cStack,cVars,a))
                oWordsResults.append({"word":str(a+b)})
                index += 1 + s
            elif wordInfo["word"] == "-":
                a = oWordsResults.pop()["word"]
                (b,s) = computeSim(cVars,cStack,words[index+1:])
                if a.isnumeric():
                    a = int(a)
                else:
                    a = int.from_bytes(getValueByName_b(cStack,cVars,a))
                oWordsResults.append({"word":str(a-b)})
                index += 1 + s
            elif wordInfo["word"] == "*":
                a = oWordsResults.pop()["word"]
                
                
                if words[index+1]["word"] == "(":
                    (b,s) = computeSim(cVars,cStack,words[index+1:words[index+1]["end"]-1])
                    s -= 2
                else:
                    if words[index+1]["word"].isnumeric():
                
                        b = int(words[index+1]["word"])
                
                    else:
                        b = int.from_bytes(getValueByName_b(cStack,cVars,words[index+1]["word"]),"little")
                    s = 0
                if a.isnumeric():
                    a = int(a)
                else:
                    a = int.from_bytes(getValueByName_b(cStack,cVars,a))
                oWordsResults.append({"word":str(a*b)})
                index += 1 + s
            elif wordInfo["word"] == "/":
                a = oWordsResults.pop()["word"]
                if words[index+1]["word"] == "(":
                    (b,s) = computeSim(cVars,cStack,words[index+1:words[index+1]["end"]-1])
                    s -= 2
                else:
                    if words[index+1]["word"].isnumeric():
                        b = int(words[index+1]["word"])
                    else:
                        b = int.from_bytes(getValueByName_b(cStack,cVars,words[index+1]["word"]),"little")
                    s = 1
                if a.isnumeric():
                    a = int(a)
                else:
                    a = int.from_bytes(getValueByName_b(cStack,cVars,a))
                oWordsResults.append({"word":str(int(a/b))})
                index += 1 + s
            # ---------------------------------
            # |   for when we have a value    |
            # ---------------------------------
            else:
                if words[index]["word"].isnumeric():
                    oWordsResults.append({"word":words[index]["word"]})
                else:
                    # print("GETTING VARIABLE FROM STACK!")
                    # print("Stack: ",cStack)
                    # print("Variables: ",cVars)
                    # print("Name: ",words[index]["word"])
                    # print("Value: ",getValueByName_b(cStack,cVars,words[index]["word"]))
                    oWordsResults.append({"word":str(int.from_bytes(getValueByName_b(cStack,cVars,words[index]["word"]),"little"))})
                #oWordsResults.append({"word":str(computeSim(cVars,cStack,words[index]))})
            index += 1
        # assert len(oWordsResults)>1, "Error: Computation stack has a value more than 1!"
        # assert len(oWordsResults)<1, "Error: Computation stack has a length of 0!"
        
        return (int(oWordsResults[0]["word"]),index)
            
                
def getLEnd(words: list,index:int):
    for i in range(index,len(words)):
        word = words[i]
        if word["line"] > words[index]["line"]:
            return i
        
    assert False, "OOPS: Something went wrong, maybe the line never ended!"
def computeCompile_X86_64 (f,words: list,stackSize: int) -> str: 
    if len(words) == 1:
        if words[0]["word"].isnumeric():
            f.write(f"   mov rdx, {words[0]['word']}")
        else:
            var = None
            for v in varList:
                if v["name"] == words[0]["word"]:
                    var = v
            assert not var == None, f"Undefined var name: {words[0]['word']}"
            f.write(f"   xor rdx, rdx\n")
            if var['size'] == 4:
                f.write(f"   mov edx, dword [rsp+{stackSize-var['ptr']-var['size']}]\n")
            elif var['size'] == 1:
                f.write(f"   mov DL, BYTE [rsp+{stackSize-var['ptr']-var['size']}]\n")
            elif var['size'] == 8:
                f.write(f"   mov rdx, qword [rsp+{stackSize-var['ptr']-var['size']}]\n")
    else:
        f.write(f"   xor rdx, rdx\n")
        f.write(f"   xor rcx, rcx\n")
        f.write(f"   xor rax, rax\n")
        index = 0
        while index< len(words):
            word = words[index]
            if word["word"] == "*":
                if words[index+1]["word"] == "(":
                    f.write(f"   push rdx\n")
                    computeCompile_X86_64(f,words[index+1:words[index+1]["end"]-1])
                    f.write(f"   pop rcx\n")
                    f.write(f"   mov rax,rdx\n")
                    f.write(f"   mul rcx\n")
                    f.write(f"   mov rax, rcx\n")
                    index += words[index+1]["end"]
                    
                elif words[index+1]["word"].isnumeric():
                    f.write(f"   mov rax,{words[index+1]['word']}\n")
                    f.write(f"   mul rcx\n")
                    f.write(f"   mov rax, rcx\n")
                    index += 1
                else:
                    var = None
                    for v in varList:
                        if v["name"] == words[index+1]["word"]:
                            var = v
                    assert not var == None, f"Undefined var name: {words[index+1]['word']}"
                    f.write(f"   xor rax, rax\n")
                    if var['size'] == 4:
                        f.write(f"   mov eax, dword [rsp+{stackSize-var['ptr']-var['size']}]\n")
                    elif var['size'] == 1:
                        f.write(f"   mov AL, BYTE [rsp+{stackSize-var['ptr']-var['size']}]\n")
                    elif var['size'] == 8:
                        f.write(f"   mov rax, qword [rsp+{stackSize-var['ptr']-var['size']}]\n")
                    f.write(f"   mul rcx\n")
                    f.write(f"   mov rax, rcx\n")
                    index += 1
            elif word["word"].isnumeric():
                f.write(f"   mov rcx, {word['word']}")
            index += 1
                    
        f.write(f"   mov rcx, rdx")
                    
                
            
            
            
def compileCodeWindows_X86_64 (words: list,outFilePath:str):
    global varList
    fromStartPtr = 0
    with open(outFilePath,"w") as ofile:
        ofile.write("BITS 64\n")
        ofile.write("global _main\n")
        ofile.write("   extern _printf\n")
        ofile.write("   extern _putchar\n")
        ofile.write("section .text\n")
        ofile.write("_main: \n")
        
        if BEFORE_STACK_BUFFER_INITIALISATION:
            ofile.write(f"   ; -- BEFORE STACK BUFFER INITIALISATION -- \n")
            ofile.write(f"   sub rsp, 4\n")
        #argc, argv, ssp    
        #argc
        varList.append({"name":"argc","size":8,"ptr":-16})
        #ARGV, as a pointer
        # ofile.write(f"   sub rsp, 8\n")
        # ofile.write(f"   mov rdx, rsp\n")
        # ofile.write(f"   add rdx, 20\n")
        # ofile.write(f"   mov rdx, qword [rsp+8]\n")
        # varList.append({"name":"argv","size":8,"ptr":-16})
        
        index = 0
        stackSize = 0
        cNumCount = 0
        # fromStartPtr += 8
        # stackSize += 8
        while index < len(words):
            wordInfo = words[index]
            word = wordInfo["word"]
            if word == "int":
                ofile.write(f"   ; -- int {words[index+1]['word']} --\n")
                ofile.write(f"   sub rsp, 4\n")
                varList.append({"name":words[index+1]["word"],"size":4,"ptr":fromStartPtr})
                fromStartPtr += 4
                stackSize += 4
                index += 1
            elif word == "=":
                var = None
                for v in varList:
                    if v["name"] == words[index-1]["word"]:
                        var = v
                if var == None:
                    assert False, f"Unknown variable name: {words[index-1]['word']}"
                ofile.write(f"   ; -- {words[index-1]['word']} = --\n")
                if words[index+1]["word"].isnumeric():
                    # OLD CODE
                        # ofile.write(f"   mov rsp,rbp\n")
                        # ofile.write(f"   add rsp,{stackSize-var['ptr']-var['size']}\n")
                        # ofile.write(f"   pop rdx\n")
                        # ofile.write(f"   xor rdx, rdx\n")
                        # ofile.write(f"   push {words[index+1]['word']}\n")
                        # ofile.write(f"   mov rbp, rsp\n")
                    # NEW CODE
                    if var['size'] == 4:
                        ofile.write(f"   mov dword [rsp+{stackSize-var['ptr']-var['size']}], {words[index+1]['word']}\n")
                    elif var['size'] == 1:
                        ofile.write(f"   mov byte  [rsp+{stackSize-var['ptr']-var['size']}], {words[index+1]['word']}\n")
                    elif var['size'] == 8:
                        ofile.write(f"   mov qword [rsp+{stackSize-var['ptr']-var['size']}], {words[index+1]['word']}\n")
                    
                index += 2
            elif word == "print":
                
                if words[index+1]["word"].isnumeric():
                    ofile.write(f";   -- printing number\n")
                    ofile.write(f"   push {words[index+1]['word']}\n")
                    ofile.write(f"   push intformt\n")
                    ofile.write(f"   call _printf\n")
                    ofile.write(f"   pop rdx\n")
                    ofile.write(f"   pop rdx\n")
                else:
                    var = None
                    for v in varList:
                        if v["name"] == words[index+1]["word"]:
                            var = v
                    assert not var == None, f"Undefined var name: {words[index+1]['word']}"
                    # OLD CODE
                        # #DEBUG
                        # ofile.write(f"\n\n\n\n\n")
                        # ofile.write(f"   ; DEBUG START\n")
                        # ofile.write(f"   push 10\n")
                        # ofile.write(f"   push chrformt\n")
                        # ofile.write(f"   call _printf\n")
                        # ofile.write(f"   pop rbx\n")
                        # ofile.write(f"   pop rbx\n")
                        
                        
                        # ofile.write(f"   push rsp\n")
                        # ofile.write(f"   push intformt\n")
                        # ofile.write(f"   call _printf\n")
                        # ofile.write(f"   pop rbx\n")
                        # ofile.write(f"   pop rbx\n")
                        
                        # ofile.write(f"   push 10\n")
                        # ofile.write(f"   push chrformt\n")
                        # ofile.write(f"   call _printf\n")
                        # ofile.write(f"   pop rbx\n")
                        # ofile.write(f"   pop rbx\n")
                        # ofile.write(f"   ; DEBUG END\n")
                        
                        
                        # ofile.write(f"   ;-- Must print {var['name']}! --\n")
                        # ofile.write(f"   mov rsp, rbp\n")
                        # ofile.write(f"   add rsp, {stackSize-var['ptr']-var['size']}\n")
                        # ofile.write(f"   pop rbx\n")
                        # ofile.write(f"   push rbx\n")
                        
                        # ofile.write(f"   mov rbp, rsp\n")
                        # ofile.write(f"   push rbx\n")
                        # ofile.write(f"   push intformt\n")
                        # ofile.write(f"   call _printf\n")
                        # ofile.write(f"   pop rbx\n")
                        # ofile.write(f"   pop rbx\n")
                        
                        
                        
                        
                        
                        
                        # # DEBUG
                        # ofile.write(f"   ; DEBUG START\n")
                        # ofile.write(f"   push 10\n")
                        # ofile.write(f"   push chrformt\n")
                        # ofile.write(f"   call _printf\n")
                        # ofile.write(f"   pop rbx\n")
                        # ofile.write(f"   pop rbx\n")
                        
                        
                        # ofile.write(f"   push rsp\n")
                        # ofile.write(f"   push intformt\n")
                        # ofile.write(f"   call _printf\n")
                        # ofile.write(f"   pop rbx\n")
                        # ofile.write(f"   pop rbx\n")
                        
                        # ofile.write(f"   push 10\n")
                        # ofile.write(f"   push chrformt\n")
                        # ofile.write(f"   call _printf\n")
                        # ofile.write(f"   pop rbx\n")
                        # ofile.write(f"   pop rbx\n")
                        # ofile.write(f"   ; DEBUG END\n")
                        # ofile.write(f"   mov rbp,rsp\n")
                        
                        # ofile.write(f"   xor rbx, rbx\n")
                        # ofile.write(f"\n\n\n\n\n")
                    # NEW CODE
                    ofile.write(f"   xor rbx, rbx\n")
                    if var['size'] == 4:
                        ofile.write(f"   mov ebx, dword [rsp+{stackSize-var['ptr']-var['size']}]\n")
                    elif var['size'] == 1:
                        ofile.write(f"   mov BL, BYTE [rsp+{stackSize-var['ptr']-var['size']}]\n")
                    elif var['size'] == 8:
                        ofile.write(f"   mov rbx, qword [rsp+{stackSize-var['ptr']-var['size']}]\n")
                    ofile.write(f"   push rbx\n")
                    ofile.write(f"   push intformt\n")
                    ofile.write(f"   call _printf\n")
                    ofile.write(f"   pop rdx\n")
                    ofile.write(f"   pop rdx\n")
                index += 2
            elif word == "char":
                ofile.write(f"   ; -- char {words[index+1]['word']} --\n")
                ofile.write(f"   sub rsp, 1\n")
                varList.append({"name":words[index+1]["word"],"size":1,"ptr":fromStartPtr})
                fromStartPtr += 1
                stackSize += 1
                index += 1
            elif word == "void":
                if words[index+1]['word'] == "*":
                    ofile.write(f"   ; -- void * {words[index+2]['word']} --\n")
                    ofile.write(f"   sub rsp, 8\n")
                    varList.append({"name":words[index+2]["word"],"size":8,"ptr":fromStartPtr})
                    fromStartPtr += 8
                    stackSize += 8
                    index += 2
                else:
                    assert False, "Unreachable"
                
            elif word == "printc":
                if words[index+1]["word"].isnumeric():
                    ofile.write(f";   -- printing char\n")
                    ofile.write(f"   push {words[index+1]['word']}\n")
                    #ofile.write(f"   push chrformt\n")
                    ofile.write(f"   call _putchar\n")
                    ofile.write(f"   pop rdx\n")
                    #ofile.write(f"   pop rdx\n")
                    #ofile.write(f"   pop rdx\n")
                    #ofile.write(f"   pop rdx\n")
                else:
                    var = None
                    for v in varList:
                        if v["name"] == words[index+1]["word"]:
                            var = v
                    assert not var == None, f"Undefined var name: {words[index+1]['word']}"
                    ofile.write(f"   xor rbx, rbx\n")
                    ofile.write(f"   mov BL, BYTE [rsp+{stackSize-var['ptr']-var['size']}]\n")
                    ofile.write(f"   push rbx\n")
                    ofile.write(f"   push chrformt\n")
                    ofile.write(f"   call _printf\n")
                    ofile.write(f"   pop rdx\n")
                    ofile.write(f"   pop rdx\n")
                index += 2
            elif word == "printstr":
                var = None
                for v in varList:
                    if v["name"] == words[index+1]["word"]:
                        var = v
                assert not var == None, f"Undefined var name: {words[index+1]['word']}"
                ofile.write(f"   xor rbx, rbx\n")
                ofile.write(f"   mov rbx, qword [rsp+{stackSize-var['ptr']-var['size']}]\n")
                ofile.write(f"   push rbx\n")
                ofile.write(f"   push strformt\n")
                ofile.write(f"   call _printf\n")
                ofile.write(f"   pop rdx\n")
                ofile.write(f"   pop rdx\n")
                index += 1
            else:
                print(f"idk what this word is {wordInfo}")
            
            index += 1
        ofile.write(f"\n\n\n\n")
        if AFTER_STACK_CLEANUP:
            ofile.write(f"   ; -- Cleanup --\n")
            l = stackSize % 4
            for i in range(int(stackSize/4)):
                ofile.write(f"   pop rdx\n")
            if l:
                ofile.write(f"   sub rsp, {l}\n")
            
        ofile.write("; -- Return -- \n")
        ofile.write("   ret\n")
        ofile.write("section .data\n")
        ofile.write("   intformt: db \"%d\",0\n")
        ofile.write("   chrformt: db \"%c\",0\n")
            
def simulate_Code(words: list):
    #out = []
    global istack
    #print(words)
    # cScope = istack
    # cVars = varList
    scopeVars = vptr(0,0)
    cVarPTL = [scopeVars]
    
    index = 0
    while index < len(words):
        wordInfo = words[index]
        word = wordInfo["word"]
        #indexWord = wordInfo["index"]
        #line = wordInfo["line"]
        #token = None
        #index = index - 1
        #print(f"Word: {word}")
        if word == "int":
            #type of token, size
            iptr = alloc(istack,4)
            #print("BEFORE: ",cVarPTL[-1].size)
            cVarPTL[-1].size += 4
            #print("AFTER: ",cVarPTL[-1].size)
            #cVarNAMES.append(words[index+1]["word"])
            #scopeVars.size += 4
            #cVars.append(iptr)
            #print("LEN: ",len(cVarPTL))
            pushVar(varList,words[index+1]["word"],iptr)
            
        elif word == "char":
            iptr = alloc(istack,1)
            cVarPTL[-1].size += 1
            pushVar(varList,words[index+1]["word"],iptr)
            #print(iptr.size)
            #print(iptr.start)
            #print(words[index+1])
        elif word == "bool":
            iptr = alloc(istack,1)
            cVarPTL[-1].size += 1
            #cVars.append(iptr)
            pushVar(varList,words[index+1]["word"],iptr)
        elif word == "+=":
            vname = words[index-1]["word"]
            #print("vname: ",vname)
            varptr = getVarByName(varList,vname)["ptr"]
            (val,s) = computeSim(varList,istack,words[index+1:getLEnd(words,index+1)])
            varval = int.from_bytes(istack[varptr.start:varptr.start+varptr.size],"little")
            mem = bytearray()
            #print("varval: ",varval)
            #print("val: ",val)
            #print("out: ",varval+val)
            mem.extend((varval+val).to_bytes(varptr.size,"little"))
            #print(mem)
            #print(istack)
            #print(var["ptr"].start)
            #print(var["ptr"].size)
            istack = istack[:varptr.start] + mem + istack[varptr.start+varptr.size:]
            #print(istack)
            index += 1
        elif word == "-=":
            vname = words[index-1]["word"]
            varptr = getVarByName(varList,vname)["ptr"]
            (val,s) = computeSim(varList,istack,words[index+1:getLEnd(words,index+1)])
            varval = int.from_bytes(istack[varptr.start:varptr.start+varptr.size],"little")
            
            
            mem = bytearray()
            mem.extend((varval-val).to_bytes(varptr.size,"little"))
            istack = istack[:varptr.start] + mem + istack[varptr.start+varptr.size:]
            index += 1
        elif word == "*=":
            vname = words[index-1]["word"]
            varptr = getVarByName(varList,vname)["ptr"]
            (val,s) = computeSim(varList,istack,words[index+1:getLEnd(words,index+1)])
            varval = int.from_bytes(istack[varptr.start:varptr.start+varptr.size],"little")
            
            mem = bytearray()
            mem.extend((varval*val).to_bytes(varptr.size,"little"))
            istack = istack[:varptr.start] + mem + istack[varptr.start+varptr.size:]
            index += 1
        
        elif word == "/=":
            vname = words[index-1]["word"]
            varptr = getVarByName(varList,vname)["ptr"]
            (val,s) = computeSim(varList,istack,words[index+1:getLEnd(words,index+1)])
            varval = int.from_bytes(istack[varptr.start:varptr.start+varptr.size],"little")
            
            mem = bytearray()
            mem.extend(int(varval/val).to_bytes(varptr.size,"little"))
            istack = istack[:varptr.start] + mem + istack[varptr.start+varptr.size:]
            index += 1
            
        elif word == "=":            
            var = getVarByName(varList,words[index-1]["word"])
            mem = bytearray()
            #print("\nblahblah")
            #print(words[index+1:getLEnd(words,index+1)])
            #print("\n")
            (o,s) = computeSim(varList,istack,words[index+1:getLEnd(words,index+1)])
            #print(o)
            #print("\n")
            mem.extend(o.to_bytes(var["ptr"].size,"little"))
            istack = istack[:var["ptr"].start] + mem + istack[var["ptr"].start+var["ptr"].size:]
            #print("I STACK IN =: ",istack)
            #print("Value: ",mem)
            #print()
            index += 1
        
        elif word == "print":
            if index+1 < len(words):
                if words[index+1]["word"].isnumeric():
                    print(words[index+1]["word"],end="")
                
                else:
                    # print("------ VAR LIST --------")
                    # for v in cVars:
                    #     print(v["name"]+" "+str(int.from_bytes(getValueByName_b(cScope,cVars,v["name"]),"little")))
                    # print("----------------------")
                    # print("------- OUR VARIABLE -----")
                    print(int.from_bytes(getValueByName_b(istack,varList,words[index+1]["word"]),"little"),end="")
                    #print("------------------------")
                    #print("VarName: "+words[index+1]["word"]+" VarList: "+str(cVars)+" "+str(int.from_bytes(getValueByName_b(cScope,cVars,words[index+1]["word"]),"little")),end="")
            else:
                print()
                #print(words[index+1])
            
            
        
            #cScope = cScope[:var["ptr"].start]+
        
        elif word == "printc":
            if words[index+1]["word"].isnumeric():
                print(chr(int(words[index+1]["word"])),end="")
                
            else:
                print(chr(int.from_bytes(getValueByName_b(istack,varList,words[index+1]["word"]),"little")),end="")
        elif word == "if":
            #print("BRUH")
            assert words[index+1]["end"] > 0, "Error: If condition opened but never closed!"
            
            (r,s)=computeSim(varList,istack,words[index+2:words[index+1]["end"]])
            if r:
                #print(r)
                #print("xddxdd")
                #print(words[index+s])
                index += s
            else:
                # print(words[index])
                # print(words[index+1])
                # print(words[index+2])
                # print(words[index+3])
                # # print(words)
                # print()
                # print(words[index+words[index+1]["end"]+1])
                # print(words[words[index+words[index+1]["end"]-4]["end"]])
                # print()
                # print(words[words[index+words[index+1]["end"]-4]["end"]])
                # print()
                # print()
                # print(words[words[index+1]["end"]+1]["end"])
                # print()
                index = words[words[index+1]["end"]+1]["end"]
        elif word == "while":
            #(v,s) = computeSim(cVars,cScope,words[index+2:words[index+1]["end"]])
            #whileSelected = True
            words[words[words[index+1]["end"]+1]["end"]]["isInLoop"] = True
            (v,s) = computeSim(varList,istack,words[index+2:words[index+1]["end"]])
            # print("IN WHILE LOOP DEFINITION")
            # print("V: ",v)
            # print("S: ",s)
            if v:
                index += s
            else:
                index = words[words[index+1]["end"]+1]["end"]
        elif word == "{":
            #print("hi")
            # print("GOT TO {\n")
            
            assert wordInfo["end"] > 0, "Error: Scope Opened but never closed"
            scopeVars = vptr(len(istack),0)
            cVarPTL.append(scopeVars)
            
            #varStack.append(cVars)
            #scopeStack.append(cScope)
        elif word == "}":
            #print(cVarPTL)
            scopePTR = cVarPTL.pop()
            #print(scopePTR)
            tempCount = 0
            while tempCount < len(varList):
                v = varList[tempCount]
                if v["ptr"].start >= scopePTR.start and v["ptr"].start <= scopePTR.start + scopePTR.size:
                    # print()
                    # print("VarList: ",varList)
                    # print("V:",v)
                    del varList[tempCount]
                    tempCount -= 1
                    # print("VarList: ",varList)
                    # print()
                tempCount += 1
            istack = free(istack,scopePTR)
            # for v in cVars:
            #     free(cScope,v["ptr"])
            # cVars = varStack.pop()
            # cScope = scopeStack.pop()
            if "isInLoop" in wordInfo:
                
                openBracketConditionStart = words[wordInfo["start"]-1]["start"]
                #print(words[openBracketConditionStart+1:words[openBracketConditionStart]["end"]])
                # print(f"Condition for while loop thingy magigy: {words[openBracketConditionStart+1:words[openBracketConditionStart]['end']]}")
                (v,s) = computeSim(varList,istack,words[openBracketConditionStart+1:words[openBracketConditionStart]["end"]])
                # print("IN WHILE LOOP REPEAT")
                # print("V: ",v)
                # print("S: ",s)
                #print(v)
                if v:
                    #print("hi")
                    index = words[openBracketConditionStart]["end"]-1
                else:                
                    del wordInfo["isInLoop"]
                    
                
            #scopeStack.append(cScope)
            
        # elif word == "(":
        #     calcLine(line,index)
            
            # if word == "+" or word =="-" or word == "*" or word == "/":
            #     a = words[index-1]
            #     b = words[index+1]
            #     if a.isnumeric():
            #         a = int(a)
            #     else:
            #         a = getVarByName(a)
            #         a = int.from_bytes(getValueInStack(a["ptr"]),"little")
                    
            #     if b.isnumeric():
            #         b = int(b)
            #     else:
            #         b = getVarByName(b)
            #         b = int.from_bytes(getValueInStack(b["ptr"]),"little")
            #     value = calcOp(a,b,word)
            
            
                
        else:
            pass
            # if word.isnumeric():
            #     constptr = alloc(4)
        index += 1
def lex_getKey(f):
    c = ""
    word = ""
    while c != " ":
        c = f.read(1).decode("utf-8")
        word += c
    f.seek(-1,1)
    return word[:len(word)-1]

def lex_isKey(f,key):    
    c = ""
    count = 0
    word = ""
    out: bool = True
    for char in key:
        c = f.read(1).decode("utf-8")
        if char != c:
            f.seek(-count-1,1)
            out = False
            break
        word += c
        count += 1
    #print("----------")
    return out

def lex(path: str):
    macros = []
    with open(path,"rb") as ifile:
        ifile.seek(0,0)
        ifile.seek(0,2)
        EOF = ifile.tell()
        ifile.seek(0,0)
        path = path.replace("/","\\")
        if path.find("\\") != -1:
            file = path[path.rfind("\\")+1:]
            opath = path[:path.rfind("\\")]
            out = opath + "/l" + file
        else:
            file = path
            out = "l"+path
        print(f"\nOutputing to: {out}")
        with open(out,"w") as t:
            t.close()
        with open(out,"wb+") as ofile:
            lexStream(ifile,ofile,macros,opath)  
        return (out,macros)
def lexStream(ifile,ofile,macros=[],opath=""):
    
    ifile.seek(0,0)
    #print(f"I file: {ifile.read()}")
    #ifile.seek(0,0)
    ifile.seek(0,2)
    EOF = ifile.tell()
    print("\nEOF: ",EOF)
    #exit(1)
    ifile.seek(0,0)
    c = ""
    while ifile.tell() < EOF:
        c = ifile.read(1).decode("utf-8")
        #print("\rCurrent Position: "+str(ifile.tell()),end="")
        if c == "#":
            if lex_isKey(ifile,"include") and ifile.read(2).decode("utf-8") == " \"":
                p = ""
                ch = ""
                while ch != "\"":
                    ch = ifile.read(1).decode("utf-8")
                    p += ch
                p = p[:len(p)-1]
                (fi,m) = lex(opath+"\\"+p)
                macros.extend(m)
                with open(fi,"r") as f:
                    ofile.write(f.read().encode())
                os.remove(fi)
            elif lex_isKey(ifile,"define"):
                ifile.seek(1,1)
                macroName = lex_getKey(ifile)
                print(f"macroName: \"{macroName}\"")
                
                macroValue = ""
                ifile.seek(1,1)
                while not lex_isKey(ifile,"#end"):
                    macroValue += ifile.read(1).decode("utf-8")
                macros.append({"name":macroName,"value":macroValue})
        elif c == "'":
            ch = ifile.read(1)
            if ch.decode("utf-8") != "'":
                chrVal = int.from_bytes(ch,"little")
                if chrVal == ord("\\"):
                    ofile.write(str(ord((ch.decode("utf-8") + ifile.read(1).decode("utf-8")).encode("utf-8").decode("unicode_escape"))).encode("utf-8"))    
                else:
                    ofile.write(str(chrVal).encode("utf-8"))
                ifile.seek(1,1)
            else:
                ofile.write("0".encode("utf-8"))
                
        elif c == "{":
            o = " "+c+" "
            ofile.write(o.encode("utf-8"))
            
        elif c == "}":
            o = " "+c+" "
            ofile.write(o.encode("utf-8"))
            
        elif c == "(": 
            ofile.write((" "+c+" ").encode("utf-8"))
            
        elif c == ")":
            ofile.write((" "+c+" ").encode("utf-8"))
        
            
        elif c == "+":
            if ifile.read(1).decode("utf-8") == "=":
                ofile.write((" "+c+"=").encode("utf-8"))
            else:
                ifile.seek(-1,1)
                ofile.write((" "+c+" ").encode("utf-8"))
        elif c == "-": 
            if ifile.read(1).decode("utf-8") == "=":
                ofile.write((" "+c+"=").encode("utf-8"))
            else:
                ifile.seek(-1,1)
                ofile.write((" "+c+" ").encode("utf-8"))
        elif c == "*": 
            if ifile.read(1).decode("utf-8") == "=":
                ofile.write((" "+c+"=").encode("utf-8"))
            else:
                ifile.seek(-1,1)
                ofile.write((" "+c+" ").encode("utf-8"))
        elif c == "=":
            if ifile.read(1).decode("utf-8") == "=":
                ofile.write((" "+c+"=").encode("utf-8"))
            else:
                ifile.seek(-1,1)
                ofile.write((" "+c+" ").encode("utf-8"))
        
        elif c == "t" and lex_isKey(ifile,"rue"):
            ofile.write("1".encode("utf-8"))
        elif c == "f" and lex_isKey(ifile,"alse"):
            ofile.write("0".encode("utf-8"))
        elif c == "/":
            ch = ifile.read(1).decode("utf-8")
            if ch == "/":
                while c != "\n":
                    c = ifile.read(1).decode("utf-8")
                
            else:
                ifile.seek(-1,1)
                ofile.write((" "+c+" ").encode("utf-8"))
        elif c == "\n" or c == "\r":
            ofile.write(b" ")
        else:
            hasFoundMacro = False
            for macro in macros:
                # print("----------------")
                # print(c)
                # print(macro["name"].encode("utf-8"))
                # print(macro["value"].encode("utf-8"))
                # #print("Is key: ",lex_isKey(ifile,macro["name"]))
                # print("----------------")
                if c == macro["name"][0] and lex_isKey(ifile,macro["name"][1:]):
                    hasFoundMacro = True
                    lexStream(io.BytesIO(macro["value"].encode("utf-8")),ofile,macros,opath)
                    break
            
            if not hasFoundMacro:
                ofile.write(c.encode("utf-8"))
    print()
def main():
    global istack
    global varList
    args = sys.argv
    args = args[1:]
    assert len(args) > 1, "Error: Invalid compilation"
    path = args[1]

    if args[0] == "sim":
        (p,m) = lex(path)
        
        with open(p,"rb") as f:
            f.seek(0,2)
            EOF = f.tell()
            f.seek(0,0)
            simulate_Code(grabWords(f))
        os.remove(p)
    if args[0] == "com":
        (p,m) = lex(path)
        with open(p,"rb") as f:
            compileCodeWindows_X86_64(grabWords(f),"out.asm")
        if len(args) > 2:
            if args[2] == "-t":
                with open("compileCommands.txt") as f:
                    cmds = f.readlines()
                    for cmd in cmds:
                        if cmd[0] != "/":
                            if cmd[-1] == "\n":
                                cmd = cmd[:len(cmd)-1]
                            
                            print(f"[CMD]: cmd /c \"{cmd}\"")
                            os.system(f"cmd /c \"{cmd}\"")    
        #os.remove(p)
    return 0
if __name__ == "__main__":
    exit(main())