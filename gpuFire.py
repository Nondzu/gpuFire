# gpuFire.py
# created by Nondzu
# version 1.0.0
# last updated 2024-12-15
# github.com/nondzu/gpuFire
# check -> dopamine.blog

import argparse
import time as t
from pynvml import *
import os
import sys

def parse_args():
    nvmlInit()
    default_devices = list(range(nvmlDeviceGetCount()))
    parser = argparse.ArgumentParser(description='Monitor Nvidia GPUs.')
    parser.add_argument('--interval', type=int, default=1, help='Sampling interval in seconds (default: 1)')
    parser.add_argument('--memtemp', action='store_true', help='Also display GDDR6 memory temperatures (requires root)')
    args = parser.parse_args()
    return args, default_devices

def move_cursor_up(lines=1):
    print(f'\033[{lines}F', end='')

def color_print(color, text, bold=False):
    color_dict = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'cyan': '\033[96m',
        'blue': '\033[94m',
        'white': '\033[97m',
        'reset': '\033[0m'
    }
    bold_seq = '\033[1m' if bold else ''
    print(f'{bold_seq}{color_dict[color]}{text}{color_dict["reset"]}')

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def display_separator(char='=', length=40):
    print(char * length)

def display_icon(value, threshold, icon="⚠️"):
    """Return an icon based on value threshold."""
    return icon if value >= threshold else "✅"

def main():
    args, default_devices = parse_args()
    total_lines = 0  # Keep track of total lines printed

    # Jeśli użytkownik zażądał memtemp:
    mem_temps = []
    if args.memtemp:
        if os.geteuid() != 0:
            # print("Aby wyświetlić temperatury GDDR6, uruchom jako root.")
            print("You need to run as root to display GDDR6 temperatures.")
            # sleep 3 seconds
            t.sleep(3)
            # Nie przerywamy całego programu, po prostu nie pokażemy memtemp
        else:
            # Importujemy memtemp i pobieramy dane
            try:
                import memtemp
                mem_temps = memtemp.get_mem_temps()
            except Exception as e:
                print(f"Failed to get GDDR6 temperatures: {e}")
                mem_temps = []

    # Clear terminal on start
    clear_terminal()

    while True:
        # Clear terminal every 10 seconds
        if int(t.time()) % 10 == 0:
            clear_terminal()

        total_power = 0
        total_vram_used = 0
        total_utilization_gpu = 0

        # Move cursor up to overwrite previous output
        if total_lines > 0:
            move_cursor_up(total_lines)

        lines_printed = 0  # Reset lines printed for this iteration

        display_separator('=')
        color_print('blue', 'NVIDIA GPU Monitoring Tool', bold=True)
        display_separator('=')
        lines_printed += 3

        for device_id in default_devices:
            handle = nvmlDeviceGetHandleByIndex(device_id)
            power = nvmlDeviceGetPowerUsage(handle) / 1000.0
            gpu_temp = nvmlDeviceGetTemperature(handle, NVML_TEMPERATURE_GPU)
            memory_info = nvmlDeviceGetMemoryInfo(handle)
            utilization = nvmlDeviceGetUtilizationRates(handle)
            gpu_clock = nvmlDeviceGetClockInfo(handle, NVML_CLOCK_GRAPHICS)
            mem_clock = nvmlDeviceGetClockInfo(handle, NVML_CLOCK_MEM)
            max_tdp = nvmlDeviceGetPowerManagementLimit(handle) / 1000.0
            gpu_name = nvmlDeviceGetName(handle)
            try:
                fan_speed = nvmlDeviceGetFanSpeed(handle)
            except NVMLError_NotSupported:
                fan_speed = 'Not Supported'

            total_power += power
            total_vram_used += memory_info.used
            total_utilization_gpu += utilization.gpu

            color_print('cyan', f'GPU {device_id} ({gpu_name}) Status:', bold=True)
            lines_printed += 1
            color_print('green', f'  Power: {power:.2f} W / Max TDP: {max_tdp:.2f} W')
            lines_printed += 1
            color_print('yellow', f'  Temp:  {gpu_temp} °C {display_icon(gpu_temp, 80, "🔥")}')
            lines_printed += 1
            # Print GDDR6 temperatures if memtemp is enabled
            if args.memtemp and mem_temps:
                # Assume the order of GPUs detected in memtemp.get_mem_temps()
                # corresponds to the order in lspci. It may not always be perfect,
                # but this is an example.
                # Here we will display all found memtemp next to the GPU:
                # In practice, it may be necessary to match by BDF.
                color_print('yellow', f'  GDDR6: {mem_temps[device_id]} °C {display_icon(mem_temps[device_id], 100, "🔥")}' if device_id < len(mem_temps) and mem_temps[device_id] is not None else '  GDDR6 Temp: Not Available')
                lines_printed += 1

            color_print('green', f'  Utilization - GPU: {utilization.gpu}%, Memory: {utilization.memory}%')
            lines_printed += 1
            color_print('green', f'  Clocks - GPU: {gpu_clock} MHz, Memory: {mem_clock} MHz')
            lines_printed += 1
            color_print('green', f'  Memory - Total: {memory_info.total / (1024**2):.2f} MB, Used: {memory_info.used / (1024**2):.2f} MB')
            lines_printed += 1
            if fan_speed != 'Not Supported':
                color_print('green', f'  Fan Speed: {fan_speed}%')
            else:
                color_print('red', '  Fan Speed: Not Supported')
            lines_printed += 1

            display_separator('-')
            lines_printed += 1

        avg_utilization_gpu = total_utilization_gpu / len(default_devices)
        color_print('cyan', f'Total power consumption: {total_power:.2f} W', bold=True)
        lines_printed += 1
        color_print('cyan', f'Total VRAM used: {total_vram_used / (1024**2):.2f} MB', bold=True)
        lines_printed += 1
        color_print('yellow', f'Total GPU utilization: {total_utilization_gpu:.2f}%', bold=True)
        lines_printed += 1
        color_print('yellow', f'Average GPU utilization: {avg_utilization_gpu:.2f}%', bold=True)
        lines_printed += 1

        total_lines = lines_printed  # Update total lines for the next iteration
        t.sleep(args.interval)

if __name__ == '__main__':
    main()
