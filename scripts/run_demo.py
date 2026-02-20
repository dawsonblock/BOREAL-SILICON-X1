#!/usr/bin/env python3

import time
import struct

# Import components
import os
import sys

# Add policy and scripts paths to allow module importing across directories
lib_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(os.path.join(lib_path, "policy"))
sys.path.append(os.path.join(lib_path, "scripts"))

from compiler import compile_policy
from chacha20 import chacha20_encrypt

CHACHA_KEY = struct.pack(
    "<8I",
    0x01020304,
    0x05060708,
    0x090A0B0C,
    0x0D0E0F10,
    0x11121314,
    0x15161718,
    0x191A1B1C,
    0x1D1E1F20,
)

# Simulated firmware components (translated from C)


class SimulatedFirmware:
    def __init__(self):
        # Shared secret
        self.MAC_KEY = struct.pack("<QQ", 0xA3B1C2D3E4F56789, 0x1020304050607080)
        self.CHACHA_KEY = CHACHA_KEY
        self.MAGIC_WORD = 0xB0A1E1A1
        self.last_seq = 0

        # Policy bytecode (loaded from local file)
        policy_path = os.path.join(
            os.path.dirname(__file__), "..", "policy", "policy.dsl"
        )
        bc = compile_policy(policy_path)
        self.POLICY_BC = bc
        self.POLICY_LEN = len(bc)
        self.prev_act_id = 0

        # Motor control simulation
        self.motors = [
            {"velocity": 0.0, "target": 0.0, "integral": 0.0, "error": 0.0}
            for _ in range(2)
        ]
        self.KP = 1.0
        self.KI = 0.1
        self.KD = 0.05
        self.MAX_INTEGRAL = 100.0
        self.CONTROL_HZ = 50

        # Watchdog
        self.watchdog_timer = 0
        self.MAX_CYCLES = 200 * 100  # 200ms @ 100Hz simulation
        self.safe_state = True  # Start safe

        # Packet buffer
        self.rx_queue = []

    def siphash24_sim(self, data, key):
        # Simplified SipHash for simulation
        h = int.from_bytes(key, "little") ^ int.from_bytes(data[:8], "little")
        h = (h * 0x9E3779B185EBCA87) & 0xFFFFFFFFFFFFFFFF
        h ^= h >> 32
        return h

    def decision_vm(self, p):
        act = {"act": 0, "v0": 0}
        pc = 0
        steps = 0
        cond_failed = False
        while pc < self.POLICY_LEN and steps < 32:
            op = self.POLICY_BC[pc]
            pc += 1
            if op == 0x01:  # OP_IF
                i = self.POLICY_BC[pc] | (self.POLICY_BC[pc + 1] << 8)
                c = self.POLICY_BC[pc + 2] | (self.POLICY_BC[pc + 3] << 8)
                pc += 4
                cond_failed = False
                if not (p["intent_id"] == i and p["conf_q15"] >= c):
                    cond_failed = True
            elif op == 0x04:  # OP_REQUIRE_PREV
                req_act = self.POLICY_BC[pc]
                pc += 1
                if self.prev_act_id != req_act and self.prev_act_id != 0:
                    cond_failed = True
            elif op == 0x02:  # OP_ACT
                act_id = self.POLICY_BC[pc]
                v0 = self.POLICY_BC[pc + 1] | (self.POLICY_BC[pc + 2] << 8)
                if v0 > 0x7FFF:
                    v0 -= 0x10000
                pc += 3
                if not cond_failed:
                    act["act"] = act_id
                    act["v0"] = v0
                    self.prev_act_id = act_id
                    return act
            elif op == 0x03:  # OP_DENY
                act["act"] = 0
                self.prev_act_id = 0
                return act
            elif op == 0xFF:  # OP_END
                break
            steps += 1
        return act

    def gate_allow(self, act, p):
        if act["act"] == 0:
            return False
        # Rate limit MOVE to 50Hz
        if act["act"] == 2:
            # Simplified: assume allowed
            pass
        return True

    def motor_control_pid(self, motor_id):
        motor = self.motors[motor_id]
        error = motor["target"] - motor["velocity"]
        motor["integral"] += error / self.CONTROL_HZ
        if motor["integral"] > self.MAX_INTEGRAL:
            motor["integral"] = self.MAX_INTEGRAL
        if motor["integral"] < -self.MAX_INTEGRAL:
            motor["integral"] = -self.MAX_INTEGRAL
        derivative = (error - motor["error"]) * self.CONTROL_HZ
        motor["error"] = error
        output = self.KP * error + self.KI * motor["integral"] + self.KD * derivative
        output = max(-1000, min(1000, output))
        return int(output)

    def motor_control_execute(self, act):
        if act["act"] == 1:  # STOP
            self.motors[0]["target"] = 0.0
            self.motors[1]["target"] = 0.0
        elif act["act"] == 2:  # MOVE
            vel = act["v0"] / 100.0
            self.motors[0]["target"] = vel
            self.motors[1]["target"] = vel
        elif act["act"] == 3:  # TURN
            turn = act["v0"] / 100.0
            self.motors[0]["target"] = turn
            self.motors[1]["target"] = -turn

    def process_packet(self, pkt):
        # Authenticate
        # The payload for MAC calculation is the header + ciphertext (first 25 unpacked elements)
        payload_for_mac = struct.pack("<IHHIIHH18h", *pkt[:25])
        calc_mac = self.siphash24_sim(payload_for_mac, self.MAC_KEY)
        if calc_mac != pkt[25]:  # pkt[25] is the MAC checksum
            print("MAC verification failed!")
            return

        # Anti-replay
        magic, version, model, seq_num, t_ms = pkt[0:5]
        if magic != self.MAGIC_WORD or seq_num <= self.last_seq:
            print("Invalid packet or replay!")
            return
        self.last_seq = seq_num

        # Decrypt Policy Body
        # The ciphertext is the last 40 bytes of the payload_for_mac (which is 56 bytes total)
        # The format string for payload_for_mac is "<IHHIIHH18h"
        # I (4 bytes) + HH (4 bytes) + II (8 bytes) = 16 bytes for header
        # HH18h (40 bytes) for encrypted part
        ciphertext = payload_for_mac[16:56]
        plaintext = chacha20_encrypt(ciphertext, self.CHACHA_KEY, seq_num, 0)
        decrypted_fields = struct.unpack("<HH18h", plaintext)

        p = {
            "magic": magic,
            "version": version,
            "model_id": model,
            "seq": seq_num,
            "t_ms": t_ms,
            "intent_id": decrypted_fields[0],
            "conf_q15": decrypted_fields[1],
            "aux": decrypted_fields[2:],
        }

        # VM Policy
        act = self.decision_vm(p)
        if self.gate_allow(act, p):
            # Actuate
            if act["act"] == 1:
                print(f"Brake engaged (GPIO {act['act']}: {act['v0']})")
            else:
                self.motor_control_execute(act)
                print(f"Motor control: act={act['act']}, value={act['v0']}")
            # Pet watchdog
            self.watchdog_timer = 0
            self.safe_state = False
        else:
            print("Action denied by safety gate!")

    def update_motors(self):
        for i in range(2):
            pwm = self.motor_control_pid(i)
            print(
                f"Motor {i}: target={self.motors[i]['target']:.2f}, vel={self.motors[i]['velocity']:.2f}, PWM={pwm}"
            )

    def update_watchdog(self):
        if not self.safe_state:
            self.watchdog_timer += 1
            if self.watchdog_timer >= self.MAX_CYCLES:
                self.safe_state = True
                print("WATCHDOG TRIGGERED: SAFE STATE ENGAGED!")


