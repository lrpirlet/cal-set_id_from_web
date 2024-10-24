#!/usr/bin/env python
# vim:fileencoding=utf-8

__license__   = 'GPL v3'
__copyright__ = '2022, Louis Richard Pirlet'

# from qt.webengine import QWebEngineView, QWebEnginePage, QWebEngineProfile

# from qt.core import (pyqtProperty, pyqtSignal, pyqtSlot, QAction, QApplication,
#                 QBrush, QByteArray, QCheckBox, QColor, QColorDialog, QComboBox,
#                 QCompleter, DateTime, QDialog, QDialogButtonBox, QEasingCurve,
#                 QEvent, QFont, QFontInfo, QFontMetrics, QFormLayout, QGridLayout,
#                 QHBoxLayout, QIcon, QInputDialog, QKeySequence, QLabel, QLineEdit,
#                 QListView, QMainWindow, QMenu, QMenuBar, QSettings, QClipboard,
#                 QMessageBox, QModelIndex, QObject, QPainter, QPalette, QPixmap,
#                 QPlainTextEdit, QProgressBar, QPropertyAnimation, QPushButton,
#                 QShortcut, QSize, QSizePolicy, QSplitter, QStackedWidget, QStatusBar,
#                 QStyle, QStyleOption, QStylePainter, QSyntaxHighlighter, Qt, QTabBar,
#                 QTabWidget, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextEdit,
#                 QTextFormat, QTextListFormat, QTimer, QToolBar, QToolButton, QUrl,
#                 QVBoxLayout, QWidget, Qt
# )
from PyQt6.QtCore import (pyqtSlot, QUrl, QSize, Qt, pyqtSignal, QTimer, QSettings, QEventLoop)

from PyQt6.QtWidgets import(QMainWindow, QToolBar, QLineEdit, QStatusBar, QProgressBar,
                            QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QDialog, QGridLayout, QFrame, QLineEdit, QMenu,
                            QListWidget, QListWidgetItem, QVBoxLayout)

from PyQt6.QtGui import (QAction, QShortcut, QKeySequence, QIcon, QFontMetrics, QCursor)

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile

from calibre.gui2 import Application
from calibre.constants import cache_dir

from json import dumps
from functools import partial
import tempfile, glob, os, sys, logging

PXLSIZE = 125   # I need this constant in several classes

try:
    load_translations()
except NameError:
    pass

class StreamToLogger():
    """
    Fake file-like stream object that redirects writes to a logger instance.
    This will help when the web browser in web_main does not pop-up (read: web_main crashes)
    """
    def __init__(self, logger, log_level=logging.INFO):
      self.logger = logger
      self.log_level = log_level
      self.linebuf = ''

    def write(self, buf):
      for line in buf.rstrip().splitlines():
         self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        for handler in self.logger.handlers:
            handler.flush()

class Bookmark_add_Dialog(QDialog):
  # signal generated
    add_bkmrk_sgnl = pyqtSignal(str)
    home_bkmrk_sgnl = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.dbg = False
        self.PXLSIZE = PXLSIZE

        self.setWindowTitle(_("Bookmark manager")) # ("Gestion des favoris")

        bkmrk_layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        label_layout = QGridLayout()

        add_btn = QPushButton(_("Add bookmark"))
        add_btn.setDefault(True)
        home_btn = QPushButton(_("Set home"))

        button_layout.addWidget(add_btn)
        button_layout.addWidget(home_btn)

        add_btn.pressed.connect(self.activate_add)
        home_btn.pressed.connect(self.activate_home)

        label1 = QLabel(_("Page name:"))
        label2 = QLabel(_("Bookmark name:"))

        self.bkmrk = QLabel()
        self.bkmrk.setFixedWidth(self.PXLSIZE)
        self.bkmrk.setFrameStyle(QFrame.Shape.Panel | QFrame.Shadow.Sunken)

        self.pgtitle = QLineEdit()
        self.pgtitle.setFixedWidth(self.PXLSIZE*3)
        self.pgtitle.setToolTip(_("Edit this line until the Bookmark name does show on a green background to get a non truncated bookmark name"))
        self.pgtitle.textChanged.connect(self.display_edited_bookmark)

        label_layout.addWidget(label1,       0, 0)
        label_layout.addWidget(self.pgtitle, 0, 1, 1, 3)
        label_layout.addWidget(label2,       1, 0)
        label_layout.addWidget(self.bkmrk,   1, 1)
        label_layout.setRowMinimumHeight(1, 30)

        bkmrk_layout.addLayout(label_layout)
        bkmrk_layout.addLayout(button_layout)

        self.setLayout(bkmrk_layout)

    @pyqtSlot(str)
    def display_edited_bookmark(self, bkmrk):
        if self.dbg : print(f"in display_edited_bookmark, bookmark = {bkmrk}")
        fm = QFontMetrics(self.font())
        bkmrk = fm.elidedText(bkmrk, Qt.TextElideMode.ElideRight, self.PXLSIZE-5)
        if bkmrk[-1] == "…":
            self.bkmrk.setStyleSheet("background-color: red")
        else:
            self.bkmrk.setStyleSheet("background-color: lightgreen")
        self.bkmrk.setText(bkmrk)

    @pyqtSlot()
    def activate_add(self):
        if self.dbg : print(f"in activate_add, title : {self.pgtitle.text()}")
        self.add_bkmrk_sgnl.emit(self.pgtitle.text())
        self.close()

    @pyqtSlot()
    def activate_home(self):
        if self.dbg : print("in activate_home")
        self.home_bkmrk_sgnl.emit()
        self.close()

    def bkmrk_title(self, bookmark_title):
        if self.dbg : print("in bkmrk_title")
        self.bookmark_title = bookmark_title
        self.pgtitle.setText(bookmark_title)
        self.pgtitle.setCursorPosition(0)

    def set_debug(self):
        self.dbg = True

