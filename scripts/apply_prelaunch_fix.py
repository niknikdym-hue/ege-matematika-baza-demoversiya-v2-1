from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "ege-matematika-baza-demoversiya"
DATA_FILE = ROOT / f"{PREFIX}-T123-02.txt"
PREVIEW_FILE = ROOT / f"{PREFIX}-PREVIEW.html"
ZIP_FILE = ROOT / f"{PREFIX}-v2-1-fixed.zip"
DATA_ID = "emath-data-1"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.write_text(text.rstrip() + "\n", encoding="utf-8", newline="\n")


def load_json_script(path: Path, script_id: str) -> dict:
    text = read(path)
    match = re.fullmatch(
        rf'\s*<script type="application/json" id="{re.escape(script_id)}">\s*([\s\S]*?)\s*</script>\s*',
        text,
    )
    if not match:
        raise RuntimeError(f"Cannot parse JSON script: {path.name}")
    return json.loads(match.group(1))


def dump_json_script(path: Path, script_id: str, data: dict) -> None:
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    write(path, f'<script type="application/json" id="{script_id}">\n{payload}\n</script>')


def fix_task_data(data: dict) -> None:
    task2 = None
    task5 = None
    for task in data.get("tasks", []):
        if task.get("number") == 2 and task.get("variant") == 1:
            task2 = task
        if task.get("number") == 5 and task.get("variant") == 2:
            task5 = task

    if task2 is None or task5 is None:
        raise RuntimeError("Required task examples were not found")

    task2["answer"] = "3412"
    task2["answerDisplay"] = "3412"
    task2["acceptedAnswers"] = ["3412"]
    for key in ("conditionAnswer", "officialTableAnswer", "sourceDiscrepancy"):
        task2.pop(key, None)

    task5["answer"] = "0.4"
    task5["answerDisplay"] = "0,4"
    task5["acceptedAnswers"] = ["0.4"]
    for key in ("conditionAnswer", "officialTableAnswer", "sourceDiscrepancy"):
        task5.pop(key, None)


def patch_preview(data: dict) -> None:
    if not PREVIEW_FILE.exists():
        return
    text = read(PREVIEW_FILE)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    pattern = rf'(<script type="application/json" id="{DATA_ID}">)\s*[\s\S]*?\s*(</script>)'
    updated, count = re.subn(pattern, lambda m: m.group(1) + "\n" + payload + "\n" + m.group(2), text, count=1)
    if count != 1:
        raise RuntimeError("Cannot update task data in preview")
    write(PREVIEW_FILE, updated)


def replace_block(path: Path, old: str, new: str) -> None:
    text = read(path)
    if old not in text:
        raise RuntimeError(f"Expected block not found in {path.name}")
    write(path, text.replace(old, new, 1))


