import sys, random, re, time

import ctypes, locale

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QObject, QEvent
from PySide6.QtGui import QFont
from PySide6.QtGui import QShortcut, QKeySequence,QKeyEvent


class SimpleEffect:
    def __init__(self, text):
        self.frames = [text]
        self.inputText = text  # добавь сюда для совместимости
    def get_frame(self, index):
        return self.frames[0]

    def frame_count(self):
        return 1

class TextSwitcher:
    """Эффектор для плавного переключения текста через последовательность фреймов"""
    def __init__(self, inputText, targetText, eraser='█', fillers='*', debug=False):

        self.debug = debug
        self.inputText = inputText
        self.targetText = targetText
        
        self.frames = []

        self.FILLER = fillers
        self.ERASER = eraser
        self.SPECIAL = "¶"   

        self.diff = 0;

        self._generate_maps()
        self._generate_frames()


    def refresh(self, inputText=None, targetText=None):
        """Перегенерирует последовательность анимации"""
        #print(f"[TextSwitcher][REFRESH] MAPS FOR NEXT SWAP: ")
        self.debug = False
        if inputText is not None:
            self.inputText = inputText
        if targetText is not None:
            self.targetText = targetText
        self.frames.clear()
        self._generate_maps()
        self._generate_frames()

    def get_frame(self, index):
        if not self.frames:
            return self.inputText
        return self.frames[min(index, len(self.frames) - 1)]

    def frame_count(self):
        return len(self.frames)

    def _generate_maps(self):
        input_chars = list(self.inputText)
        target_chars = list(self.targetText)
        self.diff = len(input_chars)-len(target_chars)

        # Инициализация карт
        if self.diff == 0:
            self.temp_map = input_chars[:]
            self.target_map = target_chars[:]
        elif self.diff > 0:
            self.temp_map = input_chars[:]
            self.target_map = target_chars[:]
            for _ in range(self.diff):
                idx = random.randint(0, len(self.target_map))
                self.target_map.insert(idx, self.ERASER)
        else:
            self.temp_map = input_chars[:]
            self.target_map = target_chars[:]
            for _ in range(-self.diff):
                idx = random.randint(0, len(self.temp_map))
                self.temp_map.insert(idx, self.SPECIAL)

        # Генерация индексной карты: случайная перестановка
        length = len(self.target_map) if self.diff >= 0 else len(self.temp_map)
        self.index_map = random.sample(list(range(length)), k=length)

        if self.debug:
            #print(f"[TextSwitcher] temp_map   = {self.temp_map}")
            #print(f"[TextSwitcher] target_map = {self.target_map}")
            #print(f"[TextSwitcher] index_map  = {self.index_map}")
            pass

    def _generate_frames(self):
        
        current = self.temp_map
        
        # Начальный кадр
        start_frame = self.inputText
        start_frame = start_frame.replace(self.SPECIAL, "")
        self.frames.append(start_frame) # Создаем фрейм

        self.flag = "S_FRAME"
        self.lenFRM = len(current)
        # Проходим по индексной карте
        if self.debug:
            #print(f"[TextSwitcher] frame0   |  current = {current}  |  FLAG = {self.flag}  |  OUT_FRAME: {self.frames[0]} ")
            print(f"[TextSwitcher][GEN] frame0   ||  OUT_FRAME: {self.frames[0]} ")

        if self.diff == 0:
            for pos in self.index_map:
                temp = current[:]                 # получаем текущий список
                temp[pos] = self.target_map[pos]  # Заменяем букву в temp на значение из index_map
                self.frames.append(''.join(temp)) # Создаем фрейм
                current = temp[:]                 # Пересохраняем current лист
        else:
            temp_spec = current[:]
            for pos in range(len(self.index_map)):
                pos_repl = self.index_map[pos]
                out_letter = self.target_map[pos_repl]
                indexVal = self.index_map[pos]
                if out_letter == self.ERASER:
                    self.flag = "DELETE "
                    # Создаём временный список без SPECIAL символов (чистим '¶')
                    temp = [c for c in current if c != self.SPECIAL]

                    # Вставляем ERASER на позицию pos\pos_repl
                    if pos_repl < len(temp):
                        temp[pos_repl] = self.ERASER
                    else:
                        temp.insert(pos_repl, self.ERASER)
                    self.frames.append(''.join(temp))

                    # Удаляем символ по pos_repl
                    temp_del = temp[:]
                    if pos_repl < len(temp_del):
                        del temp_del[pos_repl]
                    self.frames.append(''.join(temp_del))

                    # Вставляем SPECIAL вместо удалённого символа в current
                    temp_spec = current[:]  # ← сделай копию, а не ссылку
                    if pos_repl < len(temp_spec):
                        temp_spec[pos_repl] = self.SPECIAL
                    else:
                        temp_spec.append(self.SPECIAL)
                    current = temp_spec

                    temp = current
                    
                else:
                    temp_spec[pos_repl] = self.target_map[indexVal]   # обновляем текущий
                    current = temp_spec                               # сохраняем новое состояние

                    # формируем кадр уже из текущего состояния
                    temp_string = ''.join([c for c in current if c != self.SPECIAL])
                    temp_string = temp_string.lstrip()

                    self.frames.append(temp_string)
                    self.flag = "REPLACE"
  
                if self.debug:
                    out_str = ''.join([c for c in current if c != self.SPECIAL]).lstrip()
                    prntspace = ""
                    if pos<9:
                            prntspace = " "
                    #print(f"[TextSwitcher] frame{pos+1}{prntspace}  |  current = {current}  |  FLAG = {self.flag}  |  OUT_FRAME: {out_str}")



        final = ''.join(current).replace(self.SPECIAL, '')
        
        if not self.frames:
            self.frames.append(self.targetText)
        else:
            final_frame = ''.join(current).replace(self.SPECIAL, '')
            if final_frame != self.targetText:
                self.frames[-1] = self.targetText

        if final != self.targetText:
            pass

