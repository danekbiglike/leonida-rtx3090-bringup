"""Exercise the exact first-use diagnostic with concurrent calls and real tracing filters."""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path


def check(renderer, deps, rustc):
    code = (renderer / "crates/victory-gpu/src/list.rs").read_text(encoding="utf-8")
    begin = code.index("    INDIRECT.fetch_add(1,")
    end = code.index("\n}\n\n/// Indirect executions dropped", begin)
    body = code[begin:end]
    lock = "    let mut seen = SEEN.lock()"
    if body.count(lock) != 1:
        raise ValueError("The diagnostic lock changed; inspect this test")
    body = body.replace(lock, "    LOCKS.fetch_add(1, Ordering::Relaxed);\n" + lock)
    source = r"""
mod list {
    use std::sync::atomic::{AtomicUsize, Ordering};
    pub static INDIRECT: AtomicUsize = AtomicUsize::new(0);
    pub static LOCKS: AtomicUsize = AtomicUsize::new(0);
    pub fn dropped(signature: usize) {
        let (stride, args, max) = (12, [2u32], 1);
        let address = Some(4096u64);
        let count = std::ptr::null::<u8>();
        BODY
    }
}
fn main() {
    use std::sync::atomic::Ordering;
    tracing_subscriber::fmt()
        .with_env_filter(std::env::args().nth(1).unwrap())
        .with_ansi(false).without_time().init();
    std::thread::scope(|s| {
        for _ in 0..8 {
            s.spawn(|| for i in 0..200 { list::dropped(i % 2); });
        }
    });
    println!("calls={} locks={}", list::INDIRECT.load(Ordering::Relaxed), list::LOCKS.load(Ordering::Relaxed));
}
""".replace("        BODY", body)
    tracing, = deps.glob("libtracing-*.rlib")
    with tempfile.TemporaryDirectory() as folder:
        folder = Path(folder)
        src, exe = folder / "check.rs", folder / "check.exe"
        src.write_text(source, encoding="utf-8")
        errors = []
        for subscriber in sorted(deps.glob("libtracing_subscriber-*.rlib")):
            build = subprocess.run([rustc, "--edition=2024", "--crate-name", "victory_gpu",
                                    "-L", f"dependency={deps}", "--extern", f"tracing={tracing}",
                                    "--extern", f"tracing_subscriber={subscriber}", src, "-o", exe],
                                   capture_output=True, text=True)
            if build.returncode == 0:
                break
            errors.append(build.stderr)
        else:
            raise RuntimeError("Could not link the tracing fixture: " + "\n".join(errors))
        results = []
        for selection, locks, messages in (("warn,victory_gpu::host=info", 0, 0),
                                            ("warn,victory_gpu::list=info", 1600, 2)):
            run = subprocess.run([exe, selection], capture_output=True, text=True, check=True)
            if (f"calls=1600 locks={locks}" not in run.stdout.splitlines()
                    or run.stdout.count("indirect execution dropped (first time for this signature)") != messages):
                raise AssertionError(run.stdout + run.stderr)
            results.append(dict(filter=selection, recorded_drops=1600, lock_attempts=locks, messages=messages))
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("renderer", type=Path)
    parser.add_argument("deps", type=Path)
    parser.add_argument("rustc", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.write_text(json.dumps(check(args.renderer, args.deps, str(args.rustc)), indent=2) + "\n")
