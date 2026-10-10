cmake_minimum_required(VERSION 3.20)
project(ATLAS_HH_BBGG_PUBLIC_V1 VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if(CMAKE_SOURCE_DIR STREQUAL CMAKE_BINARY_DIR)
  message(FATAL_ERROR "Use an out-of-source build directory; source-tree builds are unsupported.")
endif()

find_package(ROOT 6.40.04 EXACT CONFIG REQUIRED COMPONENTS
  Core RIO Tree Hist ROOTDataFrame RooFit RooStats)
if(NOT DEFINED ROOT_CXX_STANDARD OR NOT ROOT_CXX_STANDARD STREQUAL "20")
  message(FATAL_ERROR "Step 1 requires ROOT built with C++20; ROOT_CXX_STANDARD='${ROOT_CXX_STANDARD}'.")
endif()

message(STATUS "ROOT version: ${ROOT_VERSION}")
message(STATUS "ROOT C++ standard: ${ROOT_CXX_STANDARD}")
message(STATUS "ROOT CMake package: ${ROOT_DIR}")
message(STATUS "Compiler: ${CMAKE_CXX_COMPILER_ID} ${CMAKE_CXX_COMPILER_VERSION}")
message(STATUS "Compiler path: ${CMAKE_CXX_COMPILER}")

function(add_step1_executable target source)
  add_executable(${target} ${source})
  target_compile_features(${target} PRIVATE cxx_std_20)
  set_target_properties(${target} PROPERTIES
    CXX_STANDARD 20 CXX_STANDARD_REQUIRED YES CXX_EXTENSIONS NO)
  # This generated build path is never a hard-coded installation path.
  target_compile_definitions(${target} PRIVATE
    ATLAS_STEP1_OUTPUT_DIR="$<TARGET_FILE_DIR:${target}>")
  if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(${target} PRIVATE -Wall -Wextra -Wpedantic)
  endif()
endfunction()

add_step1_executable(root_smoke apps/root_smoke.cxx)
target_link_libraries(root_smoke PRIVATE ROOT::Core ROOT::RIO ROOT::Hist)

include(CTest)
if(BUILD_TESTING)
  add_step1_executable(test_root_io tests/test_root_io.cxx)
  target_link_libraries(test_root_io PRIVATE ROOT::Core ROOT::RIO ROOT::Tree ROOT::Hist)
  add_test(NAME root_io COMMAND test_root_io)

  add_step1_executable(test_rdataframe tests/test_rdataframe.cxx)
  target_link_libraries(test_rdataframe PRIVATE ROOT::Core ROOT::Hist ROOT::ROOTDataFrame)
  add_test(NAME rdataframe COMMAND test_rdataframe)

  add_step1_executable(test_root_statistics tests/test_root_statistics.cxx)
  target_link_libraries(test_root_statistics PRIVATE ROOT::Core ROOT::RooFit ROOT::RooStats)
  add_test(NAME roofit_roostats COMMAND test_root_statistics)

  set_tests_properties(root_io rdataframe roofit_roostats PROPERTIES
    WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}" TIMEOUT 60 LABELS "step1;synthetic")
endif()

option(ATLAS_BUILD_PHASE1 "Build the bounded local ROOT schema inspector" OFF)
if(ATLAS_BUILD_PHASE1)
  add_library(atlas_root_schema src/RootSchemaInspector.cxx)
  target_include_directories(atlas_root_schema PUBLIC include)
  target_link_libraries(atlas_root_schema PUBLIC ROOT::Core ROOT::RIO ROOT::Tree ROOT::TreePlayer ROOT::ROOTVecOps)
  target_compile_features(atlas_root_schema PUBLIC cxx_std_20)
  if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
    target_compile_options(atlas_root_schema PRIVATE -Wall -Wextra -Wpedantic)
  endif()
  add_step1_executable(inspect_root_schema apps/inspect_root_schema.cxx)
  target_link_libraries(inspect_root_schema PRIVATE atlas_root_schema)
  if(BUILD_TESTING)
    find_package(Python3 REQUIRED COMPONENTS Interpreter)
    add_step1_executable(test_root_schema tests/test_root_schema.cxx)
    target_link_libraries(test_root_schema PRIVATE atlas_root_schema)
    add_test(NAME root_schema_suite COMMAND test_root_schema)
    add_test(NAME bounded_transfer COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_SOURCE_DIR}/tests/test_bounded_transfer.py")
    set_tests_properties(root_schema_suite PROPERTIES
      WORKING_DIRECTORY "${CMAKE_CURRENT_BINARY_DIR}" TIMEOUT 60 LABELS "phase1;synthetic")
    set_tests_properties(bounded_transfer PROPERTIES TIMEOUT 30 LABELS "phase1;metadata;synthetic")
  endif()
endif()

option(ATLAS_BUILD_PHASE2 "Build exploratory kinematic reconstruction" OFF)
if(ATLAS_BUILD_PHASE2)
  find_package(ROOT 6.40.04 EXACT CONFIG REQUIRED COMPONENTS MathCore TreePlayer ROOTVecOps Graf Gpad)
  add_library(atlas_kinematics src/Kinematics.cxx src/LocalEvents.cxx)
  target_include_directories(atlas_kinematics PUBLIC include)
  target_link_libraries(atlas_kinematics PUBLIC ROOT::MathCore ROOT::TreePlayer ROOT::ROOTVecOps ROOT::RIO)
  target_compile_features(atlas_kinematics PUBLIC cxx_std_20)
  target_compile_options(atlas_kinematics PRIVATE -Wall -Wextra -Wpedantic)
  add_step1_executable(probe_kinematic_units apps/probe_kinematic_units.cxx)
  target_link_libraries(probe_kinematic_units PRIVATE atlas_kinematics)
  add_step1_executable(phase2_diagnostics apps/phase2_diagnostics.cxx)
  target_link_libraries(phase2_diagnostics PRIVATE atlas_kinematics ROOT::Hist ROOT::Graf ROOT::Gpad)
  if(BUILD_TESTING)
    add_step1_executable(test_kinematics tests/test_kinematics.cxx)
    target_link_libraries(test_kinematics PRIVATE atlas_kinematics)
    add_step1_executable(test_local_events tests/test_local_events.cxx)
    target_link_libraries(test_local_events PRIVATE atlas_kinematics)
    add_test(NAME kinematic_numerics COMMAND test_kinematics)
    add_test(NAME native_local_events COMMAND test_local_events)
    set_tests_properties(kinematic_numerics native_local_events PROPERTIES TIMEOUT 60 LABELS "phase2;synthetic")
    find_package(Python3 REQUIRED COMPONENTS Interpreter)
    add_test(NAME phase2_driver_contract COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_SOURCE_DIR}/tests/test_phase2_driver.py"
      "$<TARGET_FILE:phase2_diagnostics>" "$<TARGET_FILE_DIR:test_local_events>")
    set_tests_properties(phase2_driver_contract PROPERTIES DEPENDS native_local_events TIMEOUT 60 LABELS "phase2;synthetic")
    add_test(NAME unit_evidence_gate COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_SOURCE_DIR}/tests/test_unit_evidence.py" "${CMAKE_CURRENT_SOURCE_DIR}/scripts/audit_phase2_units.py")
    set_tests_properties(unit_evidence_gate PROPERTIES TIMEOUT 30 LABELS "phase2;synthetic")
  endif()
