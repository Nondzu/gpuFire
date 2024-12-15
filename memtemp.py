# memtemp.py
# created by Nondzu
# gpuFire.py
# version 1.0.0
# last updated 2024-12-15
# github.com/nondzu/gpuFire
# check -> dopamine.blog

import os
import sys
import mmap
import struct
import time
import subprocess

class Device:
    def __init__(self, bar0=0, bus=0, dev=0, func=0, offset=0, dev_id=0, 
                 vram="", arch="", name=""):
        self.bar0 = bar0
        self.bus = bus
        self.dev = dev
        self.func = func
        self.offset = offset
        self.dev_id = dev_id
        self.vram = vram
        self.arch = arch
        self.name = name
        self.mapped_addr = None
        self.phys_addr = 0
        self.base_offset = 0

# Table of devices with their offsets, IDs, VRAM types, architectures, and names, 
# source github.com/olealgoritme/gddr6
dev_table = [
    Device(offset=0x0000E2A8, dev_id=0x2684, vram="GDDR6X", arch="AD102", name="RTX 4090"),
    Device(offset=0x0000E2A8, dev_id=0x2702, vram="GDDR6X", arch="AD103", name="RTX 4080 Super"),
    Device(offset=0x0000E2A8, dev_id=0x2704, vram="GDDR6X", arch="AD103", name="RTX 4080"),
    Device(offset=0x0000E2A8, dev_id=0x2705, vram="GDDR6X", arch="AD103", name="RTX 4070 Ti Super"),
    Device(offset=0x0000E2A8, dev_id=0x2782, vram="GDDR6X", arch="AD104", name="RTX 4070 Ti"),
    Device(offset=0x0000E2A8, dev_id=0x2783, vram="GDDR6X", arch="AD104", name="RTX 4070 Super"),
    Device(offset=0x0000E2A8, dev_id=0x2786, vram="GDDR6X", arch="AD104", name="RTX 4070"),
    Device(offset=0x0000E2A8, dev_id=0x2860, vram="GDDR6", arch="AD106", name="RTX 4070 Max-Q / Mobile"),
    Device(offset=0x0000E2A8, dev_id=0x2203, vram="GDDR6X", arch="GA102", name="RTX 3090 Ti"),
    Device(offset=0x0000E2A8, dev_id=0x2204, vram="GDDR6X", arch="GA102", name="RTX 3090"),
    Device(offset=0x0000E2A8, dev_id=0x2208, vram="GDDR6X", arch="GA102", name="RTX 3080 Ti"),
    Device(offset=0x0000E2A8, dev_id=0x2206, vram="GDDR6X", arch="GA102", name="RTX 3080"),
    Device(offset=0x0000E2A8, dev_id=0x2216, vram="GDDR6X", arch="GA102", name="RTX 3080 LHR"),
    Device(offset=0x0000EE50, dev_id=0x2484, vram="GDDR6", arch="GA104", name="RTX 3070"),
    Device(offset=0x0000EE50, dev_id=0x2488, vram="GDDR6", arch="GA104", name="RTX 3070 LHR"),
    Device(offset=0x0000E2A8, dev_id=0x2531, vram="GDDR6", arch="GA106", name="RTX A2000"),
    Device(offset=0x0000E2A8, dev_id=0x2571, vram="GDDR6", arch="GA106", name="RTX A2000"),
    Device(offset=0x0000E2A8, dev_id=0x2232, vram="GDDR6", arch="GA102", name="RTX A4500"),
    Device(offset=0x0000E2A8, dev_id=0x2231, vram="GDDR6", arch="GA102", name="RTX A5000"),
    Device(offset=0x0000E2A8, dev_id=0x26B1, vram="GDDR6", arch="AD102", name="RTX A6000"),
    Device(offset=0x0000E2A8, dev_id=0x27b8, vram="GDDR6", arch="AD104", name="L4"),
    Device(offset=0x0000E2A8, dev_id=0x26b9, vram="GDDR6", arch="AD102", name="L40S"),
    Device(offset=0x0000E2A8, dev_id=0x2236, vram="GDDR6", arch="GA102", name="A10"),
]

