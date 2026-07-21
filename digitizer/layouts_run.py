"""CLI-обёртка: оцифровать фото выбранным независимым пайплайном формата.

Использование:
    python layouts_run.py <формат: 12x1|3x4> <фото> <папка_вывода>

Печатает JSON с логом и сохраняет в папку_вывода:
  render.png  — заново отрисованная чистая ЭКГ
  signal.npy  — массив [12, N] в мВ
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

FORMATS = {
    "12x1": "layouts.format_12_1",
    "3x4": "layouts.format_3x4",
}


def main() -> None:
    if len(sys.argv) != 4:
        print(json.dumps({"error": "usage: layouts_run.py <format> <image> <out_dir>"}))
        raise SystemExit(1)

    fmt, image_path, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    if fmt not in FORMATS:
        print(json.dumps({"error": f"unknown format '{fmt}', available: {list(FORMATS)}"}))
        raise SystemExit(1)

    import importlib
    module = importlib.import_module(FORMATS[fmt])

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    result = module.run(image_path)

    np.save(out / "signal.npy", result.signals)

    from layouts.common.render import render
    render(result.signals, result.layout, result.speed, result.gain,
          result.sampling_rate, str(out / "render.png"))

    covered = int(np.count_nonzero(result.signals.any(axis=1)))
    print(json.dumps({
        "layout": result.layout,
        "shape": list(result.signals.shape),
        "leads_with_data": covered,
        "log": result.log,
    }))


if __name__ == "__main__":
    main()
