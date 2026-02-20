# Safety Test Plan

This document outlines the testing strategy for verifying safety functions in the Boreal Hybrid Control System.

## Test Objectives

1. Verify all safety functions operate as designed
2. Validate fault detection and safe-state transitions
3. Confirm diagnostic coverage meets SIL/PL requirements
4. Ensure independence of safety channels
5. Validate environmental and stress conditions

## Test Environment

- **Hardware**: Raspberry Pi + RP2040 MCU + FPGA simulator
- **Software**: Python test harness, C unit tests, formal verification
- **Tools**: pytest, SymbiYosys, ROS2 test framework

## Test Categories

### 1. Unit Tests
- Component-level testing of individual modules
- Code coverage >95% for safety-critical paths

### 2. Integration Tests
- End-to-end packet flow from AI to actuators
- ROS2 bridge functionality

### 3. Formal Verification
- Mathematical proofs of invariants
- Model checking of safety properties

### 4. Fault Injection Tests
- Simulate hardware faults, communication failures
- Validate watchdog and safe-state responses

### 5. Performance Tests
- Timing verification (200ms watchdog timeout)
- Resource utilization under load

## Key Test Cases

| Test ID | Description | Type | Safety Function | Expected Outcome |
|---------|-------------|------|-----------------|------------------|
| TC-001 | Valid packet authentication | Integration | MAC verification | Packet accepted, actuator commanded |
| TC-002 | Invalid MAC rejection | Integration | Authentication | Packet dropped, no actuator change |
| TC-003 | Sequence replay prevention | Integration | Anti-replay | Duplicate packets ignored |
| TC-004 | Watchdog timeout safe-state | Hardware | Watchdog | Brake engaged after 200ms |
| TC-005 | Policy VM bounds enforcement | Unit | Safety gate | Out-of-bounds intents denied |
| TC-006 | Rate limiting gate | Unit | Safety gate | Excessive commands rejected |
| TC-007 | Motor PID stability | Simulation | Control | Velocity converges to target |
| TC-008 | Encoder feedback accuracy | Hardware | Feedback | Position error <1% |
| TC-009 | ROS2 cmd_vel mapping | Integration | Interface | Twist commands converted to intents |
| TC-010 | Safe-state override | Formal | Hardware | Firmware commands ignored when safe |
| TC-011 | Fault injection - SPI loss | Fault | Communication | Watchdog triggers safe-state |
| TC-012 | Environmental stress | Performance | Robustness | No failures at -40°C to 85°C |
| TC-013 | Power cycle recovery | Integration | Boot | System enters safe-state on reset |
| TC-014 | Multi-channel voting | Simulation | Redundancy | Single channel failure detected |

## Test Coverage Metrics

- **Requirements Coverage**: 100%
- **Code Coverage**: >95% for safety paths
- **Fault Coverage**: >99% for detected faults
- **Diagnostic Coverage**: 95% for PL d requirements

## Test Execution

1. **Automated Tests**: Run nightly CI/CD pipeline
2. **Manual Tests**: Safety engineer validation
3. **Formal Tests**: SymbiYosys verification
4. **Hardware Tests**: HIL (Hardware-in-Loop) simulation

## Pass/Fail Criteria

- All safety tests must pass
- No regressions in formal properties
- Diagnostic coverage meets standard requirements
- Independent assessment confirms SIL/PL rating

This test plan ensures comprehensive validation of safety-critical functions.