class TextAnimator:
    """
    Универсальный класс анимации:
    - mode='simple': сдвиг символов текста
    - mode='extend': анимация скобок, c хвостом и space
    :param inputText: строка для анимации (либо целиком, либо только скобка)
    :param dir: направление (0 = слева, 1 = справа)
    :param mode: 'simple' или 'extend'
    """

    def __init__(self, inputText, dir=0, mode='simple', placeholder='¶'):
        self.inputText = inputText
        self.dir = dir
        self.mode = mode
        self.PLACEHOLDER = placeholder
        self.fix = len(inputText)
        self.frames = []
        self._generate_frames()

    def _generate_frames(self):
        if self.mode == 'simple':
            self.frames = self._generate_simple(self.inputText)
        elif self.mode == 'extend':
            self.frames = self._generate_extend(self.inputText)
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

    def _generate_simple(self, text):
        n = len(text)
        group = ''.join(c for c in text if c != ' ')
        k = len(group)

        if k == 0:
            return [' ' * n]

        f = group[0]
        frames = []

        for shift in range(0, n + 1):
            frame = (' ' * shift + group)[:n].ljust(n)
            frames.append(frame)

        for i in range(1, k + 1):
            frame = (f * i).ljust(n)
            frames.append(frame)

        return frames

    def _generate_extend(self, text):

        placeholder = self.PLACEHOLDER
        fix = self.fix  # длина окна
        conv_text = text.replace(' ', placeholder)

        if self.dir == 0:
            # первый непробел и не ¶ / при "@Z¶" → '@'
            tail_char = next((c for c in text if c != ' '), placeholder)
        else:
            # последний непробел и не ¶ / при "¶Z@" → '@'
            tail_char = next((c for c in reversed(text) if c != ' '), placeholder)

        tail = tail_char        # хвост
        space = placeholder * 2 # расстоение между блоками

        if self.dir == 0:
            res_text = conv_text + space + tail + conv_text   # При "@Z¶" : "@Z¶¶¶@@Z¶" 
        else:
            res_text = conv_text + tail + space + conv_text   # При "¶Z@" : "¶Z@@¶¶¶Z@"

        frames = []
        if self.dir == 0:
            for i in reversed(range(len(res_text) - fix + 1)):
                frames.append(res_text[i:i+fix].replace(placeholder, ' '))  # удаляем placeholder и записываем кадр
        else:
            for i in range(len(res_text) - fix + 1):
                frames.append(res_text[i:i+fix].replace(placeholder, ' ')) # удаляем placeholder и записываем кадр

        return frames


    def frame_count(self):
        return len(self.frames)

    def get_frame(self, index):
        if not self.frames:
            return self.inputText
        return self.frames[index % len(self.frames)]

