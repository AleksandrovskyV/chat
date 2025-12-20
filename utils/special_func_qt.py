from PySide6.QtGui import QGuiApplication,QPixmap, QPainter, QColor, QFont
from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QPoint, QRect, QStandardPaths

import os
from datetime import datetime

# sound

import time
from collections import deque

from PySide6.QtCore import QThread, Signal

import numpy as np
import sounddevice as sd
import soundfile as sf  # pip install soundfile
import threading

import webrtcvad
from pycaw.pycaw import AudioUtilities, IAudioMeterInformation





def is_light_color(qcolor: QColor) -> bool:
    """
    Возвращает True, если цвет ближе к светлому, False — если к тёмному.
    Используется формула относительной яркости (perceived luminance).
    """
    r, g, b, _ = qcolor.getRgb()
    # Стандартное восприятие яркости (по формуле ITU-R BT.709)
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return luminance > 128  # 0–255


def hex_to_qcolor(hex_color: str, alpha: float = 1.0) -> QColor:
    """
    Преобразует HEX-цвет (#RRGGBB или #RRGGBBAA) в объект QColor.
    alpha (0.0–1.0) используется, если в hex нет альфа-канала.
    """
    hex_color = hex_color.strip().lstrip('#')

    if len(hex_color) == 6:  # #RRGGBB
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        a = int(alpha * 255)
    elif len(hex_color) == 8:  # #RRGGBBAA
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        a = int(hex_color[6:8], 16)
    else:
        raise ValueError("hex_color должен быть в формате #RRGGBB или #RRGGBBAA")

    return QColor(r, g, b, a)


def ensure_directory_exists(path: str):
    """Создаёт директорию для файла path, если её нет."""
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)