class Bookmark_rem_Dialog(QDialog):

  # signal generated
    rem_bkmrk_sgnl = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.dbg = False
        self.PXLSIZE = PXLSIZE

        self.setWindowTitle(_("Bookmark\n to remove"))
        self.setFixedWidth(PXLSIZE+35)

        self.layout = QVBoxLayout(self)
        self.remove_btn = QPushButton(_('Remove'))
        self.remove_btn.setFixedWidth(PXLSIZE)
        self.layout.addWidget(self.remove_btn)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        self.remove_btn.clicked.connect(self.remove_items)

    def set_listWidget(self, listWidget):
        if self.dbg : print("in set_listWidget")
        self.listWidget = listWidget
        self.layout.addWidget(self.listWidget)

    @pyqtSlot()
    def remove_items(self):
        if self.dbg : print("in remove_items")
        lst = []
        for item in self.listWidget.selectedItems():
            lst.append(self.listWidget.row(item))
        if self.dbg : print(f"list of item's row to remove : {lst}")
        self.rem_bkmrk_sgnl.emit(lst)
        self.close()

    def set_debug(self):
        self.dbg = True

class BookMarkToolBar(QToolBar):
    '''
    Create a bookmark button in the toolbar. On press of this button,
    a dialog box will open giving the possibility to sort the bookmarks, to add
    a bookmark or to remove the matching bookmark.
    The Bookmark name can be edited from the page title.
    On click on a bookmark item, the webengine will go to the corresponding url.
    '''
  # signal generated for a press on a bookmark item in the bookmark (vertical) bar
    bookmark_clicked = pyqtSignal(str)
    set_url_home = pyqtSignal(str)

    def __init__(self, parent=None):
        super(BookMarkToolBar, self).__init__(parent)

        self.dbg = False
        self.actionTriggered.connect(self.onActionTriggered)        # if self involved jump to onActionTriggered()
        self.bkmrk_list = QListWidget()
        self.bkmrk_list.setSortingEnabled(False)
        self.PXLSIZE = PXLSIZE
        self.bkmrk_add_dlg = Bookmark_add_Dialog(self)
        self.bkmrk_rem_dlg = Bookmark_rem_Dialog(self)
      # set a menu on a button inside bookmark toolbar (self, this class)
        mgr_button = QPushButton(_("Bookmark manager")) # ("favoris: gestion")
        self.addWidget(mgr_button)
        mgr_menu = QMenu()
        srt_act = mgr_menu.addAction(_("Sort bookmark"))
        clr_act = mgr_menu.addAction(_("Clear bookmark"))
        # mgr_sub_menu = mgr_menu.addMenu("submenu")
        rem_act = mgr_menu.addAction(_("Del bookmark"))     # open list

        mgr_button.setMenu(mgr_menu)
        clr_act.triggered.connect(self.clear_bookmark)
        srt_act.triggered.connect(self.sort_bookmark)
        rem_act.triggered.connect(self.slct_rem_bkmrk)       # show the listwidget in a window, so an item can be selected and remved

        self.settings = QSettings(os.path.join(cache_dir(), 'getandsetidfromweb_web_main.ini'), QSettings.Format.IniFormat) # avoid using registry

      # external signals handling
        self.bkmrk_add_dlg.add_bkmrk_sgnl.connect(self.add_bkmrk)
        self.bkmrk_add_dlg.home_bkmrk_sgnl.connect(self.home_bkmrk)
        self.bkmrk_rem_dlg.rem_bkmrk_sgnl.connect(self.rem_bkmrk)

    def load_settings(self):
        if self.dbg : print("in load_settings")
        dflt_url = self.settings.value("default_url",[])    # lrp should load here a help file
        if dflt_url:
            self.default_url = dflt_url[0]
        else:
            self.default_url = "https://www.google.com"
        load_items = self.settings.value("bookmarks", [])
        # if self.dbg : print(f"load_items = self.settings.value('bookmarks', []) : {load_items}")
        if not load_items: load_items = []
        for i in range(len(load_items)):
            # if self.dbg: print(f'load_items[{i}] : {load_items[i]}')
            self.bkmrk_title, self.bkmrk_url = load_items[i][0], load_items[i][1]                           # needed for initial load
            if  self.dbg : print(f"self.bkmrk_title, self.bkmrk_url : {self.bkmrk_title, self.bkmrk_url}")
            self.add_bkmrk(self.bkmrk_title)

    def bkmrk_select_action(self, title, url):          # do not modify
        '''
        Jump here, from MainWindow, on a click on the bookmark icon, url and page title is known.
        the title must be edited to fit in the bookmark toolbar. This will identify the action item
        in the bookmark toolbar.
        '''
        self.bkmrk_title, self.bkmrk_url = title, url               # needed in initial load
        if self.dbg : print(f"in bkmrk_select_action, title : {self.bkmrk_title}, bkmrk_url : {self.bkmrk_url}")
        self.bkmrk_add_dlg.bkmrk_title(self.bkmrk_title)
        cursor_pos = QCursor.pos()
        self.bkmrk_add_dlg.move(cursor_pos.x()-4*PXLSIZE,cursor_pos.y()+10)
        if not self.bkmrk_add_dlg.exec():                                                   # make sure bkmrk_add_dlg was not closed
            return

    def sync_data(self):
        if self.dbg : print ("in sync_data")
        save_items = []
        # if self.dbg : print(f"self.bkmrk_list.count() : {self.bkmrk_list.count()}")
        for i in range(self.bkmrk_list.count()):
            it = self.bkmrk_list.item(i)
            if  self.dbg : print(f"it.text() : {it.text()}")
            action = it.data(Qt.ItemDataRole.UserRole)
            save_items.append((it.text(),action.data()))
            if  self.dbg : print(f"save_items[{i}] : {save_items[i]}")
        self.settings.setValue("bookmarks", save_items)
        self.settings.setValue("default_url", [self.default_url])
        self.settings.sync()

  # signals handling
    def slct_rem_bkmrk(self):
        if self.dbg: print("in slct_rem_bkmrk")
        self.bkmrk_rem_dlg.set_listWidget(self.bkmrk_list)
        cursor_pos = QCursor.pos()
        self.bkmrk_rem_dlg.move(cursor_pos.x(),cursor_pos.y()+10)
        if not self.bkmrk_rem_dlg.exec():                    # make sure bkmrk_rem_dlg was not closed
            return

    def rem_bkmrk(self, lst):
        if self.dbg : print("in rem_bkmrk")
        for i in range(len(lst)):
            it = self.bkmrk_list.takeItem(lst[i])
            action = it.data(Qt.ItemDataRole.UserRole)
            self.removeAction(action)
        self.sync_data()

    @pyqtSlot()
    def sort_bookmark(self):
        if self.dbg : print("in sort_bookmark")
      # create a list of label-url, order that list
        srt_lst = []
        for i in reversed(range(self.bkmrk_list.count())):
            it = self.bkmrk_list.item(i)
            if not it:
                break
            # if self.dbg : print("before : ", it.text(), it.data(Qt.ItemDataRole.UserRole).data())
            srt_lst.append((it.text(), it.data(Qt.ItemDataRole.UserRole).data()))
      # remove bkmrk
            self.bkmrk_list.takeItem(self.bkmrk_list.row(it))
            action = it.data(Qt.ItemDataRole.UserRole)
            self.removeAction(action)
      # order the list
        srt_lst.sort(key = lambda x: x[0].lower())
      # add all from ordered list
        for i in range(len(srt_lst)):
            ttl, rl = srt_lst[i]
            action = self.addAction(ttl)
            action.setData(rl)
            item = QListWidgetItem(ttl)
            item.setData(Qt.ItemDataRole.UserRole, action)
            self.bkmrk_list.addItem(item)
            # if self.dbg : print("after  : ",ttl, rl)
      # save setting
        self.sync_data()

    @pyqtSlot()
    def clear_bookmark(self):
        '''
        removes all entries from the bookmark toolbar, resets default/original
        home url.
        '''
        if self.dbg : print("in clear_bookmark")
        for i in reversed(range(self.bkmrk_list.count())):
            it = self.bkmrk_list.item(i)
            if not it:
                break
            # if self.dbg : print("deleting : ", it.text(), it.data(Qt.ItemDataRole.UserRole).data())
      # remove bkmrk
            self.bkmrk_list.takeItem(self.bkmrk_list.row(it))
            action = it.data(Qt.ItemDataRole.UserRole)
            self.removeAction(action)
      # reset home address
        self.bkmrk_url = "https://www.google.com"
        self.home_bkmrk()
      # save it all
        self.sync_data()

    @pyqtSlot(str)
    def add_bkmrk(self, bkmrk_title):
        '''
        add an entry in the bookmark, with the label returned from the bookmark dialog
        except is there is an entry with the same label
        '''
        if self.dbg : print(f"in add_bkmrk, bkmrk_title : {bkmrk_title}")
        fm = QFontMetrics(self.font())
        bkmrk_title = fm.elidedText(bkmrk_title, Qt.TextElideMode.ElideRight, self.PXLSIZE)
        if not self.bkmrk_list.findItems(bkmrk_title, Qt.MatchFlag.MatchExactly):
            action=self.addAction(bkmrk_title)
            action.setData(self.bkmrk_url)
            item = QListWidgetItem(bkmrk_title)
            item.setData(Qt.ItemDataRole.UserRole, action)
            self.bkmrk_list.addItem(item)
        self.sync_data()

    @pyqtSlot(QListWidget)
    def del_bkmrk(self, ):
        '''
        remove any label with an identic url compared to the url displayed during
        the bookmark dialog. The list will be searched in reverse so that removed
        bookmark in the list will not change the index of possible next match.
        '''
        if self.dbg : print(f"in del_bkmrk")
        for i in reversed(range(self.bkmrk_list.count())):
            it = self.bkmrk_list.item(i)
            if self.bkmrk_url == it.data(Qt.ItemDataRole.UserRole).data():
                action = it.data(Qt.ItemDataRole.UserRole)
                self.removeAction(action)
                self.bkmrk_list.takeItem(self.bkmrk_list.row(it))
        self.sync_data()

    @pyqtSlot()
    def home_bkmrk(self):
        if self.dbg : print("in home_bkmrk")
        url_home = self.bkmrk_url       # "https://www.google.com"
        self.set_url_home.emit(url_home)

    @pyqtSlot(QAction)
    def onActionTriggered(self, action):
        if self.dbg : print("in onActionTriggered")
        url = action.data()
        # if self.dbg : print(f"action.data() : {action.data()} = url : {url}")
        self.bookmark_clicked.emit(url)

    def set_debug(self):
        self.dbg = True
        self.bkmrk_add_dlg.set_debug()
        self.bkmrk_rem_dlg.set_debug()

