cmake_minimum_required(VERSION 3.8)
project(boreal_bridge)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

install(PROGRAMS
  scripts/boreal_bridge.py
  scripts/ai_agent.py
  scripts/chacha20.py
  scripts/siphash.py
  policy/compiler.py
  DESTINATION lib/${PROJECT_NAME}
)

install(FILES
  policy/policy.dsl
  firmware/src/main.c
  firmware/src/vm.c
  firmware/src/siphash.c
  firmware/src/motor_control.c
  firmware/include/protocol.h
  firmware/include/policy_bin.h
  hardware/rtl/boreal_watchdog.v
  hardware/formal/boreal_watchdog_formal.sv
  DESTINATION share/${PROJECT_NAME}/firmware
)

ament_package()
