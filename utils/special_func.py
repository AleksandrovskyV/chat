import os

import subprocess
import time
import pyautogui
import pygetwindow as gw
import ctypes
import win32gui
import win32con
import mouse
import pyperclip
import re
from datetime import datetime

from collections import defaultdict



def launch_app(name):
    app_map = {
        'notepad': ['notepad.exe', 'блокнот.exe'],
        'cmd': ['cmd.exe', 'командная строка.exe'],
        'explorer': ['explorer.exe', 'проводник.exe'],
        'sublime': [
            r'C:\Program Files\Sublime Text\sublime_text.exe',
            r'C:\Program Files (x86)\Sublime Text\sublime_text.exe',
            'subl.exe'
        ],
        'paint': ['mspaint.exe', 'paint.exe'],
    }

    variants = app_map.get(name.lower())
    if not variants:
        print(f"[ERROR] Неизвестное приложение: {name}")
        return

    for variant in variants:
        try:
            if os.path.isfile(variant) or os.path.splitext(variant)[1] == '.exe':
                subprocess.Popen([variant])
                print(f"[OK] Запущено: {variant}")
                return
            else:
                # Попробуем вызвать из PATH
                subprocess.Popen([variant])
                print(f"[OK] Запущено из PATH: {variant}")
                return
        except FileNotFoundError:
            continue

    print(f"[FAIL] Не удалось найти или запустить: {name}")


