import sys,os
from math import atan2, cos, sin, pi

from PySide6.QtCore import QObject, QEvent 
from PySide6.QtCore import QSize # для выставления размера иконки 
from PySide6.QtWidgets import QStackedLayout # для смены EyeTarget\StateButton

from PySide6.QtCore import Qt, QTimer, QPointF, QRectF, QTime
from PySide6.QtGui import QPainter, QColor, QBrush, QCursor,QIcon
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QGraphicsScene

from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtSvg import QSvgRenderer

from PySide6.QtGui import QFont

class AppEventFilter(QObject):
    def __init__(self, target_widget):
        super().__init__()
        self.target_widget = target_widget

    def eventFilter(self, obj, event):
        if event.type() == QEvent.ApplicationDeactivate:
            print(">>> Потеря фокуса приложения, включение логики слежения (target mode)")
            self.target_widget.timer.start(18)
        elif event.type() == QEvent.ApplicationActivate:
            print(">>> Приложение активировано")

            if self.target_widget.eyeRED_flag:  # если глаз красный — нужно вернуть
                print(">>> Глаз красный — запускаем возвратный таймер")
                self.target_widget.timer.stop()
                self.target_widget.returning_timer.start(18)
            else:
                print(">>> Глаз в дефолтном состоянии — ничего не делаем")
                self.target_widget.timer.stop()  # убедимся, что основной таймер выключен

        return super().eventFilter(obj, event)


