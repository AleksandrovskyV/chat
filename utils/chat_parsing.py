import os, random, json,sys
from PySide6.QtWidgets import QWidget,QMessageBox
from datetime import datetime
from dateutil import parser  # pip install python-dateutil
import string

_base_printed = False

# Режимы сборки
MPS = "MPS" # распаковка и чтения из-MePass
EXE = "EXE" # распаковка рядом с EXE
CST = "CST"
UNF = "UNF"  # новый режим: запуск без упаковки (unfrozen)

# Определяем начальный режим
CollectFlag = UNF if not getattr(sys, 'frozen', False) else MPS

def resource_path(relative_path: str) -> str:
    global _base_printed

    if CollectFlag == UNF:
        base = os.path.dirname(os.path.abspath(__file__))
    elif CollectFlag == MPS:
        base = sys._MEIPASS
    elif CollectFlag == EXE:
        base = os.path.dirname(sys.executable)
    elif CollectFlag == CST:
        base = os.path.join(tempfile.gettempdir(), CustomTempName)
    else:
        raise ValueError(f"Unknown CollectFlag: {CollectFlag}")

    if not _base_printed:
        print(f"Грузится из папки: {base}")
        _base_printed = True

    return os.path.join(base, relative_path)

def safe_parent(parent):
    return parent if isinstance(parent, QWidget) else None