class GlitchEffect:
    def __init__(self, inputTextOrEffect, fix=3, letter_n=1, placeholder='¶'):
        self.fix = fix            # сколько кадров глитча
        self.letter_n = letter_n  # сколько символов глитчим в каждом кадре
        self.PLACEHOLDER = placeholder

        if hasattr(inputTextOrEffect, 'get_frame') and hasattr(inputTextOrEffect, 'frame_count'):
            self.inner_effect = inputTextOrEffect
            self.inputText = inputTextOrEffect.inputText
        else:
            self.inner_effect = None
            self.inputText = inputTextOrEffect

        self.frames = []  # кэш кадров
        self.refresh()

    def refresh(self):
        base_text = (
            self.inner_effect.get_frame(0) if self.inner_effect else self.inputText
        )
        length = len(base_text)
        self.frames.clear()

        # 1. Стартовый кадр — вся строка в PLACEHOLDER
        self.frames.append(self.PLACEHOLDER * length)

        # 2. Основные глитч-кадры
        for _ in range(self.fix):
            frame_chars = [self.PLACEHOLDER] * length
            indices = random.sample(range(length), self.letter_n)
            for i in indices:
                frame_chars[i] = random.choice("!@#$%&=G|t(-_)eiX^'_,!×■▉▀▄")
            self.frames.append(''.join(frame_chars))

        # 3. Финальный кадр — тоже PLACEHOLDER
        #self.frames.append(self.PLACEHOLDER * length)

    def get_frame(self, index):
        if not self.frames:
            return self.inputText
        return self.frames[index % len(self.frames)]

    def frame_count(self):
        return len(self.frames)



class AnimatorLabel(QLabel):
    def __init__(self, inputText, iBrackEffect=None, parent=None, on_finished=None):
        super().__init__(parent)
        if iBrackEffect is None:
            self.anim = SimpleEffect(inputText)
        else:
            self.anim = iBrackEffect(inputText)

        self.setText(self.anim.get_frame(0))

        self.frame_timer = QTimer()
        self.frame_timer.timeout.connect(self._next_frame)

        self.repeat_timer = QTimer()
        self.repeat_timer.setSingleShot(True)
        self.repeat_timer.timeout.connect(self._start_animation)

        self.frame_pos = 0.0
        self.speed = 1.0
        self.total_loops = 1
        self.current_loop = 0

        self._mode = "once"
        self._repeat_length = 12
        self._randomize = True
        self._fps = 25
        self._shift = 0.0  # задержка перед стартом в секундах

        self.on_finished = on_finished  # ← колбэк по завершению

    def play(self, speed=1.0, fps=25, loops=3, mode="once", repeat_length=12, randomize=False, shift=0.0, on_finished=None):
        self.speed = max(0.05, speed)
        self._fps = fps
        self.total_loops = max(1, loops)
        self._mode = mode
        self._repeat_length = repeat_length
        self._randomize = randomize
        self._shift = max(0.0, shift)

        if on_finished is not None:
            self.on_finished = on_finished

        if self._shift > 0:
            self.setText(self.anim.inputText)
            QTimer.singleShot(int(self._shift * 1000), self._start_animation)
        else:
            self._start_animation()

    def _start_animation(self):
        self.frame_pos = 0.0
        self.current_loop = 0
        self.frame_timer.start(int(1000 / self._fps))

    def _next_frame(self):
        self.frame_pos += self.speed

        if self.frame_pos >= self.anim.frame_count():
            self.frame_pos -= self.anim.frame_count()
            self.current_loop += 1
            if self.current_loop >= self.total_loops:
                self.frame_timer.stop()

                if self._mode == "once":
                    self.setText(self.anim.get_frame(self.anim.frame_count() - 1))
                    #self.anim.refresh()
                else:
                    self.setText(self.anim.inputText)

                if self._mode == "repeat":
                    delay = self._repeat_length
                    if self._randomize:
                        delay = random.uniform(0.5, self._repeat_length)
                    self.repeat_timer.start(int(delay * 1000))

                if self.on_finished:
                    self.on_finished()  # ← вызов колбэка

                return

        self.setText(self.anim.get_frame(int(self.frame_pos)))

    def get_last_frame(self):
        return self.anim.get_frame(self.anim.frame_count() - 1) if self.anim.frame_count() > 0 else self.anim.inputText

