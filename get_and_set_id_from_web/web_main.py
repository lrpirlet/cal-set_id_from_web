#!/usr/bin/env python
# vim:fileencoding=utf-8

__license__   = 'GPL v3'
__copyright__ = '2022, Louis Richard Pirlet'

from qt.core import (pyqtSlot, QUrl, QSize, Qt, pyqtSignal, QTimer,
    QMainWindow, QToolBar, QAction, QLineEdit, QStatusBar, QProgressBar,
    QMessageBox, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QShortcut, QClipboard, QKeySequence, QIcon)

from qt.webengine import QWebEngineView, QWebEnginePage

# from PyQt5.QtCore import pyqtSlot, QUrl, QSize, Qt, pyqtSignal, QTimer
# from PyQt5.QtWidgets import (QMainWindow, QToolBar, QAction, QLineEdit, QStatusBar, QProgressBar,
#                                 QMessageBox, qApp, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
#                                 QPushButton, QShortcut)
# from PyQt5.QtGui import QIcon, QKeySequence
# from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage

# from qt.core import (pyqtProperty, pyqtSignal, pyqtSlot, QAction, QApplication,
#                 QBrush, QByteArray, QCheckBox, QColor, QColorDialog, QComboBox,
#                 QCompleter, DateTime, QDialog, QDialogButtonBox, QEasingCurve,
#                 QEvent, QFont, QFontInfo, QFontMetrics, QFormLayout, QGridLayout,
#                 QHBoxLayout, QIcon, QInputDialog, QKeySequence, QLabel, QLineEdit,
#                 QListView, QMainWindow, QMainWindow, QMenu, QMenuBar, QMessageBox,
#                 QMessageBox, QModelIndex, QObject, QPainter, QPalette, QPixmap,
#                 QPlainTextEdit, QProgressBar, QPropertyAnimation, QPushButton,
#                 QShortcut, QSize, QSizePolicy, QSplitter, QStackedWidget, QStatusBar,
#                 QStyle, QStyleOption, QStylePainter, QSyntaxHighlighter, Qt, QTabBar,
#                 QTabWidget, QTextBlockFormat, QTextCharFormat, QTextCursor, QTextEdit,
#                 QTextFormat, QTextListFormat, QTimer, QToolBar, QToolButton, QUrl,
#                 QVBoxLayout, QWidget
# )

from calibre.gui2 import Application
from calibre.constants import cache_dir                             # lrp

from json import dumps
from functools import partial
import tempfile, glob, os, sys, logging

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

class Search_Panel(QWidget):
    searched = pyqtSignal(str, QWebEnginePage.FindFlag)
    closed = pyqtSignal()

    def __init__(self,parent=None):
        super().__init__(parent)

        next_btn = QPushButton('Suivant')
        next_btn.setToolTip("Ce bouton recherche la prochaine occurrence dans la page")
        next_btn.clicked.connect(self.update_searching)
        if isinstance(next_btn, QPushButton): next_btn.clicked.connect(self.setFocus)

        prev_btn = QPushButton('Précédent')
        prev_btn.setToolTip("Ce bouton recherche l'occurrence précédente dans la page")
        prev_btn.clicked.connect(self.on_preview_find)
        if isinstance(prev_btn, QPushButton): prev_btn.clicked.connect(self.setFocus)

        done_btn = QPushButton("Terminé")
        done_btn.setToolTip("Ce bouton ferme la barre de recherche")
        done_btn.clicked.connect(self.closed)
        if isinstance(done_btn, QPushButton): done_btn.clicked.connect(self.setFocus)

        self.srch_dsp = QLineEdit()
        self.srch_dsp.setToolTip(" Cette boite contient le texte à chercher dans la page")
        self.setFocusProxy(self.srch_dsp)
        self.srch_dsp.textChanged.connect(self.update_searching)
        self.srch_dsp.returnPressed.connect(self.update_searching)
        self.closed.connect(self.srch_dsp.clear)

        self.srch_lt = QHBoxLayout(self)
        self.srch_lt.addWidget(self.srch_dsp)
        self.srch_lt.addWidget(next_btn)
        self.srch_lt.addWidget(prev_btn)
        self.srch_lt.addWidget(done_btn)

        QShortcut(QKeySequence.StandardKey.FindNext, self, activated=next_btn.animateClick)
        QShortcut(QKeySequence.StandardKey.FindPrevious, self, activated=prev_btn.animateClick)
        QShortcut(QKeySequence(Qt.Key_Escape), self.srch_dsp, activated=self.closed)

    @pyqtSlot()
    def on_preview_find(self):
        self.update_searching(QWebEnginePage.FindBackward)

    @pyqtSlot()
    def update_searching(self, direction=QWebEnginePage.FindFlag(0)):
        flag = direction
        self.searched.emit(self.srch_dsp.text(), flag)

    def showEvent(self, event):
        super().showEvent(event)
        self.setFocus()

