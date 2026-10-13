// API test only: initialize the installed particle table, never generate events.
#include "Pythia8/Pythia.h"
#include <iostream>
#include <stdexcept>

int main(int argc, char** argv) {
  try {
    if (argc != 2) throw std::runtime_error("provide installed Pythia xmldoc directory");
    Pythia8::Pythia database(argv[1], false);
    for (int sign : {-1, 1}) {
      for (int id : {511, 521, 411, 421, 541}) {
        const int pdg = sign * id;
        const bool bottom = database.particleData.isHadron(pdg) && database.particleData.nQuarksInCode(pdg, 5) > 0;
        const bool charm = database.particleData.isHadron(pdg) && database.particleData.nQuarksInCode(pdg, 4) > 0;
        if (bottom != (id == 511 || id == 521 || id == 541) ||
            charm != (id == 411 || id == 421 || id == 541))
          throw std::runtime_error("inclusive heavy-hadron classification failed for " + std::to_string(pdg));
      }
    }
    std::cout << "PASS: 10 signed PDG API cases; B_c inclusive in both b/c; no events generated\n";
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "FAIL: " << error.what() << '\n';
    return 1;
  }
}
