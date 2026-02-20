# BOREAL-SILICON-X1

<div align="center">
  <h3>Safety-Critical Hybrid Control System</h3>
  <i>An ISO 13849 & IEC 61508 Compliant Architecture bridging deep AI with resilient silicon operations.</i>
</div>

---

## 🛡️ Overview

**Boreal Silicon X1** is a deterministic safety-bridge designed to isolate mission-critical robotics hardware from high-level, non-deterministic Artificial Intelligence models. Instead of running raw LLM streams directly to an actuator, Boreal intercepts decisions, formally verifies state safety within an embedded Virtual Machine, and executes them over a hardened hardware interface.

The system is engineered for **1oo2D** architectures targeting up to **SIL 2** and **PL d** operational parameters.

---

## 🏗️ Architecture Stack

The Boreal topology is split into three core silos to ensure failure isolation:

1. **Python/ROS 2 Middleware (`scripts/`)**: Intercepts intelligence events. Employs ChaCha20-SipHash24 Encrypt-then-MAC algorithms to sign intent packets before traversing the system bus. Wraps control logic in managed ROS 2 Lifecycles.
2. **C Stateful Interpreter (`firmware/`)**: A tiny, bare-metal C virtual machine executes bounded `policy.dsl` opcodes. Decrypts and authenticates arriving intelligence logic before applying historical bounds checking and passing control to hardware drivers.
3. **RTL Watchdog (`hardware/`)**: A physical hardware override module. Connects via an AXI4-Lite bus interface, enforcing a bounded liveness timer that unconditionally cuts motor PWMs if the firmware stalls or panics. Mathematically proven via SymbiYosys/Z3.

---

## 📂 Repository Layout

```text
├── docs/            # Safety Certification Artifacts (ISO 13849/IEC 61508)
├── firmware/        # Bare-metal C interpreters and SPI bindings
│   ├── include/     # Firmware C Headers
│   └── src/         # VM / Control Execution / Cryptography
├── hardware/        # Verilog RTL logic and Formal Verification 
│   ├── formal/      # Symbiyosys .sby setup and SV testbenches
│   └── rtl/         # AXI4-Lite Watchdog core
├── policy/          # Internal DSL constraints and python bytecode compiler
└── scripts/         # ROS 2 Middlewares, Encryption Utilities, and Mock Runners
```

---

## 🚀 Getting Started

Boreal X1 is organized as an `ament_cmake` ROS 2 package.

### 1. Build & Install

Source your ROS 2 environment and run the following at the repo root:

```bash
colcon build --packages-select boreal_bridge
source install/setup.bash
```

*Note: Due to the `ament_cmake` build constraints, firmware assets and Python binaries are exported cohesively.*

### 2. Run the Firmware Simulation

To execute the End-To-End pipeline logic containing bounded tests, cryptographic signing, and AXI stall-checks:

```bash
python3 scripts/run_demo.py
```

### 3. Hardware Formal Verification

Install `yosys` and `SymbiYosys`, then run mathematically sound induction passes:

```bash
cd hardware/formal
sh run_formal.sh
```

---

## 📜 Certification Documentation

For auditing references spanning from FMEDA risk profiles through architecture coverage:

- [Requirements Traceability](docs/requirements_traceability.md)
- [SIL/PL Assessments](docs/sil_pl_assessment.md)
- [Test Plan](docs/test_plan.md)
- [ASIC/FPGA Resource Est.](docs/asic_estimates.md)

*Licensed under Apache-2.0.*
