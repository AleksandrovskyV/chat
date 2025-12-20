# chipmaster.spec

import sys,os
from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_submodules
from PyInstaller.building.build_main import TOC

exe_name = "ChatSPT.exe"
icon_path = "./assets/ChatSPT.ico"

debug_flag = False

project_dir = os.getcwd()

# --- Сбор assets ---
asset_files = []
for foldername, _, filenames in os.walk(os.path.join(project_dir, "assets")):
    for filename in filenames:
        full_path = os.path.join(foldername, filename)
        # Папка назначения — assets + относительный путь к папке внутри assets
        target_dir = os.path.relpath(foldername, project_dir)  # например 'assets/animated/Setting_Icon'
        asset_files.append((full_path, target_dir))

# --- Сбор data ---
data_files = []
for foldername, _, filenames in os.walk(os.path.join(project_dir, "data")):
    for filename in filenames:
        full_path = os.path.join(foldername, filename)
        target_dir = os.path.relpath(foldername, project_dir)
        data_files.append((full_path, target_dir))


# Только нужные DLL
bin_dir = os.path.join(project_dir, 'bin')
needed_dlls = [
   # ('PySide6/Qt6Core.dll', 'PySide6'),
   # ('PySide6/Qt6Gui.dll', 'PySide6'),
   # ('PySide6/Qt6Widgets.dll', 'PySide6'),
   # ('PySide6/Qt6Multimedia.dll', 'PySide6'),
]

binaries = []
for dll_path, target_dir in needed_dlls:
    src = os.path.join(bin_dir, dll_path)
    binaries.append((src, target_dir))

a = Analysis(
    ['chipmaster_bot.py'],  # путь к твоему скрипту
    pathex=[project_dir],
    binaries=binaries,
    datas=asset_files + data_files,
    #datas=collect_data_files('./assets'),  # или укажи вручную пути к папке assets
    hiddenimports=collect_submodules("submodules"),
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        "PySide6.Qt3DCore",
        "PySide6.Qt3DRender",
        "PySide6.Qt3DInput",
        "PySide6.QtBluetooth",
        "PySide6.QtCharts",
        "PySide6.QtSensors",
        "PySide6.QtSerialPort",
        "PySide6.QtSql",
        "PySide6.QtTest",
        "PySide6.QtWebEngine",
        "PySide6.QtWebSockets",
        "PySide6.QtLocation",
        "PySide6.QtDataVisualization",
        "PySide6.QtQuick", # новый текст
        "PySide6.QtQml",   # новый текст
        #"PySide6.QtMultimedia", # когда будешь добавлять звук убери
        "PyQt5",
        "PyQt6",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

excluded_dlls = [
    #"MSVCP140.dll",
    #"MSVCP140_1.dll",
    #"MSVCP140_2.dll",
    #"pyside6.abi3.dll",

    #"Qt6Core.dll",
    #"Qt6Gui.dll",
    "Qt6Multimedia.dll", #для multimedia
    "Qt6Network.dll", #для multimedia
    #"Qt6Widgets.dll",

    #"VCRUNTIME140.dll",
    #"VCRUNTIME140_1.dll",
     
     #Plugins
    "opengl32sw.dll",
    "Qt6OpenGL.dll",
    "Qt6Pdf.dll",
    "Qt6Qml.dll", # новый текст
    "Qt6QmlMeta.dll",
    "Qt6QmlModels.dll",
    "Qt6QmlWorkerScript.dll",
    "Qt6Quick.dll", #новый текст
    #"Qt6Svg.dll",
    "Qt6VirtualKeyboard.dll",
    "qtuiotouchplugin.dll",
    #"qsvgicon.dll",
    #"qgif.dll",
    #"qicns.dll",
    #"qico.dll",
    #"qjpeg.dll",
    "qpdf.dll",
    #"qsvg.dll",
    "qtga.dll",
    "qtiff.dll",
    "qwbmp.dll",
    "qwebp.dll",
    "qnetworklistmanager.dll",
    "qtvirtualkeyboardplugin.dll",
    "qdirect2d.dll",
    "qminimal.dll",
    "qoffscreen.dll",
    #"qwindows.dll",
    "qmodernwindowsstyle.dll",
    "qcertonlybackend.dll",
    "qopensslbackend.dll",
    "qschannelbackend.dll",
    
    #"shiboken6.abi3.dll",

    "ffmpegmediaplugin.dll",
    "windowsmediaplugin.dll",
]

a.binaries = TOC([b for b in a.binaries if os.path.basename(b[0]) not in excluded_dlls])

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=exe_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=debug_flag,
    icon=icon_path,  # иконка из PackageMode
)