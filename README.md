# gpuFire

**Version:** 1.0.0  
**Last Updated:** 2024-12-15  
**Author:** Nondzu  
**GitHub:** [github.com/nondzu](https://github.com/nondzu)  
**Check:** [dopamine.blog](https://dopamine.blog)  
**Inspiration:** [olealgoritme/gddr6](https://github.com/olealgoritme/gddr6)

## Description

`gpuFire.py` is a Python tool for monitoring NVIDIA GPUs using the NVIDIA Management Library (NVML). It displays information such as power usage, GPU temperature, utilization, clocks, memory usage, and fan speeds.

Optionally, it can also display GDDR6 memory temperatures if run as `root` and with the `--memtemp` argument. This temperature data is obtained through low-level memory mapping of the GPU's registers, requiring special system configurations (e.g., `iomem=relaxed` and root privileges).

## Features

- Monitors multiple NVIDIA GPUs simultaneously.
- Displays:
  - Power usage (W)
  - GPU temperature (°C)
  - GPU utilization (%)
  - Memory usage (MB)
  - GPU and Memory clocks (MHz)
  - Fan speed (%)
- **Optional:** GDDR6 memory temperature readings with `--memtemp` (root required).

## Requirements

- **Operating System:** Linux-based OS with NVIDIA drivers.
- **NVIDIA Management Library (NVML):**  
  Install via `sudo apt-get install nvidia-cuda-toolkit` or from [NVIDIA official sources](https://developer.nvidia.com/nvidia-system-management-interface).
- **Python 3** and `pynvml` library:  
  ```
  pip install pynvml
  ```
- For GDDR6 memory temperature readings:
  - Root access is required.
  - `iomem=relaxed` kernel parameter may need to be set at boot time (varies by distribution).  
    Example:  
    Edit `/etc/default/grub` and add `iomem=relaxed` to `GRUB_CMDLINE_LINUX`, then `update-grub` and reboot.
  - `memtemp.py` should be in the same directory as `gpuFire.py`.
  - `lspci` and `memtemp.py` dependencies must be satisfied.

## Usage

1. **Basic GPU monitoring (non-root):**
   ```bash
   python3 gpuFire.py
   ```
   By default, it updates every 1 second. You can adjust the interval with `--interval`:
   ```bash
   python3 gpuFire.py --interval 2
   ```

2. **Including GDDR6 memory temperatures (root required):**
   ```bash
   sudo python3 gpuFire.py --memtemp
   ```
   If you run it without root privileges and use `--memtemp`, you will get a message prompting you to run as root.

3. **Help:**
   ```bash
   python3 gpuFire.py --help
   ```

## Notes

- Running as root is required to access and map GPU memory addresses for reading GDDR6 temperatures.
- Ensure that `iomem=relaxed` is enabled if the script fails to map memory.
- The GDDR6 temperature matching to a specific GPU is based on assumptions and may require matching by PCI BDF in a more complex environment. For most setups, it should display correct temperatures if compatible GPUs are detected.
![image](https://github.com/user-attachments/assets/39b22f2e-eb05-463f-92dc-a75f162f3781)

## License

This project is licensed under the **MIT License**.  
See the full license text in the [LICENSE](https://github.com/Nondzu/gpuFire/blob/master/LICENSE) file.  
