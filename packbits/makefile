
CPP  = g++.exe
CC   = gcc.exe
WINDRES = windres.exe
RES  = 
OBJ  = packbits.o  $(RES)
LINKOBJ  = packbits.o  $(RES)
LIBS = -mwindows -lwinmm -L"C:/MinGW32/lib"
INCS = -I"C:/MinGW32/include"
CXXINCS = -I"C:/MinGW32/include"
OUTPUT_NAME = packbits
BIN  = packbits.dll
CXXFLAGS =  -Wall $(CXXINCS)  
CFLAGS = -O2 $(INCS)  
RM = rm -f

.PHONY: all all-before all-after clean clean-custom

all: all-before $(BIN) all-after


clean: clean-custom
	${RM} $(OBJ) $(BIN)


DLLWRAP = dllwrap.exe
DEFFILE = $(OUTPUT_NAME).def
STATICLIB = $(OUTPUT_NAME).a

$(BIN): $(LINKOBJ)
	$(DLLWRAP) --output-def $(DEFFILE) --driver-name c++ --implib $(STATICLIB) $(LINKOBJ) $(LIBS) -o $(BIN)
	$(RM) $(OBJ)
	$(RM) $(STATICLIB)
	$(RM) $(DEFFILE)
	
packbits.o: packbits.c
	$(CC) -c packbits.c -o packbits.o $(CFLAGS)