class MainWindow(QMainWindow):
    """
    this process, running in the calibre environment, is detached from calibre program
    It does receive data from set_id_from_web, processes it, then communicates back the result and dies.
    In fact this is a very basic WEB browser to report the selected_url of the choosen book.

    """

    def __init__(self, data):
        super().__init__()

      # Initialize environment..
      # note: web_main is NOT supposed to output anything over STDOUT or STDERR
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

        print(f"I want to verifiy I know cache_dir(): {cache_dir()}")   # lrp

      # data = [url, isbn, auteurs, titre]
        self.isbn, self.auteurs, self.titre = data[1].replace("-",""), data[2], data[3]

        self.set_browser()
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
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
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

      # browser
    def set_browser(self):
        print("in set_browser")
        self.browser = QWebEngineView()
        self.browser.setUrl(QUrl("http://www.google.com"))

      # info boxes
    def set_isbn_box(self):        # info boxes isbn
        print("in set_isbn_box")
        self.isbn_btn = QPushButton(" ISBN ", self)
        self.isbn_btn.setToolTip('Action sur la page initiale: "Mots-clefs à rechercher" = ISBN, coche la case "Livre".')
                                   # Action on home page: "Mots-clefs à rechercher" = ISBN, set checkbox "Livre".
        self.isbn_dsp = QLineEdit()
        self.isbn_dsp.setReadOnly(True)
        self.isbn_dsp.setText(self.isbn)
        self.isbn_dsp.setToolTip(" Cette boite montre l'ISBN protégé en écriture. Du texte peut y être sélectionné pour chercher dans la page")
                                   # This box displays the ISBN write protected. Some text may be selected here to search the page.

        self.isbn_lt = QHBoxLayout()
        self.isbn_lt.addWidget(self.isbn_btn)
        self.isbn_lt.addWidget(self.isbn_dsp)

    def set_auteurs_box(self):                  # info boxes auteurs
        print("in set_auteurs_box")
        self.auteurs_btn = QPushButton("Auteur(s)", self)
        self.auteurs_btn.setToolTip('Action sur la page babelio initiale: "Mots-clefs à rechercher" = Auteur(s), coche la case "Auteurs".')
                                      # Action on home page: "Mots-clefs à rechercher" = Auteur(s), set checkbox "Auteurs".
        self.auteurs_dsp = QLineEdit()
        self.auteurs_dsp.setReadOnly(True)
        self.auteurs_dsp.setText(self.auteurs)
        self.auteurs_dsp.setToolTip(" Cette boite montre le ou les Auteur(s) protégé(s) en écriture. Du texte peut être manuellement introduit pour chercher dans la page")
                                      # This box displays the Author(s) write protected. Some text may be written here to search the page.
        self.auteurs_lt = QHBoxLayout()
        self.auteurs_lt.addWidget(self.auteurs_btn)
        self.auteurs_lt.addWidget(self.auteurs_dsp)

    def set_titre_box(self):                    # info boxes titre
        print("in set_titre_box")
        self.titre_btn = QPushButton("Titre", self)
        self.titre_btn.setToolTip('Action sur la page babelio initiale: "Mots-clefs à rechercher" = Titre, coche la case "Livres".')
                                    # Action on home page: "Mots-clefs à rechercher" = Titre, set checkbox "Livres".
        self.titre_dsp = QLineEdit()
        self.titre_dsp.setReadOnly(True)
        self.titre_dsp.setText(self.titre)
        self.titre_dsp.setToolTip(" Cette boite montre le Titre protégé en écriture. Tout ou partie du texte peut être sélectionné pour chercher dans la page")
                                    # This box displays the Title write protected. Some text may be selected here to search the page.
        self.titre_lt = QHBoxLayout()
        self.titre_lt.addWidget(self.titre_btn)
        self.titre_lt.addWidget(self.titre_dsp)

  # search bar hidden when inactive ready to find something (I hope :-) )
    def set_search_bar(self):
        print("in set_search_bar")
        self.search_pnl = Search_Panel()
        self.search_toolbar = QToolBar()
        self.search_toolbar.addWidget(self.search_pnl)
        self.addToolBar(Qt.BottomToolBarArea, self.search_toolbar)
        self.search_toolbar.hide()
        self.search_pnl.searched.connect(self.on_searched)
        self.search_pnl.closed.connect(self.search_toolbar.hide)

    def join_all_boxes(self):                   # put all that together, center, size and make it central widget
        print("in join_all_boxes")
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
        print("in set_nav_and_status_bar")
        nav_tb = QToolBar("Navigation")
        nav_tb.setIconSize(QSize(24,24))
        self.addToolBar(nav_tb)

        back_btn = QAction(get_icons('blue_icon/back.png'), "Back", self)
        back_btn.setToolTip("On revient à la page précédente")                    # Back to the previous page
        back_btn.triggered.connect(self.browser.back)
        nav_tb.addAction(back_btn)

        next_btn = QAction(get_icons('blue_icon/forward.png'), "Forward", self)
        next_btn.setToolTip("On retourne à la page suivante")                     # Back to the next page
        next_btn.triggered.connect(self.browser.forward)
        nav_tb.addAction(next_btn)

        reload_btn = QAction(get_icons('blue_icon/reload.png'), "Reload", self)
        reload_btn.setToolTip("On recharge la page présente")                     # Reload the page
        reload_btn.triggered.connect(self.browser.reload)
        nav_tb.addAction(reload_btn)

        home_btn = QAction(get_icons('blue_icon/home.png'), "Home", self)
        home_btn.setToolTip("On va à la page recherche avancée de babelio")           # We go to the search page of babelio
        home_btn.triggered.connect(self.navigate_home)
        nav_tb.addAction(home_btn)

        stop_btn = QAction(get_icons('blue_icon/stop.png'), "Stop", self)
        stop_btn.setToolTip("On arrête de charger la page")                       # Stop loading the page
        stop_btn.triggered.connect(self.browser.stop)
        nav_tb.addAction(stop_btn)

        nav_tb.addSeparator()

        find_btn = QAction(get_icons('blue_icon/search.png'), "Search", self)
        find_btn.setToolTip("Ce bouton fait apparaitre la barre de recherche... Z'avez pas vu Mirza? Oh la la la la la. Où est donc passé ce chien. Je le cherche partout...  (Merci Nino Ferrer)")   # search, search...
        find_btn.triggered.connect(self.wake_search_panel)
        find_btn.setShortcut(QKeySequence.StandardKey.Find)
        nav_tb.addAction(find_btn)

        self.urlbox = QLineEdit()
        self.urlbox.returnPressed.connect(self.navigate_to_url)
        self.urlbox.setToolTip("On peut même introduire une adresse, hors babelio, mais A TES RISQUES ET PERILS... babelio est sûr (https://), la toile par contre...")
                                # You can even enter an address, outside of babelio, but AT YOUR OWN RISK... babelio is safe: (https://), the web on the other side...
        nav_tb.addWidget(self.urlbox)

        abort_btn = QAction(get_icons('blue_icon/abort.png'), "Abort", self)
        abort_btn.setToolTip("On arrête, on oublie, on ne change rien au livre... au suivant")
                              # Stop everything, forget everything and change nothing... proceed to next book
        abort_btn.triggered.connect(self.abort_book)
        nav_tb.addAction(abort_btn)

        nav_tb.addSeparator()

        exit_btn = QAction(get_icons('blue_icon/exit.png'), "Select and exit", self)
        exit_btn.setToolTip("On sélectionne cet URL pour extraction de l'id... au suivant")
                             # select this URL for extraction of the id, continue
        exit_btn.triggered.connect(self.select_and_exit)
        nav_tb.addAction(exit_btn)

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
        print("in on_searched text : {}, flag : {}".format(text, flag))
        def callback(found):
            if text and not found:
                self.msg_label.setText('Désolé, {} pas trouvé...'.format(text))     # Sorry "text" not found
            else:
                self.msg_label.setText('')
        self.browser.findText(text, flag, callback)

  # info boxes actions
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
            cb = Application.clipboard()
            print(type(cb))
            cb.clear(mode=cb.Mode.Clipboard)
            if iam == "isbn": cb.setText(self.isbn.replace("-","") + " ", mode=cb.Mode.Clipboard)
            elif iam == "auteurs": cb.setText(self.auteurs + " ", mode=cb.Mode.Clipboard)
            else: cb.setText(self.titre + " ", mode=cb.Mode.Clipboard)

    @pyqtSlot()
    def wake_search_panel(self):
        print("in wake_search_panel")
        self.search_toolbar.show()

  # Navigation actions
    def initial_url(self, url="http://www.google.com"):
        print("in initial_url url : {}".format(url))
        self.browser.setUrl(QUrl(url))

    def navigate_home(self):
        print("in navigate_home")
        self.browser.setUrl(QUrl("https://www.babelio.com/recherche"))

    def navigate_to_url(self):                    # Does not receive the Url, activated when url bar is manually changed
        print("in navigate_to_url")
        q = QUrl(self.urlbox.text())
        self.browser.setUrl(q)

    def update_urlbar(self, q):
        print("in update_urlbar")
        self.urlbox.setText(q.toString())
        self.urlbox.setCursorPosition(0)

    def loading_title(self):
        print("in loading_title")
      # anytime we change page we come here... let's clear and hide the search panel
        self.search_pnl.closed.emit()           # by sending a close search panel signal
      # before doubling indication that we load a page in the title
        title="En téléchargement de l'url"
        self.setWindowTitle(title)

    def update_title(self):
        print("in update_title")
        title = self.browser.page().title()
        self.setWindowTitle(title)

    def report_returned_url(self, returned_url):
        print("in report_returned_url returned_url : {}".format(returned_url))
        with open(os.path.join(tempfile.gettempdir(),"GetAndSetIdFromWeb_report_url"),"w",encoding="utf_8") as report_tpf:
            report_tpf.write(returned_url)

    def set_progress_bar(self):
        print("in set_progress_bar")
        self.page_load_pb.show()
        self.page_load_label.show()

    def update_progress_bar(self, progress):
        print("in update_progress_bar progress : {}".format(progress))
        self.page_load_pb.setValue(progress)
        self.page_load_label.setText("En téléchargement de l'url... ({}/100)".format(str(progress)))

    def reset_progress_bar(self):
        print("in reset_progress_bar")
        def wait_a_minut():
            self.page_load_pb.hide()
            self.page_load_label.hide()
        QTimer.singleShot(1000, wait_a_minut)

    def select_and_exit(self):                    # sent response over report_returned_url file in temp dir
      # create a temp file with name ( now starting with babelio_id)
        print("in select_and_exit")
        self.report_returned_url(self.urlbox.text())
        selected_url = self.urlbox.text()            # get url displayed in urlbox
        if selected_url:
        # if "/livres/" in selected_url:
            print('selected_url : {}'.format(selected_url))
        #     selected_url = selected_url.split("/livres/")[1]
        #     print("selected_url : {}".format(selected_url))
        #     self.report_returned_url(selected_url)
            self.report_returned_url(selected_url)
        # else:
        #     print('No book selected, no change will take place: unset')
        #     self.report_returned_url("unset")
        Application.instance().exit()               # exit application...

    def abort_book(self):                           # we want to NOT change the book and proceed to the next one
        print("in abort_book")
        reply = QMessageBox.question(self, 'Certain', "Oublier ce livre et passer au suivant", QMessageBox.No | QMessageBox.Yes, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            print("WebEngineView was aborted: aborted")
            self.report_returned_url("aborted")
            Application.instance().exit()           # exit application...


    def closeEvent(self, event):                    # abort hit window exit "X" button we stop processing this and all following books
        print("in closeEvent event : {}".format(event))
        reply = QMessageBox.question(self, 'Vraiment', "Quitter et ne plus rien changer", QMessageBox.No | QMessageBox.Yes, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            event.accept()
            print("WebEngineView was closed: killed")
            self.report_returned_url("killed")
            super().closeEvent(event)
        else:
            event.ignore()

    def chk_for_shutdown(self):                     # presence of such file means that calibre shutdown
        if glob.glob(os.path.join(tempfile.gettempdir(),"babelio_utl_terminate-cal-qweb*")):
            print("WebEngineView was closed: killed")
            self.report_returned_url("killed")       # report main calibre shutdown
            Application.instance().exit()           # exit application...



def main(data):

    # create a temp file... while it exists launcher program will wait... this file will disappear with the process
    sync_tpf=tempfile.NamedTemporaryFile(prefix="babelio_utl_sync-cal-qweb")

    # retrieve component from data
    #        data = [url, isbn, auteurs, titre]
    url, isbn, auteurs, titre = data[0], data[1], data[2], data[3],
    # Start QWebEngineView and associated widgets
    app = Application([])
    window = MainWindow(data)
    window.initial_url(url)     # supposed to be a valid page, fixed by launcher program
    app.exec()

    # signal launcher program that we are finished
    sync_tpf.close           # close temp file


if __name__ == '__main__':
    '''
    watch out: name 'get_icons' is not defined, and can't be defined easyly...
    workaround, swap it with QIcon + path to icon
    replace all get_icons(' with QIcon('./ (do NOT replace me :-) )
    AND to get errors on screen, comment out class StreamToLogger(object)
    along with the 10 first lines in __init__ of class MainWindow(QMainWindow
    '''
    url = "https://www.google.com"    # jump directly to google
    isbn = "2-277-12362-5"
    auteurs = "Alfred Elton VAN VOGT"                       # forget not that auteurs may be a list of auteurs
    titre = "Le Monde des Ã"
    data = [url, isbn, auteurs, titre]
    main(data)

    def get_icons(text):
        return QIcon(text)

    with open (os.path.join(tempfile.gettempdir(),"GetAndSetIdFromWeb_report_url"), "r",encoding='utf_8') as tf:
        returned_url = tf.read()

  # from here should modify the metadata, or not.
    # if returned_url.replace("vl$","").replace("-","").isnumeric():
    if returned_url:
        selected_url = returned_url
        print("selected_url : {}".format(selected_url))
    elif "unset" in returned_url:
        print('unset, no change will take place...')
    elif "killed" in returned_url:
        print('killed, no change will take place...')
    else:
        print("should not ends here... returned_url : ", returned_url)
