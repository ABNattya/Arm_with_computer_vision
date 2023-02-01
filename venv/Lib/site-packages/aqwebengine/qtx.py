engine = None
import importlib

for engine in ('PyQt5', 'PySide2', 'PySide6'):
    try:
        importlib.import_module(engine + '.QtWebEngineWidgets')
        break
    except ModuleNotFoundError:
        pass
else:
    raise RuntimeError('No Qt engine found. Please, install PyQt5+PyQtWebEngine, or PySide2, or PySide6')

if engine == 'PyQt5':
    from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEngineScript, QWebEngineSettings
    from PyQt5.QtWebChannel import QWebChannel
    from PyQt5.QtCore import QFile, QIODevice, pyqtSlot as Slot, QObject, pyqtSignal as Signal, QUrl
    from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QWidget

elif engine == 'PySide2':
    from PySide2.QtWebEngineWidgets import QWebEngineView, QWebEngineScript, QWebEngineSettings
    from PySide2.QtWebChannel import QWebChannel
    from PySide2.QtCore import QFile, QIODevice, Slot, QObject, Signal, QUrl
    from PySide2.QtWidgets import QPushButton, QVBoxLayout, QWidget
