"""Sample committed address-space regions in a running x64 VIctory process."""
import argparse
import csv
import ctypes as c
from ctypes import wintypes as w
from collections import Counter
from pathlib import Path
import time


class Region(c.Structure):
    _fields_ = [("base", c.c_void_p), ("allocation", c.c_void_p), ("initial", w.DWORD),
                ("partition", w.WORD), ("length", c.c_size_t), ("state", w.DWORD),
                ("protection", w.DWORD), ("kind", w.DWORD)]


PRIVATE_GROUPS = ("console_private", "host_fd0000", "host_4m", "host_writecombine",
                  "host_other_large", "host_other_small")


def committed(query, handle):
    region = Region()
    totals, allocations = Counter(), Counter()
    extents, special = Counter(), Counter()
    address = 0
    while query(handle, address, c.byref(region), c.sizeof(region)):
        end = (region.base or 0) + region.length
        if end <= address:
            raise RuntimeError("Region walk stopped advancing")
        if region.allocation:
            extents[region.allocation] += region.length
        if region.state == 0x1000:
            totals[region.kind] += region.length
            if region.kind == 0x20000:
                allocations[region.allocation] += region.length
                if region.protection & 0x400:
                    special[region.allocation] += region.length
        address = end
    if c.get_last_error() != 87:
        raise c.WinError(c.get_last_error())
    groups, writecombine_sizes = Counter(), Counter()
    for base, size in allocations.items():
        extent = extents[base]
        if base < 1 << 40:
            groups["console_private"] += size
        elif extent == 0xfd0000:
            groups["host_fd0000"] += size
        elif extent == 4 << 20:
            groups["host_4m"] += size
        else:
            groups["host_writecombine"] += special[base]
            if special[base]:
                writecombine_sizes[extent] += special[base]
            group = "host_other_large" if extent >= 1 << 20 else "host_other_small"
            groups[group] += size - special[base]
    if sum(groups.values()) != totals[0x20000]:
        raise ValueError("Private region totals disagree")
    return totals, allocations, groups, writecombine_sizes


def run(pid, expected, output, seconds, period, size_output=None):
    if c.sizeof(Region) != 48 or expected.name.lower() != "victory.exe":
        raise ValueError("Expected a 64-bit VIctory executable")
    k = c.WinDLL("kernel32", use_last_error=True)
    k.OpenProcess.argtypes, k.OpenProcess.restype = [w.DWORD, w.BOOL, w.DWORD], w.HANDLE
    k.CloseHandle.argtypes = [w.HANDLE]
    k.QueryFullProcessImageNameW.argtypes = [w.HANDLE, w.DWORD, w.LPWSTR, c.POINTER(w.DWORD)]
    k.VirtualQueryEx.argtypes = [w.HANDLE, c.c_void_p, c.POINTER(Region), c.c_size_t]
    k.VirtualQueryEx.restype = c.c_size_t
    k.GetExitCodeProcess.argtypes = [w.HANDLE, c.POINTER(w.DWORD)]
    handle = k.OpenProcess(0x0400, False, pid)
    if not handle:
        raise c.WinError(c.get_last_error())
    try:
        name = c.create_unicode_buffer(32768)
        size = w.DWORD(len(name))
        if not k.QueryFullProcessImageNameW(handle, 0, name, c.byref(size)) or Path(name.value).resolve() != expected.resolve():
            raise ValueError("Unexpected process image")
        start = time.monotonic()
        first = None
        size_rows = []
        with output.open("x", encoding="utf8", newline="") as f:
            out = csv.writer(f, lineterminator="\n")
            out.writerow(("utc_us", "elapsed_s", "scan_ms", "private_bytes", "mapped_bytes", "image_bytes",
                          "private_allocation_bases", "added_bases_bytes", "removed_bases_bytes", "persistent_bases_net_bytes",
                          *PRIVATE_GROUPS))
            for offset in range(0, seconds + 1, period):
                time.sleep(max(0, start + offset - time.monotonic()))
                scan = time.monotonic()
                stamp = time.time_ns() // 1000
                state = w.DWORD()
                if not k.GetExitCodeProcess(handle, c.byref(state)) or state.value != 259:
                    raise RuntimeError("Renderer ended before the next sample")
                totals, now, groups, sizes = committed(k.VirtualQueryEx, handle)
                if size_output:
                    size_rows.extend((stamp, extent, count) for extent, count in sorted(sizes.items()))
                if first is None:
                    first = now
                added = sum(now[key] for key in now.keys() - first.keys())
                removed = sum(first[key] for key in first.keys() - now.keys())
                persistent = sum(now[key] - first[key] for key in now.keys() & first.keys())
                out.writerow((stamp, round(scan - start, 3), round((time.monotonic() - scan) * 1000, 2),
                              totals[0x20000], totals[0x40000], totals[0x1000000], len(now), added, removed, persistent,
                              *(groups[key] for key in PRIVATE_GROUPS)))
                f.flush()
        if size_output:
            with size_output.open("x", encoding="utf8", newline="") as f:
                out = csv.writer(f, lineterminator="\n")
                out.writerow(("utc_us", "allocation_extent_bytes", "committed_writecombined_bytes"))
                out.writerows(size_rows)
    finally:
        k.CloseHandle(handle)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pid", type=int)
    parser.add_argument("executable", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--seconds", type=int, default=180)
    parser.add_argument("--period", type=int, default=30)
    parser.add_argument("--size-output", type=Path)
    args = parser.parse_args()
    if args.seconds < 0 or args.period <= 0 or args.seconds % args.period:
        parser.error("Duration must be a nonnegative multiple of a positive period")
    run(args.pid, args.executable, args.output, args.seconds, args.period, args.size_output)
