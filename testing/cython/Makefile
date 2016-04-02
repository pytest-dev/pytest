
clib: clib/sqrc.c clib/sqrcpp.cpp
	gcc -c -fPIC -I. clib/sqrc.c -o clib/sqrc.o
	gcc -c -fPIC -I. clib/sqrcpp.cpp -o clib/sqrcpp.o
	gcc -shared -I. -o clib/libsqrc.so clib/sqrc.o
	gcc -shared -I. -o clib/libsqrcpp.so clib/sqrcpp.o
