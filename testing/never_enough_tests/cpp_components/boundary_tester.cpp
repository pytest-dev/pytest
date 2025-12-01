/**
 * Boundary Tester: C++ Component for Cross-Language Testing
 *
 * Purpose:
 * This C++ program validates boundary conditions that are difficult or
 * impossible to test purely in Python. It exposes edge cases in:
 * - Integer overflow/underflow
 * - Null pointer handling
 * - Memory allocation limits
 * - Buffer boundary conditions
 * - Numeric precision limits
 *
 * Integration:
 * Called from pytest via subprocess to validate cross-language behavior
 * and ensure pytest can handle external process failures gracefully.
 *
 * Usage:
 *   g++ -std=c++17 -O2 boundary_tester.cpp -o boundary_tester
 *   ./boundary_tester <test_mode> [args...]
 *
 * Test Modes:
 *   int_overflow       - Test integer overflow detection
 *   null_pointer       - Test null pointer handling
 *   memory_stress      - Stress test memory allocation
 *   buffer_test <size> - Test buffer boundary conditions
 *   float_precision    - Test floating point precision limits
 *   recursion_depth    - Test stack overflow conditions
 *   exception_handling - Test C++ exception propagation
 */

#include <iostream>
#include <string>
#include <vector>
#include <limits>
#include <cstring>
#include <cstdlib>
#include <memory>
#include <stdexcept>
#include <chrono>
#include <cmath>

// ============================================================================
// INTEGER OVERFLOW TESTING
// ============================================================================

int test_integer_overflow() {
    std::cout << "Testing integer overflow boundaries..." << std::endl;

    // Test signed integer overflow
    int max_int = std::numeric_limits<int>::max();
    int min_int = std::numeric_limits<int>::min();

    std::cout << "Max int: " << max_int << std::endl;
    std::cout << "Min int: " << min_int << std::endl;

    // Detect overflow (undefined behavior, but we can check)
    long long overflow_test = static_cast<long long>(max_int) + 1;
    std::cout << "Max int + 1 (as long long): " << overflow_test << std::endl;

    // Test unsigned overflow (well-defined wrapping)
    unsigned int max_uint = std::numeric_limits<unsigned int>::max();
    unsigned int wrapped = max_uint + 1;  // Wraps to 0

    if (wrapped == 0) {
        std::cout << "PASS: Unsigned overflow wrapped correctly" << std::endl;
        return 0;
    } else {
        std::cerr << "FAIL: Unexpected unsigned overflow behavior" << std::endl;
        return 1;
    }
}

// ============================================================================
// NULL POINTER HANDLING
// ============================================================================

int test_null_pointer() {
    std::cout << "Testing null pointer handling..." << std::endl;

    // Test 1: nullptr with smart pointers
    std::unique_ptr<int> ptr = nullptr;
    if (!ptr) {
        std::cout << "PASS: nullptr detection with smart pointer" << std::endl;
    }

    // Test 2: Explicit null check
    int* raw_ptr = nullptr;
    if (raw_ptr == nullptr) {
        std::cout << "PASS: nullptr comparison" << std::endl;
    }

    // Test 3: Safe dereferencing pattern
    try {
        if (raw_ptr != nullptr) {
            int value = *raw_ptr;  // Would segfault if executed
            std::cout << "Value: " << value << std::endl;
        } else {
            std::cout << "PASS: Avoided null dereference" << std::endl;
        }
    } catch (...) {
        std::cerr << "FAIL: Exception during null pointer test" << std::endl;
        return 1;
    }

    return 0;
}

// ============================================================================
// MEMORY STRESS TESTING
// ============================================================================

