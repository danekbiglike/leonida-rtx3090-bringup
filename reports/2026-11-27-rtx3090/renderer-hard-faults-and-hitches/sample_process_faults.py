"""Sample the specified renderer's Windows hard-fault count; retain only that PID."""
import csv
import ctypes as c
from ctypes import wintypes as wt
from pathlib import Path
import sys
import time


class UnicodeString(c.Structure):
    _fields_ = [("length", wt.USHORT), ("maximum", wt.USHORT), ("buffer", c.c_void_p)]


class ProcessPrefix(c.Structure):
    _fields_ = [("next", wt.ULONG), ("threads", wt.ULONG), ("private_working_set", c.c_int64),
                ("hard_faults", wt.ULONG), ("thread_high_watermark", wt.ULONG), ("cycles", c.c_uint64),
                ("created", c.c_int64), ("user_time", c.c_int64), ("kernel_time", c.c_int64),
                ("image", UnicodeString), ("base_priority", wt.LONG), ("pid", c.c_void_p)]


def sample(pid, output, seconds):
    if c.sizeof(c.c_void_p) != 8 or ProcessPrefix.pid.offset != 80 or ProcessPrefix.hard_faults.offset != 16:
        raise RuntimeError("Unexpected Windows process layout")
    query = c.WinDLL("ntdll").NtQuerySystemInformation
    query.argtypes = [wt.ULONG, c.c_void_p, wt.ULONG, c.POINTER(wt.ULONG)]
    query.restype = wt.LONG
    buf = c.create_string_buffer(1 << 20)
    created = None
    with output.open("x", encoding="utf8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["utc_us", "hard_faults", "cpu_cycles"])
        next_sample = time.monotonic()
        for _ in range(seconds+1):
            time.sleep(max(0, next_sample - time.monotonic()))
            next_sample += 1
            while True:
                length = wt.ULONG()
                status = query(5, buf, len(buf), c.byref(length))
                if status & 0xffffffff == 0xc0000004:
                    buf = c.create_string_buffer(max(length.value + 65536, len(buf)*2))
                    continue
                if status < 0:
                    raise RuntimeError(f"Process snapshot failed: {status & 0xffffffff:#x}")
                break
            stamp = time.time_ns()//1000
            offset = 0
            while offset + c.sizeof(ProcessPrefix) <= length.value:
                r = ProcessPrefix.from_buffer(buf, offset)
                if r.pid == pid:
                    if (created is not None and created != r.created) or not r.image.buffer or c.wstring_at(r.image.buffer, r.image.length//2).lower() != "victory.exe":
                        raise RuntimeError("Renderer identity changed")
                    created = r.created
                    writer.writerow([stamp, r.hard_faults, r.cycles])
                    f.flush()
                    break
                if not r.next:
                    raise RuntimeError("Renderer exited")
                offset += r.next


if __name__ == "__main__":
    sample(int(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]))
