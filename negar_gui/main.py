#!/usr/bin/env python

"""negar-gui.

Usage:
    negar-gui -h
    negar-gui -v
    negar-gui

Options:
    -h, --help          Show this screen.
    -v, --version       Show version and exit
"""

import asyncio
import re
import sys
import tempfile
from pathlib import Path
from threading import Thread

import requests
import toml
from docopt import docopt
from pyperclip import copy as pyclipcopy
from PyQt5.QtCore import QAbstractTableModel, Qt, QTimer, QTranslator, QUrl, QSize, QPoint
from PyQt5.QtGui import QColor, QDesktopServices, QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog, QHeaderView, QMainWindow
import qdarktheme
from pyuca import Collator
from qrcode import ERROR_CORRECT_L, QRCode

# https://stackoverflow.com/questions/16981921
sys.path.append(Path(__file__).parent.parent.as_posix())
from negar.constants import INFO # noqa: E402
from negar.constants import __version__ as negar__version # noqa: E402
from negar.virastar import PersianEditor, UnTouchable # noqa: E402

from negar_gui.constants import LOGO, __version__, SETTING_FILE # noqa: E402
from negar_gui.Ui_hwin import Ui_Dialog # noqa: E402
from negar_gui.Ui_mwin import Ui_MainWindow # noqa: E402
from negar_gui.Ui_uwin import Ui_uwWindow # noqa: E402

NEGARGUIPATH = Path(__file__).parent.as_posix()

collator = Collator()

def init_decorator(func):
    def wrapper(*args, **kwargs):
        func(*args, **kwargs)
        self, parent = args[0], kwargs.pop("parent", None)
        # Maximize Frame Size if either height or width exceeds real screen dimensionsq
        screen = QApplication.desktop().screenGeometry()
        h, w = screen.height(), screen.width()
        if self.width() > w or self.height() > h:
            self.showMaximized()
        # set layout direction automatically
        if parent:
            try:
                self.centralwidget.setLayoutDirection(parent.layoutDirection())
            except: # QDialog  has no centralwidget
                pass
        # connect widgets to their proper slot
        self.connectSlots()
    return wrapper


class TableModel(QAbstractTableModel):

    def __init__(self, data):
        super().__init__()
        self._data = data

    def data(self, index, role):
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignVCenter
        if role == Qt.ItemDataRole.BackgroundRole:
            if index.row()%2:
                return QColor("gray")
        if role == Qt.ItemDataRole.ForegroundRole:
            if index.row()%2:
                return QColor("white")
        if role == Qt.ItemDataRole.DisplayRole:
            try:
                return self._data[index.row()][index.column()]
            except:
                return ""

    def rowCount(self, index):
        """Get length of the outer list."""
        del index
        return len(self._data)

    def columnCount(self, index):
        """Take the first sub-list, and returns the length.

        (only works if all rows are an equal length).
        """
        del index
        return len(self._data[0])

    def headerData(self, section, orientation, role):
        """Section is the index of the column/row."""
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return ""
            if orientation == Qt.Orientation.Vertical:
                return str(section+1)
        return None


class WindowSettings(QMainWindow):

    _settings = {}

    @property
    def settings(self):
        return self._settings

    @settings.setter
    def settings(self, value):
        self._settings = value


    def __save_settings(self):
        self.settings = {
            "window_size": {"width": self.width(), "height": self.height()},
            "window_position": {"x": self.x(), "y": self.y()},
        }

        with open(SETTING_FILE, "w") as toml_file:
            toml.dump(self.settings, toml_file)

        print("Settings Saved on Close!")

    def __load_settings(self):
        try:
            with open(SETTING_FILE) as toml_file:
                self.settings = toml.load(toml_file)
            window_size = QSize(
                self.settings["window_size"]["width"],
                self.settings["window_size"]["height"],
            )
            window_position = QPoint(
                self.settings["window_position"]["x"],
                self.settings["window_position"]["y"],
            )
            self.resize(window_size)
            self.move(window_position)
        except FileNotFoundError:
            print("Settings File Not Found!")
        except KeyError:
            print("Settings File Has Been Corrupted!")

    def closeEvent(self, event):
        del event
        self.__save_settings()

    def showEvent(self, event):
        # This method is called when the window is being shown
        # You can perform initialization tasks here
        del event
        self.__load_settings()


