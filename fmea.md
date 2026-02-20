# Failure Mode and Effects Analysis (FMEA)

This FMEA identifies potential failure modes, their effects, causes, detection methods, and mitigation strategies for the Boreal Hybrid Control System.

## FMEA Scope

- **System**: Complete robotics control stack
- **Boundaries**: AI host to actuator outputs
- **Severity**: Rated 1-10 (10 = catastrophic)
- **Occurrence**: Rated 1-10 (10 = frequent)
- **Detection**: Rated 1-10 (10 = undetectable)

## Failure Modes Analysis

| Item | Function | Failure Mode | Local Effects | System Effects | End Effects | S | O | D | Risk Priority |
|------|----------|--------------|---------------|----------------|-------------|---|---|---|---------------|
| 1 | Packet Authentication | MAC verification fails | Packet accepted incorrectly | Unauthorized actuator command | Robot collision/injury | 10 | 2 | 2 | 40 |
| 1 | Packet Authentication | Valid packet rejected | Control loss | Robot stops | Mission failure | 5 | 3 | 2 | 30 |
| 2 | Sequence Checking | Replay attack succeeds | Stale command executed | Unexpected movement | Safety hazard | 8 | 1 | 3 | 24 |
| 3 | Policy VM | Bounds violation allowed | Actuator over-driven | Mechanical damage | System failure | 7 | 2 | 2 | 28 |
| 3 | Policy VM | Valid intent denied | Control loss | Robot stops | Mission failure | 5 | 3 | 2 | 30 |
| 4 | Safety Gate | Rate limit bypassed | Actuator oscillation | Instability | Loss of control | 6 | 3 | 2 | 36 |
| 5 | Watchdog Timer | Timeout fails to trigger | No safe-state on fault | Uncontrolled movement | Catastrophic | 10 | 1 | 2 | 20 |
| 5 | Watchdog Timer | False timeout trigger | Unnecessary braking | Mission interruption | Operational | 3 | 2 | 3 | 18 |
| 6 | Motor Control | PID instability | Oscillation | Mechanical stress | Component failure | 4 | 3 | 4 | 48 |
| 6 | Motor Control | Encoder failure undetected | Open-loop control | Position drift | Navigation error | 5 | 4 | 5 | 100 |
| 7 | Hardware Override | Safe-state fails | Fault not contained | Uncontrolled actuators | Safety hazard | 10 | 1 | 1 | 10 |
| 8 | SPI Communication | Link loss | Packet timeout | Watchdog trigger | Safe stop | 2 | 5 | 1 | 10 |
| 8 | SPI Communication | Noise corruption | Invalid data | Packet rejection | Temporary control loss | 4 | 6 | 3 | 72 |
| 9 | Power Supply | Voltage drop | MCU reset | Safe-state entry | System restart | 3 | 4 | 2 | 24 |
| 10 | ROS2 Bridge | Message loss | Command not received | No action | Operational delay | 3 | 7 | 4 | 84 |

## Mitigation Strategies

### Design Mitigations
- Cryptographic authentication prevents injection attacks
- Hardware watchdog provides independent safety layer
- Redundant checks in firmware and hardware
- Rate limiting prevents oscillation
- Formal verification proves critical invariants

### Detection Methods
- MAC verification for authenticity
- Sequence checking for freshness
- Bounds checking at compile and runtime
- Watchdog monitoring for liveness
- Encoder feedback for closed-loop validation

### Risk Reduction
- **Total High-Risk Items**: 3 (Risk Priority >50)
- **Mitigation Coverage**: 100% of high-risk items have multiple layers
- **Residual Risk**: All catastrophic failures have hardware containment
- **Common Cause Analysis**: Independent power, clocks, and processing for safety channels

This FMEA demonstrates that all credible failure modes are detected and mitigated with multiple independent layers.
