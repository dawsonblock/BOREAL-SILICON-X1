# Requirements Traceability Matrix

This matrix traces safety requirements from standards to implementation and verification.

## Safety Requirements

| Req ID | Description | Standard | Implementation Component | Verification Method |
|--------|-------------|----------|--------------------------|---------------------|
| SR-001 | System shall authenticate control packets using cryptographic MAC | IEC 61508 | firmware/src/siphash.c - SipHash-2-4 verification | Formal verification (SymbiYosys), Unit tests |
| SR-002 | System shall prevent packet replay attacks | IEC 61508 | firmware/src/main.c - Sequence number checking | Integration tests, FMEA analysis |
| SR-003 | System shall execute safety policy deterministically | ISO 13849 | firmware/src/vm.c - Decision VM bytecode execution | Formal verification, Code review |
| SR-004 | System shall enforce physical actuator bounds | IEC 61508 | host/compiler.py - Static bounds checking | Unit tests, Compiler validation |
| SR-005 | System shall engage emergency brake on watchdog timeout | ISO 13849 | hardware/boreal_watchdog.v - Deadman switch | Formal verification, Hardware tests |
| SR-006 | System shall limit actuator update rate to 50Hz | IEC 61508 | firmware/src/vm.c - Rate limiting gate | Integration tests |
| SR-007 | System shall provide closed-loop motor control | ISO 13849 | firmware/src/motor_control.c - PID velocity control | Simulation tests, Encoder feedback validation |
| SR-008 | System shall override firmware on hardware fault | IEC 61508 | hardware/boreal_watchdog.v - Safe-state logic | Formal verification, Fault injection tests |
| SR-009 | System shall maintain odometry for feedback | ISO 13849 | ros2_bridge/boreal_bridge.py - Dead reckoning | ROS2 integration tests |
| SR-010 | System shall reject invalid AI intents | IEC 61508 | firmware/src/vm.c - Policy VM denial | Policy DSL validation, Simulation |

## Functional Requirements

| Req ID | Description | Implementation Component | Verification Method |
|--------|-------------|--------------------------|---------------------|
| FR-001 | AI shall interface via authenticated packet protocol | host/ai_agent.py | Integration tests |
| FR-002 | ROS2 bridge shall map cmd_vel to intents | ros2_bridge/boreal_bridge.py | ROS2 tests |
| FR-003 | Motor control shall use quadrature encoder feedback | firmware/src/motor_control.c | Hardware tests |
| FR-004 | Watchdog shall reset on valid packet | hardware/boreal_watchdog.v | Formal verification |

## Traceability Coverage

- **Total Requirements**: 14
- **Fully Traced**: 14 (100%)
- **Test Coverage**: All requirements have verification methods defined
- **Formal Verification**: 3 requirements (hardware watchdog, VM, MAC)
- **Integration Tests**: 8 requirements
- **Unit Tests**: 3 requirements

This matrix ensures complete traceability from standards to code to tests.
