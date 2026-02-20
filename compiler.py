import struct
import hashlib

OP_IF = 0x01
OP_SET = 0x02
OP_DENY = 0x03
OP_REQUIRE_PREV = 0x04
OP_END = 0xFF

# Physical Hardware Limits (Min, Max)
BOUNDS = {1: (0, 1), 2: (-50, 50), 3: (-30, 30)}


def compile_policy(filepath):
    with open(filepath, "r") as f:
        lines = [
            line_str.split("#")[0].strip()
            for line_str in f
            if line_str.split("#")[0].strip()
        ]

    bc = bytearray()
    has_default = False

    for line in lines:
        parts = line.split()
        if parts[0] == "IF":
            bc += bytes([OP_IF]) + struct.pack("<HH", int(parts[3]), int(parts[7]))
        elif parts[0] == "REQUIRE_PREV":
            bc += bytes([OP_REQUIRE_PREV, int(parts[1])])
        elif parts[0] == "ACT":
            act, param = int(parts[1]), int(parts[2])
            if act not in BOUNDS or not (BOUNDS[act][0] <= param <= BOUNDS[act][1]):
                raise ValueError(
                    f"FATAL: Actuator {act} param {param} out of physical bounds!"
                )
            bc += bytes([OP_SET, act]) + struct.pack("<h", param)
        elif parts[0] == "DEFAULT" and parts[1] == "DENY":
            bc += bytes([OP_DENY])
            has_default = True
            break

    if not has_default:
        raise ValueError("FATAL: Policy MUST end with DEFAULT DENY.")
    bc += bytes([OP_END])
    return bc


if __name__ == "__main__":
    bc = compile_policy("policy.dsl")
    with open("policy_bin.h", "w") as f:
        f.write(f"// SHA256: {hashlib.sha256(bc).hexdigest()}\n")
        f.write(f"const uint8_t POLICY_BC[] = {{{', '.join(hex(b) for b in bc)}}};\n")
        f.write(f"const size_t POLICY_LEN = {len(bc)};\n")
    print("Compiled successfully to policy_bin.h")
