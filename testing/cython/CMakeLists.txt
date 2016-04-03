
cmake_minimum_required(VERSION 2.8)

project (cython_clib)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/clib)

add_library(sqrc SHARED clib/sqrc.c)
add_library(sqrcpp SHARED clib/sqrcpp.cpp)