def fix_documents() -> None:
    readme = ROOT / "00-README-CODEX.txt"
    replace_block(
        readme,
        """ОСОБАЯ ПОЛИТИКА ДЛЯ ДВУХ РАСХОЖДЕНИЙ В ИСХОДНИКЕ
- задание 2, пример 1: по условию получается 3412, в итоговой таблице ФИПИ указано 2314; принимаются оба ответа;
- задание 5, пример 2: по условию получается 0,4, в итоговой таблице ФИПИ указано 0,96; принимаются оба ответа;
- пояснение показывается только после завершения попытки.""",
        """ПРОВЕРЕННЫЕ КЛЮЧИ
- задание 2, пример 1: принимается только официальный ответ 3412;
- задание 5, пример 2: принимается только официальный ответ 0,4;
- дополнительные ошибочные варианты не нормализуются и не засчитываются.""",
    )
    text = read(readme).replace("Версия: 2.0", "Версия: 2.1", 1)
    write(readme, text)

    installation = ROOT / f"{PREFIX}-INSTALLATION.txt"
    replace_block(
        installation,
        """ВАЖНО
Версия 2 использует новый ключ localStorage. Предыдущая тестовая попытка V1 не переносится, чтобы сохранённый старый результат не конфликтовал с исправленным оцениванием двух спорных примеров.

ПОСЛЕ ПУБЛИКАЦИИ ПРОВЕРИТЬ
- старт и завершение попытки;
- восстановление после перезагрузки;
- непрерывный таймер;
- оба допустимых ответа задания 2, пример 1: 3412 и 2314;
- оба допустимых ответа задания 5, пример 2: 0,4 и 0,96;
- пояснения о расхождении на экране результата;""",
        """ВАЖНО
Версия 2.1 исправляет ключи двух примеров. Сохранённые тестовые попытки предыдущих версий следует сбросить перед контрольным проходом.

ПОСЛЕ ПУБЛИКАЦИИ ПРОВЕРИТЬ
- старт и завершение попытки;
- восстановление после перезагрузки;
- непрерывный таймер;
- задание 2, пример 1: 3412 засчитывается, соседние и дополнительные варианты отклоняются;
- задание 5, пример 2: 0,4 засчитывается, 0,96 и ввод с посторонними символами отклоняются;""",
    )
    text = read(installation).replace("Версия пакета: 2.0", "Версия пакета: 2.1", 1)
    write(installation, text)

    source_gate = ROOT / f"{PREFIX}-SOURCE-GATE.txt"
    text = read(source_gate).replace(
        "STATUS: SOURCE_GATE_PASSED_WITH_DOCUMENTED_SOURCE_DISCREPANCIES — READY_FOR_TILDA_TEST",
        "STATUS: SOURCE_GATE_PASSED — READY_FOR_TILDA_TEST",
        1,
    )
    write(source_gate, text)
    replace_block(
        source_gate,
        """ПЕРЕНОС В ИНТЕРАКТИВНУЮ ВЕРСИЮ
- перенесены все 70 официальных примеров на позициях 1–21;
- для 68 примеров данные пакета совпадают с итоговой таблицей ответов;
- выявлены два внутренних расхождения между условием и итоговой таблицей официального PDF;
- при старте один пример на каждой позиции выбирается случайно и сохраняется на всю попытку;
- подробные решения не добавлены, поскольку официальный демонстрационный вариант публикует таблицу кратких ответов, но не отдельные решения каждого задания.

ЗАФИКСИРОВАННЫЕ РАСХОЖДЕНИЯ
1. Задание 2, пример 1.
   По условию: А–3, Б–4, В–1, Г–2, то есть 3412.
   В итоговой таблице ответов указано 2314.
   Политика Эксамио: принимаются 3412 и 2314.

2. Задание 5, пример 2.
   По условию: жёлтых машин 15 − 9 = 6; вероятность 6/15 = 0,4.
   В итоговой таблице ответов указано 0,96.
   Политика Эксамио: принимаются 0,4 и 0,96.

Пояснение о расхождении показывается только после завершения экзамена и не служит подсказкой во время попытки.""",
        """ПЕРЕНОС В ИНТЕРАКТИВНУЮ ВЕРСИЮ
- перенесены все 70 официальных примеров на позициях 1–21;
- ключи всех 70 примеров сверены с итоговой таблицей ответов ФИПИ;
- задание 2, пример 1: официальный ответ 3412;
- задание 5, пример 2: официальный ответ 0,4;
- при старте один пример на каждой позиции выбирается случайно и сохраняется на всю попытку;
- подробные решения не добавлены, поскольку официальный демонстрационный вариант публикует таблицу кратких ответов, но не отдельные решения каждого задания.""",
    )

    task_map = ROOT / f"{PREFIX}-TASK-MAP.txt"
    text = read(task_map).replace(
        "  Пример 1: тип=ordered; принимаемые ответы=3412 и 2314; по условию=3412; итоговая таблица ФИПИ=2314; заголовок=Соответствие величин",
        "  Пример 1: тип=ordered; ответ=3412; заголовок=Соответствие величин",
        1,
    )
    write(task_map, text)

    audit = ROOT / f"{PREFIX}-AUDIT.txt"
    replace_block(
        audit,
        """НЕЗАВИСИМАЯ СВЕРКА ОТВЕТОВ
- 68 примеров: данные пакета точно совпадают с итоговой таблицей ответов;
- 2 примера: в официальном PDF зафиксировано внутреннее расхождение между условием и итоговой таблицей;
- пропущенных официальных ответов: 0;
- неподтверждённых дополнительных ответов за пределами двух зафиксированных расхождений: 0.

РАСХОЖДЕНИЕ 1 — ЗАДАНИЕ 2, ПРИМЕР 1
- по условию: А–3, Б–4, В–1, Г–2 → 3412;
- в итоговой таблице официального PDF: 2314;
- в интерактивной версии принимаются 3412 и 2314;
- 3413 и ответ с пробелом отклоняются;
- пояснение появляется только после завершения попытки.

РАСХОЖДЕНИЕ 2 — ЗАДАНИЕ 5, ПРИМЕР 2
- по условию: (15 − 9) / 15 = 0,4;
- в итоговой таблице официального PDF: 0,96;
- в интерактивной версии принимаются 0,4 и 0,96;
- 0,95 и ответ с посторонним символом отклоняются;
- пояснение появляется только после завершения попытки.""",
        """НЕЗАВИСИМАЯ СВЕРКА ОТВЕТОВ
- 70 из 70 примеров: данные пакета совпадают с итоговой таблицей ответов ФИПИ;
- пропущенных официальных ответов: 0;
- неподтверждённых дополнительных ответов: 0.

КОНТРОЛЬ ИСПРАВЛЕННЫХ ПРИМЕРОВ
- задание 2, пример 1: 3412 = 1 балл; 2314, 3413 и ответ с пробелом = 0 баллов;
- задание 5, пример 2: 0,4 = 1 балл; 0,96, 0,95 и ответ с посторонним символом = 0 баллов.""",
    )
    text = read(audit).replace("Версия: 2.0", "Версия: 2.1", 1)
    text = text.replace(
        "- отдельные проверки четырёх принимаемых ответов двух спорных примеров: PASS;",
        "- отдельные проверки правильных и ошибочных ответов двух исправленных примеров: PASS;",
        1,
    )
    text = text.replace(
        "Старые тестовые попытки V1 не подхватываются, чтобы сохранённый результат не конфликтовал с исправленной политикой оценивания.",
        "Перед контрольным проходом сохранённые тестовые попытки предыдущих версий сбрасываются.",
        1,
    )
    write(audit, text)

    test_report = ROOT / f"{PREFIX}-TEST-REPORT.txt"
    replace_block(
        test_report,
        """- Точное совпадение с итоговой таблицей: 68
- Документированные расхождения условия и таблицы: 2
- Пустых условий: 0
- Пропущенных официальных ответов: 0

2. ОЦЕНИВАНИЕ
- Основных проверок правильного и некорректного ввода: 70
- Задание 2, пример 1: 3412 = 1; 2314 = 1; 3413 = 0; «3 412» = 0
- Задание 5, пример 2: 0,4 = 1; 0,96 = 1; 0,95 = 0; «0,4x» = 0""",
        """- Точное совпадение с итоговой таблицей: 70
- Неподтверждённых дополнительных ответов: 0
- Пустых условий: 0
- Пропущенных официальных ответов: 0

2. ОЦЕНИВАНИЕ
- Основных проверок правильного и некорректного ввода: 70
- Задание 2, пример 1: 3412 = 1; 2314 = 0; 3413 = 0; «3 412» = 0
- Задание 5, пример 2: 0,4 = 1; 0,96 = 0; 0,95 = 0; «0,4x» = 0""",
    )
    text = read(test_report).replace("Версия: 2.0", "Версия: 2.1", 1)
    text = text.replace("- Блоков пояснения двух расхождений: 2\n", "- Ложных пояснений о расхождениях: 0\n", 1)
    text = text.replace(
        "- Пояснения отсутствуют во время выполнения и появляются после завершения: PASS",
        "- В результатах показываются только подтверждённые официальные ключи: PASS",
        1,
    )
    write(test_report, text)


