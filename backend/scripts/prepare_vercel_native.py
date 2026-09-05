"""Preserve Xberg's ONNX runtime in Vercel's optimized function bundle."""

import shutil
import sys
from importlib.metadata import distribution
from pathlib import Path


def main() -> None:
    if sys.platform != "linux":
        return

    site_packages = Path(distribution("xberg").locate_file(""))
    candidates = sorted((site_packages / "xberg").glob("libonnxruntime*.so*"))
    if not candidates:
        candidates = sorted((site_packages / "xberg.libs").glob("libonnxruntime*.so*"))
    if not candidates:
        raise RuntimeError("The installed Linux Xberg wheel has no ONNX runtime library")

    target = Path("app/_native/libonnxruntime.bin")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(candidates[0], target)


if __name__ == "__main__":
    main()
