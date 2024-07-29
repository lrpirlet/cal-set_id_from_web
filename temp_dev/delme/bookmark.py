# from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets
from PyQt6 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets

class BookMarkToolBar(QtWidgets.QToolBar):
    bookmarkClicked = QtCore.pyqtSignal(QtCore.QUrl, str)

    def __init__(self, parent=None):
        super(BookMarkToolBar, self).__init__(parent)
        self.actionTriggered.connect(self.onActionTriggered)
        self.bookmark_list = []

    def setBoorkMarks(self, bookmarks):
        for bookmark in bookmarks:
            self.addBookMarkAction(bookmark["title"], bookmark["url"])

    def addBookMarkAction(self, title, url):
        bookmark = {"title": title, "url": url}
        fm = QtGui.QFontMetrics(self.font())
        if bookmark not in self.bookmark_list:
            text = fm.elidedText(title, QtCore.Qt.TextElideMode.ElideRight, 150)
            action = self.addAction(text)
            action.setData(bookmark)
            self.bookmark_list.append(bookmark)

    @QtCore.pyqtSlot(QtWidgets.QAction)
    def onActionTriggered(self, action):
        bookmark = action.data()
        self.bookmarkClicked.emit(bookmark["url"], bookmark["title"])


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.defaultUrl = QtCore.QUrl()

        self.tabs = QtWidgets.QTabWidget()
        self.tabs.setTabsClosable(True)
        self.setCentralWidget(self.tabs)

        self.urlLe = QtWidgets.QLineEdit()
        self.urlLe.returnPressed.connect(self.onReturnPressed)
        self.favoriteButton = QtWidgets.QToolButton()
        self.favoriteButton.setIcon(QtGui.QIcon("images/star.png"))
        self.favoriteButton.clicked.connect(self.addFavoriteClicked)

        toolbar = self.addToolBar("")
        toolbar.addWidget(self.urlLe)
        toolbar.addWidget(self.favoriteButton)

        self.addToolBarBreak()
        self.bookmarkToolbar = BookMarkToolBar()
        self.bookmarkToolbar.bookmarkClicked.connect(self.add_new_tab)
        self.addToolBar(self.bookmarkToolbar)
        self.readSettings()

    def onReturnPressed(self):
        self.tabs.currentWidget().setUrl(QtCore.QUrl.fromUserInput(self.urlLe.text()))

    def addFavoriteClicked(self):
        loop = QtCore.QEventLoop()

        def callback(resp):
            setattr(self, "title", resp)
            loop.quit()

        web_browser = self.tabs.currentWidget()
        web_browser.page().runJavaScript("(function() { return document.title;})();", callback)
        url = web_browser.url()
        loop.exec_()
        self.bookmarkToolbar.addBookMarkAction(getattr(self, "title"), url)

    def add_new_tab(self, qurl=QtCore.QUrl(), label='Blank'):
        web_browser = QtWebEngineWidgets.QWebEngineView()
        web_browser.setUrl(qurl)
        web_browser.adjustSize()
        web_browser.urlChanged.connect(self.updateUlrLe)
        index = self.tabs.addTab(web_browser, label)
        self.tabs.setCurrentIndex(index)
        self.urlLe.setText(qurl.toString())

    def updateUlrLe(self, url):
        self.urlLe.setText(url.toDisplayString())

    def readSettings(self):
        setting = QtCore.QSettings()
        self.defaultUrl = setting.value("defaultUrl", QtCore.QUrl('http://www.google.com'))
        self.add_new_tab(self.defaultUrl, 'Home Page')
        self.bookmarkToolbar.setBoorkMarks(setting.value("bookmarks", []))

    def saveSettins(self):
        settings = QtCore.QSettings()
        settings.setValue("defaultUrl", self.defaultUrl)
        settings.setValue("bookmarks", self.bookmarkToolbar.bookmark_list)

    def closeEvent(self, event):
        self.saveSettins()
        super(MainWindow, self).closeEvent(event)


if __name__ == '__main__':
    import sys

    QtCore.QCoreApplication.setOrganizationName("eyllanesc.org")
    QtCore.QCoreApplication.setOrganizationDomain("www.eyllanesc.com")
    QtCore.QCoreApplication.setApplicationName("MyApp")
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())