def generate_dialog_pairs(file_path, parent=None, mode="custom_mode", spt_name=""):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = data["messages"]
    pairs = []

    if mode == "custom_mode":
        prev = None
        for msg in messages:
            if msg["type"] != "message":
                continue
            sender = msg.get("from")
            text = msg.get("text", "")
            if isinstance(text, list):
                text = "".join(t["text"] if isinstance(t, dict) else t for t in text)

            if prev and sender == spt_name:
                q = prev.get("text", "")
                if isinstance(q, list):
                    q = "".join(t["text"] if isinstance(t, dict) else t for t in q)
                pairs.append({"prompt": q.strip(), "response": text.strip()})

            prev = msg

        with open("dialog_pairs.jsonl", "w", encoding="utf-8") as f:
            for pair in pairs:
                f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    if mode == "extend_mode":
        senders = []
        for msg in messages:
            if msg["type"] == "message":
                sender = msg.get("from")
                if sender and sender not in senders:
                    senders.append(sender)
                    if len(senders) == 2:
                        break

        if len(senders) < 2:
            QMessageBox.warning(parent, "Недостаточно данных", "Нужно минимум два разных отправителя.")
            return

        sender_a, sender_b = senders

        MAX_SERIES_LEN = 5
        MAX_TIME_DIFF_SECONDS = 300  # 5 минут

        def parse_time(ts):
            try:
                return parser.isoparse(ts)
            except Exception:
                return None

        n = len(messages)

        def get_next_series(start_idx):
            if start_idx >= n:
                return None, None, None, None, None

            sender = messages[start_idx].get("from")
            series_texts = []
            series_start_time = None
            series_end_time = None
            count = 0
            idx = start_idx

            while idx < n and messages[idx].get("from") == sender and count < MAX_SERIES_LEN:
                msg = messages[idx]
                if msg["type"] != "message":
                    idx += 1
                    continue

                text = msg.get("text", "")
                if isinstance(text, list):
                    text = "".join(t["text"] if isinstance(t, dict) else t for t in text)
                text = text.strip()
                series_texts.append(text)

                ts = parse_time(msg.get("date", ""))
                if ts:
                    if not series_start_time:
                        series_start_time = ts
                    series_end_time = ts

                idx += 1
                count += 1

            series_text = " ".join(series_texts).strip()

            import string
            if series_text and series_text[-1] not in string.punctuation:
                series_text += "._"

            return sender, series_text, series_start_time, series_end_time, idx

        idx = 0
        prev_series = None

        # Разделяем пары по направлениям (sender_a -> sender_b и sender_b -> sender_a)
        gsk_pairs = []
        spt_pairs = []

        while idx < n:
            sender, text, start_time, end_time, next_idx = get_next_series(idx)
            if sender is None:
                break

            if sender not in (sender_a, sender_b):
                idx = next_idx
                continue

            if prev_series is None:
                prev_series = (sender, text, start_time, end_time)
            else:
                prev_sender, prev_text, prev_start, prev_end = prev_series
                if sender != prev_sender:
                    if prev_end and start_time:
                        delta = (start_time - prev_end).total_seconds()
                    else:
                        delta = None

                    if delta is not None and delta <= MAX_TIME_DIFF_SECONDS:
                        # Формируем пару
                        if prev_sender == sender_a and sender == sender_b:
                            gsk_pairs.append({"prompt": prev_text, "response": text})
                        elif prev_sender == sender_b and sender == sender_a:
                            spt_pairs.append({"prompt": prev_text, "response": text})
                        prev_series = (sender, text, start_time, end_time)
                    else:
                        prev_series = (sender, text, start_time, end_time)
                else:
                    # Тот же отправитель подряд — расширяем серию
                    prev_series = (
                        sender,
                        prev_text + " " + text,
                        prev_start,
                        end_time or prev_end,
                    )

            idx = next_idx

        # Пути вывода - как в auto_mode
        output_files = {
            resource_path("data/gsk_dialog_pairs.jsonl"): gsk_pairs,
            resource_path("data/spt_dialog_pairs.jsonl"): spt_pairs
        }

        existing_paths = [path for path in output_files if os.path.exists(path)]
        if existing_paths:
            file_list = "\n".join(os.path.basename(p) for p in existing_paths)
            reply = QMessageBox.question(
                safe_parent(parent),
                "Подтверждение перезаписи",
                f"Данные будут перезаписаны. Продолжить?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        for path, content in output_files.items():
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                for pair in content:
                    f.write(json.dumps(pair, ensure_ascii=False) + "\n")

        QMessageBox.information(
            safe_parent(parent),
            "Готово",
            f"Найдено пар GSK: {len(gsk_pairs)}, SPT: {len(spt_pairs)}"
        )

        return True

    elif mode == "auto_mode":
        # 1. Найти двух разных отправителей
        senders = []
        for msg in messages:
            if msg["type"] == "message":
                sender = msg.get("from")
                if sender and sender not in senders:
                    senders.append(sender)
                    if len(senders) == 2:
                        break

        if len(senders) < 2:
            QMessageBox.warning(parent, "Недостаточно данных", "Нужно минимум два разных отправителя.")
            return

        # 2. Перемешать их случайным образом
        random.shuffle(senders)
        sender_a, sender_b = senders

        # 3. Собрать пары в обоих направлениях
        prev = None
        gsk_pairs = []  # A -> B
        spt_pairs = []  # B -> A

        for msg in messages:
            if msg["type"] != "message":
                continue
            sender = msg.get("from")
            text = msg.get("text", "")
            if isinstance(text, list):
                text = "".join(t["text"] if isinstance(t, dict) else t for t in text)

            if prev:
                prev_sender = prev.get("from")
                q = prev.get("text", "")
                if isinstance(q, list):
                    q = "".join(t["text"] if isinstance(t, dict) else t for t in q)

                if prev_sender == sender_a and sender == sender_b:
                    gsk_pairs.append({"prompt": q.strip(), "response": text.strip()})
                elif prev_sender == sender_b and sender == sender_a:
                    spt_pairs.append({"prompt": q.strip(), "response": text.strip()})

            prev = msg

        # 4. Подготовка и проверка на существование файлов
        output_files = {
            resource_path("data/gsk_dialog_pairs.jsonl"): gsk_pairs,
            resource_path("data/spt_dialog_pairs.jsonl"): spt_pairs
        }

        # ✅ Проверяем: есть ли уже существующие файлы
        existing_paths = [path for path in output_files if os.path.exists(path)]

        if existing_paths:
            file_list = "\n".join(os.path.basename(p) for p in existing_paths)
            reply = QMessageBox.question(
                safe_parent(parent),
                "Подтверждение перезаписи",
                f"Данные будут перезаписаны. Продолжить?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # 5. Сохраняем файлы
        for path, content in output_files.items():
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                for pair in content:
                    f.write(json.dumps(pair, ensure_ascii=False) + "\n")

        QMessageBox.information(
            safe_parent(parent),
            "^  V ^",
            "     ...:"
        )

        return True  # сигнал успешного завершения