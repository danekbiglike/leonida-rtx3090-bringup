"""Measure five no-input intervals on one Windows renderer and restore its original mask."""
import csv
import ctypes as c
from ctypes import wintypes as wt
import json
from pathlib import Path
import statistics
import sys
import time


class ProcessorInfo(c.Structure):
    _fields_ = [("mask", c.c_size_t), ("relationship", wt.DWORD), ("details", c.c_uint64 * 2)]


def run(pid, executable, trace, out):
    kernel = c.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes = [wt.DWORD, wt.BOOL, wt.DWORD]
    kernel.OpenProcess.restype = wt.HANDLE
    kernel.CloseHandle.argtypes = [wt.HANDLE]
    kernel.QueryFullProcessImageNameW.argtypes = [wt.HANDLE, wt.DWORD, wt.LPWSTR, c.POINTER(wt.DWORD)]
    kernel.GetProcessAffinityMask.argtypes = [wt.HANDLE, c.POINTER(c.c_size_t), c.POINTER(c.c_size_t)]
    kernel.SetProcessAffinityMask.argtypes = [wt.HANDLE, c.c_size_t]
    kernel.GetLogicalProcessorInformation.argtypes = [c.POINTER(ProcessorInfo), c.POINTER(wt.DWORD)]
    kernel.WaitForSingleObject.argtypes = [wt.HANDLE, wt.DWORD]
    def check(result):
        if not result:
            raise c.WinError(c.get_last_error())
    size = wt.DWORD()
    kernel.GetLogicalProcessorInformation(None, c.byref(size))
    records = (ProcessorInfo * (size.value // c.sizeof(ProcessorInfo)))()
    check(kernel.GetLogicalProcessorInformation(records, c.byref(size)))
    cores = [r.mask for r in records if r.relationship == 0]
    handle = kernel.OpenProcess(0x100000 | 0x1000 | 0x200, False, pid)
    check(handle)
    original, system = c.c_size_t(), c.c_size_t()
    phases = []
    try:
        name = c.create_unicode_buffer(32768)
        length = wt.DWORD(len(name))
        check(kernel.QueryFullProcessImageNameW(handle, 0, name, c.byref(length)))
        if Path(name.value).resolve() != executable.resolve() or executable.name.lower() != "victory.exe":
            raise ValueError("Unexpected renderer identity")
        check(kernel.GetProcessAffinityMask(handle, c.byref(original), c.byref(system)))
        physical = [mask & original.value for mask in cores]
        if len(physical) != 8 or any(mask.bit_count() != 2 for mask in physical):
            raise ValueError("Expected eight physical cores and sixteen allowed logical processors")
        one_per_core = sum(mask & -mask for mask in physical)
        out.mkdir(exist_ok=False)
        try:
            for profile, mask in [("all", original.value), ("one_per_core", one_per_core),
                                  ("all", original.value), ("one_per_core", one_per_core), ("all", original.value)]:
                check(kernel.SetProcessAffinityMask(handle, mask))
                if kernel.WaitForSingleObject(handle, 5000) != 258:
                    raise RuntimeError("Renderer stopped during warmup")
                start = time.time_ns() // 1000
                if kernel.WaitForSingleObject(handle, 30000) != 258:
                    raise RuntimeError("Renderer stopped during measurement")
                end = time.time_ns() // 1000
                phases.append(dict(profile=profile, mask=hex(mask), start_us=start, end_us=end))
        finally:
            if kernel.WaitForSingleObject(handle, 0) == 258:
                check(kernel.SetProcessAffinityMask(handle, original.value))
                final = c.c_size_t()
                check(kernel.GetProcessAffinityMask(handle, c.byref(final), c.byref(system)))
                if final.value != original.value:
                    raise RuntimeError("Restored affinity did not match")
            (out / "phases.json").write_text(json.dumps(phases, indent=2)+"\n", encoding="utf8")
    finally:
        kernel.CloseHandle(handle)
    summarize(trace, out)


def summarize(trace, out):
    phases = json.loads((out / "phases.json").read_text(encoding="utf8"))
    if len(phases) != 5:
        raise ValueError("Incomplete affinity sequence")
    deadline = time.monotonic() + 30
    while True:
        with (trace / "frame-times.csv").open() as f:
            frames = list(csv.DictReader(f))
        if frames and int(frames[-1]["utc_us"]) >= phases[-1]["end_us"]:
            break
        if time.monotonic() >= deadline:
            raise ValueError("Incomplete final present boundary")
        time.sleep(1)
    for phase in phases:
        start, end = phase["start_us"], phase["end_us"]
        hits = [r for r in frames if start <= int(r["utc_us"]) < end]
        if not hits:
            raise ValueError("No presents in interval")
        phase.update(presents=len(hits), fps=round(len(hits)*1e6/(end-start), 3),
                     median_draws=statistics.median(int(r["draw_calls"]) for r in hits),
                     median_interval_ms=statistics.median(int(r["present_interval_us"]) for r in hits)/1000)
    with (out / "results.csv").open("w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=list(phases[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(phases)
    print([(p["profile"], p["fps"]) for p in phases])


if __name__ == "__main__":
    run(int(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
