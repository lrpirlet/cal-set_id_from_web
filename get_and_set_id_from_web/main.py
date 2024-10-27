#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

__license__   = 'GPL v3'
__copyright__ = '2021, Louis Richard Pirlet'

# from pickle import FALSE
# from typing import Collection
from calibre import prints
from calibre.constants import cache_dir, DEBUG
from calibre.gui2 import open_url, error_dialog, info_dialog
from calibre.gui2.actions import InterfaceAction, menu_action_unique_name
from calibre.utils.date import UNDEFINED_DATE
from calibre_plugins.get_and_set_id_from_web.config import prefs

from qt.core import (QMenu, QMessageBox, QToolButton, QUrl, QEventLoop, QTimer)

import tempfile, glob, os, contextlib

try:
    load_translations()
except NameError:
    pass

def create_menu_action_unique(ia, parent_menu, menu_text, image=None, tooltip=None,
                       shortcut=None, triggered=None, is_checked=None, shortcut_name=None,
                       unique_name=None, favourites_menu_unique_name=None):
    '''
    Create a menu action with the specified criteria and action, using the new
    InterfaceAction.create_menu_action() function which ensures that regardless of
    whether a shortcut is specified it will appear in Preferences->Keyboard

    extracted from common_utils.py, found in many plugins ... header as follow:
    __license__   = 'GPL v3'
    __copyright__ = '2011, Grant Drake <grant.drake@gmail.com>
    __docformat__ = 'restructuredtext en'
    change to notice is the use of get_icons instead of get_icon in: ac.setIcon(get_icons(image))

    P.S. I like blue icons :-)...
    '''

    orig_shortcut = shortcut
    kb = ia.gui.keyboard
    if unique_name is None:
        unique_name = menu_text
    if not shortcut is False:
        full_unique_name = menu_action_unique_name(ia, unique_name)
        if full_unique_name in kb.shortcuts:
            shortcut = False
        else:
            if shortcut is not None and not shortcut is False:
                if len(shortcut) == 0:
                    shortcut = None
                else:
                    shortcut = _(shortcut)

    if shortcut_name is None:
        shortcut_name = menu_text.replace('&','')

    ac = ia.create_menu_action(parent_menu, unique_name, menu_text, icon=None, shortcut=shortcut,
        description=tooltip, triggered=triggered, shortcut_name=shortcut_name)
    if shortcut is False and not orig_shortcut is False:
        if ac.calibre_shortcut_unique_name in ia.gui.keyboard.shortcuts:
            kb.replace_action(ac.calibre_shortcut_unique_name, ac)
    if image:
        ac.setIcon(get_icons(image))
    if is_checked is not None:
        ac.setCheckable(True)
        if is_checked:
            ac.setChecked(True)
    return ac