class Search_Panel(QWidget):
    '''
    A dynamic search panel. Shows up on signal "searched" when search is activated (via button or <ctrl f>).
    Disapear on signal "closesrch" as soon as not relevant anymore (change url, button done, esc key).
    No automatic information is passed in search line, manual cut and paste may be used to populate.
    '''
  # signal generated for a press on a bookmark item in the bookmark (vertical) bar
    searched = pyqtSignal(str, QWebEnginePage.FindFlag)
    closesrch = pyqtSignal()

    def __init__(self,parent=None):
        super(Search_Panel,self).__init__(parent)

        self.dbg = False
        next_btn = QPushButton(_("Next")) # 'Suivant')
        next_btn.setToolTip(_("This button search the next occurance in the page")) #("Ce bouton recherche la prochaine occurrence dans la page")
        next_btn.clicked.connect(self.update_searching)
        if isinstance(next_btn, QPushButton): next_btn.clicked.connect(self.setFocus)

        prev_btn = QPushButton(_("Previous"))  #('Précédent')
        prev_btn.setToolTip(_("This button search for the previous occurance in the page")) #("Ce bouton recherche l'occurrence précédente dans la page")
        prev_btn.clicked.connect(self.on_preview_find)
        if isinstance(prev_btn, QPushButton): prev_btn.clicked.connect(self.setFocus)

        done_btn = QPushButton(_("Done"))  #("Terminé")
        done_btn.setToolTip(_("This button closes the search bar")) #("Ce bouton ferme la barre de recherche")
        done_btn.clicked.connect(self.closesrch)
        if isinstance(done_btn, QPushButton): done_btn.clicked.connect(self.setFocus)

        self.srch_dsp = QLineEdit()
        self.srch_dsp.setToolTip(_("This box contains the text to search in the page"))    #("Cette boite contient le texte à chercher dans la page")
        self.setFocusProxy(self.srch_dsp)
        self.srch_dsp.textChanged.connect(self.update_searching)
        self.srch_dsp.returnPressed.connect(self.update_searching)
        self.closesrch.connect(self.srch_dsp.clear)

        self.srch_lt = QHBoxLayout(self)
        self.srch_lt.addWidget(self.srch_dsp)
        self.srch_lt.addWidget(next_btn)
        self.srch_lt.addWidget(prev_btn)
        self.srch_lt.addWidget(done_btn)

        QShortcut(QKeySequence.StandardKey.FindNext, self, activated=next_btn.animateClick)
        QShortcut(QKeySequence.StandardKey.FindPrevious, self, activated=prev_btn.animateClick)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self.srch_dsp, activated=self.closesrch)

    @pyqtSlot()
    def on_preview_find(self):
        if self.dbg: print("in class Search_Panel : on_preview_find")
        self.update_searching(QWebEnginePage.FindFlag.FindBackward)

    @pyqtSlot()
    def update_searching(self, direction=QWebEnginePage.FindFlag(0)):
        if self.dbg: print("in class Search_Panel : update_searching")
        flag = direction
        self.searched.emit(self.srch_dsp.text(), flag)

    def showEvent(self, event):
        if self.dbg: print("in class Search_Panel : showEvent")
        super(Search_Panel, self).showEvent(event)
        self.setFocus()

    def set_debug(self):
        self.dbg = True

