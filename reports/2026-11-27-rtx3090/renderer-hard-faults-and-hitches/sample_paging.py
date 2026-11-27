"""Sample system paging and the game and paging disks during one live session."""
import csv
import ctypes
import sys
import time
from ctypes import wintypes


class Value(ctypes.Structure):
    _fields_ = [("status", wintypes.DWORD), ("number", ctypes.c_double)]


pdh = ctypes.WinDLL("pdh")
handle = ctypes.c_void_p
pdh.PdhOpenQueryW.argtypes = [wintypes.LPCWSTR, ctypes.c_size_t, ctypes.POINTER(handle)]
pdh.PdhAddEnglishCounterW.argtypes = [handle, wintypes.LPCWSTR, ctypes.c_size_t, ctypes.POINTER(handle)]
pdh.PdhCollectQueryData.argtypes = [handle]
pdh.PdhGetFormattedCounterValue.argtypes = [handle, wintypes.DWORD, ctypes.c_void_p, ctypes.POINTER(Value)]
pdh.PdhCloseQuery.argtypes = [handle]


def check(status):
    if status:
        raise OSError(f"Performance counter error 0x{status & 0xffffffff:08x}")


def sample(path, seconds):
    query = handle()
    check(pdh.PdhOpenQueryW(None, 0, ctypes.byref(query)))
    try:
        counters = {}
        paths = {
            "paging_disk_read_bytes_s": r"\PhysicalDisk(1 E:)\Disk Read Bytes/sec",
            "paging_disk_write_bytes_s": r"\PhysicalDisk(1 E:)\Disk Write Bytes/sec",
            "paging_disk_read_latency_s": r"\PhysicalDisk(1 E:)\Avg. Disk sec/Read",
            "game_disk_read_bytes_s": r"\PhysicalDisk(2 D:)\Disk Read Bytes/sec",
            "system_pages_in_s": r"\Memory\Pages Input/sec",
            "system_pages_out_s": r"\Memory\Pages Output/sec",
            "available_physical_mib": r"\Memory\Available MBytes",
        }
        for name, counter_path in paths.items():
            counter = handle()
            check(pdh.PdhAddEnglishCounterW(query, counter_path, 0, ctypes.byref(counter)))
            counters[name] = counter
        check(pdh.PdhCollectQueryData(query))
        with open(path, "x", newline="", encoding="utf8") as out:
            writer = csv.writer(out, lineterminator="\n")
            writer.writerow(["utc_s", *counters])
            start = time.monotonic()
            for second in range(1, seconds + 1):
                time.sleep(max(0, start + second - time.monotonic()))
                check(pdh.PdhCollectQueryData(query))
                row = [round(time.time(), 3)]
                for counter in counters.values():
                    value = Value()
                    check(pdh.PdhGetFormattedCounterValue(counter, 0x200, None, ctypes.byref(value)))
                    row.append(round(value.number, 6) if value.status in (0, 1) else "")
                writer.writerow(row)
                out.flush()
    finally:
        pdh.PdhCloseQuery(query)


if __name__ == "__main__":
    sample(sys.argv[1], int(sys.argv[2]))
