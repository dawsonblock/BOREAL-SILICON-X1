#include "../include/protocol.h"
#include <string.h>

// --- HAL Hooks (Map to your MCU SDK: RP2040, STM32, etc.) ---
extern void hw_multicore_launch_core1(void (*entry)(void));
extern void hw_irq_disable_all_core0(void);
extern void hw_gpio_set(uint8_t act, int16_t val);
extern void hw_strobe_hardware_watchdog_pin(void);
extern int hw_spi_read_frame(uint8_t *cmd, uint8_t *len, uint8_t *data);

extern action_t decision_vm(const pkt_t *p);
extern int gate_allow(const action_t *a, const pkt_t *p);

extern void motor_control_init(void);
extern void motor_control_execute_action(const action_t *act);
extern void motor_control_run(uint32_t current_ms);
extern uint32_t hw_get_ms(void);

// 128-bit MAC Key
const uint64_t MAC_KEY[2] = {0xA3B1C2D3E4F56789ULL, 0x1020304050607080ULL};
// 256-bit ChaCha20 Cipher Key
const uint32_t CHACHA_KEY[8] = {0x01020304, 0x05060708, 0x090a0b0c, 0x0d0e0f10,
                                0x11121314, 0x15161718, 0x191a1b1c, 0x1d1e1f20};

// Lock-Free Ring Buffer (Core 1 -> Core 0)
#define Q_SIZE 8
volatile pkt_t RX_Q[Q_SIZE];
volatile uint8_t q_w = 0, q_r = 0;
uint32_t last_seq = 0;

// ==========================================
// CORE 1: Insecure IO & SPI Polling
// ==========================================
void core1_main(void) {
  uint8_t cmd, len, buf[64];
  while (1) {
    if (hw_spi_read_frame(&cmd, &len, buf)) {
      if (cmd == 0x01 && len == 64) {
        uint8_t next_w = (q_w + 1) % Q_SIZE;
        if (next_w != q_r) {
          memcpy((void *)&RX_Q[q_w], buf, 64);
          q_w = next_w; // Atomic commit to Core 0
        }
      }
    }
  }
}

// ==========================================
// CORE 0: Hard Real-Time Deterministic VM
// ==========================================
int main(void) {
  hw_multicore_launch_core1(core1_main);

  // Disable ALL interrupts on Core 0 for pure polling determinism
  hw_irq_disable_all_core0();

  motor_control_init();

  while (1) {
    if (q_r != q_w) {
      pkt_t p = RX_Q[q_r];
      q_r = (q_r + 1) % Q_SIZE; // Atomic pop

      // 1. Authenticate (MAC over first 56 bytes)
      if (siphash24((uint8_t *)&p, 56, MAC_KEY) != p.mac)
        continue;

      // 1.5 Decrypt Payload (skip magic/version/seq/timestamp headers)
      // Offset 16 = intent_id, conf_q15, aux[18]. Total 40 bytes.
      chacha20_encrypt(((uint8_t *)&p) + 16, 40, CHACHA_KEY, p.seq, 0);

      // 2. Anti-Replay
      if (p.magic != MAGIC_WORD || p.seq <= last_seq)
        continue;
      last_seq = p.seq;

      // 3. VM Policy & Software Gate
      action_t act = decision_vm(&p);
      if (gate_allow(&act, &p)) {
        // 4. Actuate
        if (act.act == 1) {
          hw_gpio_set(act.act, act.v0); // Brake via GPIO
        } else if (act.act >= 2) {
          motor_control_execute_action(&act); // Motor control for move/turn
        }

        // 5. Strobe the RTL Watchdog
        hw_strobe_hardware_watchdog_pin();
      }

      // Run motor control loop (assume packet rate ~50 Hz)
      motor_control_run(hw_get_ms());
    }
  }
}
