import os
import sys

import lcm
import matplotlib.pyplot as plt
import numpy as np

from lcmtypes import mbot_encoder_t, mbot_motor_command_t, timestamp_t, odometry_t


def is_between(a, b, c):
    return a <= c <= b or b <= c <= a


sys.path.append("lcmtypes")

WHEEL_BASE = 0.15
WHEEL_DIAMETER = 0.084
GEAR_RATIO = 78
ENCODER_RES = 20
enc2meters = WHEEL_DIAMETER * np.pi / (GEAR_RATIO * ENCODER_RES)

if len(sys.argv) < 2:
    sys.stderr.write("usage: plot_square.py <logfile>")
    sys.exit(1)

file = sys.argv[1]
log = lcm.EventLog(file, "r")

encoder_data = np.empty((0, 5), dtype=int)
encoder_init = 0

command_data = np.empty((0, 3), dtype=float)
command_init = 0

odom_data = np.empty((0, 4), dtype=float)
odom_init = 0

timesync_data = np.empty((0, 1), dtype=int)

for event in log:
    if event.channel == "MBOT_ENCODERS":
        encoder_msg = mbot_encoder_t.decode(event.data)
        if encoder_init == 0:
            enc_start_utime = encoder_msg.utime
            print("enc_start_utime: {}".format(enc_start_utime))
            encoder_init = 1
        encoder_data = np.append(encoder_data, np.array([[
            (encoder_msg.utime - enc_start_utime)/1.0E6,
            encoder_msg.leftticks,
            encoder_msg.rightticks,
            encoder_msg.left_delta,
            encoder_msg.right_delta
        ]]), axis=0)

    if event.channel == "MBOT_MOTOR_COMMAND":
        command_msg = mbot_motor_command_t.decode(event.data)
        if command_init == 0:
            cmd_start_utime = command_msg.utime
            print("cmd_start_utime: {}".format(cmd_start_utime))
            command_init = 1
        command_data = np.append(command_data, np.array([[
            (command_msg.utime - cmd_start_utime)/1.0E6,
            command_msg.trans_v,
            command_msg.angular_v
        ]]), axis=0)

    if event.channel == "MBOT_TIMESYNC":
        timesync_msg = timestamp_t.decode(event.data)
        timesync_data = np.append(timesync_data, np.array([[
            (timesync_msg.utime)/1.0E6,
        ]]), axis=0)

    if event.channel == "ODOMETRY":
        odom_msg = odometry_t.decode(event.data)
        if odom_init == 0:
            odom_start_utime = odom_msg.utime
            print("odom_start_utime: {}".format(odom_start_utime))
            odom_init = 1
        odom_data = np.append(odom_data, np.array([[
            (odom_msg.utime - odom_start_utime)/1.0E6,
            odom_msg.x,
            odom_msg.y,
            odom_msg.theta
        ]]), axis=0)

# Encoder data
enc_time = encoder_data[:, 0]
enc_time_diff = np.diff(enc_time)
leftticks = encoder_data[:, 1]
rightticks = encoder_data[:, 2]
left_delta = encoder_data[:, 3]
right_delta = encoder_data[:, 4]

# Compute the wheel velocities from encoders
left_measured_vel = np.diff(leftticks) * enc2meters / enc_time_diff
right_measured_vel = np.diff(rightticks) * enc2meters / enc_time_diff

# print(timesync_data[0, 0], timesync_data[1, 0])

# Wheel command data
cmd_time = command_data[:, 0]
# print(cmd_time[0] , cmd_time[1])
trans_v = command_data[:, 1]
angular_v = command_data[:, 2]
left_setpoint_vel = trans_v - WHEEL_BASE * angular_v / 2
right_setpoint_vel = trans_v + WHEEL_BASE * angular_v / 2
left_setpoint_vel = np.insert(left_setpoint_vel, 0, 0)
right_setpoint_vel = np.insert(right_setpoint_vel, 0, 0)

# Repeat each item in the setpoint lists twice in a numpy array
left_setpoint_vel = np.repeat(left_setpoint_vel, 2)
right_setpoint_vel = np.repeat(right_setpoint_vel, 2)

# Move the command points to the frst time where the encoders change
# possible issue as this is not a great solution
first_enc_change_left = np.where(left_delta != 0)[0][0]
first_enc_change_right = np.where(right_delta != 0)[0][0]

i = 1
while first_enc_change_left != first_enc_change_right:
    first_enc_change_left = np.where(left_delta != 0)[0][i]
    first_enc_change_right = np.where(right_delta != 0)[0][i]
    i += 1

# Start forming the command lines
left_cmd_times = cmd_time + enc_time[first_enc_change_left]
right_cmd_times = cmd_time + enc_time[first_enc_change_right]
left_cmd_times = np.repeat(left_cmd_times, 2)
right_cmd_times = np.repeat(right_cmd_times, 2)

# Add a value to the beginning of the command lines to make them start at the same time
left_cmd_times_ = np.ones((left_cmd_times.shape[0] + 2)) * enc_time[1]
right_cmd_times_ = np.ones((right_cmd_times.shape[0] + 2)) * enc_time[1]
left_cmd_times_[1:-1] = left_cmd_times
right_cmd_times_[1:-1] = right_cmd_times
left_cmd_times_[-1] = enc_time[-1]
right_cmd_times_[-1] = enc_time[-1]

# Odom data
odom_time = odom_data[:, 0]
odom_x = odom_data[:, 1]
odom_y = odom_data[:, 2]
odom_theta = odom_data[:, 3]

# Plot everything
plt.figure(figsize=(10, 10))

# Plot Expected Square Pattern - 0,0 -> 1,0 -> 1,1 -> 0,1 -> 0,0
plt.plot([0, 0.61, 0.61, 1.22, 1.22], [0, 0, 0.61, 0.61, -0.61], 'r', label="Expected Path")

# Plot Actual Path
plt.plot(odom_x, odom_y, 'b', label="Actual Path")
plt.legend()

# X - axis -> X (meters)
# Y - axis -> Y (meters)
plt.xlabel("X (meters)")
plt.ylabel("Y (meters)")
plt.title("Square Path")

# # Plot Linear & Angular Velocity - Robot Frame
# axs[1].plot(enc_time[1:], left_measured_vel, 'b', label="Measured Velocity")
# axs[1].plot(left_cmd_times_, left_setpoint_vel, c='r', label="Target Velocity")

# axs[1].legend()
# axs[1].set_xlabel("Time (s)")
# axs[1].set_ylabel("Velocity (m/s)")
# axs[1].set_title("Right Wheel")

plt.savefig(f"{file}.png")

plt.show()
