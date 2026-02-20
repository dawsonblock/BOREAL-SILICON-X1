cmake_minimum_required(VERSION 3.8)
project(boreal_bridge)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

find_package(ament_cmake REQUIRED)

install(PROGRAMS
  boreal_bridge.py
  ai_agent.py
  compiler.py
  chacha20.py
  siphash.py
  DESTINATION lib/${PROJECT_NAME}
)

install(FILES
  policy.dsl
  main.c
  vm.c
  siphash.c
  motor_control.c
  protocol.h
  policy_bin.h
  boreal_watchdog.v
  boreal_watchdog_formal.sv
  DESTINATION share/${PROJECT_NAME}/firmware
)

ament_package()