int test_memory_stress() {
    std::cout << "Testing memory stress conditions..." << std::endl;

    const size_t ALLOCATION_SIZE = 100 * 1024 * 1024;  // 100 MB
    const int ALLOCATION_COUNT = 10;

    std::vector<std::unique_ptr<char[]>> allocations;

    try {
        for (int i = 0; i < ALLOCATION_COUNT; ++i) {
            auto buffer = std::make_unique<char[]>(ALLOCATION_SIZE);

            // Write to buffer to ensure it's actually allocated
            std::memset(buffer.get(), 0xAA, ALLOCATION_SIZE);

            allocations.push_back(std::move(buffer));

            std::cout << "Allocated block " << (i + 1) << " ("
                      << (ALLOCATION_SIZE / 1024 / 1024) << " MB)" << std::endl;
        }

        std::cout << "PASS: Successfully allocated "
                  << (ALLOCATION_SIZE * ALLOCATION_COUNT / 1024 / 1024)
                  << " MB total" << std::endl;

        return 0;

    } catch (const std::bad_alloc& e) {
        std::cerr << "Memory allocation failed (expected on low-memory systems): "
                  << e.what() << std::endl;
        return 1;  // Not necessarily a failure, just OOM

    } catch (...) {
        std::cerr << "FAIL: Unexpected exception during memory stress test" << std::endl;
        return 2;
    }
}

// ============================================================================
// BUFFER BOUNDARY TESTING
// ============================================================================

int test_buffer_boundaries(size_t buffer_size) {
    std::cout << "Testing buffer boundaries with size: " << buffer_size << std::endl;

    // Edge case: zero-size buffer
    if (buffer_size == 0) {
        std::cout << "PASS: Zero-size buffer handled" << std::endl;
        return 0;
    }

    try {
        // Allocate buffer
        std::vector<char> buffer(buffer_size);

        // Test: Write to first byte
        buffer[0] = 'A';

        // Test: Write to last byte (only if different from first)
        if (buffer_size > 1) {
            buffer[buffer_size - 1] = 'Z';
        }

        // Test: Read back
        bool first_ok = (buffer[0] == 'A');
        bool last_ok = (buffer_size == 1) ? true : (buffer[buffer_size - 1] == 'Z');

        if (first_ok && last_ok) {
            std::cout << "PASS: Buffer boundary access successful" << std::endl;

            // Test: Fill entire buffer
            std::fill(buffer.begin(), buffer.end(), 0xFF);

            std::cout << "PASS: Buffer fill successful (" << buffer_size << " bytes)" << std::endl;
            return 0;
        } else {
            std::cerr << "FAIL: Buffer boundary read/write mismatch" << std::endl;
            return 1;
        }

    } catch (const std::exception& e) {
        std::cerr << "FAIL: Exception during buffer test: " << e.what() << std::endl;
        return 1;
    }
}

// ============================================================================
// FLOATING POINT PRECISION TESTING
// ============================================================================

int test_float_precision() {
    std::cout << "Testing floating point precision boundaries..." << std::endl;

    // Test special values
    double inf = std::numeric_limits<double>::infinity();
    double neg_inf = -std::numeric_limits<double>::infinity();
    double nan = std::numeric_limits<double>::quiet_NaN();

    std::cout << "Infinity: " << inf << std::endl;
    std::cout << "Negative infinity: " << neg_inf << std::endl;
    std::cout << "NaN: " << nan << std::endl;

    // Test NaN comparisons
    if (std::isnan(nan) && !std::isnan(inf) && std::isinf(inf)) {
        std::cout << "PASS: Special float values handled correctly" << std::endl;
    } else {
        std::cerr << "FAIL: Special float value detection failed" << std::endl;
        return 1;
    }

    // Test precision limits
    double epsilon = std::numeric_limits<double>::epsilon();
    double one_plus_epsilon = 1.0 + epsilon;

    if (one_plus_epsilon > 1.0) {
        std::cout << "PASS: Epsilon precision detected (epsilon = " << epsilon << ")" << std::endl;
    } else {
        std::cerr << "FAIL: Epsilon precision test failed" << std::endl;
        return 1;
    }

    // Test denormalized numbers
    double min_normal = std::numeric_limits<double>::min();
    double denorm = min_normal / 2.0;

    std::cout << "Min normal: " << min_normal << std::endl;
    std::cout << "Denormalized: " << denorm << std::endl;

    return 0;
}

// ============================================================================
// RECURSION DEPTH TESTING
// ============================================================================

int recursion_counter = 0;

void recursive_function(int depth, int max_depth) {
    recursion_counter++;

    if (depth >= max_depth) {
        return;
    }

    // Allocate some stack space to stress the stack
    char stack_buffer[1024];
    std::memset(stack_buffer, 0, sizeof(stack_buffer));

    recursive_function(depth + 1, max_depth);
}