class CombinedLabel(QLabel):
    def __init__(self,
                 base_label: AnimatorLabel,
                 glitch_label: AnimatorLabel,
                 parent=None,
                 placeholder='¶',
                 fps=25):
        super().__init__(parent)
        self.base_label   = base_label
        self.glitch_label = glitch_label
        self.PLACEHOLDER  = placeholder


        # Таймер для обновления комбинированного текста
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._update)
        self.timer.start(int(1000 / fps))

        # Начальное содержимое
        self.setText(self.base_label.text())

    def _update(self):
        base = self.base_label.text()
        frame_idx = int(self.glitch_label.frame_pos)
        glitch_frame = self.glitch_label.anim.get_frame(frame_idx)

        length = min(len(base), len(glitch_frame))
        combined = ''.join(
            (g if g != self.PLACEHOLDER else b)
            for b, g in zip(base[:length], glitch_frame[:length])
        ) + base[length:]
        self.setText(combined)

# --- Получение текущей раскладки Windows ---
def get_keyboard_language():
    user32 = ctypes.windll.user32
    hwnd = user32.GetForegroundWindow()
    thread_id = user32.GetWindowThreadProcessId(hwnd, 0)
    layout_id = user32.GetKeyboardLayout(thread_id)
    language_id = layout_id & 0xFFFF
    return locale.windows_locale.get(language_id, "Unknown")