# === DRAFT GSK OR SPT BUTTON ===
class StateButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFixedSize(70, 70)
        self.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 0px solid #7A8A96;
            }
            QPushButton:hover {
                border: 1px solid #25A2EF;
            }
            QPushButton:pressed {
                border: 1px solid #0D71C1;
                background: rgba(17, 75, 111, 0.2);
            }
        """)


        self.setIcon( QIcon("n_assets/GSK_WAIT.png") )
        self.setIconSize(self.size()*1.05)
        

class EyeTargetWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        #WIDGET SETTING

        self.s = 1 # может использовать как глобальный множитель скейла?
        self.global_size_x = 70
        self.global_size_y = 70

        self.setFixedSize(self.global_size_x, self.global_size_y)

        #self.button = QPushButton()
        #self.button.setFixedSize(self.global_size_x, self.global_size_y)

        # для тестов, не забыть отключить
        #self.button.setStyleSheet("""
        #    QPushButton {
        #        background: transparent;
        #        border: 0px solid #7A8A96;
        #    }
        #    QPushButton:hover {
        #        border: 1px solid #25A2EF;
        #    }
        #    QPushButton:pressed {
        #        border: 1px solid #0D71C1;
        #        background: rgba(17, 75, 111, 0.2);  /* лёгкий прозрачный фон при нажатии */
        #    }
        #""")
        
        #self.button.setParent(self)
        #self.button.move(0, 0)
        ##self.button.setIcon( QIcon("n_assets/GSK_WAIT.png") )
        #self.button.setIconSize(self.size())
        #self.button.clicked.connect()


        #SVGs

        self.GraphScene = QGraphicsScene()

        self.eye = QGraphicsSvgItem("assets/s-eye.svg") # DEFAULT IDLE EYE
        self.eye_red = QGraphicsSvgItem("assets/s-eye.svg") # RED EYE FOR TARGET MODE _red
        self.eyeRED_flag = False
        self.body = QGraphicsSvgItem("assets/s-body.svg")

        self.icon_size = 128

        self.eye.setZValue(1)
        self.eye_red.setZValue(1)
        self.body.setZValue(2)

        self.eye_red.setVisible(False)  # красный глаз только для режима Target

        self.GraphScene.addItem(self.body)
        self.GraphScene.addItem(self.eye)
        self.GraphScene.addItem(self.eye_red)

        # SVG INIT VARIABLES

        br = self.eye.boundingRect()
        self.eye.setTransformOriginPoint(br.width()/2, br.height()/2)
        self.eye_red.setTransformOriginPoint(br.width()/2, br.height()/2)

        br_body = self.body.boundingRect()
        self.body.setTransformOriginPoint(br_body.width()/2, br_body.height()/2)

        # FOLLOW MOUSE VARIABLES / INTERACTION

        self.eye_radius = 8 
        # не физический размер глаза, а технический, 
        # Реальный размер глаза берёт на себя размер svg элемента

        self.eye_Max_shift = 12
        self.idle_delay_ms = 1100

        self.angle = 0.0
        self.mem_angle = 0.0
        self.rest_angle = 0.0
        self.rest_position = QPointF(self.width() / 2, self.height() / 2)

        self.eye_pos = QPointF(self.rest_position)
        self.body_pos = QPointF(self.rest_position)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timeout)

        # Частота обновления кнопки в режиме TARGET
        #self.timer.start(18)

        self.returning_timer = QTimer(self)
        self.returning_timer.timeout.connect(self.return_to_center_step)
        self.returning_from_idle = False

        self.smoothed_mouse_pos = QPointF(self.rest_position)
        self.prev_mouse_pos = None
        self.last_mouse_move_time = QTime.currentTime()

        #INIT FLAGS 
        self.setMouseTracking(True)
        self.eye_active = False


    def lerp(self, a, b, t):
        return a + (b - a) * t


    def map_value(self, value, left_min, left_max, right_min, right_max):
        if value < left_min:
            value = left_min
        if value > left_max:
            value = left_max
        left_span = left_max - left_min
        right_span = right_max - right_min
        value_scaled = (value - left_min) / left_span
        return right_min + value_scaled * right_span


    def resizeEvent(self, event):
        self.rest_position = QPointF(self.width() / 2, self.height() / 2)
        # Обновляем eye_Max_shift при ресайзе
        # self.eye_Max_shift = self.width() / 3
        super().resizeEvent(event)

    def reset_position(self):
        self.eye_pos = QPointF(self.rest_position)
        self.smoothed_mouse_pos = QPointF(self.rest_position)
        self.prev_mouse_pos = QPointF(self.rest_position)
        self.update()

    def on_timeout(self):
        
        self.eye_active = True

        global_pos = QCursor.pos()
        local_pos = self.mapFromGlobal(global_pos)

        dx = local_pos.x() - self.rest_position.x()
        dy = local_pos.y() - self.rest_position.y()
        distance = (dx ** 2 + dy ** 2) ** 0.5

        max_input_distance = min(self.width(), self.height()) / 2

        if distance > max_input_distance:
            factor = max_input_distance / distance
            mx = self.rest_position.x() + dx * factor
            my = self.rest_position.y() + dy * factor
        else:
            mx = local_pos.x()
            my = local_pos.y()

        raw_mouse_pos = QPointF(mx, my)

        move_threshold = 1.0
        if self.prev_mouse_pos is None:
            self.smoothed_mouse_pos = QPointF(raw_mouse_pos)
            self.last_mouse_move_time = QTime.currentTime()
        else:
            dist_moved = ((raw_mouse_pos.x() - self.smoothed_mouse_pos.x()) ** 2 +
                          (raw_mouse_pos.y() - self.smoothed_mouse_pos.y()) ** 2) ** 0.5
            if dist_moved > move_threshold:
                self.last_mouse_move_time = QTime.currentTime()
                self.smoothed_mouse_pos.setX(self.lerp(self.smoothed_mouse_pos.x(), raw_mouse_pos.x(), 0.3))
                self.smoothed_mouse_pos.setY(self.lerp(self.smoothed_mouse_pos.y(), raw_mouse_pos.y(), 0.3))

        self.prev_mouse_pos = raw_mouse_pos

        elapsed = self.last_mouse_move_time.msecsTo(QTime.currentTime())
        is_idle = elapsed > self.idle_delay_ms

        if is_idle and self.eye_active:
            # мы уходим в «idle mode»
            #self.eye_active = False
            # вернём дефолтный SVG‑глаз
            self.eye.setVisible(True)
            self.eye_red.setVisible(False)

        dx = self.smoothed_mouse_pos.x() - self.rest_position.x()
        dy = self.smoothed_mouse_pos.y() - self.rest_position.y()
        distance = (dx ** 2 + dy ** 2) ** 0.5
        angle = atan2(dy, dx) if distance != 0 else 0

        dead_zone = self.eye_Max_shift / 8 
        #print (f"dead_zone {dead_zone}")

        input_limit = max_input_distance

        if distance < dead_zone:
            shift = 0
        elif distance > input_limit:
            shift = self.eye_Max_shift
        else:
            shift = self.map_value(distance, dead_zone, input_limit, 0, self.eye_Max_shift)

        if not is_idle:
            target_x = self.rest_position.x() - shift * cos(angle)
            target_y = self.rest_position.y() - shift * sin(angle)
            lerp_factor = 0.15

        else:
            target_x = self.rest_position.x()
            target_y = self.rest_position.y()
            lerp_factor = 0.1
            #self.eye_active = False

            #self.angle = 0.0

        old_pos = QPointF(self.eye_pos)

        self.eye_pos.setX(self.lerp(self.eye_pos.x(), target_x, lerp_factor))
        self.eye_pos.setY(self.lerp(self.eye_pos.y(), target_y, lerp_factor))

        if (old_pos - self.eye_pos).manhattanLength() > 0.05:
            self.update()

        # Body движение напрямую от smoothed_mouse_pos
        body_factor = 0.3  # на сколько меньше двигать

        dx = self.eye_pos.x() - self.rest_position.x()
        dy = self.eye_pos.y() - self.rest_position.y()
        self.body_pos.setX(self.rest_position.x() + dx * body_factor)
        self.body_pos.setY(self.rest_position.y() + dy * body_factor)

        #body_factor = 0.1  # на сколько меньше двигать - проблема ребэка\ пока не удалять, позже вернуться
        #target_body = self.rest_position + (self.smoothed_mouse_pos - self.rest_position) * body_factor
        #self.body_pos.setX(target_body.x())
        #self.body_pos.setY(target_body.y())

        #self.angle = angle # включи если хочешь, чтобы он запоминал угол
        self.mem_angle = angle # включи если хочешь, чтобы он запоминал угол

        
        #self.update() # MANHAAATOP UPDATE UP!!

    def return_to_center_step(self):
        self.returning_from_idle = True

        # Быстрый возврат — за 300 мс (18 * ~16ms ≈ 288ms → используем сильный lerp)
        lerp_factor = 0.35
        self.eye_pos.setX(self.lerp(self.eye_pos.x(), self.rest_position.x(), lerp_factor))
        self.eye_pos.setY(self.lerp(self.eye_pos.y(), self.rest_position.y(), lerp_factor))
        #self.angle.set(self.lerp(self.angle(), self.rest_angle, lerp_factor))

        self.body_pos.setX(self.lerp(self.body_pos.x(), self.rest_position.x(), lerp_factor))
        self.body_pos.setY(self.lerp(self.body_pos.y(), self.rest_position.y(), lerp_factor))

        self.angle *= 0.8  # быстрее сбрасываем угол

        self.update()

        # Конец возврата
        if (self.eye_pos - self.rest_position).manhattanLength() < 0.1: #0.5
            self.returning_timer.stop()
            self.returning_from_idle = False
            self.reset_position()
            self.eyeRED_flag = False  # сбрасываем вручную!
            self.eye_active = False
            self.timer.stop()  # убедимся, что после возврата глаз "спит"
            print(">>> Глаз вернулся в центр")


    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # 1) Debug‑круг
        painter.save()
        painter.translate(self.rest_position)
        painter.rotate(self.mem_angle * 180 / pi)

        dist = ((self.eye_pos.x() - self.rest_position.x())**2 +
                (self.eye_pos.y() - self.rest_position.y())**2)**0.5

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor(153, 204, 0))) # цвет дебаг круга
        painter.drawEllipse(QPointF(dist, 0),
                            self.eye_radius * 2,
                            self.eye_radius * 2)
        painter.restore()

        # 2) Подготовка сцены
        w, h = self.width(), self.height()
        source = QRectF(0, 0, self.icon_size, self.icon_size)
        scale = min(w / source.width(), h / source.height())

        br = self.eye.boundingRect()

        # 4а) Переводим eye_pos из виджетовских координат в координаты сцены
        rel = self.rest_position - self.eye_pos
        scene_x = rel.x() / scale + source.width() / 2
        scene_y = rel.y() / scale + source.height() / 2

        # 4б) Компенсируем offset — позиционируем левый верхний угол
        eye_scene_pos = QPointF(scene_x - br.width() / 2,
                                scene_y - br.height() / 2)

        self.eye.setPos(eye_scene_pos)
        self.eye_red.setPos(eye_scene_pos)
        # 4в) Инвертируем угол
        self.eye.setRotation(self.angle * 90 / pi)
        self.eye_red.setRotation(self.angle * 90 / pi)

        self.eyeRED_flag = dist > 2
        self.eye.setVisible(not self.eyeRED_flag)
        self.eye_red.setVisible(self.eyeRED_flag)

        # --- позиция body (меньшее смещение) ---
        br_body = self.body.boundingRect()
        # вычисляем сцену-позицию для body
        rel_body = self.rest_position - self.body_pos
        scene_x_body = rel_body.x() / scale + source.width() / 2
        scene_y_body = rel_body.y() / scale + source.height() / 2

        body_scene_pos = QPointF(scene_x_body - br_body.width() / 2,
                                 scene_y_body - br_body.height() / 2)

        self.body.setPos(body_scene_pos)
        #self.body.setRotation(-self.angle * 180 / pi)


        # 5) Рендерим сцену поверх дебаг‑круга
        painter.save()
        painter.translate(self.rest_position)  # центр дебаг‑круга
        painter.scale(scale, scale)
        painter.translate(-source.width()/2,
                          -source.height()/2)

        self.GraphScene.render(painter, source, source)
        #print (f"TARGET: {self.eyeRED_flag}")
        painter.restore()
        # Никакого painter.end() — Qt закроет сам закроет painter 

class ChatWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Chat Window")  # по желанию
        self.setFixedSize(300, 300)         # подгоняй под контекст

        # === Основной layout ===
        main_layout = QVBoxLayout(self)

        # === Создаём виджеты ===
        self.BotWidget = EyeTargetWidget()
        self.BotButton = StateButton()

        # === Создаём стек ===
        self.BotIconStacked = QStackedLayout()
        self.BotIconStacked.addWidget(self.BotButton)  # индекс 0
        self.BotIconStacked.addWidget(self.BotWidget)  # индекс 1

        # Показываем кнопку по умолчанию
        self.BotIconStacked.setCurrentIndex(0)

        # Добавляем в layout
        main_layout.addLayout(self.BotIconStacked)

        # === Таймер для переключения ===
        self.monitor_timer = QTimer(self)
        self.monitor_timer.timeout.connect(self.EyeTargetVisibility)
        self.monitor_timer.start(100)

        print("ChatWindow инициализирован")

    def EyeTargetVisibility(self):
        if self.BotWidget.eye_active:
            if self.BotIconStacked.currentIndex() != 1:
                print(">>> EyeTarget активен, показываем глаз")
                self.BotIconStacked.setCurrentIndex(1)
        else:
            if self.BotIconStacked.currentIndex() != 0:
                print(">>> EyeTarget в idle, возвращаем кнопку")
                self.BotIconStacked.setCurrentIndex(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    font = QFont("Consolas", 14)
    app.setFont(font)


    # === Создаём главное окно ===
    window = ChatWindow()

    # === Устанавливаем фильтр событий (передаём EyeTarget внутрь) ===
    app_event_filter = AppEventFilter(window.BotWidget)
    app.installEventFilter(app_event_filter)

    window.show()
    sys.exit(app.exec())