class MainWindow(QMainWindow):
    """
    this process, running in the calibre environment, is detached from calibre program
    It does receive data from set_id_from_web, processes it, then communicates back the
    result and dies.
    Data received is title, authors, ISDN and DEBUG; data reurned is one or more IDs
    related to the book
    In fact this is a very basic WEB browser to report the selected_url of the choosen book.
    To debug web_main do execute calibre in debug mode (calibre-debug --gui)
    """

    def __init__(self, data):
        super().__init__()

      # Initialize environment..
      # note: web_main is NOT supposed to output anything over STDOUT or STDERR as those are redirected to GetAndSetIdFromWeb.log, a temp file
        logging.basicConfig(
        level = logging.DEBUG,
        format = '%(asctime)s:%(levelname)s:%(name)s:%(message)s',
        filename = os.path.join(tempfile.gettempdir(), 'GetAndSetIdFromWeb.log'),
        filemode = 'a')
        stdout_logger = logging.getLogger('STDOUT')
        sl = StreamToLogger(stdout_logger, logging.INFO)
        sys.stdout = sl
        stderr_logger = logging.getLogger('STDERR')
        sl = StreamToLogger(stderr_logger, logging.ERROR)
        sys.stderr = sl

      # data = [url, isbn, auteurs, titre, type de browser, DEBUG]
        self.isbn, self.auteurs, self.titre, self.type, self.dbg = data[1].replace("-",""), data[2], data[3], data[4], data[5]
        print("in __init__")
        print(f"isbn    : {self.isbn}")
        print(f"auteurs : {self.auteurs}")
        print(f"titre   : {self.titre}")
        print(f"type    : {self.type}")
        print(f"dbg     : {self.dbg}")

      # initialize self.selected_url
        self.selected_url = []

        self.create_empty_results_file()
        self.set_browser()
        self.set_profile()
        self.set_isbn_box()
        self.set_auteurs_box()
        self.set_titre_box()
        self.set_search_bar()
        self.join_all_boxes()
        self.set_nav_and_status_bar()

      # Create a timer object to periodicaly check for shutdown communication from main calibre
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.chk_for_shutdown)
        self.timer.start(250)


      # make all that visible... I want this window on top ready to work with
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        self.show()
        self.activateWindow()

      # signals
        self.browser.urlChanged.connect(self.update_urlbar)
        self.browser.loadStarted.connect(self.loading_title)
        self.browser.loadStarted.connect(self.set_progress_bar)
        self.browser.loadProgress.connect(self.update_progress_bar)
        self.browser.loadFinished.connect(self.update_title)
        self.browser.loadFinished.connect(self.reset_progress_bar)
        self.isbn_btn.clicked.connect(partial(self.set_noosearch_page, "isbn"))
        self.auteurs_btn.clicked.connect(partial(self.set_noosearch_page, "auteurs"))
        self.titre_btn.clicked.connect(partial(self.set_noosearch_page, "titre"))
        self.bookmarkToolbar.bookmark_clicked.connect(self.goto_this_url)
        self.bookmarkToolbar.set_url_home.connect(self.set_home_with_current_url)

        self.url_home = "https://www.noosfere.org/livres/noosearch.asp"

      # create a new empty GetAndSetIdFromWeb_report_url to ensure that no old file gets used
    def create_empty_results_file(self):
        open(os.path.join(tempfile.gettempdir(),"GetAndSetIdFromWeb_report_url"),"w",encoding="utf_8").close()

      # browser
    def set_browser(self):
        print(f"in set_browser, value of self.dbg : {self.dbg}\n")      # entry point for each iteration of the browser
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("http://www.google.com"))

      # set profile to enable remembering cookies...
    def set_profile(self):
        if self.dbg: print("in set_profile")
        profile = QWebEngineProfile("savecookies", self.browser)
        browser_storage_folder = os.path.join(cache_dir(), 'getandsetidfromweb')

        print(f"browser_storagefolder : {browser_storage_folder}")          # browser_storagefolder : C:\Users\lrpir\AppData\Local\calibre-cache\getandsetidfromweb
        profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)
        profile.setPersistentStoragePath(browser_storage_folder)
        profile.setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)

        self.webpage = QWebEnginePage(profile, self.browser)
        self.browser.setPage(self.webpage)

    # def set_it_secure(self):    # disable javascript to reduce malware surface grip
    # Not a good idea really, to suppress Javascript capabilities remove too much...
    # In fact default seems most appropiate.
    #
    # from  src/calibre/utils :
    #
    # def secure_webengine(view_or_page_or_settings, for_viewer=False):
    #     s = view_or_page_or_settings.settings() if hasattr(
    #         view_or_page_or_settings, 'settings') else view_or_page_or_settings
    #     a = s.setAttribute
    #     a(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
    #     if not for_viewer:
    #         a(QWebEngineSettings.WebAttribute.JavascriptEnabled, False)
    #         s.setUnknownUrlSchemePolicy(QWebEngineSettings.UnknownUrlSchemePolicy.DisallowUnknownUrlSchemes)
    #         if hasattr(view_or_page_or_settings, 'setAudioMuted'):
    #             view_or_page_or_settings.setAudioMuted(True)
    #     a(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False)
    #     a(QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, False)
    #     # ensure javascript cannot read from local files
    #     a(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, False)
    #     a(QWebEngineSettings.WebAttribute.AllowWindowActivationFromJavaScript, False)
    #     return s

      # info boxes
    def set_isbn_box(self):        # info boxes isbn
        if self.dbg: print("in set_isbn_box")
        self.isbn_btn = QPushButton(" ISBN ", self)
        self.isbn_btn.setToolTip(_("ISBN is copied in the clipboard (and fills noosfere search page)"))
        self.isbn_dsp = QLineEdit()
        self.isbn_dsp.setReadOnly(True)
        self.isbn_dsp.setText(self.isbn)
        self.isbn_dsp.setToolTip(_("This box shows the write protected ISBN. Text may be selected here for a search in the page")) #(" Cette boite montre l'ISBN protégé en écriture. Du texte peut y être sélectionné pour chercher dans la page")
        self.isbn_lt = QHBoxLayout()
        self.isbn_lt.addWidget(self.isbn_btn)
        self.isbn_lt.addWidget(self.isbn_dsp)

    def set_auteurs_box(self):                  # info boxes auteurs
        if self.dbg: print("in set_auteurs_box")
        self.auteurs_btn = QPushButton(_("Author"), self)
        self.auteurs_btn.setToolTip(_("Author is copied in the clipboard (and fills noosfere search page)"))
        self.auteurs_dsp = QLineEdit()
        self.auteurs_dsp.setReadOnly(True)
        self.auteurs_dsp.setText(self.auteurs)
        self.auteurs_dsp.setToolTip(_("This box shows the write protected author(s). Text may be selected here for a search in the page")) #(" Cette boite montre le ou les Auteur(s) protégé(s) en écriture. Du texte peut être manuellement introduit pour chercher dans la page")
        self.auteurs_lt = QHBoxLayout()
        self.auteurs_lt.addWidget(self.auteurs_btn)
        self.auteurs_lt.addWidget(self.auteurs_dsp)

    def set_titre_box(self):                    # info boxes titre
        if self.dbg: print("in set_titre_box")
        self.titre_btn = QPushButton(_("Title"), self)
        self.titre_btn.setToolTip(_("Title is copied in the clipboard (and fills noosfere search page)"))
        self.titre_dsp = QLineEdit()
        self.titre_dsp.setReadOnly(True)
        self.titre_dsp.setText(self.titre)
        self.titre_dsp.setToolTip(_("This box shows the write protected title. Text may be selected here for a search in the page"))   #(" Cette boite montre le Titre protégé en écriture. Tout ou partie du texte peut être sélectionné pour chercher dans la page")
        self.titre_lt = QHBoxLayout()
        self.titre_lt.addWidget(self.titre_btn)
        self.titre_lt.addWidget(self.titre_dsp)

  # search bar hidden when inactive ready to find something (I hope :-) )
    def set_search_bar(self):
        if self.dbg: print("in set_search_bar")
        self.search_pnl = Search_Panel()
        if self.dbg: self.search_pnl.set_debug()
        self.search_toolbar = QToolBar()
        self.search_toolbar.addWidget(self.search_pnl)
        self.addToolBar(Qt.BottomToolBarArea, self.search_toolbar)
        self.search_toolbar.hide()
        self.search_pnl.searched.connect(self.on_searched)
        self.search_pnl.closesrch.connect(self.search_toolbar.hide)

    def join_all_boxes(self):                   # put all that together, center, size and make it central widget
        if self.dbg: print("in join_all_boxes")
        layout = QVBoxLayout()
        layout.addWidget(self.browser)
        layout.addLayout(self.isbn_lt)
        layout.addLayout(self.auteurs_lt)
        layout.addLayout(self.titre_lt)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.resize(1200,1000)

      # set navigation toolbar
    def set_nav_and_status_bar(self) :
        if self.dbg: print("in set_nav_and_status_bar")
        nav_tb = QToolBar(_("Navigation"))
        nav_tb.setIconSize(QSize(24,24))
        self.addToolBar(nav_tb)

        back_btn = QAction(get_icons('blue_icon/back.png'), "Back", self)
        back_btn.setToolTip(_("Back to the previous page")) #("On revient à la page précédente")
        back_btn.triggered.connect(self.browser.back)
        nav_tb.addAction(back_btn)

        next_btn = QAction(get_icons('blue_icon/forward.png'), "Forward", self)
        next_btn.setToolTip(_("Back to the next page")) #("On retourne à la page suivante")
        next_btn.triggered.connect(self.browser.forward)
        nav_tb.addAction(next_btn)

        reload_btn = QAction(get_icons('blue_icon/reload.png'), "Reload", self)
        reload_btn.setToolTip(_("Reload the current page"))   #("On recharge la page courante")
        reload_btn.triggered.connect(self.browser.reload)
        nav_tb.addAction(reload_btn)

        home_btn = QAction(get_icons('blue_icon/home.png'), "Home", self)
        home_btn.setToolTip(_("Go home")) #("On va à la page accueil")
        home_btn.triggered.connect(self.navigate_home)
        nav_tb.addAction(home_btn)

        stop_btn = QAction(get_icons('blue_icon/stop.png'), "Stop", self)
        stop_btn.setToolTip(_("Stop loading the page")) #("On arrête de charger la page")
        stop_btn.triggered.connect(self.browser.stop)
        nav_tb.addAction(stop_btn)

        nav_tb.addSeparator()

        find_btn = QAction(get_icons('blue_icon/search.png'), "Search", self)
        find_btn.setToolTip(_("Pops search bar")) #("Ce bouton fait apparaitre la barre de recherche... Z'avez pas vu Mirza? Oh la la la la la. Où est donc passé ce chien. Je le cherche partout...  (Merci Nino Ferrer)")   # search, search...
        find_btn.triggered.connect(self.wake_search_panel)
        find_btn.setShortcut(QKeySequence.StandardKey.Find)
        nav_tb.addAction(find_btn)

        self.urlbox = QLineEdit()
        self.urlbox.returnPressed.connect(self.navigate_to_url)
        self.urlbox.setToolTip(_("You can enter any address you like, but remember, AT YOUR OWN RISK... No malware filtering in this browser.")) #("On peut même introduire une adresse quelconque mais, cATTENTION, A VOS RISQUES ET PERILS... Il n'y a pas de filtre malware dans ce browser")
        nav_tb.addWidget(self.urlbox)

        favorite_btn = QAction(get_icons("blue_icon/star.png"), "bookmark", self)
        favorite_btn.setToolTip(_("Sets the bookmark for favorites, sets home")) #("Défini le signet des sites favoris, défini le site d'accueil")
        favorite_btn.triggered.connect(self.addFavoriteClicked)
        nav_tb.addAction(favorite_btn)

        nav_tb.addSeparator()
        abort_btn = QAction(get_icons('blue_icon/abort.png'), "Abort", self)
        abort_btn.setToolTip(_("Stop everything, forget everything and change nothing... proceed to next book"))    #("On arrête, on oublie, on ne change rien au livre... au suivant")
        abort_btn.triggered.connect(self.abort_book)
        nav_tb.addAction(abort_btn)

        nav_tb.addSeparator()

        choice_btn = QAction(get_icons('blue_icon/choice.png'), "Select and store", self)
        choice_btn.setToolTip(_("select this URL for extracting the id, another id?"))   #("On sélectionne cet URL pour extraction de l'id... un autre id?")
        choice_btn.triggered.connect(self.select_an_id)
        nav_tb.addAction(choice_btn)

        nav_tb.addSeparator()

        exit_btn = QAction(get_icons('blue_icon/exit.png'), "Done and exit", self)
        exit_btn.setToolTip(_("Done selecting id(s)... next")) #("On a fini de sélectionner les id... livre suivant")
        exit_btn.triggered.connect(self.done_do_exit)
        nav_tb.addAction(exit_btn)
  # bookmark bar (need a def)
        self.addToolBarBreak()
        self.bookmarkToolbar = BookMarkToolBar()
        self.bookmarkToolbar.setMovable(True)
        if self.dbg : self.bookmarkToolbar.set_debug()
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.bookmarkToolbar)
        self.bookmarkToolbar.load_settings()                             # initial fill of home, and remembered URL of interest
  # set status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
  # Create page loading progress bar that is displayed in the status bar.
        self.msg_label = QLabel()
        self.page_load_label = QLabel()
        self.page_load_pb = QProgressBar()
  # Set up widgets on the statusbar
        self.statusBar().addPermanentWidget(self.msg_label, stretch=36)
        self.statusBar().addPermanentWidget(self.page_load_label, stretch=14)
        self.statusBar().addPermanentWidget(self.page_load_pb, stretch=50)

  # search action
    @pyqtSlot(str, QWebEnginePage.FindFlag)
    def on_searched(self, text, flag):
        print(f"in on_searched text : {text}, flag : {flag}")
        def callback(found):
            if text and not found:
                self.msg_label.setText(_("Sorry {} not found").format(text))   #('Désolé, {} pas trouvé...'.format(text))
            else:
                self.msg_label.setText('')
        self.browser.findText(text, flag, callback)

  # info boxes actions, noosfere is a special case... cause noosfere is the best in my opinion.
    @pyqtSlot()
    def set_noosearch_page(self, iam):
        print(f"in set_noosearch_page iam : {iam}")
        print(f"self.urlbox.text() : {self.urlbox.text()}")
        if self.urlbox.text() == "https://www.noosfere.org/livres/noosearch.asp" :
            if iam == "isbn": val = self.isbn
            elif iam == "auteurs": val = self.auteurs
            else: val = self.titre
            self.browser.page().runJavaScript("document.getElementsByName('Mots')[1].value =" + dumps(val))
            if iam == "auteurs":
                self.browser.page().runJavaScript("document.getElementsByName('auteurs')[0].checked = true")
                self.browser.page().runJavaScript("document.getElementsByName('livres')[0].checked = false")
            else:
                self.browser.page().runJavaScript("document.getElementsByName('livres')[0].checked = true")
                self.browser.page().runJavaScript("document.getElementsByName('auteurs')[0].checked = false")
        else:
            cb = Application.instance().clipboard()
            cb.clear(mode=cb.Mode.Clipboard)
            if iam == "isbn": cb.setText(self.isbn.replace("-","") + " ", mode=cb.Mode.Clipboard)
            elif iam == "auteurs": cb.setText(self.auteurs + " ", mode=cb.Mode.Clipboard)
            else: cb.setText(self.titre + " ", mode=cb.Mode.Clipboard)

    @pyqtSlot()
    def wake_search_panel(self):
        if self.dbg: print("in wake_search_panel")
        self.search_toolbar.show()

  # bookmark actions
    @pyqtSlot(str)
    def set_home_with_current_url(self, url_home):
        self.url_home = url_home
        if self.dbg: print(f"url_home : {url_home}")

  # Navigation actions
    def jump_to_this_url(self, url="http://www.google.com"):
        '''
        initial url if no defined ulr_home
        '''
        if self.url_home: url = self.url_home
        if self.dbg: print(f"in jump_to_this_url url : {url}")
        self.browser.setUrl(QUrl(url))

    def goto_this_url(self, url="http://www.google.com"):
        if self.dbg: print(f"in goto_this_url url : {url}")
        self.browser.setUrl(QUrl(url))

    def navigate_home(self):
        if self.dbg: print(f"in navigate_home : {self.url_home}")
        self.browser.setUrl(QUrl(self.url_home))      # home for the 'get_and_set_id_from_web' browser

    def navigate_to_url(self):                    # Does not receive the Url, activated when url bar is manually changed
        if self.dbg: print("in navigate_to_url", end = " : ",)
        url = self.urlbox.text()
        if not url.startswith("http"):
            url = "https://" + url
        if self.dbg: print(url)
        self.browser.setUrl(QUrl(url))

    def update_urlbar(self, q):
        if self.dbg: print(f"in update_urlbar : {q.toString()}")
        self.urlbox.setText(q.toString())
        self.urlbox.setCursorPosition(0)

    def loading_title(self):
        if self.dbg: print("in loading_title")
      # anytime we change page we come here... let's clear and hide the search panel
        self.search_pnl.closesrch.emit()           # by sending a close search panel signal
      # before doubling indication that we load a page in the title
        title=self.type + "En téléchargement de l'url"
        self.setWindowTitle(title)

    def update_title(self):
        if self.dbg: print("in update_title")
        title = self.type + self.browser.page().title()
        self.setWindowTitle(title)

    def set_progress_bar(self):
        if self.dbg: print("in set_progress_bar")
        self.page_load_pb.show()
        self.page_load_label.show()

    def update_progress_bar(self, progress):
        if self.dbg: print("in update_progress_bar progress : {}".format(progress))
        self.page_load_pb.setValue(progress)
        self.page_load_label.setText(_("Downloading url... ({}/100)").format(str(progress)))    #("En téléchargement de l'url... ({}/100)".format(str(progress)))

    def reset_progress_bar(self):
        if self.dbg: print("in reset_progress_bar")
        def wait_a_minut():
            self.page_load_pb.hide()
            self.page_load_label.hide()
        QTimer.singleShot(1000, wait_a_minut)

    def report_returned_url(self, returned_url):                # sent response over report_returned_url file in temp dir
        returned_url = list(set(returned_url))                  # returns NO duplicates
        if self.dbg: print(f"in report_returned_url returned_url : {returned_url}")
        with open(os.path.join(tempfile.gettempdir(),"GetAndSetIdFromWeb_report_url"),"w",encoding="utf_8") as report_tpf:
            for i in range(len(returned_url)):
                report_tpf.writelines(returned_url[i] + "\n")

    def select_an_id(self):
      # build a list of URL that will be converted to ID
        if self.dbg: print("in select_an_id")
        self.selected_url.append(self.urlbox.text())            # add url displayed in urlbox
        if self.selected_url:
            print(f'self.selected_url : {self.selected_url}')

  # Bookmark actions
    def addFavoriteClicked(self):
        title = self.browser.page().title()
        chsn_url = self.urlbox.text()
        self.bookmarkToolbar.bkmrk_select_action(title, chsn_url)

  # exit actions
    def done_do_exit(self):
        if self.dbg: print("in done_do_exit")
        if self.selected_url:
            for i in range(len(self.selected_url)):
                print(f'self.selected_url[{i}] : {self.selected_url[i]}')
            self.report_returned_url(self.selected_url)
        self.lets_go()

    def abort_book(self):                           # we want to NOT change the book and proceed to the next one
        if self.dbg: print("in abort_book")
        d_ttl = _("Sure?")  #'Certain?'
        d_txt = _("Forget this book and proceed with next")    # "Oublier ce livre et passer au suivant"
        reply = QMessageBox.question(self, d_ttl, d_txt, QMessageBox.No | QMessageBox.Yes, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            print("WebEngineView was aborted for this book: aborted")
            self.report_returned_url(["aborted by user"])  # "aborted by user" is tested in main
            self.lets_go()

    def closeEvent(self, event):                    # abort hit window exit "X" button we stop processing this and all following books
        print(f"in closeEvent event : {event}")
        d_ttl = _("Really?")    #'Vraiment?'
        d_txt = _("Quit now and change nothing anymore")    # "Quitter ici et ne plus rien changer"
        reply = QMessageBox.question(self, d_ttl, d_txt, QMessageBox.No | QMessageBox.Yes, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            event.accept()
            print("WebEngineView was closed: killed")
            self.report_returned_url(["killed by user"])    # "killed by user" is tested in main
            self.webpage.deleteLater()
            super().closeEvent(event)
        else:
            event.ignore()

    def chk_for_shutdown(self):                     # presence of such file means that calibre shutdown
        if glob.glob(os.path.join(tempfile.gettempdir(),"GetAndSetIdFromWeb_terminate-cal-qweb*")):
            print("Calibre shutdown WebEngineView was closed: killed")
            self.report_returned_url(["killed on calibre shutdown"])       # report main calibre shutdown
            self.lets_go()

    def lets_go(self):
        Application.instance().exit()           # exit application...

def main(data):

# create a temp file... while it exists launcher program will wait...
    # this file will disappear with the process
    sync_tpf=tempfile.NamedTemporaryFile(prefix="GetAndSetIdFromWeb_sync-cal-qweb")

    # retrieve component from data
    #        data = [url, isbn, auteurs, titre, type, DEBUG]
    url = data[0]
    # Start QWebEngineView and associated widgets
    app = Application([])
    window = MainWindow(data)
    window.jump_to_this_url(url)     # supposed to be a valid page, fixed by launcher program
    app.exec()

    # signal launcher program that we are finished
    sync_tpf.close           # close temp file

########################################################################################

if __name__ == '__main__':
    '''
    watch out: name 'get_icons' is not defined, and can't be defined easyly...
    workaround, swap it with QIcon + path to icon
    replace all get_icons(' with QIcon('./ (do NOT replace me :-) )
    AND to get errors on screen, comment out class StreamToLogger(object)
    along with the 10 first lines in __init__ of class MainWindow(QMainWindow
    To debug web_main, do set self.dbg = True in class MainWindow
    '''
    url = "https://www.google.com"    # jump directly to google
    isbn = "2-277-12362-5"
    auteurs = "Alfred Elton VAN VOGT"                       # forget not that auteurs may be a list of auteurs
    titre = "Le Monde des Ã"
    data = [url, isbn, auteurs, titre, "Recherche d'un ID en standalone", True]
    main(data)

    with open (os.path.join(tempfile.gettempdir(),"GetAndSetIdFromWeb_report_url"), "r",encoding='utf_8') as tf:
        returned_url = tf.read()

  # from here should modify the metadata, or not.
    # if returned_url.replace("vl$","").replace("-","").isnumeric():
    if returned_url:
        selected_url = returned_url
        for i in range(len(selected_url)):
            print(f"selected_url[{i}] : {selected_url[i]}")
    elif "aborted" in returned_url:
        print('aborted, no change will take place...')
    elif "killed" in returned_url:
        print('killed, no change will take place...')
    else:
        print("should not ends here... returned_url : ", returned_url)
