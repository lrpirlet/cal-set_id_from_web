
# see https://www.pythonguis.com/tutorials/pyqt6-dialogs/

import sys

from PyQt6.QtWidgets import QApplication, QDialog, QMainWindow, QPushButton, QDialogButtonBox
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QHBoxLayout, 
                             QLabel, QPushButton, QVBoxLayout,
                             QGridLayout, QFrame, QLineEdit, QFormLayout, QScrollArea)
from PyQt6.QtGui import QFontMetrics, QCursor
from PyQt6.QtCore import Qt, pyqtSlot, pyqtSignal

PXLSIZE = 125

class Bookmark_Dialog(QDialog):
  # signal generated 
    srt_bkmrk_sgnl = pyqtSignal()
    add_bkmrk_sgnl = pyqtSignal(str)
    del_bkmrk_sgnl = pyqtSignal(str)
    home_bkmrk_sgnl = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.PXLSIZE = PXLSIZE

        self.setWindowTitle("Manage bookmark")

        bkmrk_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        label_layout = QGridLayout()

        srt_btn = QPushButton("Sort bookmark")
        add_btn = QPushButton("Add bookmark")
        add_btn.setDefault(True)
        del_btn = QPushButton("Delete bookmark")
        home_btn = QPushButton("Set home")

        button_layout.addWidget(srt_btn)
        button_layout.addWidget(add_btn)
        button_layout.addWidget(del_btn)
        button_layout.addWidget(home_btn)

        srt_btn.pressed.connect(self.activate_srt)
        add_btn.pressed.connect(self.activate_add)
        del_btn.pressed.connect(self.activate_del)
        home_btn.pressed.connect(self.activate_home)

        label1 = QLabel("Page name:")
        label2 = QLabel("Bookmark name:")

        self.bkmrk = QLabel()
        self.bkmrk.setFixedWidth(self.PXLSIZE) 
        self.bkmrk.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)

        self.pgtitle = QLineEdit()
        self.pgtitle.setFixedWidth(self.PXLSIZE*3)
        self.pgtitle.setToolTip("Edit this line until the Bookmark name does show on a green background to get a non truncated bookmark name")
        self.pgtitle.textChanged.connect(self.display_edited_bookmark)

        label_layout.addWidget(label1,       0, 0)
        label_layout.addWidget(self.pgtitle, 0, 1)
        label_layout.addWidget(label2,       1, 0)
        label_layout.addWidget(self.bkmrk,   1, 1)
        label_layout.setRowMinimumHeight(1, 30)
        
        bkmrk_layout.addLayout(label_layout)
        bkmrk_layout.addLayout(button_layout)

        self.setLayout(bkmrk_layout)

    @pyqtSlot(str)
    def display_edited_bookmark(self, bkmrk):
        print(f"in display_edited_bookmark, bookmark = {bkmrk}")
        fm = QFontMetrics(self.font())
        bkmrk = fm.elidedText(bkmrk, Qt.TextElideMode.ElideRight, self.PXLSIZE-5)
        if bkmrk[-1] == "…":
            self.bkmrk.setStyleSheet("background-color: red")
        else:
            self.bkmrk.setStyleSheet("background-color: lightgreen")
        self.bkmrk.setText(bkmrk)

    @pyqtSlot()
    def activate_srt(self):
        # self.stacklayout.setCurrentIndex(0)
        print("activate_sort")
        self.srt_bkmrk_sgnl.emit()

    @pyqtSlot()
    def activate_add(self):
        # self.stacklayout.setCurrentIndex(1)
        print(f"activate_add, title : {self.pgtitle.text()}")
        self.add_bkmrk_sgnl.emit(self.pgtitle.text())

    @pyqtSlot()
    def activate_del(self):
        # self.stacklayout.setCurrentIndex(2)
        print(f"activate_delete, title : {self.bookmark_title}")
        self.del_bkmrk_sgnl.emit(self.bookmark_title)

    @pyqtSlot()
    def activate_home(self):
        # self.stacklayout.setCurrentIndex(2)
        print("activate_home")
        self.home_bkmrk_sgnl.emit()

    def url_title(self, bookmark_title):
        print(f"in url_title, bookmark : {bookmark_title}")
        self.bookmark_title = bookmark_title
        self.pgtitle.setText(bookmark_title)
        self.pgtitle.setCursorPosition(0)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")

        button = QPushButton("Press me for a dialog!")
        button.clicked.connect(self.button_clicked)
        self.setCentralWidget(button)
        self.bkmrk_dlg = Bookmark_Dialog(self)

      # signals
        self.bkmrk_dlg.srt_bkmrk_sgnl.connect(self.srt_bkmrk)
        self.bkmrk_dlg.add_bkmrk_sgnl.connect(self.add_bkmrk)
        self.bkmrk_dlg.del_bkmrk_sgnl.connect(self.del_bkmrk)
        self.bkmrk_dlg.home_bkmrk_sgnl.connect(self.home_bkmrk)

      # signal handling

    @pyqtSlot()
    def srt_bkmrk(self):
        print("in srt_bkmrk, I 'just' need to develop some")

    @pyqtSlot(str)
    def add_bkmrk(self, bkmrk_title):
        print(f"in add_bkmrk, bkmrk_title : {bkmrk_title}")

    @pyqtSlot(str)
    def del_bkmrk(self, bookmark_title):
        print(f"in del_bkmrk, bkmrk_title : {bookmark_title}")

    @pyqtSlot()
    def home_bkmrk(self):
        print("in home_bkmrk,I 'just' need to develop some")

    @pyqtSlot(bool)
    def button_clicked(self, s):
        print("click", s)

        # bkmrk_dlg = Bookmark_Dialog(self)
        self.bkmrk_dlg.url_title("Enter your text, the longest the better... In fact I like even more text... a bit like that")
        self.cursor_pos = QCursor.pos()    
        self.bkmrk_dlg.move(self.cursor_pos.x()-4*PXLSIZE,self.cursor_pos.y()+10)

        if self.bkmrk_dlg.exec():
            print("Success!")
        else:
            print("Cancel!")

    

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
