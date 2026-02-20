#include "../include/protocol.h"
#include <stdint.h>

// --- Motor Control HAL Hooks (Map to your MCU SDK) ---
extern int32_t hw_encoder_get_count(uint8_t motor_id);
extern void hw_encoder_reset(uint8_t motor_id);
extern void hw_pwm_set_duty(uint8_t motor_id, int16_t duty); // -1000 to 1000

#define NUM_MOTORS 2 // Left, Right for differential drive
#define PID_KP 1.0f
#define PID_KI 0.1f
#define PID_KD 0.05f
#define MAX_INTEGRAL 100.0f
#define CONTROL_HZ 50 // 50 Hz control loop

typedef struct {
  int32_t prev_count;
  float velocity; // rad/s
  float target_velocity;
  float integral;
  float prev_error;
  uint32_t last_update_ms;
} motor_pid_t;

static motor_pid_t motors[NUM_MOTORS];

void motor_control_init(void) {
  for (int i = 0; i < NUM_MOTORS; i++) {
    motors[i].prev_count = 0;
    motors[i].velocity = 0.0f;
    motors[i].target_velocity = 0.0f;
    motors[i].integral = 0.0f;
    motors[i].prev_error = 0.0f;
    motors[i].last_update_ms = 0;
    hw_encoder_reset(i);
  }
}

void motor_control_update_velocity(uint8_t motor_id, uint32_t current_ms) {
  if (motor_id >= NUM_MOTORS)
    return;

  int32_t count = hw_encoder_get_count(motor_id);
  int32_t delta_count = count - motors[motor_id].prev_count;
  motors[motor_id].prev_count = count;

  // Assume 1000 counts per revolution, control at 50 Hz
  float dt = (current_ms - motors[motor_id].last_update_ms) / 1000.0f;
  if (dt > 0.0f) {
    motors[motor_id].velocity =
        (delta_count * 2 * 3.14159f) / (1000.0f * dt); // rad/s
  }
  motors[motor_id].last_update_ms = current_ms;
}

int16_t motor_control_pid_update(uint8_t motor_id) {
  if (motor_id >= NUM_MOTORS)
    return 0;

  float error = motors[motor_id].target_velocity - motors[motor_id].velocity;
  motors[motor_id].integral += error * (1.0f / CONTROL_HZ);
  if (motors[motor_id].integral > MAX_INTEGRAL)
    motors[motor_id].integral = MAX_INTEGRAL;
  if (motors[motor_id].integral < -MAX_INTEGRAL)
    motors[motor_id].integral = -MAX_INTEGRAL;

  float derivative = (error - motors[motor_id].prev_error) * CONTROL_HZ;
  motors[motor_id].prev_error = error;

  float output =
      PID_KP * error + PID_KI * motors[motor_id].integral + PID_KD * derivative;

  // Clamp to PWM range
  if (output > 1000.0f)
    output = 1000.0f;
  if (output < -1000.0f)
    output = -1000.0f;

  return (int16_t)output;
}

void motor_control_set_target(uint8_t motor_id, float target_vel) {
  if (motor_id < NUM_MOTORS) {
    motors[motor_id].target_velocity = target_vel;
  }
}

void motor_control_run(uint32_t current_ms) {
  for (uint8_t i = 0; i < NUM_MOTORS; i++) {
    motor_control_update_velocity(i, current_ms);
    int16_t pwm = motor_control_pid_update(i);
    hw_pwm_set_duty(i, pwm);
  }
}

// High-level interface for actions
void motor_control_execute_action(const action_t *act) {
  if (act->act == 1) { // STOP
    motor_control_set_target(0, 0.0f);
    motor_control_set_target(1, 0.0f);
  } else if (act->act == 2) {     // MOVE forward/backward
    float vel = act->v0 / 100.0f; // Scale from int16 to float
    motor_control_set_target(0, vel);
    motor_control_set_target(1, vel);
  } else if (act->act == 3) {      // TURN
    float turn = act->v0 / 100.0f; // Differential turn
    motor_control_set_target(0, turn);
    motor_control_set_target(1, -turn);
  }
}
