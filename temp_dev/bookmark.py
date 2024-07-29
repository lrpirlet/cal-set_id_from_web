
#from PyQt6 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets

from PyQt6.QtCore import (pyqtSlot, QUrl, QSize, Qt, pyqtSignal, QTimer, QCoreApplication, QSettings, QEventLoop)
from PyQt6.QtWidgets import(QMainWindow, QToolBar, QLineEdit,QStatusBar, QProgressBar, 
                            QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QApplication, QTabWidget, QToolButton)
from PyQt6.QtGui import (QAction, QShortcut, QKeySequence, QIcon, QFontMetrics)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings

from pathlib import Path

class BookMarkToolBar(QToolBar):
    bookmarkClicked = pyqtSignal(QUrl, str)

    def __init__(self, parent=None):
        super(BookMarkToolBar, self).__init__(parent)
        self.actionTriggered.connect(self.onActionTriggered)
        self.bookmark_list = []

    def setBoorkMarks(self, bookmarks):
        for bookmark in bookmarks:
            self.addBookMarkAction(bookmark["title"], bookmark["url"])

    def addBookMarkAction(self, title, url):
        bookmark = {"title": title, "url": url}
        fm = QFontMetrics(self.font())
        if bookmark not in self.bookmark_list:
            text = fm.elidedText(title, Qt.TextElideMode.ElideRight, 150)
            action = self.addAction(text)
            action.setData(bookmark)
            self.bookmark_list.append(bookmark)

    @pyqtSlot(QAction)
    def onActionTriggered(self, action):
        bookmark = action.data()
        self.bookmarkClicked.emit(bookmark["url"], bookmark["title"])


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.defaultUrl = QUrl()

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.setCentralWidget(self.tabs)

        self.urlLe = QLineEdit()
        self.urlLe.returnPressed.connect(self.onReturnPressed)
        
        self.favoriteButton = QToolButton()
        # self.favoriteButton.setIcon(QIcon("images/star.png"))
        self.favoriteButton.setIcon(QIcon("./blue_icon/star.png"))
        self.favoriteButton.clicked.connect(self.addFavoriteClicked)

        toolbar = self.addToolBar("")
        toolbar.addWidget(self.urlLe)
        toolbar.addWidget(self.favoriteButton)

        self.addToolBarBreak()
        self.bookmarkToolbar = BookMarkToolBar()
        self.bookmarkToolbar.bookmarkClicked.connect(self.add_new_tab)
        self.addToolBar(self.bookmarkToolbar)
        self.readSettings()                             # initial fill of home, and remembered URL of interest

    def onReturnPressed(self):
        self.tabs.currentWidget().setUrl(QUrl.fromUserInput(self.urlLe.text()))

    def addFavoriteClicked(self):
        loop = QEventLoop()

        def callback(resp):
            setattr(self, "title", resp)
            loop.quit()

        web_browser = self.tabs.currentWidget()
        web_browser.page().runJavaScript("(function() { return document.title;})();", callback)
        url = web_browser.url()
        loop.exec()
        self.bookmarkToolbar.addBookMarkAction(getattr(self, "title"), url)

    def add_new_tab(self, qurl=QUrl(), label='Blank'):
        web_browser = QWebEngineView()
        web_browser.setUrl(qurl)
        web_browser.adjustSize()
        web_browser.urlChanged.connect(self.updateUlrLe)
        index = self.tabs.addTab(web_browser, label)
        self.tabs.setCurrentIndex(index)
        self.urlLe.setText(qurl.toString())

    def updateUlrLe(self, url):
        self.urlLe.setText(url.toDisplayString())

    def readSettings(self):
        # Path.home().as_posix() + '/.test_bookmark'
        setting = QSettings(Path.home().as_posix() + "/.test_bookmark/MyApp.ini", QSettings.Format.IniFormat) # avoid using registry
        self.defaultUrl = setting.value("defaultUrl", QUrl('http://www.google.com'))
        self.add_new_tab(self.defaultUrl, 'Home Page')
        self.bookmarkToolbar.setBoorkMarks(setting.value("bookmarks", []))

    def saveSettins(self):
        settings = QSettings(Path.home().as_posix() + "/.test_bookmark/MyApp.ini", QSettings.Format.IniFormat) # avoid using registry
        settings.setValue("defaultUrl", self.defaultUrl)
        settings.setValue("bookmarks", self.bookmarkToolbar.bookmark_list)

    def closeEvent(self, event):
        self.saveSettins()
        super(MainWindow, self).closeEvent(event)


if __name__ == '__main__':
    import sys

    QCoreApplication.setOrganizationName("eyllanesc.org")
    QCoreApplication.setOrganizationDomain("www.eyllanesc.com")
    QCoreApplication.setApplicationName("MyApp")
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())