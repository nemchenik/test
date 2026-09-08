#!/usr/bin/env python3
"""Batch 48: premium high-conversion choice cards."""

from pathlib import Path


base = Path(__file__).with_name("batch44_modern_minimal_video.py")
source = base.read_text(encoding="utf-8")

replacements = {
    "batch44": "batch48",
    "batch_44": "batch_48",
    "modern_minimal": "premium_choice",
    "8112": "8912",
    "#FFFFFF": "#F7F2E8",
    "#36454F": "#173C36",
    "#708090": "#B48745",
    "#D3D3D3": "#D9CCB5",
    "#F1F3F4": "#EEE7DA",
    "АРХИТЕКТУРНЫЙ ПРОЕКТ": "ПРЕМИАЛЬНАЯ ПОДБОРКА",
    "ОБЛИК ДОМА": "АРХИТЕКТУРА ДОМА",
    "КРАТКО О ПРОЕКТЕ": "ПРОЕКТ ДЛЯ ВАШЕЙ СЕМЬИ",
    "Дом {record.area} м²: архитектура без лишнего": "Дом {record.area} м² — оцените проект",
    "Проект №{record.project}: форма и функция": "Проект №{record.project}: продуманный выбор",
    "Планы, фасады и точные пропорции": "Откройте полный проект дома",
    "Планировка и пропорции": "Оцените сценарии жизни",
    "Фасады и геометрия дома": "Архитектура со всех сторон",
    "визуализация  •  планы  •  фасады": "откройте проект  •  сравните решения",
    "Архитектура без лишнего": "Продуманный дом для семьи",
    "Архитектура дома №{p} без лишнего": "Проект №{p}: премиальный обзор",
    "Современный дом №{p}: полный обзор": "Дом №{p}: полный обзор проекта",
    "Проект №{p} — планы и фасады": "Проект №{p}: откройте все детали",
    "Дом №{p}: визуализация и планы": "Дом №{p}: готовое решение",
    "Дом №{p}: планировка и пропорции": "Дом №{p}: пространство для жизни",
    "Проект №{p}: четыре фасада дома": "Проект №{p}: архитектура в деталях",
}

for old, new in replacements.items():
    if old not in source:
        raise RuntimeError(f"Не найден шаблон: {old}")
    source = source.replace(old, new)

namespace = {"__name__": "__main__", "__file__": str(Path(__file__).resolve())}
exec(compile(source, str(Path(__file__).with_name("batch48_premium_choice_runtime.py")), "exec"), namespace)
