# ===============================

# chipmaster_bot.py [ > chipmaster_bot.spec > ChatSPT.exe ]

import sys
from pathlib import Path

from PySide6.QtCore import Qt,QTimer
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QPushButton, QWidget, QVBoxLayout
from PySide6.QtGui import QPalette, QColor


# custom import: chipmaster_upd.py
import chipmaster_upd as updater  

# ===============================

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ChatSPT")
        self.setFixedSize(600, 400)

        # Красный фон
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor("black"))
        self.setPalette(palette)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        layout = QVBoxLayout()
        self.central_widget.setLayout(layout)

        # Кнопка вызова ChatSPT-Updater.exe 
        self.btn_updater = QPushButton("ChatSPT: Updater") 
        self.btn_updater.setFixedSize(200, 50)
        self.btn_updater.clicked.connect(updater.call_updater)
        layout.addStretch(1)
        layout.addWidget(self.btn_updater, 0, alignment=Qt.AlignHCenter)  # Qt.AlignHCenter | Qt.AlignVCenter
        layout.addStretch(1)


# пока убрал handoff для EXE > вернул, без него конфиг некорректно прописывается

# если конфиг существует, а в нём есть путь до ChatSPT.exe который отличается отличается от текущего запускаемого, 
# > запускаем из SPT_PATH (тот что в USER_PATH находится)

print("bfre_handoff_ChatSPT.exe")
exe_path = str(Path(sys.argv[0]).resolve())
path_key = "SPT_PATH"
if updater.try_handoff(current_exe=exe_path, path_config_key=path_key):
    sys.exit(0)
print("aftr_handoff_ChatSPT.exe")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyWindow()
    window.show()
    # Метод скрытой проверки новой версии ChatSPT.exe c гита
    QTimer.singleShot(1, lambda: updater.check_silent_spt_update(exe=exe_path))
    
    print(f"CHATSPT_LOAD ={exe_path}")

    sys.exit(app.exec())