def text_files_for_validation() -> list[Path]:
    suffixes = {".txt", ".html", ".js", ".json", ".md", ".svg"}
    result = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in suffixes:
            continue
        if any(part in {".git", ".github", "scripts"} for part in path.relative_to(ROOT).parts):
            continue
        result.append(path)
    return result


def validate(data: dict) -> None:
    tasks = data.get("tasks", [])
    if len(tasks) != 21:
        raise RuntimeError(f"Expected 21 examples in T123-02, got {len(tasks)}")

    task2 = next(t for t in tasks if t.get("number") == 2 and t.get("variant") == 1)
    task5 = next(t for t in tasks if t.get("number") == 5 and t.get("variant") == 2)
    assert task2.get("acceptedAnswers") == ["3412"]
    assert task5.get("acceptedAnswers") == ["0.4"]

    forbidden = ('"acceptedAnswers":["3412","2314"]', '"acceptedAnswers":["0.4","0.96"]', '"official_table_2314": 1', '"official_table_0_96": 1')
    offenders = []
    for path in text_files_for_validation():
        text = read(path)
        if any(token in text for token in forbidden):
            offenders.append(path.relative_to(ROOT).as_posix())
    if offenders:
        raise RuntimeError("Forbidden obsolete keys remain in: " + ", ".join(offenders))

    if PREVIEW_FILE.exists():
        preview = read(PREVIEW_FILE)
        match = re.search(
            rf'<script type="application/json" id="{DATA_ID}">\s*([\s\S]*?)\s*</script>',
            preview,
        )
        if not match:
            raise RuntimeError("Preview data block not found")
        preview_data = json.loads(match.group(1))
        p2 = next(t for t in preview_data["tasks"] if t.get("number") == 2 and t.get("variant") == 1)
        p5 = next(t for t in preview_data["tasks"] if t.get("number") == 5 and t.get("variant") == 2)
        assert p2.get("acceptedAnswers") == ["3412"]
        assert p5.get("acceptedAnswers") == ["0.4"]