def kill_apps(source_cmd):
    name = source_cmd.lower().rstrip('s')  # убираем 's' на конце, если есть

    app_map = {
        'notepad': ['notepad.exe', 'блокнот.exe'],
        'cmd': ['cmd.exe', 'командная строка.exe'],
        'explorer': ['explorer.exe', 'проводник.exe'],
        'sublime': [
            'sublime_text.exe',
            'subl.exe'
        ],
        'paint': ['mspaint.exe', 'paint.exe'],
    }

    variants = app_map.get(name)

    if not variants:
        print(f"[ERROR] Неизвестное приложение: {name}")
        return

    killed_any = False
    for variant in variants:
        try:
            # Проверяем, не путь ли это, а просто имя процесса
            exe_name = os.path.basename(variant)
            subprocess.run(["taskkill", "/f", "/im", exe_name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            killed_any = True
        except Exception as e:
            continue

    if killed_any:
        print(f"[OK] Завершены процессы для: {name}")
    else:
        print(f"[FAIL] Не удалось завершить процессы: {name}")


#Generate_UniqNames

def gen_date_id(name="pic", folder=None):
    """
    folder — полный путь к папке (например, resource_path('./files'))
    Возвращает имя файла с уникальным номером, например pic_250726_3.jpg
    """
    if folder is None:
        raise ValueError("Папка должна быть указана")

    date_str = datetime.now().strftime("%y%m%d")  # YYMMDD
    base_name = f"{name}_{date_str}"

    os.makedirs(folder, exist_ok=True)

    for i in range(1, 1000):
        filename = f"{base_name}_{i}.jpg"
        full_path = os.path.join(folder, filename)
        if not os.path.exists(full_path):
            return filename  # возвращаем только имя файла

    return f"{base_name}_999.jpg"  # последний вариант


# Make Tree Folder 

def check_isSequence(path):
    """
    Ищет группы файлов с одинаковым именем и числовыми суффиксами.
    Возвращает словарь: (base_name, ext) -> (list файлов, длина чисел)
    """
    pattern = re.compile(r"^(.*?)(\d+)\.(\w+)$", re.IGNORECASE)
    sequences = {}

    try:
        for fname in os.listdir(path):
            match = pattern.match(fname)
            if match:
                base, num, ext = match.groups()
                key = (base, ext)
                if key not in sequences:
                    sequences[key] = {"files": [], "num_len": len(num)}
                sequences[key]["files"].append(fname)
    except Exception:
        return {}

    # Оставляем только те, где более одного файла
    return {
        k: v for k, v in sequences.items()
        if len(v["files"]) >= 2
    }

def get_FolderTree(path, max_depth=2, prefix="", is_root=True):
    if max_depth < 0:
        return ""

    try:
        entries = sorted(os.listdir(path))
    except PermissionError:
        return ""

    result = ""

    if is_root:
        root_name = os.path.basename(os.path.normpath(path)) or path
        result += root_name + "\\\n"

    sequences = check_isSequence(path)
    used_files = set(f for seq in sequences.values() for f in seq["files"])

    entries_to_show = []
    for entry in sorted(os.listdir(path)):
        full_path = os.path.join(path, entry)
        if os.path.isfile(full_path) and entry in used_files:
            continue
        entries_to_show.append(entry)

    total_items = len(entries_to_show) + len(sequences)

    for idx, entry in enumerate(entries_to_show):
        full_path = os.path.join(path, entry)
        is_last = idx == total_items - 1
        connector = "└─ " if is_last else "├─ "

        if os.path.isdir(full_path):
            display_name = entry + "\\"
            result += prefix + connector + display_name + "\n"
            extension = "    " if is_last else "│   "
            result += get_FolderTree(full_path, max_depth - 1, prefix + extension, is_root=False)
        else:
            result += prefix + connector + entry + "\n"

    # Добавляем секвенции как отдельные строки
    for seq_idx, ((base, ext), data) in enumerate(sequences.items()):
        is_last = (len(entries_to_show) + seq_idx) == total_items - 1
        connector = "└─ " if is_last else "├─ "
        hashes = "#" * data["num_len"]
        display = f"{base}{hashes}.{ext} [SEQ!]"
        result += prefix + connector + display + "\n"

    return result


# Text Formating

def remove_brack_cmd(self, text):
    result = ""
    while "[code]" in text and "[/code]" in text:
        before, rest = text.split("[code]", 1)
        code_content, after = rest.split("[/code]", 1)
        result += before.rstrip('\n') + "\n"
        indented_code = "\n".join(line for line in code_content.splitlines())
        result += indented_code + "\n"
        text = after
    result += text
    return result


# Calculator


def lerp(start, end, t):
    return start + (end - start) * t

def distance(p1, p2):
    return ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2) ** 0.5

class CalculatorAutomation:
    def __init__(self, expression: str, type_delay: float = 0.1, final_pos=(500, 200)):
        self.expression = expression
        self.type_delay = type_delay
        self.final_x, self.final_y = final_pos
        self.hwnd = None

    def _find_calc_window(self):
        for w in gw.getAllWindows():
            title = w.title.lower()
            try:
                visible = w.isVisible()
            except AttributeError:
                visible = True
            if ("калькулятор" in title or "calculator" in title) and visible:
                return w
        return None

    def open_or_activate_calculator(self):
        calc_window = self._find_calc_window()

        if not calc_window:
            subprocess.Popen("calc.exe")
            timeout = 3
            start = time.time()
            while not calc_window and time.time() - start < timeout:
                time.sleep(0.3)
                calc_window = self._find_calc_window()

        if not calc_window:
            raise RuntimeError("Не удалось найти окно калькулятора после запуска.")

        self.hwnd = calc_window._hWnd

        # Показать и активировать окно
        win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
        ctypes.windll.user32.SetForegroundWindow(self.hwnd)

        # Ждём, пока окно действительно станет активным
        timeout = 1.5
        start = time.time()
        while win32gui.GetForegroundWindow() != self.hwnd and time.time() - start < timeout:
            time.sleep(0.2)

        # Финальная проверка, что активное окно — калькулятор
        fg_hwnd = win32gui.GetForegroundWindow()
        active_title = win32gui.GetWindowText(fg_hwnd).lower()
        if "калькулятор" not in active_title and "calculator" not in active_title:
            raise RuntimeError("Активное окно — не калькулятор. Ввод отменён.")

        return calc_window


    def get_result_from_calculator(self):
        # Курсор уже на поле результата
        time.sleep(0.7)  # ждём, чтобы калькулятор успел показать результат
        # Выделяем всё (Ctrl+A) и копируем (Ctrl+C)
        #pyautogui.hotkey('ctrl', 'a')
        # time.sleep(0.1)
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.2)  # ждем, пока буфер обновится
        result = pyperclip.paste()

        if re.fullmatch(r"[0-9\s\+\-\*\/=]+", result):
            pass
        else:
            result = "..."

        return result.strip()


    def move_window_lerp(self, window, start_pos, end_pos, duration=2.2, steps=120):
        x0, y0 = start_pos
        x1, y1 = end_pos
        width = window.width
        height = window.height

        for i in range(steps + 1):
            t = i / steps
            x = int(lerp(x0, x1+25, t))
            y = int(lerp(y0, y1, t))
            win32gui.MoveWindow(self.hwnd, x, y, width, height, True)
            ctypes.windll.user32.SetCursorPos(x + 30, y + 20)  # смещение курсора аналогично начальному offset
            time.sleep(duration / steps)

        return True  # Возврат результата для проверки


    def automate(self):
        calc_window = self.open_or_activate_calculator()
        rect = win32gui.GetWindowRect(self.hwnd)
        start_pos = (rect[0], rect[1])
        end_pos = (self.final_x, self.final_y)
        result = None

        # Проверяем расстояние между текущей и конечной позицией
        if distance(start_pos, end_pos) > 5:  # если больше 5 пикселей, анимируем
            moved = self.move_window_lerp(calc_window, start_pos, end_pos, duration=0.5, steps=30)
            if moved:
                self.run_Print()
                result = self.get_result_from_calculator()
        else:
            # Просто перемещаем сразу без анимации
            width = calc_window.width
            height = calc_window.height
            win32gui.MoveWindow(self.hwnd, end_pos[0], end_pos[1], width, height, True)
            # ctypes.windll.user32.SetCursorPos(end_pos[0] + 30, end_pos[1] + 20)
            self.run_Print()
            result = self.get_result_from_calculator()

        ctypes.windll.user32.SetForegroundWindow(self.hwnd)


        
        return result


    def run_Print(self):
        # Очистка и ввод
        time.sleep(.3)
        pyautogui.press('backspace')
        for char in self.expression:
            if char == ' ':
                continue
            elif char == '*':
                pyautogui.press('multiply')
            elif char == '/':
                pyautogui.press('divide')
            elif char == '+':
                pyautogui.press('add')
            elif char == '-':
                pyautogui.press('subtract')
            elif char == '=':
                pyautogui.press('enter')
            elif char.isdigit():
                pyautogui.press(char)
            else:
                print(f"⚠️ Неподдерживаемый символ: {char}")
            time.sleep(self.type_delay)


# testing

#calc = CalculatorAutomation("12+7*3=", type_delay=0.3)
#calc.open_calculator()