int test_recursion_depth() {
    std::cout << "Testing recursion depth limits..." << std::endl;

    const int MAX_SAFE_DEPTH = 10000;

    try {
        recursion_counter = 0;
        recursive_function(0, MAX_SAFE_DEPTH);

        std::cout << "PASS: Achieved recursion depth: " << recursion_counter << std::endl;
        return 0;

    } catch (const std::exception& e) {
        std::cerr << "Exception at depth " << recursion_counter << ": " << e.what() << std::endl;
        return 1;
    } catch (...) {
        std::cerr << "Stack overflow or unknown error at depth " << recursion_counter << std::endl;
        return 1;
    }
}

// ============================================================================
// EXCEPTION HANDLING TESTING
// ============================================================================

void throw_nested_exceptions(int depth) {
    if (depth <= 0) {
        throw std::runtime_error("Base exception");
    }

    try {
        throw_nested_exceptions(depth - 1);
    } catch (...) {
        std::throw_with_nested(std::runtime_error("Nested exception at depth " + std::to_string(depth)));
    }
}

int test_exception_handling() {
    std::cout << "Testing exception handling and propagation..." << std::endl;

    // Test 1: Basic exception
    try {
        throw std::runtime_error("Test exception");
    } catch (const std::runtime_error& e) {
        std::cout << "PASS: Basic exception caught: " << e.what() << std::endl;
    }

    // Test 2: Nested exceptions
    try {
        throw_nested_exceptions(5);
    } catch (const std::exception& e) {
        std::cout << "PASS: Nested exception caught: " << e.what() << std::endl;
    }

    // Test 3: Multiple exception types
    try {
        int test_case = rand() % 3;
        switch (test_case) {
            case 0: throw std::runtime_error("Runtime error");
            case 1: throw std::logic_error("Logic error");
            case 2: throw std::out_of_range("Out of range");
        }
    } catch (const std::exception& e) {
        std::cout << "PASS: Multiple exception types handled: " << e.what() << std::endl;
    }

    return 0;
}

// ============================================================================
// MAIN ENTRY POINT
// ============================================================================

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <test_mode> [args...]" << std::endl;
        std::cerr << "Test modes:" << std::endl;
        std::cerr << "  int_overflow       - Integer overflow testing" << std::endl;
        std::cerr << "  null_pointer       - Null pointer handling" << std::endl;
        std::cerr << "  memory_stress      - Memory allocation stress test" << std::endl;
        std::cerr << "  buffer_test <size> - Buffer boundary testing" << std::endl;
        std::cerr << "  float_precision    - Floating point precision" << std::endl;
        std::cerr << "  recursion_depth    - Recursion depth limits" << std::endl;
        std::cerr << "  exception_handling - Exception handling" << std::endl;
        return 1;
    }

    std::string test_mode = argv[1];

    auto start_time = std::chrono::high_resolution_clock::now();
    int result = 0;

    try {
        if (test_mode == "int_overflow") {
            result = test_integer_overflow();
        } else if (test_mode == "null_pointer") {
            result = test_null_pointer();
        } else if (test_mode == "memory_stress") {
            result = test_memory_stress();
        } else if (test_mode == "buffer_test") {
            size_t buffer_size = (argc >= 3) ? std::stoull(argv[2]) : 1024;
            result = test_buffer_boundaries(buffer_size);
        } else if (test_mode == "float_precision") {
            result = test_float_precision();
        } else if (test_mode == "recursion_depth") {
            result = test_recursion_depth();
        } else if (test_mode == "exception_handling") {
            result = test_exception_handling();
        } else {
            std::cerr << "Unknown test mode: " << test_mode << std::endl;
            return 1;
        }
    } catch (const std::exception& e) {
        std::cerr << "FATAL: Unhandled exception: " << e.what() << std::endl;
        return 2;
    } catch (...) {
        std::cerr << "FATAL: Unhandled unknown exception" << std::endl;
        return 2;
    }

    auto end_time = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end_time - start_time);

    std::cout << "\nExecution time: " << duration.count() << " ms" << std::endl;
    std::cout << "Result: " << (result == 0 ? "SUCCESS" : "FAILURE") << std::endl;

    return result;
}
