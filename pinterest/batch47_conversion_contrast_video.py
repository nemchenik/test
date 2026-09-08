#!/usr/bin/env python3
"""Batch 47: high-conversion contrast cards."""

from pathlib import Path


base = Path(__file__).with_name("batch44_modern_minimal_video.py")
source = base.read_text(encoding="utf-8")

replacements = {
    "batch44": "batch47",
    "batch_44": "batch_47",
    "modern_minimal": "conversion_contrast",
    "8112": "8712",
    "#FFFFFF": "#FFF9F1",
    "#36454F": "#14213D",
    "#708090": "#E76F51",
    "#D3D3D3": "#F2D6C7",
    "#F1F3F4": "#F8EDE3",
    "АРХИТЕКТУРНЫЙ ПРОЕКТ": "ВЫБЕРИТЕ СВОЙ ДОМ",
    "ОБЛИК ДОМА": "ГЛАВНЫЙ ВИД",
    "КРАТКО О ПРОЕКТЕ": "ВАЖНОЕ С ПЕРВОГО ВЗГЛЯДА",
    "Дом {record.area} м²: архитектура без лишнего": "Дом {record.area} м² — посмотрите внутри",
    "Проект №{record.project}: форма и функция": "Проект №{record.project}: ваш будущий дом",
    "Планы, фасады и точные пропорции": "Всё для уверенного выбора",
    "Планировка и пропорции": "Проверьте удобство планировки",
    "Фасады и геометрия дома": "Сравните все стороны дома",
    "визуализация  •  планы  •  фасады": "смотрите проект  •  сохраняйте идею",
    "Архитектура без лишнего": "Дом, который стоит рассмотреть",
    "Архитектура дома №{p} без лишнего": "Проект дома №{p}: смотрите детали",
    "Современный дом №{p}: полный обзор": "Дом №{p}: планировки и фасады",
    "Проект №{p} — планы и фасады": "Проект №{p}: выберите свой дом",
    "Дом №{p}: визуализация и планы": "Дом №{p}: быстрый обзор проекта",
    "Дом №{p}: планировка и пропорции": "Дом №{p}: удобно ли внутри?",
    "Проект №{p}: четыре фасада дома": "Проект №{p}: вид со всех сторон",
}

for old, new in replacements.items():
    if old not in source:
        raise RuntimeError(f"Не найден шаблон: {old}")
    source = source.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
exec(compile(source, str(Path(__file__).with_name("batch47_conversion_contrast_runtime.py")), "exec"), namespace)