class UntouchWindow(QMainWindow, Ui_uwWindow):

    @init_decorator
    def __init__(self, parent=None):
        self.parent = parent
        super().__init__(parent)
        self.setupUi(self)
        self.setup_table()
        # if parent: self.centralwidget.setLayoutDirection(parent.layoutDirection())

    def setup_table(self, col=8):
        self.untouch_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        data = sorted(list(UnTouchable().get()), key=collator.sort_key)
        data = [data[i*col:(i+1)*col] for i in range(int(len(data)//col)+1)]
        model = TableModel(data)
        self.untouch_table.setModel(model)

    def connectSlots(self):
        self.untouch_word.textChanged.connect(self.untouch_add_enabler)
        self.untouch_button.clicked.connect(self.untouch_add)

    def untouch_add_enabler(self):
        """Enable `Add` button when a single word is entered in the untouchable text input."""
        word_list = self.untouch_word.text().split()
        self.untouch_button.setEnabled(len(word_list) == 1)

    def untouch_add(self):
        """Add a new word into untouchable words."""
        word = [self.untouch_word.text().strip()]
        UnTouchable.add(word)
        self.untouch_word.clear()
        self.setup_table() # updates untouchable list

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_F11:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event):
        del event
        if self.parent:
            self.parent.show()
            self.parent.edit_text()

class HelpWindow(QDialog, Ui_Dialog):

    @init_decorator
    def __init__(self, parent=None, title=None, label=None):
        self.parent = parent
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle(title)
        if isinstance(label, str):
            self.label.setText(label)
        if isinstance(label, QPixmap):
            self.label.setPixmap(label)
            # self.setFixedSize(QSize(600,600))

    def connectSlots(self):
        pass

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)


class MyWindow(WindowSettings, QMainWindow, Ui_MainWindow):

    @init_decorator
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.input_editor.setStyleSheet("border: 1px solid #d89e76;")
        self.output_editor.setStyleSheet("border: 1px solid #d89e76;")
        self.setWindowIcon(QIcon(LOGO))
        self.input_editor.setFocus(True)
        #  Translator
        self.trans = QTranslator()
        # destination language
        self.dest = "en"
        # ui language : 0->en, 1->fa
        self.lang = "English"
        self.editing_options = []
        self.clipboard = QApplication.clipboard()
        self.fileDialog = QFileDialog()
        self.filename = None # will be defined later
        self._statusBar()
        # Checks for new release
        Thread(target=lambda: asyncio.run(self.updateCheck()), daemon=True).start()

    async def updateCheck(self):
        nurl  = "https://raw.github.com/shahinism/python-negar/master/negar/constants.py"
        ngurl = "https://raw.github.com/javadr/negar-gui/master/negar_gui/constants.py"
        async def get(link):
            with requests.get(link) as response:
                VERSION_PATTERN = r'(__version__ = "(\d\.\d(\.\d+)?)")'
                return re.search(VERSION_PATTERN, response.text, re.M).group(2)
        try:
            requests.get("https://github.com") # check the internet connection
            negar_t = asyncio.create_task(get(nurl))
            negargui_t = asyncio.create_task(get(ngurl))
            negar_v = await negar_t
            negargui_v = await negargui_t
        except:
            negar_v, negargui_v = "0.0", "0.0"
        version = lambda v: list(map(int,v.split(".")))
        negar_nv, negargui_nv = (version(i) for i in (negar_v, negargui_v))
        negar_ov, negargui_ov = (version(i) for i in (negar__version, __version__))
        notification = ""
        message = "New version is available for {}. Use `pip install --upgrade {}` to update"
        if negar_nv>negar_ov:
            notification = message.format("negar", "python-negar")
        if negargui_nv>negargui_ov:
            notification = message.format("negar-gui", "negar-gui")
        self._statusBar(f"{notification}" if notification!=message else "")

    def connectSlots(self):
        self.autoedit_handler()
        # connect to slots
        self.autoedit_chkbox.stateChanged.connect(self.autoedit_handler)
        self.edit_btn.clicked.connect(self.edit_text)
        self.actionOpen.triggered.connect(self.openFileSlot)
        self.actionSave.triggered.connect(self.saveFileSlot)
        self.actionExport.triggered.connect(self.exportFileSlot)
        self.actionExit.triggered.connect(self.close)
        self.font_slider.valueChanged.connect(self._set_font_size)
        self.actionIncrease_Font_Size.triggered.connect(
            lambda: (self.font_slider.setValue(self.font_slider.value()+1), self._set_font_size()),
        )
        self.actionDecrease_Font_Size.triggered.connect(
            lambda: (self.font_slider.setValue(self.font_slider.value()-1), self._set_font_size()),
        )
        self.actionPersian.triggered.connect(lambda: self.changeLanguage("Persian"))
        self.actionEnglish.triggered.connect(lambda: self.changeLanguage("English"))

        self.actionNegar_Help.triggered.connect(lambda: self.input_editor.setText(INFO) )
        self.actionAbout_Negar.setShortcut("CTRL+H")
        self.actionAbout_Negar.triggered.connect(lambda:
            (HelpWindow(parent=self, title="About Negar", label=self.edit_text(INFO)).show()),
        )
        self.actionAbout_Negar_GUI.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/javadr/negar-gui")),
        )
        self.actionDonate.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/javadr/negar-gui#donation")),
        )
        self.actionReport_Bugs.triggered.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://github.com/javadr/negar-gui/issues")),
        )
        self.actionFix_Dashes.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionFix_three_dots.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionFix_English_quotes.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionFix_hamzeh.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionUse_Persian_yeh_to_show_hamzeh.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionFix_spacing_braces_and_quotes.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionFix_Arabic_numbers.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionFix_English_numbers.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionFix_non_Persian_chars.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionFix_prefix_spacing.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionFix_prefix_separating.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionFix_suffix_spacing.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionFix_suffix_separating.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionFix_aggressive_punctuation.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionCleanup_kashidas.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionCleanup_extra_marks.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionCleanup_spacing.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionTrim_Leading_Trailing_Whitespaces.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionExaggerating_ZWNJ.triggered.connect(
            lambda: (self.option_control(), self.autoedit_handler()))
        self.actionUntouchable_Words.triggered.connect(
            lambda: (UntouchWindow(parent=self).show(), MAIN_WINDOW.hide()))
        self.actionCopy.triggered.connect(self.copy_slot)
        self.copy_btn.clicked.connect(self.copy_slot)

        self.actionInteractive_Clipboard.triggered.connect(lambda:
            self.clipboard.dataChanged.connect(self.onClipboardChanged)
            if self.actionInteractive_Clipboard.isChecked()
            else self.clipboard.dataChanged.disconnect(self.onClipboardChanged))
        self.actionQr_Code.triggered.connect(self.qrcode)

        self.vertical_btn.clicked.connect(
            lambda: (self.actionSide_by_Side_View.setChecked(True), self._grid_layout("v")) )
        self.horizontal_btn.clicked.connect(
            lambda: (self.actionSide_by_Side_View.setChecked(False), self._grid_layout("h")) )
        self.actionSide_by_Side_View.triggered.connect(lambda:
            self._grid_layout("v") if self.actionSide_by_Side_View.isChecked() else self._grid_layout("h")
        )

        self.actionFull_Screen_Input.triggered.connect(lambda:
            (
                self._grid_full_input() if self.actionFull_Screen_Input.isChecked() else
                self._grid_layout("v") if self.actionSide_by_Side_View.isChecked() else
                self._grid_layout("h")
            ),
        )

        self.action_dark.triggered.connect(lambda:
            qdarktheme.setup_theme("dark",
            custom_colors={
                "[dark]": {
                    "primary": "#D0BCFF",
                    "primary>button.hoverBackground": "#ffffff",
                },
            }) )
        self.action_Light.triggered.connect(lambda: qdarktheme.setup_theme("light") )
        self.action_Auto.triggered.connect(lambda: qdarktheme.setup_theme("auto") )

    # Change GridLayout Orientation
    def _grid_layout(self, layout="h"):
        if layout=="v":
            self.gridLayout.setHorizontalSpacing(5)
        elif layout == "h":
            self.gridLayout.setVerticalSpacing(0)
        widgets = (self.input_editor_label, self.input_editor,
                    self.output_editor_label, self.output_editor)
        for widget in widgets:
            self.gridLayout.removeWidget(widget)
            widget.setParent(None)
        elements = (
            (0, 0, 1, 1),  # Position: 0x0 1 rowspan 1 colspan
            (1, 0, 1, 1),  # Position: 1x0 1 rowspan 1 colspan
            (0, 1, 1, 1),  # Position: 0x1 1 rowspan 1 colspan
            (1, 1, 1, 1),  # Position: 1x1 1 rowspan 1 colspan
        ) if layout=="v" else (
            (0, 0, 1, 2),  # Position: 0x0 1 rowspan 2 colspan
            (1, 0, 1, 2),  # Position: 1x0 1 rowspan 2 colspan
            (2, 0, 1, 2),  # Position: 2x0 1 rowspan 2 colspan
            (3, 0, 1, 2),  # Position: 3x0 1 rowspan 2 colspan
        )
        for i, widget in enumerate(widgets):
            self.gridLayout.addWidget(widget, *elements[i])

    def _grid_full_input(self):
        widgets = (self.output_editor_label, self.output_editor)
        for widget in widgets:
            self.gridLayout.removeWidget(widget)
            widget.setParent(None)

    def qrcode(self):
        if len(self.output_editor.toPlainText().strip())==0:
            if self.lang == "Persian":
                statusbar_timeout(self, "هیچ متنی برای نمایش از طریق کد QR وجود ندارد!")
            else: # English
                statusbar_timeout(self, "There is no text to be fed to the QR Code!")
            return
        qr = QRCode(
            version = 1,
            error_correction = ERROR_CORRECT_L,
            box_size = 10,
            border = 4,
        )
        qr.add_data(self.output_editor.toPlainText())
        qr.make(fit = True)
        img = qr.make_image()
        temp_path = Path(tempfile.gettempdir())
        img.save(temp_path/"negar-gui_qrcode.png")
        pixmap = QPixmap(f"{(temp_path/'negar-gui_qrcode.png').absolute()}")
        screen = QApplication.desktop().screenGeometry()
        w = min(screen.height(), screen.width())
        if w-90 < img.size[0]:
            pixmap = pixmap.scaled(w-90, w-90, Qt.KeepAspectRatio)
        HelpWindow(parent=self, title="QR Code", label=pixmap).show()
        (Path(temp_path)/"negar-gui_qrcode.png").unlink()

    def _statusBar(self, notification="", timeout=0):
        message = f"Negar v{negar__version} [[Negar-GUI v{__version__}]] {notification}"
        self.statusBar.showMessage(message, timeout)

    def openFileSlot(self):
        filename, _ = self.fileDialog.getOpenFileName(self, "Open File - A Plain Text", ".")
        if filename:
            with open(filename, encoding="utf-8") as f:
                try:
                    self.input_editor.setPlainText(str(f.read()))
                    self.filename = Path(filename)
                    MAIN_WINDOW.setWindowTitle(f"Negar - {self.filename.name}")
                    statusbar_timeout(self,"File Opened.")
                except Exception as e:
                    self.input_editor.setPlainText(e.args[1])

    def saveFileSlot(self):
        if not self.output_editor.toPlainText():
            return
        if hasattr(self, "filename") and self.filename:
            with open(self.filename, "w", encoding="utf-8") as f:
                try:
                    f.write(self.output_editor.toPlainText())
                    statusbar_timeout(self,"File Saved.")
                except Exception as e:
                    self.output_editor.setPlainText(e.args[1])
        else:
            self.exportFileSlot()

    def exportFileSlot(self):
        if not self.output_editor.toPlainText():
            return
        filename, _ = self.fileDialog.getSaveFileName(self, "Save File", ".")
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                try:
                    f.write(self.output_editor.toPlainText())
                    self.filename = Path(filename)
                    MAIN_WINDOW.setWindowTitle(f"Negar - {self.filename.name}")
                    statusbar_timeout(self,"File Saved.")
                except Exception as exception:
                    self.output_editor.setPlainText(exception.args[1])

    def changeLanguage(self, lang):
        """Change ui language."""
        if lang=="Persian" and self.lang!="Persian":
            self.lang = "Persian"
            self.trans.load("fa", directory=f"{NEGARGUIPATH}/ts")
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            self.centralwidget.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            self.autoedit_chkbox.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            self.statusBar.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        elif lang=="English" and self.lang!="English":
            self.lang = "English"
            self.trans.load("en")
            self.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            self.centralwidget.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            self.autoedit_chkbox.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        else:
            return
        _app = QApplication.instance()
        _app.installTranslator(self.trans)
        self.retranslateUi(self)

    # def retranslateUi(self, MyWindow):
        # super(MyWindow, self).retranslateUi()
        # _translate = QtCore.QCoreApplication.translate
        # print(dir(self))
        # MyWindow.fileDialog.setText(_translate(self.fileDialog.name(), "Open File - A Plain Text"))
        # pass

    def copy_slot(self):
        output = self.output_editor.toPlainText()
        if output:
            QApplication.clipboard().setText(output)
        return output

    def onClipboardChanged(self):
        text = self.clipboard.text()
        if text:
            self.input_editor.setPlainText(text)
            self._set_font_size()

    def closeEvent(self, event):
        WindowSettings.closeEvent(self, event)
        del event
        # event = QEvent(QEvent.Clipboard)
        # QApplication.sendEvent(QApplication.clipboard(), event)
        pyclipcopy(self.copy_slot())
        self.__save_settings()

    def showEvent(self, event):
        WindowSettings.showEvent(self, event)
        del event
        self.__load_settings()

    def __load_settings(self):
        try:
            with open(SETTING_FILE) as toml_file:
                self.settings.update(toml.load(toml_file))
            ## view menu
            self.actionSide_by_Side_View.setChecked(self.settings["view"]["side-by-side"])
            self.actionFull_Screen_Input.setChecked(self.settings["view"]["full-screen-input"])
            ( # check full screen or horizontal/vertical layout
                self._grid_full_input() if self.actionFull_Screen_Input.isChecked() else
                self._grid_layout("v") if self.actionSide_by_Side_View.isChecked() else
                self._grid_layout("h")
            )
            self.font_slider.setValue(self.settings["view"]["font-size"]),
            self.autoedit_chkbox.setChecked(self.settings["view"]["real-time-edit"]),
            ## settings menu
            self.actionInteractive_Clipboard.setChecked(self.settings["settings"]["interactive-clipboard"])
            ### connect interactive clipboard slot if it is checked
            if self.actionInteractive_Clipboard.isChecked():
                self.clipboard.dataChanged.connect(self.onClipboardChanged)
            ## settings.editing-options
            sdict = self.settings["settings"]["editing-option"]
            self.actionFix_Dashes.setChecked(sdict["fix-dashes"])
            self.actionFix_three_dots.setChecked(sdict["fix-three-dots"])
            self.actionFix_English_quotes.setChecked(sdict["fix-english-quotes"])
            self.actionFix_hamzeh.setChecked(sdict["fix-hamzeh"])
            self.actionUse_Persian_yeh_to_show_hamzeh.setChecked(sdict["hamzeh-with-yeh"])
            self.actionFix_spacing_braces_and_quotes.setChecked(sdict["fix-spacing-bq"])
            self.actionFix_Arabic_numbers.setChecked(sdict["fix-arabic-num"])
            self.actionFix_English_numbers.setChecked(sdict["fix-english-num"])
            self.actionFix_non_Persian_chars.setChecked(sdict["fix-non-persian-chars"])
            self.actionFix_prefix_spacing.setChecked(sdict["fix-p-spacing"])
            self.actionFix_prefix_separating.setChecked(sdict["fix-p-separate"])
            self.actionFix_suffix_spacing.setChecked(sdict["fix-s-spacing"])
            self.actionFix_suffix_separating.setChecked(sdict["fix-s-separate"])
            self.actionFix_aggressive_punctuation.setChecked(sdict["aggressive"])
            self.actionCleanup_kashidas.setChecked(sdict["cleanup-kashidas"])
            self.actionCleanup_extra_marks.setChecked(sdict["cleanup-ex-marks"])
            self.actionCleanup_spacing.setChecked(sdict["cleanup-spacing"])
            self.actionTrim_Leading_Trailing_Whitespaces.setChecked(sdict["trim-lt-whitespaces"])
            self.actionExaggerating_ZWNJ.setChecked(sdict["exaggerating-zwnj"])
        except FileNotFoundError:
            print("Settings File Not Found!")
        except KeyError:
            print("Settings File Has Been Corrupted!")

    def __save_settings(self):
        settings = {
            "view": {
                "side-by-side": self.actionSide_by_Side_View.isChecked(),
                "full-screen-input": self.actionFull_Screen_Input.isChecked(),
                "font-size": self.font_slider.value(),
                "real-time-edit": self.autoedit_chkbox.isChecked(),
            },
            "settings": {
                "interactive-clipboard": self.actionInteractive_Clipboard.isChecked(),
                "editing-option": {
                    "fix-dashes": self.actionFix_Dashes.isChecked(),
                    "fix-three-dots": self.actionFix_three_dots.isChecked(),
                    "fix-english-quotes": self.actionFix_English_quotes.isChecked(),
                    "fix-hamzeh": self.actionFix_hamzeh.isChecked(),
                    "hamzeh-with-yeh": self.actionUse_Persian_yeh_to_show_hamzeh.isChecked(),
                    "fix-spacing-bq": self.actionFix_spacing_braces_and_quotes.isChecked(),
                    "fix-arabic-num": self.actionFix_Arabic_numbers.isChecked(),
                    "fix-english-num": self.actionFix_English_numbers.isChecked(),
                    "fix-non-persian-chars": self.actionFix_non_Persian_chars.isChecked(),
                    "fix-p-spacing": self.actionFix_prefix_spacing.isChecked(),
                    "fix-p-separate": self.actionFix_prefix_separating.isChecked(),
                    "fix-s-spacing": self.actionFix_suffix_spacing.isChecked(),
                    "fix-s-separate": self.actionFix_suffix_separating.isChecked(),
                    "aggressive": self.actionFix_aggressive_punctuation.isChecked(),
                    "cleanup-kashidas": self.actionCleanup_kashidas.isChecked(),
                    "cleanup-ex-marks": self.actionCleanup_extra_marks.isChecked(),
                    "cleanup-spacing": self.actionCleanup_spacing.isChecked(),
                    "trim-lt-whitespaces": self.actionTrim_Leading_Trailing_Whitespaces.isChecked(),
                    "exaggerating-zwnj": self.actionExaggerating_ZWNJ.isChecked(),
                },
            },
        }
        settings.update(self.settings)
        with open(SETTING_FILE, "w") as toml_file:
            toml.dump(settings, toml_file)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_F11:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        modifiers = QApplication.keyboardModifiers()
        if modifiers == Qt.ControlModifier:
            delta_notches = int(event.angleDelta().y() / 120)
            self.font_slider.setValue(self.font_slider.value()+delta_notches)
            self._set_font_size()

    def autoedit_handler(self):
        """Edits the input text automatically if `autoedit` is checked."""
        if self.autoedit_chkbox.isChecked():
            self.edit_btn.setEnabled(False)
            self.input_editor.textChanged.connect(self.edit_text)
        else:
            self.edit_btn.setEnabled(True)
            # This line will disconnect autoedit signal and will disable autoamtic edit option
            self.input_editor.textChanged.disconnect(self.edit_text)
        self._set_font_size()

    def _set_font_size(self):
        size = self.font_slider.value()
        self.input_editor.setFontPointSize(size)
        self.output_editor.setFontPointSize(size)
        lines = self.input_editor.toPlainText()
        self.input_editor.clear()
        self.input_editor.append(lines)
        self.edit_text()

    def option_control(self):
        """Enable/Disable Editing features."""
        self.editing_options = []
        if not self.actionFix_Dashes.isChecked():
            self.editing_options.append("fix-dashes")
        if not self.actionFix_three_dots.isChecked():
            self.editing_options.append("fix-three-dots")
        if not self.actionFix_English_quotes.isChecked():
            self.editing_options.append("fix-english-quotes")
        if not self.actionFix_hamzeh.isChecked():
            self.editing_options.append("fix-hamzeh")
        if not self.actionUse_Persian_yeh_to_show_hamzeh.isChecked():
            self.editing_options.append("hamzeh-with-yeh")
        if not self.actionFix_spacing_braces_and_quotes.isChecked():
            self.editing_options.append("fix-spacing-bq")
        if not self.actionFix_Arabic_numbers.isChecked():
            self.editing_options.append("fix-arabic-num")
        if not self.actionFix_English_numbers.isChecked():
            self.editing_options.append("fix-english-num")
        if not self.actionFix_non_Persian_chars.isChecked():
            self.editing_options.append("fix-non-persian-chars")
        if not self.actionFix_prefix_spacing.isChecked():
            self.editing_options.append("fix-p-spacing")
        if not self.actionFix_prefix_separating.isChecked():
            self.editing_options.append("fix-p-separate")
        if not self.actionFix_suffix_spacing.isChecked():
            self.editing_options.append("fix-s-spacing")
        if not self.actionFix_suffix_separating.isChecked():
            self.editing_options.append("fix-s-separate")
        if not self.actionFix_aggressive_punctuation.isChecked():
            self.editing_options.append("aggressive")
        if not self.actionCleanup_kashidas.isChecked():
            self.editing_options.append("cleanup-kashidas")
        if not self.actionCleanup_extra_marks.isChecked():
            self.editing_options.append("cleanup-ex-marks")
        if not self.actionCleanup_spacing.isChecked():
            self.editing_options.append("cleanup-spacing")
        if not self.actionTrim_Leading_Trailing_Whitespaces.isChecked():
            self.editing_options.append("trim-lt-whitespaces")
        if not self.actionExaggerating_ZWNJ.isChecked():
            self.editing_options.append("exaggerating-zwnj")

    def edit_text(self, text=None):
        if not text:
            self.output_editor.clear()
            persian_editor = PersianEditor(self.input_editor.toPlainText(), *self.editing_options)
            self.output_editor.append(persian_editor.cleanup())
        else:
            return PersianEditor(text, *self.editing_options).cleanup()


def statusbar_timeout(self, notification, timeout=5000): # Timeout in milliseconds
    self.statusBar.showMessage(notification, timeout)
    timer = QTimer()
    timer.setSingleShot( True )
    timer.timeout.connect( self.statusBar.clearMessage )
    timer.start(timeout)

def main(args=docopt(__doc__)):
    """Program entry point."""
    if args["--version"]:
        print (f"negar-gui, Version {__version__}")
        sys.exit()

    global MAIN_WINDOW
    qdarktheme.enable_hi_dpi()
    app = QApplication(sys.argv)
    qdarktheme.setup_theme("dark")
    MAIN_WINDOW = MyWindow()
    MAIN_WINDOW.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
