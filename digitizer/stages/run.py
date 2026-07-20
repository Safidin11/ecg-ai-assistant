"""Прогон пайплайна по этапам с сохранением debug-картинки каждого этапа.

Использование:
    python -m stages.run путь/к/фото.png [папка_вывода]

Каждый этап сохраняет своё изображение NN_имя.png в папку вывода — так можно
проверять и оценивать этапы по отдельности.
"""
from __future__ import annotations

import sys
from pathlib import Path

from stages import (
    s1_preprocess,
    s2_baseline_detection,
    s3_configuration,
    s4_vertical_anchors,
)
from stages.context import StageContext

# Порядок этапов: (модуль, порядковый номер для имени файла).
STAGES = [
    s1_preprocess,
    s2_baseline_detection,
    s3_configuration,
    s4_vertical_anchors,
]


def run_pipeline(image_path: str, out_dir: str) -> StageContext:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    ctx = StageContext(image_path=image_path)
    for i, stage in enumerate(STAGES, start=1):
        ctx = stage.run(ctx)
        img = stage.visualize(ctx)
        img.save(out / f"{i:02d}_{stage.NAME}.png")
    return ctx


def main() -> None:
    if len(sys.argv) < 2:
        print("Использование: python -m stages.run <фото> [папка_вывода]")
        raise SystemExit(1)
    image_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "debug"
    ctx = run_pipeline(image_path, out_dir)
    print("=== Лог этапов ===")
    for line in ctx.log:
        print(" ", line)
    print(f"\nDebug-картинки сохранены в: {out_dir}/")


if __name__ == "__main__":
    main()