class InterfacePlugin(InterfaceAction):

    name = 'get and set id from web'
    action_spec = (_("Fix id from web"), None,
            _("Run a webengine to set one or more ID manually"), None)
    popup_type = QToolButton.InstantPopup
    action_add_menu = True
    action_type = 'current'
    current_instance = None

  # assume main calibre is NOT in shutdown until genesis is called
    do_shutdown = False     # (note: refered later by self.do_shutdown, do not delete)
  # remove previous log files for web_main process in the temp dir
    with contextlib.suppress(FileNotFoundError): os.remove(os.path.join(tempfile.gettempdir(), 'GetAndSetIdFromWeb.log'))
  # remove help file that may have been updated anyway
    with contextlib.suppress(FileNotFoundError): os.remove(os.path.join(tempfile.gettempdir(), "GetAndSetIdFromWeb_doc.html"))
  # remove all trace of an old synchronization file between calibre and the detached process running QWebEngineView
    for i in glob.glob( os.path.join(tempfile.gettempdir(),"GetAndSetIdFromWeb_sync-cal-qweb*")):
            with contextlib.suppress(FileNotFoundError): os.remove(i)
  # remove all trace of a main calibre shutdown file to warn the detached process running QWebEngineView
    for i in glob.glob( os.path.join(tempfile.gettempdir(),"GetAndSetIdFromWeb_terminate-cal-qweb*")):
            with contextlib.suppress(FileNotFoundError): os.remove(i)
  # if size of the "browser_storage_folder = os.path.join(cache_dir(), 'getandsetidfromweb')"
  # is too big (>15 MBytes), delete it... I do not want clutering the calibre cache nor
  # do I want to depend on the temporary folders (that may be deleted at any boot if not anytime)
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(os.path.join(cache_dir(), 'getandsetidfromweb')):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):  # Skip symbolic links
                total_size += os.path.getsize(fp)
    prints(f"total_size of{os.path.join(cache_dir(), 'getandsetidfromweb')} is : {total_size} bytes, remove it.")
    if total_size >= 15728640:    # = (15*1024*1024)
        import shutil
        shutil.rmtree(os.path.join(cache_dir(), 'getandsetidfromweb'))

    def genesis(self):
        self.debug = DEBUG
      # get_icons and get_resources are partially defined function (zip location is defined)
      # those are known when genesis is called by calibre
        icon = get_icons('blue_icon/top_icon.png')
      # qaction is created and made available by calibre for get_and_set_id_from_web
        self.qaction.setIcon(icon)
      # load the prefs so that they are available
        self.collection_name = prefs["COLLECTION_NAME"]
        self.coll_srl_name = prefs["COLL_SRL_NAME"]
      # here we create a menu in calibre
        self.build_menus()
      # here we define how to process the shutdown_started signal
        self.gui.shutdown_started.connect(self.handle_shutdown)

    def build_menus(self):
        self.menu = QMenu(self.gui)
        self.menu.clear()
        # create_menu_action_unique(self, self.menu, _('Efface les métadonnées en surplus'), 'blue_icon/wipe_it.png',
        #                           triggered=self.wipe_selected_metadata)
        # self.menu.addSeparator()

        create_menu_action_unique(self, self.menu, _('Web browser to add one or more id to the selected book(s) before optionally downloading metadata'), 'blue_icon/choice.png',
                                  triggered=self.get_more_ids_for_books)
        self.menu.addSeparator()

        create_menu_action_unique(self, self.menu, _('Web browser to add a series of empty books associated to the selected books before optionally downloading metadata'), 'blue_icon/choice.png',
                                  triggered=self.add_series_of_books_from_web)
        self.menu.addSeparator()

        create_menu_action_unique(self, self.menu, _("Distribute overloaded information in publisher field (noosfere specific)"), 'blue_icon/eclate.png',
                                  triggered=self.unscramble_publisher)
        self.menu.addSeparator()

        create_menu_action_unique(self, self.menu, _("Create and configure the customized columns for noosfere")+'...', 'blue_icon/config.png',
                                  triggered=self.set_configuration)
        self.menu.addSeparator()

        create_menu_action_unique(self, self.menu, _('Help'), 'blue_icon/documentation.png',
                                  triggered=self.show_help)
        create_menu_action_unique(self, self.menu, _('About'), 'blue_icon/about.png',
                                  triggered=self.about)

        self.gui.keyboard.finalize()

      # Assign our menu to this action and an icon, also add dropdown menu
        self.qaction.setMenu(self.menu)

    def handle_shutdown(self):
        '''
        The web_browser is spawned from main calibre so both calibre and this process run concurrently.
        It is possible to kill (main) calibre while the get_and_set_id_from_web web_browser
        detached process is still running. If a book is selected, then the probability of hanging
        (main) calibre is very high, preventing to restart calibre.
        A process named "The main calibre program" is still running...
        The workaround is to kill this process or to reboot...

        To avoid this situation, A signal named "shutdown_started" was implemented so that about
        2 seconds are available to the get_and_set_id_from_web web_browser detached process
        to shutdown cleanly.

        The handle_shutdown(), triggered by the signal, do create a temp file that tells
        the web_browser detached process, to terminate, simulating the user aborting...
        At the same time, the handle_shutdown() will simulate the answer from the web_browser detached
        process to speed-up the reaction...

        Some temporary files will be left behind that will be killed at next invocation of get_and_set_id_from_web.
        '''
        if self.debug : prints("in handle_shutdown()")
        self.do_shutdown = True
        if self.debug : prints("self.do_shutdown = True")
        # if sync file is present, web_main detached process is still running.. send him a flag to kill itself
        if (glob.glob(os.path.join(tempfile.gettempdir(),"GetAndSetIdFromWeb_sync-cal-qweb*"))):
            terminate_tpf=tempfile.NamedTemporaryFile(prefix="GetAndSetIdFromWeb_terminate-cal-qweb", delete=False)
            terminate_tpf.close
            if self.debug : prints("tmp file GetAndSetIdFromWeb_terminate-cal-qweb created")

    def deduce_id_frm_url(self, url):
        '''
        id_from_url : takes an URL and extracts the identifier details...
        Id must be unique enough for other plugin(s) to verify/adopt, or not, this id
        '''

        if self.debug : prints(f"in deduce_id_frm_url(self, {url})")

        from calibre.customize.ui import all_metadata_plugins

        for plugin in all_metadata_plugins():
            if self.debug: prints(f"plugin is {plugin}")
            try:
                identifier = plugin.id_from_url(url)
                if identifier:
                    if self.debug: prints(f"identifier : {identifier}")
                    return identifier
            except Exception:
                pass
        return None

    def extract_info_sent_by_web_main(self):
        '''
        extract the info from the file "GetAndSetIdFromWeb_report_url" created by web_main,
        validate the info. Either returned_id or vld is signifiant (not None)
        returns returned_id, vld
        '''

        def detect_abort_kill_in_returned_url(returned_url):

            if self.debug :
                prints(f"in detect_abort_kill_in_returned_url(returned_url)")
                for i in range(len(returned_url)):
                    prints(f"returned_url[{i}] : {returned_url[i]}")

            for x in returned_url:
                if "killed by user" in x:
                    print('Killed, ' + _('no change will take place...'))
                    return (False, False)        # NO gt_st_id_frm_wb_id received, NO more boo
                if "aborted by user" in x:
                    print('Aborted, ' + _('no change will take place...'))
                    return (False, True)       # NO gt_st_id_frm_wb_id received, more book

            return None

        if self.debug: prints(f"in extract_info_sent_by_web_main(self)")

        returned_id, vld = None, None

        with open(os.path.join(tempfile.gettempdir(),"GetAndSetIdFromWeb_report_url"), "r", encoding="utf_8") as tpf:
            returned_url = [line.rstrip('\n') for line in tpf]

        if returned_url:
            vld = detect_abort_kill_in_returned_url(returned_url)
            if vld:
                return returned_id, vld

            returned_id=[]  #id_name, gt_st_id_frm_wb_id
            for i in range(len(returned_url)):
                rtnid=self.deduce_id_frm_url(returned_url[i])
                if rtnid :
                    returned_id.append(rtnid)

        if not (returned_url and returned_id):
            prints(_('No id could be extracted from url, ') + _('no change will take place...'))
            vld = (False, True)                             # gt_st_id_frm_wb_id NOT received, more book

        return returned_id, vld

    def get_more_ids_for_books(self):
        '''
        For the selected books:
        wipe metadata, launch a web-browser to select the desired volumes,
        set the gt_st_id_frm_wb_id, (?fire a metadata download?)
        '''
        if self.debug: prints("in get_more_ids_for_books")

      # Get currently selected books
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows or len(rows) == 0:
            return error_dialog(self.gui, _("No metadata touched"),_("No book selected"), show=True)

      # Map the rows to book ids
        ids = list(map(self.gui.library_view.model().id, rows))
        if self.debug : prints("ids : ", ids)

      # do the job for one book
      # gt_st_id_frm_wb_id_recu is true if metadata was updated, false if web_returned no gt_st_id_frm_wb_id
        nbr_ok = 0
        set_ok = set()      # will get a number associated with the selected line
        for book_id in ids:
          # if main calibre does shutdown, stop processing any more book_id
            if not self.do_shutdown:
                answer = self.get_more_ids_for_one_book(book_id)
                gt_st_id_frm_wb_id_recu, more = answer[0], answer[1]
            else:
                more = False        # if NOT more, gt_st_id_frm_wb_id_recu is False
            if not more:
                break
          # mark books that have NOT been bypassed... so we can fetch metadata on selected
            if gt_st_id_frm_wb_id_recu:
                nbr_ok += 1
                set_ok.add(book_id)
                if self.debug : prints("set_ok", set_ok)

      # tell user about what has been done...sorry, NOT if main calibre is closed...
        if not self.do_shutdown:
            if self.debug: prints('gt_st_id_frm_wb_id is recorded, metadata is prepared for {} book(s) out of {}'.format(nbr_ok, len(ids)))
            info_dialog(self.gui, _('Fix id from web') + ":" + _('id(s) recorded'),
                _('The metadata id field is filled for {} book(s) out of {} selected').format(nbr_ok, len(ids)),
                show=True)
          # new_api does not know anything about marked books, so we use the full db object
            if len(set_ok):
                self.gui.current_db.set_marked_ids(set_ok)
                self.gui.search.setEditText('marked:true')
                self.gui.search.do_search()
              # then we fill in the corresponding metadata
                self.gui.iactions['Edit Metadata'].download_metadata(ids=list(set_ok), ensure_fields=frozenset(['title', 'authors']))

    def get_more_ids_for_one_book(self, book_id):
        '''
        For the books_id:
        wipe metadata, launch a web-browser to select the desired volumes,
        set the gt_st_id_frm_wb_id, remove the ISBN (?fire a metadata download?)
        '''
        if self.debug: prints("in get_more_ids_for_one_book")

      # check for presence of needed column (needed for noosfere only)
        if not self.test_for_column():
            return

      # make current the book processed so that main calibre displays "Book details"
        self.gui.library_view.select_rows([book_id])

        db = self.gui.current_db.new_api
        mi = db.get_metadata(book_id, get_cover=False, cover_as_data=False)
        isbn, auteurs, titre="","",""

        if self.debug: prints("book_id          : ", book_id)
        if self.debug and mi.title: prints("title       *    : ", mi.title)
        if self.debug and mi.authors: prints("authors     *    : ", mi.authors)
        if self.debug and "isbn" in mi.get_identifiers(): prints("isbn             : ", mi.get_identifiers()["isbn"])

      # set url, isbn, auteurs, titre and debug level
        url = "https://www.google.com"     # jump directly to google if not overwritten in detached process
        if "isbn" in mi.get_identifiers(): isbn = mi.get_identifiers()["isbn"]
        auteurs = " & ".join(mi.authors)
        titre = mi.title
        data = [url, isbn, auteurs, titre, _('Search id(s) to add to selected book.') + '\t', self.debug]
      # data = [url, isbn, auteurs, titre, _('Search id(s) to create empty book(s).') + '\t', self.debug]      # must be same lenght for a nice presentation in the spawned web browser

      # unless shutdown_started signal asserted Launch a separate process to view the URL in WebEngine
        if not self.do_shutdown:
            self.gui.job_manager.launch_gui_app('webengine-dialog', kwargs={'module':'calibre_plugins.get_and_set_id_from_web.web_main', 'data':data})
            if self.debug: prints("webengine-dialog process submitted")          # WARNING: "webengine-dialog" is defined in calibre\src\calibre\utils\ipc\worker.py ...DO NOT CHANGE...
      # wait for web_main.py to settle and create a temp file to synchronize QWebEngineView with calibre...
      # watch out, self.do_shutdown is set by a signal, any time...
        while not (self.do_shutdown or glob.glob(os.path.join(tempfile.gettempdir(),"GetAndSetIdFromWeb_sync-cal-qweb*"))):
            loop = QEventLoop()
            QTimer.singleShot(200, loop.quit)
            loop.exec_()
      # wait till file is removed but loop fast enough for a user to feel the operation instantaneous...
      # watch out, self.do_shutdown is set by a signal, any time...
        while (not self.do_shutdown) and (glob.glob(os.path.join(tempfile.gettempdir(),"GetAndSetIdFromWeb_sync-cal-qweb*"))):
            loop = QEventLoop()
            QTimer.singleShot(200, loop.quit)
            loop.exec_()
      # unless shutdown_started signal asserted
        if not self.do_shutdown:
          # sync file is gone, meaning either QWebEngineView process is closed so, we can collect the result,
          # bypass if shutdown_started OR if web_main did crash (examine GetAndSetIdFromWeb.log in system temp folder)
            returned_id, vld = self.extract_info_sent_by_web_main()
            if vld:
                return vld
            if self.debug: prints(f"returned_id : {returned_id}, len(returned_id) : {len(returned_id)}")

            for key in mi.custom_field_keys():
                display_name, val, oldval, fm = mi.format_field_extended(key)
                if self.coll_srl_name == key : cstm_coll_srl_fm=fm
                if self.collection_name == key : cstm_collection_fm=fm
            mi.publisher=""
            mi.series=""
            mi.language=""
            mi.pubdate=UNDEFINED_DATE
            for i in range(len(returned_id)):
                id_name, gt_st_id_frm_wb_id = returned_id[i]
                mi.set_identifier(id_name, gt_st_id_frm_wb_id)
            if cstm_coll_srl_fm:
                cstm_coll_srl_fm["#value#"] = ""
                mi.set_user_metadata(self.coll_srl_name, cstm_coll_srl_fm)
            if cstm_collection_fm:
                cstm_collection_fm["#value#"] = ""
                mi.set_user_metadata(self.collection_name, cstm_collection_fm)

        if self.do_shutdown:
            return(False,False)                             # shutdown_started, do not try to change db
        else:      # commit the change, force reset of the above fields, leave the others alone
            db.set_metadata(book_id, mi, force_changes=True)
            return (True, True)                                 # gt_st_id_frm_wb_id received, more book

    def add_series_of_books_from_web(self, book_id):
        '''
        For the selected books:
        launch a web-browser to select the associated books in the series,
        set the gt_st_id_frm_wb_id, (?fire a metadata download?)
        '''
        if self.debug: prints("in add_series_of_books_from_web")

      # Get currently selected books
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows or len(rows) == 0:
            return error_dialog(self.gui, _("No metadata touched"),_("No book selected"), show=True)
            # return error_dialog(self.gui, 'Pas de métadonnées affectées','Aucun livre sélectionné', show=True)

      # Map the rows to book ids
        ids = list(map(self.gui.library_view.model().id, rows))
        if self.debug : prints("ids : ", ids)

      # do the job for one book tied with a series
      # gt_st_id_frm_wb_id_recu is true if metadata was updated, false if web_returned no gt_st_id_frm_wb_id

        for book_id in ids:
          # if main calibre does shutdown, stop processing any more book_id
            if not self.do_shutdown:
                gt_st_id_frm_wb_id_recu, more = self.add_one_series_of_books_from_web(book_id)
            else:
                more = False        # if NOT more, gt_st_id_frm_wb_id_recu is False
            if not more:
                break

    def add_one_series_of_books_from_web(self, book_id):
        '''
        For each of the selected book(s) :
        launch a web-browser to select the desired books in the series (isbn, title and authors provided)
        make a valid list and submit it to self.gui.iactions['Add Books'].add_isbns()
        params being: add_isbns(self, books, add_tags=[], check_for_existing=False)
        '''
        if self.debug: prints("in add_one_series_of_books_from_web")

      # make current the book processed so that main calibre displays "Book details"
        self.gui.library_view.select_rows([book_id])

        db = self.gui.current_db.new_api
        mi = db.get_metadata(book_id, get_cover=False, cover_as_data=False)
        isbn, auteurs, titre="","",""

        if self.debug: prints("book_id          : ", book_id)
        if self.debug and mi.title: prints("title       *    : ", mi.title)
        if self.debug and mi.authors: prints("authors     *    : ", mi.authors)
        if self.debug and "isbn" in mi.get_identifiers(): prints("isbn             : ", mi.get_identifiers()["isbn"])

      # set url, isbn, auteurs, titre and debug level
        url = "https://www.google.com"     # jump directly to google
        if "isbn" in mi.get_identifiers(): isbn = mi.get_identifiers()["isbn"]
        auteurs = " & ".join(mi.authors)
        titre = mi.title
      # data = [url, isbn, auteurs, titre, _('Search id(s) to add to selected book.') + '\t', self.debug]
        data = [url, isbn, auteurs, titre, _('Search id(s) to create empty book(s).') + '\t', self.debug]      # must be same lenght for a nice presentation in the spawned web browser

      # unless shutdown_started signal asserted Launch a separate process to view the URL in WebEngine
        if not self.do_shutdown:
            self.gui.job_manager.launch_gui_app('webengine-dialog', kwargs={'module':'calibre_plugins.get_and_set_id_from_web.web_main', 'data':data})
            if self.debug: prints("webengine-dialog process submitted")          # WARNING: "webengine-dialog" is defined in calibre\src\calibre\utils\ipc\worker.py ...DO NOT CHANGE...
      # wait for web_main.py to settle and create a temp file to synchronize QWebEngineView with calibre...
      # watch out, self.do_shutdown is set by a signal, any time...
        while not (self.do_shutdown or glob.glob(os.path.join(tempfile.gettempdir(),"GetAndSetIdFromWeb_sync-cal-qweb*"))):
            loop = QEventLoop()
            QTimer.singleShot(200, loop.quit)
            loop.exec_()
      # wait till file is removed but loop fast enough for a user to feel the operation instantaneous...
      # watch out, self.do_shutdown is set by a signal, any time...
        while (not self.do_shutdown) and (glob.glob(os.path.join(tempfile.gettempdir(),"GetAndSetIdFromWeb_sync-cal-qweb*"))):
            loop = QEventLoop()
            QTimer.singleShot(200, loop.quit)
            loop.exec_()
      # unless shutdown_started signal asserted
        if not self.do_shutdown:
          # sync file is gone, meaning either QWebEngineView process is closed so, we can collect the result,
          # bypass if shutdown_started OR if web_main did crash (examine GetAndSetIdFromWeb.log in system temp folder)
            returned_id, vld = self.extract_info_sent_by_web_main()
            if vld:
                return vld
            if self.debug: prints(f"returned_id : {returned_id}, len(returned_id) : {len(returned_id)}")

          # format returned_id to expected books format then call self.gui.iactions['Add Books'].add_isbns() (if not shutdown)
            books = []
            for i in range(len(returned_id)):
                if self.debug: prints(f"returned_id[{i}] : {returned_id[i]} /t type(returned_id[{i})] : {type(returned_id[i])}")
                prefix, val = returned_id[i]
                books.append({prefix: val, 'path': None, '':prefix})
            if self.debug: prints(f"books : {books}")

        if self.do_shutdown:
            return(False,False)                             # shutdown_started, do not try to change db
        else:     # commit the added books in the db
            self.gui.iactions['Add Books'].add_isbns(books, add_tags=["DESIRE"], check_for_existing=True)
            return (True, True)                                 # gt_st_id_frm_wb_id received, more book

    def unscramble_publisher(self):
        if self.debug: prints("in unscramble_publisher")
      # check for presence of needed column
        if not self.test_for_column():
            return
      # Get currently selected books
        rows = self.gui.library_view.selectionModel().selectedRows()
        if not rows or len(rows) == 0:
            return error_dialog(self.gui, _("No metadata touched"),_("No book selected"), show=True)
            # return error_dialog(self.gui, 'Pas de métadonnées affectées','Aucun livre sélectionné', show=True)

        # Map the rows to book ids
        ids = list(map(self.gui.library_view.model().id, rows))
        if self.debug: prints("ids : ", ids)
        db = self.gui.current_db.new_api
        for book_id in ids:
          # Get the current metadata of interest for this book from the db
            mi = db.get_metadata(book_id, get_cover=False, cover_as_data=False)
            scrbl_dt = mi.publisher
            if (scrbl_dt and (("€" in scrbl_dt) or ("§" in scrbl_dt))):
                val_collection, val_coll_srl = None, None
                if "€" in scrbl_dt: scrbl_dt, val_coll_srl = scrbl_dt.split("€")
                if "§" in scrbl_dt: scrbl_dt, val_collection = scrbl_dt.split("§")
                if self.debug:
                    prints("val_collection : ", val_collection) if val_collection else prints("val_collection not in publisher")
                    prints("val_coll_srl   : ", val_coll_srl) if val_coll_srl else prints("val_coll_srl not in publisher")
                    prints("éditeur (scrbl_dt)   : ", scrbl_dt)
              # Set the current metadata of interest for this book in the db
                if val_collection: db.set_field(self.collection_name, {book_id: val_collection})
                if val_coll_srl: db.set_field(self.coll_srl_name, {book_id: val_coll_srl})
                db.set_field("publisher", {book_id: scrbl_dt})
                self.gui.iactions['Edit Metadata'].refresh_gui([book_id])

        info_dialog(self.gui, _('Information distributed'),
                _("The information was distributed for {} book(s).").format(len(ids)),
                show=True)

    def test_for_column(self):
        if self.debug:
            prints("in test_for_column")
            prints("recorded self.collection_name", self.collection_name)
            prints("recorded self.coll_srl_name", self.coll_srl_name)

        custom_columns = self.gui.library_view.model().custom_columns
        all_custom_col = []
        for key, column in custom_columns.items(): all_custom_col.append(key)
        if self.debug: prints("all_custom_col :", all_custom_col)
        if (self.collection_name and self.coll_srl_name) not in all_custom_col:
            if self.debug: prints("Okay, Houston...we've had a problem here (Apollo 13): non existant column")
            text = _("<p> One column or the other, if not both are missing... Please do correct that.")
            text += "</p><p> <strong>" + _("Fix id from web") + "</strong>"
            text += _(' may be used to ')
            text += '<br/><strong>'
            text += _('Create and configure the customized columns for noosfere')
            text += "</strong>.</p>"

            error_dialog(self.gui, _('Non existing columns'), text, show=True)
            return False
        return True

    def set_configuration(self):
        '''
        will present the configuration widget... should handle custom columns needed for
        self.collection_name (#collection) and self.coll_srl_name (#coll_srl).
        '''
        if self.debug: prints("in set_configuration")

        self.interface_action_base_plugin.do_user_config(self.gui)

    def show_help(self):
         # Extract on demand the help file resource to a temp file
        def get_help_file_resource():
          # keep "GetAndSetIdFromWeb_doc.html" as the last item in the list, this is the help entry point
          # we need both files for the help
            file_path = os.path.join(tempfile.gettempdir(), "GetAndSetIdFromWeb_075.png")
            file_data = self.load_resources('doc/' + "GetAndSetIdFromWeb_075.png")['doc/' + "GetAndSetIdFromWeb_075.png"]
            if self.debug: prints('show_help picture - file_path:', file_path)
            with open(file_path,'wb') as fpng:
                fpng.write(file_data)

            file_path = os.path.join(tempfile.gettempdir(), "GetAndSetIdFromWeb_doc.html")
            file_data = self.load_resources('doc/' + "GetAndSetIdFromWeb_doc.html")['doc/' + "GetAndSetIdFromWeb_doc.html"]
            if self.debug: prints('show_help - file_path:', file_path)
            with open(file_path,'wb') as fhtm:
                fhtm.write(file_data)
            return file_path
        url = 'file:///' + get_help_file_resource()
        url = QUrl(url)
        open_url(url)

    def about(self):
        text = get_resources("doc/about.txt")
        text += "\n" + (_("The name of publisher's collection will be under") + " : {},".format(self.collection_name)).encode('utf-8')
        text += "\n" + (_("The code in the publisher collection's will be under") + " : {}".format(self.coll_srl_name)).encode('utf-8')
        QMessageBox.about(self.gui, _('About the get_and_set_id_from_web'), text.decode('utf-8'))

    def apply_settings(self):
        from calibre_plugins.get_and_set_id_from_web.config import prefs
        # In an actual non trivial plugin, you would probably need to
        # do something based on the settings in prefs
        if self.debug: prints("in apply_settings")
        if self.debug: prints("prefs['COLLECTION_NAME'] : ", prefs['COLLECTION_NAME'])
        if self.debug: prints("prefs['COLL_SRL_NAME'] : ", prefs['COLL_SRL_NAME'])
        prefs

'''
to do : utilise ngettext pour singulier/pluriel

from calibre.utils.localization import ngettext

        msg = '<p>' + ngettext(
            'Finished downloading metadata for the selected book.',
            'Finished downloading metadata for <b>{} books</b>.', len(id_map)).format(len(id_map)) + ' ' + \
            _('Proceed with updating the metadata in your library?')

to do : executer le remplissage des liivre apres selection manuelle des id's

'''