class GDDR6Context:
    def __init__(self):
        self.devices = []
        self.fd = -1
        self.page_size = os.sysconf("SC_PAGE_SIZE")

ctx = GDDR6Context()

def init():
    try:
        ctx.fd = os.open("/dev/mem", os.O_RDONLY)
    except OSError:
        return False
    return True

def cleanup():
    for d in ctx.devices:
        if d.mapped_addr is not None:
            d.mapped_addr.close()
    if ctx.fd != -1:
        os.close(ctx.fd)

def detect_compatible_gpus():
    try:
        output = subprocess.check_output(["lspci", "-nn", "-D"], universal_newlines=True)
    except subprocess.CalledProcessError:
        return 0

    devices_found = []
    for line in output.splitlines():
        parts = line.strip().split()
        if len(parts) < 3:
            continue
        bdf = parts[0]
        for p in parts:
            if p.startswith("[") and p.endswith("]"):
                vd = p.strip("[]").split(":")
                if len(vd) == 2:
                    vendor_hex = vd[0]
                    device_hex = vd[1]
                    try:
                        vendor_id = int(vendor_hex,16)
                        device_id = int(device_hex,16)
                    except ValueError:
                        continue
                    for entry in dev_table:
                        if entry.dev_id == device_id and vendor_id == 0x10de:
                            seg, bus, dev_func = bdf.split(":")
                            dev_hex, func_hex = dev_func.split(".")
                            b = int(bus,16)
                            d = int(dev_hex,16)
                            f = int(func_hex,16)

                            # get BAR0
                            try:
                                detail = subprocess.check_output(["lspci","-v","-s", bdf], universal_newlines=True)
                            except:
                                continue
                            bar0_addr = 0
                            for l in detail.splitlines():
                                if "Memory at" in l and "[size=" in l:
                                    mem_str = l.split()[2]
                                    mem_str = mem_str.split("(")[0]
                                    try:
                                        bar0_addr = int(mem_str,16)
                                        break
                                    except:
                                        pass
                            if bar0_addr == 0:
                                continue
                            new_dev = Device(bar0=bar0_addr, bus=b, dev=d, func=f,
                                             offset=entry.offset, dev_id=entry.dev_id,
                                             vram=entry.vram, arch=entry.arch, name=entry.name)
                            devices_found.append(new_dev)
    ctx.devices = devices_found
    return len(devices_found)

def memory_map():
    for d in ctx.devices:
        d.phys_addr = d.bar0 + d.offset
        d.base_offset = d.phys_addr & ~(ctx.page_size - 1)
        try:
            m = mmap.mmap(ctx.fd, ctx.page_size, mmap.MAP_SHARED, mmap.PROT_READ, offset=d.base_offset)
            d.mapped_addr = m
        except OSError:
            d.mapped_addr = None

def get_mem_temps():
    # returns list of GDDR6 temps for detected devices
    if not init():
        # cannot open /dev/mem
        return []
    n = detect_compatible_gpus()
    if n == 0:
        cleanup()
        return []
    memory_map()

    temps = []
    for d in ctx.devices:
        if d.mapped_addr is not None:
            addr_offset = d.phys_addr - d.base_offset
            d.mapped_addr.seek(addr_offset)
            data = d.mapped_addr.read(4)
            read_result = struct.unpack("<I", data)[0]
            temp = (read_result & 0x00000FFF) // 0x20
            temps.append(temp)
        else:
            temps.append(None)
    cleanup()
    return temps

if __name__ == "__main__":
    # if run directly, print detected temps
    if os.geteuid() != 0:
        print("Run as root to see GDDR6 temps.")
        sys.exit(1)
    temps = get_mem_temps()
    if temps:
        print("VRAM Temps:", temps)
    else:
        print("No compatible devices or access denied.")
