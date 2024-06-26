from multiprocessing import Process, Queue
import time

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtWebEngineWidgets import *

##import sys

class MainWindow(QMainWindow):
    def __init__(self, url, isbn, auteurs, titre, que):
        super(MainWindow,self).__init__()

        self.isbn = isbn
        self.auteurs = auteurs
        self.titre = titre
        self.que = que
        qDebug("isbn    : "+self.isbn)
        qDebug("auteurs : "+self.auteurs)
        qDebug("titre   : "+self.titre)
        qDebug("que     : "+str(type(self.que)))

    # set browser, make it central
        self.browser = QWebEngineView()
        self.browser.resize(1200,800)
        self.browser.setUrl(QUrl("http://www.google.com"))

        self.setCentralWidget(self.browser)

    # set get info toolbar
        info_tb = QToolBar("Get")
        info_tb.setIconSize(QSize(60,30))
        self.addToolBar(Qt.BottomToolBarArea, info_tb)

        ISBN_btn = QAction(QIcon('./blue_icon/ISBN.png'), "ISBN", self)
        ISBN_btn.setStatusTip("Montre et copie le ISBN dans le presse-papier pour coller dans Mots-clefs à rechercher")
                                # Show authors, copy in clipboard to paste in search field of noosfere
        ISBN_btn.triggered.connect(self.set_isbn_info)
        info_tb.addAction(ISBN_btn)

        Auteurs_btn = QAction(QIcon('./blue_icon/Auteurs.png'), "Auteur(s)", self)
        Auteurs_btn.setStatusTip("Montre et copie le(s) Auteur(s) dans le presse-papier pour coller dans Mots-clefs à rechercher")
                                # Show authors, copy in clipboard to paste in search field of noosfere
        Auteurs_btn.triggered.connect(self.set_auteurs_info)
        info_tb.addAction(Auteurs_btn)

        Titre_btn = QAction(QIcon('./blue_icon/Titre.png'), "Titre", self)
        Titre_btn.setStatusTip("Montre le Titre")                                   # show title
        Titre_btn.triggered.connect(self.set_titre_info)
        info_tb.addAction(Titre_btn)

        self.infobox = QLineEdit()
        self.infobox.setReadOnly(True)
        self.infobox.setStatusTip(" Aucune action, ce box montre l'ISBN, le(s) Auteur(s) ou le Titre, protégé en écriture."
                                  " Tout ou partie du texte peut être sélectionné pour copier et coller")
                                 # No action, this box displays the ISBN, the Author(s) or the Title, in write protect.
                                 # Part or the whole text may be selected for copy paste.
        info_tb.addWidget(self.infobox)

    # set navigation toolbar
        nav_tb = QToolBar("Navigation")
        nav_tb.setIconSize(QSize(20,20))
        self.addToolBar(nav_tb)

        home_btn = QAction(QIcon('./blue_icon/home.png'), "Home", self)
        home_btn.setStatusTip("On va à la une de noosfere")                         # We go to the front page of noosfere
        home_btn.triggered.connect(self.navigate_home)
        nav_tb.addAction(home_btn)

        back_btn = QAction(QIcon('./blue_icon/back.png'), "Back", self)
        back_btn.setStatusTip("On revient à la page précédente")                    # Back to the previous page
        back_btn.triggered.connect(self.browser.back)
        nav_tb.addAction(back_btn)

        next_btn = QAction(QIcon('./blue_icon/forward.png'), "Forward", self)
        next_btn.setStatusTip("On retourne à la page suivante")                     # Back to the next page
        next_btn.triggered.connect(self.browser.forward)
        nav_tb.addAction(next_btn)

        reload_btn = QAction(QIcon('./blue_icon/reload.png'), "Reload", self)
        reload_btn.setStatusTip("On recharge la page")                              # Reload the page
        reload_btn.triggered.connect(self.browser.reload)
        nav_tb.addAction(reload_btn)

        stop_btn = QAction(QIcon('./blue_icon/stop.png'), "Stop", self)
        stop_btn.setStatusTip("On arrête de charger la page")                       # Stop loading the page
        stop_btn.triggered.connect(self.browser.stop)
        nav_tb.addAction(stop_btn)

        self.urlbox = QLineEdit()
        self.urlbox.returnPressed.connect(self.navigate_to_url)
        self.urlbox.setStatusTip("Tu peut même introduire une adresse, hors noosfere, mais A TES RISQUES ET PERILS... noosfere est sûr ( https:// ), la toile par contre...")
                                # You can even enter an address, outside of noosfere, but AT YOUR OWN RISK... noosfere is safe: ( https:// ), the web on the other side...
        nav_tb.addWidget(self.urlbox)

        self.browser.urlChanged.connect(self.update_urlbar)
        self.browser.loadStarted.connect(self.loading_title)
        self.browser.loadFinished.connect(self.update_title)

        abort_btn = QAction(QIcon('./blue_icon/abort.png'), "Abort", self)
        abort_btn.setStatusTip("On arrête tout, on oublie tout et on ne change rien")
                              # Stop everything, forget everything and change nothing
        abort_btn.triggered.connect(self.close)
        nav_tb.addAction(abort_btn)

        exit_btn = QAction(QIcon('./blue_icon/exit.png'), "Select and exit", self)
        exit_btn.setStatusTip("On sélectionne cet URL pour extraction de nsfr_id, on continue")
                             # select this URL for extraction of nsfr_id, continue
        exit_btn.triggered.connect(self.select_and_exit)
        nav_tb.addAction(exit_btn)

        self.show()

        self.setStatusBar(QStatusBar(self))

  # get info actions
    def set_isbn_info(self):
        self.infobox.setText( self.isbn )
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(self.isbn.replace("-",""), mode=cb.Clipboard)

    def set_auteurs_info(self):
        self.infobox.setText( self.auteurs )
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(self.auteurs, mode=cb.Clipboard)

    def set_titre_info(self):
        self.infobox.setText( self.titre )

  # Navigation actions
    def initial_url(self,url="http://www.google.com"):
        self.browser.setUrl(QUrl(url))
        #self.urlbox.setText(url)

    def navigate_home(self):
        self.browser.setUrl( QUrl("https://www.noosfere.org/") )

    def navigate_to_url(self):                    # Does not receive the Url
        q = QUrl( self.urlbox.text() )
        self.browser.setUrl(q)

    def update_urlbar(self, q):
        self.urlbox.setText( q.toString() )
        self.urlbox.setCursorPosition(0)

    def loading_title(self):
        title="En téléchargement de l'url"
        self.setWindowTitle(title)

    def update_title(self):
        title = self.browser.page().title()
        self.setWindowTitle(title)

    def select_and_exit(self):                    #sent q to the queue wait till consumed then exit
        self.que.put(self.urlbox.text())
        #sys.exit(0)
        qApp.quit()

    def closeEvent(self, event):                  # hit window exit "X" button
        qDebug('MainWindow.closeEvent()')
        reply = QMessageBox.question(self, 'Vraiment', "Quitter et ne rien changer", QMessageBox.No | QMessageBox.Yes, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            event.accept()
            self.que.put("")
            super().closeEvent(event)
        else:
            event.ignore()

def wmain(url, isbn, auteurs, titre, que):
    app = QApplication([])
    window = MainWindow(url, isbn, auteurs, titre, que)
    window.initial_url(url)
    app.exec_()

if __name__ == '__main__':
    url="https://www.noosfere.org/livres/noosearch.asp"
    que = Queue()
    isbn = "2-277-12362-5"
    auteurs = "Alfred Elton VAN VOGT"
    titre = "Un tres tres long titre qui n'a rien a voir avec l'auteur ou l'ISBN"
    prc = Process(target=wmain, args=(url, isbn, auteurs, titre, que))
    prc.start()
    response = que.get()
    print("In main, la dernier url est: ", response, "len",  len(response), "type", type(response))
    prc.join()