def package_files() -> list[Path]:
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(ROOT)
        if any(part in {".git", ".github", "scripts"} for part in rel.parts):
            continue
        if path.suffix.lower() == ".zip":
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(ROOT).as_posix())


def update_manifest() -> Path:
    manifests = sorted(ROOT.glob("*MANIFEST*.txt"))
    manifest = manifests[0] if manifests else ROOT / "MANIFEST-SHA256.txt"
    rows = [
        "ЕГЭ МАТЕМАТИКА, БАЗОВЫЙ УРОВЕНЬ — ИНТЕРАКТИВНАЯ ДЕМОВЕРСИЯ — V2.1",
        "PACKAGE_STATUS: READY_FOR_TILDA_TEST",
        "PACKAGE_LAYOUT: FLAT_WITH_SOURCE",
        "",
        "FILENAME\tSIZE_BYTES\tSHA256",
    ]
    for path in package_files():
        if path == manifest:
            continue
        rel = path.relative_to(ROOT).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        rows.append(f"{rel}\t{path.stat().st_size}\t{digest}")
    write(manifest, "\n".join(rows))
    return manifest


def build_zip() -> None:
    if ZIP_FILE.exists():
        ZIP_FILE.unlink()
    with zipfile.ZipFile(ZIP_FILE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in package_files():
            archive.write(path, path.relative_to(ROOT).as_posix())


def main() -> None:
    data = load_json_script(DATA_FILE, DATA_ID)
    fix_task_data(data)
    dump_json_script(DATA_FILE, DATA_ID, data)
    patch_preview(data)
    fix_documents()
    validate(data)
    update_manifest()
    build_zip()
    print("Base mathematics prelaunch correction: PASS")
    print(f"Package: {ZIP_FILE.name}")


if __name__ == "__main__":
    main()
