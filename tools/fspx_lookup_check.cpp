#include "shader_library.h"

#include <array>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <stdexcept>

namespace fs = std::filesystem;

static std::vector<std::uint8_t> read_part(const fs::path& path) {
    const auto size = fs::file_size(path);
    if (!size || size > leonida::kFspxPartLimit)
        throw std::runtime_error("FSPX input has an invalid size");
    std::vector<std::uint8_t> bytes(static_cast<std::size_t>(size));
    std::ifstream input(path, std::ios::binary);
    if (!input.read(reinterpret_cast<char*>(bytes.data()), bytes.size()))
        throw std::runtime_error("could not read FSPX input");
    return bytes;
}

int main(int argc, char** argv) try {
    if (argc != 3 && argc != 4) {
        std::cerr << "Usage: fspx_lookup_check CATALOG EXTRACTED_PARTS [MATCHED_KEYS_OUTPUT]\n";
        return 1;
    }
    leonida::ShaderLibrary library;
    std::string error;
    if (!library.load(argv[1], &error)) throw std::runtime_error(error);
    std::size_t total = 0, missed = 0, ambiguous = 0, unreadable = 0, matched = 0;
    std::set<std::pair<std::string, std::string>> matched_keys;
    for (const auto& file : fs::directory_iterator(argv[2])) {
        if (!file.is_regular_file() || file.path().extension() != ".code") continue;
        const auto code = read_part(file.path());
        auto state_path = file.path();
        const auto state = read_part(state_path.replace_extension(".state"));
        const std::array<leonida::FspxPart, 2> parts{{{0, state.data(), state.size()}, {6, code.data(), code.size()}}};
        auto payload = leonida::fspx_payload_from_parts(parts);
        auto program = leonida::compute_program(payload);
        if (program.kind != leonida::ComputeProgram::Kind::fspx || program.bytes != code || program.state != state)
            throw std::runtime_error("could not round-trip the extracted program and state through the runtime");
        ++total;
        bool conflict = false;
        const auto entries = library.program_candidates("cs", program, &conflict);
        if (conflict) { ++ambiguous; continue; }
        if (entries.empty()) { ++missed; continue; }
        const auto words = library.spirv(*entries.front());
        if (words.empty()) { ++unreadable; continue; }
        bool same = true;
        for (std::size_t i = 1; i < entries.size(); ++i)
            if (library.spirv(*entries[i]) != words) { same = false; break; }
        if (!same) { ++ambiguous; continue; }
        ++matched;
        matched_keys.emplace(leonida::sha256_hex(code), leonida::sha256_hex(state));
    }
    if (!total) throw std::runtime_error("no .code files in directory");
    if (argc == 4) {
        std::ofstream keys(argv[3]);
        for (const auto& [code, state] : matched_keys) keys << code << ' ' << state << '\n';
        keys.close();
        if (!keys) throw std::runtime_error("could not write matched keys");
    }
    std::cout << "inputs=" << total << " matched=" << matched << " distinct_matched=" << matched_keys.size()
              << " absent=" << missed << " ambiguous=" << ambiguous << " unreadable=" << unreadable
              << " indexed_fspx=" << library.fspx_size() << '\n';
    return (ambiguous || unreadable) ? 2 : 0;
} catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
}