def screenshot_entire_window(widget: QWidget, full_path: str = None, watermark: bool = False, wm_path: str = None, to_clipboard: bool = False, portrait_text: str = "LOVE withhSCRBEN"):
    screen = QGuiApplication.primaryScreen()
    if screen is None:
        print("❌ Экран не найден")
        return

    widget.repaint()
    QGuiApplication.processEvents()

    top_left = widget.mapToGlobal(QPoint(0, 0))
    x, y = top_left.x(), top_left.y()
    width = widget.width()
    height = widget.height()

    pixmap = screen.grabWindow(0, x, y, width, height)
    source_pixmap = pixmap

    if not full_path:
        return source_pixmap        

    pw, ph = pixmap.width(), pixmap.height()

    is_portrait = ph > pw

    # === Почти квадратный режим ===
    if abs(pw - ph) <= 120:
        square_size = max(pw, ph)
        margin = 60  # фиксированная ширина полос
        new_width = square_size + 2 * margin

        new_pixmap = QPixmap(new_width, square_size)
        new_pixmap.fill(QColor("black"))

        offset_x = margin + (square_size - pw) // 2
        offset_y = (square_size - ph) // 2

        painter = QPainter(new_pixmap)
        painter.drawPixmap(offset_x, offset_y, pixmap)

        # Текст на левой полосе — вертикально
        font_size = max(10, int(square_size * 0.045))
        font = QFont("Consolas", font_size)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(Qt.white)

        painter.save()
        painter.translate(margin // 2, square_size // 2)
        painter.rotate(90)

        text = "..Ъ SCREeN WitH luvV"
        text_rect = QRect(-square_size // 2, -margin // 2, square_size, margin)
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, text)
        painter.restore()

        painter.end()
        pixmap = new_pixmap

    elif is_portrait:
        # Чёрные полосы слева и справа + вертикальный текст
        #margin = int(pw * 0.2)
        margin = 60
        max_ph = int(margin * 0.9)
        new_width = pw + 2 * margin
        new_pixmap = QPixmap(new_width, ph)
        new_pixmap.fill(QColor("black"))

        painter = QPainter(new_pixmap)
        painter.drawPixmap(margin, 0, pixmap)

        font_size = max(10, int(pw * 0.045))
        font = QFont("Consolas", font_size)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(Qt.white)

        painter.save()
        painter.translate(margin // 2, ph // 2)
        painter.rotate(90)

        text = portrait_text
        text_rect = QRect(-ph // 2, -margin // 2, ph, margin)
        painter.drawText(text_rect, Qt.AlignCenter | Qt.TextWordWrap, text)
        painter.restore()

        painter.end()
        pixmap = new_pixmap

    elif wm_path:
        watermark_val = QPixmap(wm_path)
        if not watermark_val.isNull():
            ww, wh = watermark_val.width(), watermark_val.height()

            # Фиксированная высота полос сверху/снизу
            margin = 60
            max_wh = int(margin * 0.9)

            # Масштаб watermark_val'а, если он слишком большой
            if wh > max_wh:
                scale_factor = max_wh / wh
                watermark_val = watermark_val.scaled(int(ww * scale_factor), max_wh,
                                             Qt.KeepAspectRatio, Qt.SmoothTransformation)
                ww, wh = watermark_val.width(), watermark_val.height()

            new_height = ph + 2 * margin
            new_pixmap = QPixmap(pw, new_height)
            new_pixmap.fill(QColor("black"))

            painter = QPainter(new_pixmap)
            painter.drawPixmap(0, margin, pixmap)

            # Вотермарк в верхней левой части полосы
            pos_x = int(0.02 * pw)
            pos_y = (margin - wh) // 2
            painter.drawPixmap(pos_x, pos_y, watermark_val)

            painter.end()
            pixmap = new_pixmap

    if to_clipboard:
        QGuiApplication.clipboard().setPixmap(pixmap)
        print("📋 Скриншот скопирован в буфер обмена")

    # Сохранение
    if full_path:
        try:
            from os import makedirs
            from os.path import dirname, exists
            if not exists(dirname(full_path)):
                makedirs(dirname(full_path))
            source_pixmap.save(full_path)
            print(f"✅ Скриншот сохранён: {full_path}")
        except Exception as e:
            print(f"⚠️ Ошибка при сохранении: {e}")

    return source_pixmap


def take_screenshot_qt(widget, path=None):
    if path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"pic_{timestamp}.png"
    pixmap = widget.grab()
    if pixmap.save(path):
        print(f"Скриншот сохранён в {path}")
    else:
        print(f"❌ Не удалось сохранить скриншот")


def screenshot_to_clipboard(widget):
    pixmap = widget.grab()
    clipboard = QGuiApplication.clipboard()
    clipboard.setPixmap(pixmap)
    print("📋 Скриншот скопирован в буфер обмена")



### MusicPlayer

# Глобальный кэш аудио
AUDIO_CACHE = {}

def get_cached_sound(path):
    if path not in AUDIO_CACHE:
        data, sr = sf.read(path, dtype='float32')
        if data.ndim == 1:
            data = np.column_stack((data, data))
        AUDIO_CACHE[path] = (data, sr)
    return AUDIO_CACHE[path]

class SoundFileSource:
    def __init__(self, filepath, volume=1.0, pan=0.0, loop=False, tag=None):
        data, sr = get_cached_sound(filepath)
        if sr != 44100:
            raise ValueError("WAV должен быть 44100 Гц")

        left = data[:, 0] * (1 - pan) * 0.5
        right = data[:, 1] * (1 + pan) * 0.5
        self.data = np.column_stack((left, right))

        self.volume = volume
        self.target_volume = volume
        self.loop = loop
        self.alive = True
        self.position = 0
        self.fade_speed = 0.0
        self.tag = tag
        self.sr = 44100
        self.limitable = True

    def set_volume(self, volume, fade_time=0.0):
        self.target_volume = max(0.0, min(1.0, volume))
        if fade_time > 0:
            total_frames = int(self.sr * fade_time)
            self.fade_speed = (self.target_volume - self.volume) / total_frames
        else:
            self.volume = self.target_volume
            self.fade_speed = 0.0

    def stop(self, fade_time=0.0):
        """Останавливает звук мгновенно или с fade-out"""
        if fade_time > 0:
            self.set_volume(0.0, fade_time)
        else:
            self.alive = False

    def generate(self, frames):
        if not self.alive:
            return np.zeros((frames, 2), np.float32)

        end = self.position + frames
        if end >= len(self.data):
            if self.loop:
                part1 = self.data[self.position:]
                rest = frames - len(part1)
                part2 = self.data[:rest]
                chunk = np.vstack((part1, part2))
                self.position = rest
            else:
                chunk = self.data[self.position:]
                pad = np.zeros((frames - len(chunk), 2), np.float32)
                chunk = np.vstack((chunk, pad))
                self.alive = False
                self.position = len(self.data)
        else:
            chunk = self.data[self.position:end]
            self.position = end

        #  применение фейда (вынесено за условия)
        if self.fade_speed != 0.0:
            vols = np.clip(self.volume + np.arange(frames) * self.fade_speed, 0.0, 1.0)
            self.volume = vols[-1]
            chunk *= vols[:, np.newaxis]
            if abs(self.volume - self.target_volume) < 1e-4:
                if self.volume == 0.0:
                    self.alive = False
                self.fade_speed = 0.0
        else:
            chunk *= self.volume

        return chunk


class SineWave:
    def __init__(self, freq=440, volume=0.3, pan=0.0, sr=44100):
        self.freq = freq
        self.volume = volume
        self.pan = pan
        self.sr = sr
        self.phase = 0.0
        self.alive = True

    def generate(self, frames):
        if not self.alive:
            return np.zeros((frames, 2), np.float32)

        t = (np.arange(frames) + self.phase) / self.sr
        self.phase += frames
        wave = np.sin(2 * np.pi * self.freq * t) * self.volume
        left = wave * (1 - self.pan) * 0.5
        right = wave * (1 + self.pan) * 0.5
        return np.column_stack((left, right))

    def stop(self):
        self.alive = False


# --- Мастер ---
class MasterPlayer:
    def __init__(self):
        self.sr = 44100
        self.master_volume = 0.2 #0.8
        self.sources = []
        self.lock = threading.Lock()
        self.stream = sd.OutputStream(
            samplerate=self.sr,
            channels=2,
            callback=self.audio_callback
        )
        self.stream.start()

        # 🔧 Настройки ограничителей по тегам
        self.limit_enabled = True
        self.max_instances_per_tag = {
            "teleport": 5,
            "landing": 3,
            "slanding": 1,
            "opendoor": 1,
            "transition": 1,
            "level_theme": 1,
            # можно добавлять другие теги
        }

    def add_source(self, src):
        with self.lock:
            if self.limit_enabled and getattr(src, "tag", None):
                tag = src.tag
                # находим все активные источники с этим тегом
                same_tag = [s for s in self.sources if getattr(s, "tag", None) == tag]

                # если лимит превышен — удаляем/глушим старейший
                if len(same_tag) >= self.max_instances_per_tag.get(tag, 0):
                    print("LIMIT_TRACKS")
                    oldest = same_tag[0]
                    #  мягкий вариант — плавное затухание
                    #oldest.stop(fade_time=0.2)
                    # или мгновенно удалить: 
                    oldest.alive = False
                    self.sources.remove(oldest)

            self.sources.append(src)

    def stop_by_tag(self, tag, fade_time=0.0, exclude_last=False):
        """Останавливает все источники с указанным тегом"""
        with self.lock:
            tagged = [s for s in self.sources if getattr(s, "tag", None) == tag]
            if exclude_last and tagged:
                #print("STOP_BY_TAG")
                tagged = tagged[:-1]  # оставить последний
            for s in tagged:
                s.stop(fade_time)

    def stop_all(self):
        with self.lock:
            for s in self.sources:
                s.stop()

    def audio_callback(self, outdata, frames, time, status):
        buffer = np.zeros((frames, 2), np.float32)
        with self.lock:
            alive = []
            for src in self.sources:
                chunk = src.generate(frames)
                buffer += chunk
                if src.alive:
                    alive.append(src)
            self.sources = alive
        outdata[:] = np.clip(buffer * self.master_volume, -1, 1)


### SOUND DETECTION

_PYCAW_AVAILABLE = True

def find_loopback_device():
    """Ищем подходящее устройство для loopback (попытки: loopback/stereo mix, WASAPI output, дефолт)."""
    try:
        devs = sd.query_devices()
        hostapis = sd.query_hostapis()
    except Exception:
        return None

    # 1) явные loopback / stereo mix по имени
    for i, d in enumerate(devs):
        name = (d.get('name') or "").lower()
        if 'loopback' in name or 'stereo mix' in name:
            return i

    # 2) попытаться взять WASAPI output device (используем output device для loopback)
    for i, d in enumerate(devs):
        host = hostapis[d['hostapi']]['name'].lower()
        if 'wasapi' in host and d.get('max_output_channels', 0) > 0:
            return i

    # 3) fallback: вернуть default input (может не работать как loopback)
    try:
        default = sd.default.device
        if isinstance(default, tuple) or isinstance(default, list):
            return default[0]  # input default
        return default
    except Exception:
        return None

class MusicDetector(QThread):
    """
    QThread — слушает системный выход (loopback) если возможно,
    иначе использует pycaw session-level fallback.

    Эмиссии:
      music_started()
      music_stopped()
      debug(str)
    """
    music_started = Signal()
    music_stopped = Signal()
    debug = Signal(str)

    def __init__(self,
                 sample_rate=16000,
                 frame_ms=30,
                 threshold_rms=0.01,
                 min_continuous_sec=2.0,
                 debounce_sec=1.0,
                 vad_aggressiveness=2,
                 device=None,
                 parent=None):
        super().__init__(parent)
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.frame_samples = int(self.sample_rate * self.frame_ms / 1000)
        self.threshold_rms = threshold_rms
        self.min_continuous_sec = min_continuous_sec
        self.debounce_sec = debounce_sec
        self.vad = webrtcvad.Vad(vad_aggressiveness)

        self._running = False
        self._q = deque(maxlen=400)  # входные блоки
        self._device = device or find_loopback_device()
        self._channels = 2  # обычно стерео

        # состояния для loopback
        self._continuous_frames = 0
        self._continuous_speech_frames = 0
        self._music_state = False
        self._last_state_change = 0.0

        # состояния для pycaw-fallback
        self._fallback_continuous_seconds = 0.0
        self._fallback_music_state = False
        self._fallback_last_state_change = 0.0

    def stop(self):
        self._running = False

    def pcm_from_float32(self, arr):
        """float32 [-1..1] -> int16"""
        arr = np.clip(arr, -1.0, 1.0)
        return (arr * 32767).astype(np.int16)

    def is_speech(self, frame_bytes):
        try:
            return self.vad.is_speech(frame_bytes, self.sample_rate)
        except Exception:
            return False

    def audio_callback(self, indata, frames, time_info, status):
        # callback в отдельном потоке от sounddevice
        try:
            self._q.append(indata.copy())
        except Exception:
            pass

    # pycaw helper
    def any_active_session(self, threshold=0.03):
        """Возвращает (active: bool, process_name, peak) если pycaw доступен."""
        if not _PYCAW_AVAILABLE:
            return False, None, 0.0
        try:
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                try:
                    if not getattr(session, "_ctl", None):
                        continue
                    meter = session._ctl.QueryInterface(IAudioMeterInformation)
                    peak = meter.GetPeakValue()
                    if peak > threshold:
                        pname = session.Process.name() if session.Process else None
                        return True, pname, peak
                except Exception:
                    continue
        except Exception:
            pass
        return False, None, 0.0

    def run(self):
        self._running = True
        try:
            sd.default.samplerate = self.sample_rate
        except Exception:
            pass

        # --- Подготовка dev_info и channels ---
        dev_info = None
        if self._device is not None:
            try:
                dev_info = sd.query_devices(self._device)
                hostapi_name = sd.query_hostapis()[dev_info['hostapi']]['name'].lower()
                self.debug.emit(f"Device chosen: index={self._device}, name='{dev_info['name']}', hostapi='{hostapi_name}', in={dev_info['max_input_channels']}, out={dev_info['max_output_channels']}")
            except Exception as e:
                self.debug.emit(f"query_devices failed for {self._device}: {e}")
                dev_info = None

        # число каналов
        if dev_info:
            if int(dev_info.get('max_input_channels', 0)) == 0 and int(dev_info.get('max_output_channels', 0)) > 0:
                self._channels = int(dev_info['max_output_channels'])
            else:
                self._channels = max(1, int(dev_info.get('max_input_channels', 1)))
        else:
            self._channels = 2

        # Попытки открыть InputStream / WASAPI loopback
        stream = None
        wasapi_settings = None
        try:
            wasapi_settings = sd.WasapiSettings(loopback=True)
        except Exception:
            wasapi_settings = None


        # helper: получить индекс реального устройства из device_arg (int или (in,out))
        def _resolve_device_index(device_arg):
            if device_arg is None:
                return None
            if isinstance(device_arg, (tuple, list)):
                # берем первый непустой элемент
                for x in device_arg:
                    if x is not None:
                        return x
                return None
            return device_arg

        # helper: вычислить корректное число каналов для данного device index
        def _channels_for_device(device_idx, default_channels):
            try:
                if device_idx is None:
                    return default_channels
                info = sd.query_devices(device_idx)
                in_ch = int(info.get('max_input_channels', 0) or 0)
                out_ch = int(info.get('max_output_channels', 0) or 0)
                # если устройство имеет input каналы — используем их
                if in_ch > 0:
                    return in_ch
                # иначе используем output каналы (для loopback)
                if out_ch > 0:
                    return out_ch
            except Exception as e:
                self.debug.emit(f"_channels_for_device failed for {device_idx}: {e}")
            return default_channels


        def try_open(device_arg, extra=None):
            resolved = _resolve_device_index(device_arg)
            # получаем рекомендованное channels из инфо
            resolved_channels = _channels_for_device(resolved, self._channels)

            # кандидаты каналов: сначала рекомендованный, затем 1 и 2
            channel_candidates = []
            if resolved_channels:
                channel_candidates.append(resolved_channels)
            for c in (1, 2):
                if c not in channel_candidates:
                    channel_candidates.append(c)

            # кандидаты sample rates: сначала ваш, затем распространённые значения
            sr_candidates = []
            if self.sample_rate not in sr_candidates:
                sr_candidates.append(self.sample_rate)
            for sr in (48000, 44100, 32000, 16000, 8000):
                if sr not in sr_candidates:
                    sr_candidates.append(sr)

            # Пробуем все комбинации (логируем каждую попытку)
            for sr in sr_candidates:
                for ch in channel_candidates:
                    try:
                        self.debug.emit(f"try_open attempt: device={device_arg} (resolved={resolved}), channels={ch}, samplerate={sr}, extra={'yes' if extra else 'no'}")
                    except Exception:
                        pass
                    try:
                        s = sd.InputStream(
                            channels=int(ch),
                            samplerate=int(sr),
                            blocksize=self.frame_samples,
                            dtype='float32',
                            callback=self.audio_callback,
                            device=device_arg,
                            latency='low',
                            extra_settings=extra
                        )
                        # если удалось создать объект — возвращаем его (успешная попытка)
                        return s
                    except Exception as e:
                        try:
                            self.debug.emit(f"try_open failed: device={device_arg} (resolved {resolved}), ch={ch}, sr={sr} -> {e}")
                        except Exception:
                            pass
                        # пробуем дальше
                        continue

            # если ничего не сработало — возвращаем None
            try:
                self.debug.emit(f"try_open: all attempts failed for device={device_arg} (resolved={resolved})")
            except Exception:
                pass
            return None

                
        # 1) если hostapi == wasapi и есть wasapi_settings
        try:
            if wasapi_settings and dev_info and 'wasapi' in sd.query_hostapis()[dev_info['hostapi']]['name'].lower():
                self.debug.emit("Attempting WASAPI loopback on chosen device")
                stream = try_open(self._device, wasapi_settings)
        except Exception:
            pass

        # 2) разные формы device (index, (index,None), (None,index))
        if stream is None and wasapi_settings and self._device is not None:
            self.debug.emit("Attempting alternate device forms for loopback")
            stream = try_open((self._device, None), wasapi_settings)
            if stream is None:
                stream = try_open((None, self._device), wasapi_settings)
            if stream is None:
                stream = try_open(self._device, wasapi_settings)

        # 3) поиск любого WASAPI output device и пробуем его
        if stream is None:
            try:
                devs = sd.query_devices()
                hostapis = sd.query_hostapis()
                target_name = (dev_info['name'].lower() if dev_info else "")
                wasapi_candidates = []
                for i, d in enumerate(devs):
                    host = hostapis[d['hostapi']]['name'].lower()
                    if 'wasapi' in host and int(d.get('max_output_channels', 0)) > 0:
                        wasapi_candidates.append((i, d['name']))
                if wasapi_candidates:
                    chosen_wasapi = None
                    for idx, nm in wasapi_candidates:
                        if target_name and target_name in nm.lower():
                            chosen_wasapi = idx
                            break
                    if chosen_wasapi is None:
                        chosen_wasapi = wasapi_candidates[0][0]
                    self.debug.emit(f"Trying WASAPI device index {chosen_wasapi} for loopback")
                    stream = try_open(chosen_wasapi, wasapi_settings)
                    if stream is None:
                        stream = try_open((chosen_wasapi, None), wasapi_settings)
            except Exception as e:
                self.debug.emit(f"Error while searching WASAPI devices: {e}")

        # 4) fallback: default input
        if stream is None:
            self.debug.emit("Falling back to default input device (no loopback).")
            try:
                stream = sd.InputStream(
                    channels=self._channels,
                    samplerate=self.sample_rate,
                    blocksize=self.frame_samples,
                    dtype='float32',
                    callback=self.audio_callback,
                    device=None,
                    latency='low'
                )
                self.debug.emit("Opened fallback InputStream device=None")
            except Exception as e:
                self.debug.emit(f"Unable to open any input stream: {e}")
                stream = None

        # 5) Если stream None => включаем pycaw-fallback (если pycaw установлен)
        pycaw_fallback = False
        if stream is None:
            if _PYCAW_AVAILABLE:
                pycaw_fallback = True
                self.debug.emit("No InputStream — using pycaw session-level fallback.")
            else:
                self.debug.emit("No InputStream and pycaw not available — cannot detect system audio. Install pycaw or enable loopback device.")
                # Завершаем поток аккуратно
                self._running = False
                return

        frames_needed = int((self.min_continuous_sec * 1000) / self.frame_ms)

        # --- Если есть stream, используем loopback/микрофонный поток ---
        if stream is not None:
            with stream:
                self.debug.emit(f"MusicDetector started (stream). device={self._device}, sample_rate={self.sample_rate}, frame_ms={self.frame_ms}")
                try:
                    while self._running:
                        if not self._q:
                            time.sleep(0.01)
                            continue

                        frame = self._q.popleft()  # shape (N, channels)
                        mono = frame.mean(axis=1)
                        rms = np.sqrt(np.mean(mono ** 2))

                        pcm = self.pcm_from_float32(mono)
                        frame_bytes = pcm.tobytes()

                        speech = self.is_speech(frame_bytes)
                        loud = rms > self.threshold_rms

                        if loud:
                            self._continuous_frames += 1
                        else:
                            self._continuous_frames = 0

                        if speech:
                            self._continuous_speech_frames += 1
                        else:
                            self._continuous_speech_frames = 0

                        if self._continuous_frames >= frames_needed and self._continuous_speech_frames < frames_needed // 2:
                            if not self._music_state:
                                self._music_state = True
                                self._last_state_change = time.time()
                                self.debug.emit(f"Music started (stream), rms={rms:.4f}")
                                self.music_started.emit()
                        else:
                            if self._music_state and time.time() - self._last_state_change > self.debounce_sec:
                                if self._continuous_frames == 0 or self._continuous_speech_frames >= frames_needed // 2:
                                    self._music_state = False
                                    self.debug.emit("Music stopped (stream)")
                                    self.music_stopped.emit()
                except Exception as e:
                    self.debug.emit(f"Exception in MusicDetector stream loop: {e}")

            self.debug.emit("MusicDetector stream thread exiting")
            return

        # --- pycaw-fallback loop (polling session peaks) ---
        if pycaw_fallback:
            poll_interval = max(0.02, self.frame_ms / 1000.0)  # период опроса
            self.debug.emit("MusicDetector started (pycaw fallback). Poll interval: {:.3f}s".format(poll_interval))
            try:
                while self._running:
                    active, proc, peak = self.any_active_session(self.threshold_rms)
                    now = time.time()
                    if active:
                        self._fallback_continuous_seconds += poll_interval
                    else:
                        self._fallback_continuous_seconds = 0.0

                    if self._fallback_continuous_seconds >= self.min_continuous_sec:
                        if not self._fallback_music_state:
                            self._fallback_music_state = True
                            self._fallback_last_state_change = now
                            self.debug.emit(f"Music started (pycaw), proc={proc}, peak={peak:.3f}")
                            self.music_started.emit()
                    else:
                        if self._fallback_music_state and now - self._fallback_last_state_change > self.debounce_sec:
                            if self._fallback_continuous_seconds == 0.0:
                                self._fallback_music_state = False
                                self.debug.emit("Music stopped (pycaw)")
                                self.music_stopped.emit()

                    # небольшой сон
                    time.sleep(poll_interval)
            except Exception as e:
                self.debug.emit(f"Exception in MusicDetector pycaw-fallback loop: {e}")

            self.debug.emit("MusicDetector pycaw thread exiting")
            return