class KeyListener(QObject):
    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if isinstance(event, QKeyEvent):
                char = event.text()
                if char:
                    layout = get_keyboard_language()
                    print(f"Symbol: '{char}' — Language: {layout}")
        return super().eventFilter(obj, event)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        #self.setFocusPolicy(Qt.StrongFocus)  # важно для перехвата клавиш

        # Разрешить окну получать фокус
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        font = QFont("Consolas", 12)
        self.setFont(font)

        # базовый текст
        self.last_lang = get_keyboard_language()


        self.lang = "EN"
        if self.last_lang=="ru_RU":
            self.lang = "RU"
        
        self.mode = 0    # 0 -text , 1 -text_alt
        print(f"[START] CurrentMode:{self.mode} , CurrentLang:{self.lang}, LastLang:{self.last_lang} ")
        
        if self.lang=="EN":
            self.text        = "_KEEP IT CLEAN_" # Может _ на прозрачный
            self.text_alt    = "FOLLOW PROTOCOL"
        elif self.lang =="RU":
            self.text        = "ДЕРЖИ ЭТО ЧИСТЫМ"
            self.text_alt    = "СЛЕДУЙ ПРОТОКОЛУ"
        else:
            pass
        
        self.Switcher = TextSwitcher(self.text, self.text_alt, debug=True)
        self.SwitchAnimLabel = AnimatorLabel(inputText=self.text, iBrackEffect=lambda _: self.Switcher)
        self.SwitcherLabel = self.SwitchAnimLabel 

        # отдельные скобки
        br_left  = ">> "
        br_right = " <<"

        # тип анимации
        self.br_anim_L = AnimatorLabel(inputText=br_left,  iBrackEffect=lambda txt: TextAnimator(txt, mode='extend', dir=0))
        self.br_anim_R = AnimatorLabel(inputText=br_right, iBrackEffect=lambda txt: TextAnimator(txt, mode='extend', dir=1))

        # анимация скобок
        self.br_anim_L.play(speed=.27, fps=30, loops=3, mode="repeat", repeat_length=12)
        self.br_anim_R.play(speed=.27, fps=30, loops=3, mode="repeat", repeat_length=12)


        # combine
        self.BrackText = self.br_anim_L.text() + self.SwitcherLabel.text() + self.br_anim_R.text() # извлекаем текст
        self.BrackAnimLabel = AnimatorLabel(self.BrackText)   # создаём AnimatorLabel [текст + скобки]
        
        # создаём glitch аниматор
        self.GlitchAnimLabel = AnimatorLabel(
            inputText=self.BrackText,  
            iBrackEffect=lambda _: GlitchEffect(self.BrackAnimLabel.anim)
        )
        # запуск glitch анимации 
        self.GlitchAnimLabel.play(speed=0.14, fps=30, loops=1, mode="repeat", repeat_length=10, randomize=True, shift=4.0)

        # создаём CombineLabel [текст + скобки] < поверх глитч
        self.ResultLabel = CombinedLabel(
            base_label   = self.BrackAnimLabel,
            glitch_label = self.GlitchAnimLabel,
            fps=30 
        )

        # добавляем в layout
        #self.layout.addWidget(self.SwitcherLabel)   # без скобок
        #self.layout.addWidget(self.BrackAnimLabel)  # скобки + текст
        self.layout.addWidget(self.ResultLabel)      # скобки + текст + глитч поверх
        
        # Выравниватель Qтекста
        #self.SwitcherLabel.setAlignment(Qt.AlignCenter)
        #self.BrackAnimLabel.setAlignment(Qt.AlignCenter)
        self.ResultLabel.setAlignment(Qt.AlignCenter) 

        # updates
        self.BrackText_timer = QTimer()
        self.BrackText_timer.timeout.connect(self.update_BrackText)
        self.BrackText_timer.start(40)  # 25 FPS → 1000/25 ≈ 40 мс


        # Устанавливаем глобальный перехватчик
        self.listener = KeyListener()
        app.installEventFilter(self.listener)


        
    def keyPressEvent(self, event: QKeyEvent):
        key = event.key()
        mods = event.modifiers()
        char = event.text()

        if key == Qt.Key_P and mods & Qt.ControlModifier and mods & Qt.ShiftModifier:
            print("[CTRL+SHIFT+P] STARTING TOGGLE MODE (text <-> alt)")
            self.toggle_mode()
            return

        if key == Qt.Key_L and mods & Qt.ControlModifier and mods & Qt.ShiftModifier:
            print("[CTRL+SHIFT+L] STARTING SWITCH LANG (EN <-> RU)")
            self.update_lang()
            return

        # Автоопределение смены раскладки
        if char and char.isalpha():
            current_lang = get_keyboard_language()
            if current_lang != self.last_lang:
                print(f"[AUTO_LANG] Раскладка изменилась: {self.last_lang} → {current_lang}")
                self.last_lang = current_lang
                self.update_lang()
            else:
                print(f"[AUTO_LANG] Символ: '{char}' — Язык: {current_lang} (без изменений)")



    def toggle_mode(self):
        self.mode = 1 - self.mode  # переключение 0 <-> 1
        
        # Подготовка: берём реальный текст с экрана и сразу настраиваем Switcher
        current = self.SwitcherLabel.text()
        target = self.text_alt if current == self.text else self.text

        #print("[TOGGLE_MODE] STARTING... ")
        self.Switcher.refresh(inputText=current, targetText=target)

        def swap_texts():
            # После завершения анимации просто перезапускаем глитч
            self.refresh_glitch()
            print("[TOGGLE_MODE] FINISH!")
            print(f"[STAT] CurrentMode:{self.mode} , CurrentLang:{self.lang}, LastLang:{self.last_lang} ")

        # Запускаем анимацию от текущего текста к целевому
        #print("[TextSwitcher][PLAY_SEQ]...")
        self.SwitchAnimLabel.play(
            speed=0.65, fps=30, loops=1, mode="once",
            on_finished=swap_texts
        )

    def update_lang(self):
        # 1) Переключаем язык и обновляем поля text/text_alt
        self.lang = "EN" if self.lang == "RU" else "RU"
        if self.lang == "EN":
            self.text, self.text_alt = "_KEEP IT CLEAN_", "FOLLOW PROTOCOL"
        else:
            self.text, self.text_alt = "ДЕРЖИ ЭТО ЧИСТЫМ", "СЛЕДУЙ ПРОТОКОЛУ"

        # 2) Анимируем от того, что сейчас на экране, к нужному тексту
        current = self.SwitcherLabel.text()
        new_text = self.text if self.mode == 0 else self.text_alt
        self.Switcher.refresh(inputText=current, targetText=new_text)

        def on_finished():
            self.refresh_glitch()
            print(f"[STAT] CurrentMode:{self.mode} , CurrentLang:{self.lang}, LastLang:{self.last_lang} ")
            

        # 3) Запускаем анимацию
        self.SwitchAnimLabel.play(
            speed=0.65, fps=30, loops=1, mode="once",
            on_finished=on_finished
        )

    def update_BrackText(self):
        left_text = self.br_anim_L.text()
        midd_text= self.SwitcherLabel.text()
        rght_text = self.br_anim_R.text()
        self.BrackAnimLabel.setText(left_text + midd_text + rght_text)
        #self.refresh_glitch()  


    def refresh_glitch(self):
        ge = self.GlitchAnimLabel.anim  # это GlitchEffect
        if hasattr(ge, "refresh"):
            ge.refresh()                      
            # и перезапускаем его AnimatorLabel, т.к. frame_timer остановился
            self.GlitchAnimLabel.play(speed=0.14, fps=30, loops=1, mode="repeat", repeat_length=10, randomize=True, shift=4.0)
            print("[GlitchEffect][REFRESH][PLAY]")



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()

    # моноширный шрифт обязательно
    window.setFont(QFont("Consolas", 14))  

    window.show()
    sys.exit(app.exec())