endif()

option(ATLAS_BUILD_PHASE3 "Build study-defined exploratory preselection" OFF)
if(ATLAS_BUILD_PHASE3)
  if(NOT ATLAS_BUILD_PHASE2)
    message(FATAL_ERROR "Enable ATLAS_BUILD_PHASE2 for the Phase 3 reconstruction dependency.")
  endif()
  add_library(atlas_selection src/ExploratorySelection.cxx)
  target_include_directories(atlas_selection PUBLIC include)
  target_compile_features(atlas_selection PUBLIC cxx_std_20)
  target_compile_options(atlas_selection PRIVATE -Wall -Wextra -Wpedantic)
  add_step1_executable(phase3_cutflow apps/phase3_cutflow.cxx)
  target_link_libraries(phase3_cutflow PRIVATE atlas_selection ROOT::Hist ROOT::Graf ROOT::Gpad)
  if(BUILD_TESTING)
    find_package(Python3 REQUIRED COMPONENTS Interpreter)
    add_step1_executable(test_exploratory_selection tests/test_exploratory_selection.cxx)
    target_link_libraries(test_exploratory_selection PRIVATE atlas_selection)
    add_test(NAME selection_boundaries COMMAND test_exploratory_selection "${CMAKE_CURRENT_SOURCE_DIR}/metadata/phase3_selection_config.ini")
    add_test(NAME phase3_driver_contract COMMAND "${Python3_EXECUTABLE}" -B "${CMAKE_CURRENT_SOURCE_DIR}/tests/test_phase3_driver.py" "$<TARGET_FILE:phase3_cutflow>" "${CMAKE_CURRENT_SOURCE_DIR}/metadata/phase3_selection_config.ini")
    set_tests_properties(selection_boundaries phase3_driver_contract PROPERTIES TIMEOUT 60 LABELS "phase3;synthetic")
  endif()
endif()

file(WRITE "${CMAKE_CURRENT_BINARY_DIR}/step1_cmake_environment.txt"
  "ROOT_VERSION=${ROOT_VERSION}\nROOT_CXX_STANDARD=${ROOT_CXX_STANDARD}\n"
  "ROOT_DIR=${ROOT_DIR}\nCXX_COMPILER=${CMAKE_CXX_COMPILER}\n"
  "CXX_COMPILER_ID=${CMAKE_CXX_COMPILER_ID}\n"
  "CXX_COMPILER_VERSION=${CMAKE_CXX_COMPILER_VERSION}\n"
  "PROJECT_CXX_STANDARD=${CMAKE_CXX_STANDARD}\n"
  "CXX_STANDARD_REQUIRED=${CMAKE_CXX_STANDARD_REQUIRED}\n"
  "CXX_EXTENSIONS=${CMAKE_CXX_EXTENSIONS}\n"
  "CMAKE_VERSION=${CMAKE_VERSION}\n")
