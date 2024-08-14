# see https://stackoverflow.com/questions/51333771/removing-dynamically-created-qmenu-items

#!/usr/bin/env python
# vim:fileencoding=utf-8

__license__   = 'GPL v3'
__copyright__ = '2022, Louis Richard Pirlet'

from PyQt6.QtCore import (pyqtSlot, QUrl, QSize, Qt, pyqtSignal, QTimer, QSettings, QEventLoop)

from PyQt6.QtWidgets import(QMainWindow, QToolBar, QLineEdit, QStatusBar, QProgressBar, 
                            QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QDialog, QGridLayout, QFrame, QLineEdit, QMenu,
                            QListWidget, QListWidgetItem)

from PyQt6.QtGui import (QAction, QShortcut, QKeySequence, QIcon, QFontMetrics, QCursor)

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings

# from calibre.gui2 import Application # lrp
from PyQt6.QtWidgets import QApplication

from json import dumps
from functools import partial
import tempfile, os, sys, logging

from pathlib import Path

DEBUG = True
# DEBUG = False

class MainWindow(QWidget):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        layout = QHBoxLayout(self)

        menu_btn = QPushButton('menu btn')
        open_list_btn = QPushButton('open list')
        layout.addWidget(menu_btn)
        layout.addWidget(open_list_btn)

        menu = QMenu()
        menu_btn.setMenu(menu)

        self.menu_manager = MenuManager("menu_items", "Menu")
        menu.addMenu(self.menu_manager.menu)
        self.menu_manager.menu.triggered.connect(self.menu_clicked)
        open_list_btn.clicked.connect(self.menu_manager.show)

    def menu_clicked(self, action):
        itmData = action.data()
        print(f"content is : {itmData}")
        # content is : ['itemdata00', 'itemdata01', 'itemdata02']


class MenuManager(QWidget):
    def __init__(self, key, menuname, parent=None):
        super(MenuManager, self).__init__(parent)

        self.settings = QSettings(Path.home().as_posix() + "/.test_bookmark3/MyApp.ini", QSettings.Format.IniFormat) # avoid using registry
        self.key = key
        if  DEBUG : print(f"in class MenuManager; key : {key}, menuname : {menuname}")
        # in class MenuManager; key : menu_items, menuname : Menu
        self.layout = QVBoxLayout(self)
        self.listWidget = QListWidget()
        self.remove_btn = QPushButton('Remove')
        self.add_btn = QPushButton('add')
        self.layout.addWidget(self.listWidget)
        self.layout.addWidget(self.remove_btn)
        self.layout.addWidget(self.add_btn)
        self.remove_btn.clicked.connect(self.remove_items)
        self.add_btn.clicked.connect(self.add_item)

        self.menu = QMenu(menuname)
        self.load_settings()

    def load_settings(self):
        load_items = self.settings.value(self.key, [])
        if DEBUG : print(f"self.key : {self.key}")
        # 
        if DEBUG : print(f"load_items = self.settings.value(self.key, []) : {load_items}")
        # load_items = self.settings.value(self.key, []) : {'item0': ['itemdata00', 'itemdata01', 'itemdata02'], 'item1': ['itemdata10', 'itemdata11', 'itemdata12'], 'item2': ['itemdata20', 'itemdata21', 'itemdata22']}
        if not load_items: load_items = {}
        for bkmrk_title, bkmrk_url in load_items.items():
            if  DEBUG : print(f"bkmrk_title, bkmrk_url : {bkmrk_title, bkmrk_url}")
            # bkmrk_title, bkmrk_url : ('item0', ['itemdata00', 'itemdata01', 'itemdata02'])
            self.add_one_item(bkmrk_title, bkmrk_url)

    def remove_items(self):
        if  DEBUG : print("in remove_items")
        # in remove_items
        for item in self.listWidget.selectedItems():
            it = self.listWidget.takeItem(self.listWidget.row(item))
            action = it.data(Qt.ItemDataRole.UserRole)
            self.menu.removeAction(action)
        self.sync_data()

    def add_item(self):
        if  DEBUG : print("in add_item")
        # in add_item
        for i in range(5):
            bkmrk_title = "item{}".format(i)
            bkmrk_url = ["bkmrk_url{}{}".format(i, j) for j in range(3)]
            if  DEBUG : print(bkmrk_title, " : ", bkmrk_url)
            # item0  :  ['itemdata00', 'itemdata01', 'itemdata02']
            self.add_one_item(bkmrk_title, bkmrk_url)


    def add_one_item(self, bkmrk_title, bkmrk_url):
            if  DEBUG : print(f"in add_one_item; bkmrk_title : {bkmrk_title}, bkmrk_url : {bkmrk_url}")
            # in add_one_item; bkmrk_title : item0, bkmrk_url : ['itemdata00', 'itemdata01', 'itemdata02']
            if not self.listWidget.findItems(bkmrk_title, Qt.MatchFlag.MatchExactly):
                action = QAction(bkmrk_title, self.menu)
                action.setData(bkmrk_url)
                self.menu.addAction(action)

                item = QListWidgetItem(bkmrk_title)
                item.setData(Qt.ItemDataRole.UserRole, action)
                self.listWidget.addItem(item)
                self.sync_data()

    def sync_data(self):
        if  DEBUG : print("in sync_data")
        # in sync_data
        save_items = {}
        for i in range(self.listWidget.count()):
            it = self.listWidget.item(i)
            if  DEBUG : print(f"it.text() : {it.text()}")           
            # it.text() : item0
            action = it.data(Qt.ItemDataRole.UserRole)
            save_items[it.text()] = action.data()
            if  DEBUG : print(f"save_items[it.text()] = action.data() : {action.data()}")
            # save_items[it.text()] = action.data() : ['itemdata00', 'itemdata01', 'itemdata02']
        self.settings.setValue(self.key, save_items)
        if  DEBUG : print(f"self.settings.setValue(self.key, save_items); self.key : {self.key}, save_items {save_items}")
        # self.settings.setValue(self.key, save_items); self.key : menu_items, save_items {'item0': ['itemdata00', 'itemdata01', 'itemdata02']}
        self.settings.sync()

if __name__ == '__main__':

    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())