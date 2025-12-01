/**
 * Fuzzer: Advanced Input Fuzzing Component
 *
 * Purpose:
 * Generate randomized, malformed, and edge-case inputs to stress-test
 * systems under chaotic conditions. This component produces:
 * - Random byte sequences
 * - Malformed UTF-8 strings
 * - Extreme numeric values
 * - Pathological data structures
 *
 * Integration:
 * Can be called from pytest to generate fuzzing payloads for testing
 * parser robustness, input validation, and error handling.
 *
 * Usage:
 *   g++ -std=c++17 -O2 fuzzer.cpp -o fuzzer
 *   ./fuzzer <mode> <count> [seed]
 *
 * Modes:
 *   random_bytes    - Generate random byte sequences
 *   malformed_utf8  - Generate malformed UTF-8 strings
 *   extreme_numbers - Generate extreme numeric values
 *   json_fuzzing    - Generate malformed JSON structures
 */

#include <iostream>
#include <string>
#include <vector>
#include <random>
#include <sstream>
#include <iomanip>
#include <cstring>

class Fuzzer {
private:
    std::mt19937 rng;
    std::uniform_int_distribution<int> byte_dist{0, 255};
    std::uniform_int_distribution<int> bool_dist{0, 1};

public:
    Fuzzer(unsigned int seed = std::random_device{}()) : rng(seed) {}

    // Generate random bytes
    std::vector<unsigned char> random_bytes(size_t count) {
        std::vector<unsigned char> result;
        result.reserve(count);

        for (size_t i = 0; i < count; ++i) {
            result.push_back(static_cast<unsigned char>(byte_dist(rng)));
        }

        return result;
    }

    // Generate malformed UTF-8 sequences
    std::string malformed_utf8(size_t count) {
        std::string result;

        for (size_t i = 0; i < count; ++i) {
            int choice = byte_dist(rng) % 10;

            switch (choice) {
                case 0:
                    // Invalid continuation byte
                    result += static_cast<char>(0x80 + (byte_dist(rng) % 64));
                    break;
                case 1:
                    // Incomplete multi-byte sequence
                    result += static_cast<char>(0xC0 + (byte_dist(rng) % 32));
                    break;
                case 2:
                    // Overlong encoding
                    result += "\xC0\x80";
                    break;
                case 3:
                    // Invalid byte
                    result += static_cast<char>(0xFF);
                    break;
                case 4:
                    // Null byte
                    result += '\0';
                    break;
                default:
                    // Valid ASCII
                    result += static_cast<char>(32 + (byte_dist(rng) % 95));
                    break;
            }
        }

        return result;
    }

    // Generate extreme numeric values
    std::vector<std::string> extreme_numbers(size_t count) {
        std::vector<std::string> result;

        std::vector<std::string> templates = {
            "0",
            "-0",
            "Infinity",
            "-Infinity",
            "NaN",
            "1e308",      // Near max double
            "-1e308",
            "1e-308",     // Near min double
            "9999999999999999999999999999",  // Huge integer
            "0.00000000000000000000000001",  // Tiny decimal
        };

        for (size_t i = 0; i < count; ++i) {
            if (i < templates.size()) {
                result.push_back(templates[i]);
            } else {
                // Generate random extreme value
                std::ostringstream oss;
                int sign = bool_dist(rng) ? 1 : -1;
                int exponent = byte_dist(rng) * 4 - 512;
                double mantissa = static_cast<double>(byte_dist(rng)) / 255.0;

                oss << sign * mantissa << "e" << exponent;
                result.push_back(oss.str());
            }
        }

        return result;
    }

    // Generate malformed JSON
    std::string malformed_json() {
        std::vector<std::string> patterns = {
            "{",                                    // Unclosed object
            "[",                                    // Unclosed array
            "{\"key\": }",                         // Missing value
            "{: \"value\"}",                       // Missing key
            "[1, 2, 3,]",                          // Trailing comma
            "{\"key\": \"value\",}",               // Trailing comma in object
            "{'key': 'value'}",                    // Single quotes
            "{\"key\": undefined}",                // Undefined value
            "{\"key\": 0x123}",                    // Hex literal
            "[1, 2, NaN, 3]",                      // NaN in array
            "{\"key\": .5}",                       // Leading decimal
            "{\"key\": 5.}",                       // Trailing decimal
            "[1 2 3]",                             // Missing commas
            "{\"a\" \"b\"}",                       // Missing colon
            "\"unclosed string",                   // Unclosed string
            "{\"key\": \"value\", \"key\": \"dup\"}", // Duplicate keys
        };

        return patterns[byte_dist(rng) % patterns.size()];
    }
};

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "Usage: " << argv[0] << " <mode> <count> [seed]" << std::endl;
        return 1;
    }

    std::string mode = argv[1];
    size_t count = std::stoull(argv[2]);
    unsigned int seed = (argc >= 4) ? std::stoul(argv[3]) : std::random_device{}();

    Fuzzer fuzzer(seed);

    if (mode == "random_bytes") {
        auto bytes = fuzzer.random_bytes(count);
        std::cout.write(reinterpret_cast<const char*>(bytes.data()), bytes.size());

    } else if (mode == "malformed_utf8") {
        std::string result = fuzzer.malformed_utf8(count);
        std::cout << result;

    } else if (mode == "extreme_numbers") {
        auto numbers = fuzzer.extreme_numbers(count);
        for (const auto& num : numbers) {
            std::cout << num << std::endl;
        }

    } else if (mode == "json_fuzzing") {
        for (size_t i = 0; i < count; ++i) {
            std::cout << fuzzer.malformed_json() << std::endl;
        }

    } else {
        std::cerr << "Unknown mode: " << mode << std::endl;
        return 1;
    }

    return 0;
}