def ai_inference():
    # Simulate AI decisions
    intents = [
        (1, 0, "STOP"),  # Intent 1: STOP
        (2, 30000, "APPROACH"),  # Intent 2: APPROACH
        (3, 20000, "TURN_LEFT"),  # Intent 3: TURN_LEFT
    ]
    return intents[int(time.time() * 2) % len(intents)]


def main():
    firmware = SimulatedFirmware()

    seq = 0
    while True:
        # AI Brain: Decide intent
        intent_id, conf, intent_name = ai_inference()
        print(f"\nAI Decision: {intent_name} (ID {intent_id}, conf {conf})")

        # Cerebellum: Motion planning (simplified)
        aux_data = [30]  # Some aux data
        aux_padded = (aux_data + [0] * 18)[:18]

        # Host: Sign and send packet
        seq += 1
        plaintext = struct.pack("<HH18h", intent_id, conf, *aux_padded)
        ciphertext = chacha20_encrypt(plaintext, CHACHA_KEY, seq, 0)

        header = struct.pack(
            "<IHHII", 0xB0A1E1A1, 1, 1, seq, int(time.time() * 1000) & 0xFFFFFFFF
        )
        payload = header + ciphertext

        mac = firmware.siphash24_sim(payload, firmware.MAC_KEY)

        # To simulate the SPI packet, we unpack it back into 25 independent struct elements
        # followed by the 8-byte MAC checksum.
        pkt = list(struct.unpack("<IHHIIHH18hQ", payload + mac.to_bytes(8, "little")))

        # Brainstem: Process in firmware
        firmware.process_packet(pkt)

        # Update motors and watchdog
        firmware.update_motors()
        firmware.update_watchdog()

        time.sleep(0.1)  # 10 Hz demo loop


if __name__ == "__main__":
    main()
