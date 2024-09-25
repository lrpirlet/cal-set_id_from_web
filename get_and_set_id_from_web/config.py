#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai


__license__   = 'GPL v3'
__copyright__ = '2021, Louis Richard Pirlet'

from qt.core import (QWidget, QLabel, QComboBox, QHBoxLayout, QVBoxLayout, QFont, Qt, QIcon, QDialogButtonBox)

from calibre import prints
from calibre.constants import DEBUG
from calibre.gui2 import info_dialog
from calibre.gui2.ui import get_gui
from calibre.gui2.preferences.create_custom_column import CreateNewCustomColumn
from calibre.utils.config import JSONConfig

prefs = JSONConfig('plugins/get_and_set_id_manually_from_web')

# Set defaults
prefs.defaults["COLLECTION_NAME"] = "#collection"
prefs.defaults["COLL_SRL_NAME"] = "#coll_srl"

try:
    load_translations()
except NameError:
    pass

class ConfigWidget(QWidget):

    def __init__(self, plugin_action):
        QWidget.__init__(self)
        self.plugin_action = plugin_action

        self.collection_name = prefs.defaults["COLLECTION_NAME"]
        self.coll_srl_name = prefs.defaults["COLL_SRL_NAME"]

        self.current_collection_name = prefs["COLLECTION_NAME"]
        self.current_coll_srl_name = prefs["COLL_SRL_NAME"]

        if DEBUG:
            prints("In ConfigWidget")
            prints("self.current_collection_name : ", self.current_collection_name)
            prints("self.current_coll_srl_name : ", self.current_coll_srl_name)

      # define here a creator = CreateNewCustomColumn(gui) so that it remain common during the whole configuration
      # The parameter 'gui' passed when creating a class instance is the main calibre gui (calibre.gui2.ui.get_gui())

        self.gui = get_gui()
        self.creator = CreateNewCustomColumn(self.gui)

      # create the combo box
        self.create_combo_box_list("text")
        self.create_combo_box_list("comments")
        self.setGeometry(100, 100, 300, 200)
        self.pick_columns_name()
        self.show()

    def create_combo_box_list(self, column_type):
        """
        creates a list for the comboboxes to use, list is ordered
        column_type is "text" for pertinent_collection_list
        column_type is "comments" for pertinent_coll_srl_list
        """
        if DEBUG: prints("\nIn create_combo_box_list(self, column_type); column_type : ", column_type)
        if column_type == "text" :
            self.pertinent_collection_list = self.get_custom_columns("text")
            self.pertinent_collection_list.extend(["", _('Add and select a column')])
            if DEBUG: prints("self.pertinent_collection_list: ", self.pertinent_collection_list)
        elif column_type == "comments":
            self.pertinent_coll_srl_list = self.get_custom_columns("comments")
            self.pertinent_coll_srl_list.extend(["", _('Add and select a column')])
            if DEBUG: prints("self.pertinent_coll_srl_list: ", self.pertinent_coll_srl_list)

    def get_custom_columns(self, column_type):
        """
        return a list of column suitable for column_type
          (either "comment": column not shown in the Tag browser,
          or "text": column shown in the Tag browser)
        """
        if DEBUG: prints("\nIn get_custom_columns(self, column_type : {})".format(column_type))
        custom_columns = self.creator.current_columns()
        possible_columns = []
        for key, column in custom_columns.items():
            typ = column['datatype']
            if typ in column_type and not column['is_multiple']:
                possible_columns.append(key)
        if DEBUG: prints("In get_custom_columns; possible_columns :", possible_columns)
        return sorted(possible_columns)

    def pick_columns_name(self):
        """
        Create the widgets so users can select or create a column from the combo boxes
        """
        if DEBUG: prints("\nIn pick_columns_name")

        info_label = QLabel(_("Select the columns to distribute the publisher overloaded information (noosfere)."))
        info_label.setFont(QFont('Arial', 11))
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setToolTip(_("To create and/or select a column means restarting calibre."))
            
        label_collection = QLabel(_("Name of collection publisher"))
        label_collection.setToolTip(_("Displayed column is actualy selected"))
        self.name_collection = QComboBox(self)
        self.name_collection.addItems(self.pertinent_collection_list)
        self.name_collection.setCurrentIndex(self.name_collection.findText(self.current_collection_name,Qt.MatchFixedString))
        self.name_collection.textActivated.connect(self.select_for_collection)

        label_coll_srl = QLabel(_("Code in the publisher's collection"))
        self.name_coll_srl = QComboBox(self)
        label_coll_srl.setToolTip(_("Displayed column is actualy selected"))
        self.name_coll_srl.addItems(self.pertinent_coll_srl_list)
        self.name_coll_srl.setCurrentIndex(self.name_coll_srl.findText(self.current_coll_srl_name,Qt.MatchFixedString))
        self.name_coll_srl.textActivated.connect(self.select_for_coll_srl)
      # First line
        h_box1 = QHBoxLayout()
        h_box1.addWidget(label_collection)
        h_box1.addWidget(self.name_collection)
      # Second line
        h_box2 = QHBoxLayout()
        h_box2.addWidget(label_coll_srl)
        h_box2.addWidget(self.name_coll_srl)
      # Add widgets and layouts to QVBoxLayout
        v_box = QVBoxLayout()
        v_box.addWidget(info_label)
        v_box.addLayout(h_box1)
        v_box.addLayout(h_box2)
      # v_box.addWidget(self.display_total_label)
        self.setLayout(v_box)

    def select_for_collection(self, name):
        if DEBUG: prints("\nIn select_for_collection(self, name : {}".format(name))
        if name ==  _('Add and select a column'):
            self.create_custom_column(lookup_name = "#collection")
        else:
            self.collection_name = name
            self.name_collection.setCurrentIndex(self.name_collection.findText(name,Qt.MatchFixedString))
        if DEBUG: prints("self.collection_name : ", self.collection_name)

    def select_for_coll_srl(self, name):
        if DEBUG: prints("\nIn select_for_coll_srl(self, name : {}".format(name))
        if name ==  _('Add and select a column'):
            self.create_custom_column(lookup_name = "#coll_srl")
        else:
            self.coll_srl_name = name
            self.name_coll_srl.setCurrentIndex(self.name_coll_srl.findText(name,Qt.MatchFixedString))
        if DEBUG: prints("self.coll_srl_name : ", self.coll_srl_name)


    def create_custom_column(self, lookup_name=None):
        if DEBUG: prints("\nIn create_custom_column - lookup_name:", lookup_name)
        if lookup_name == "#collection" :
            display_params = {"description": _("The publisher collection name for the volume")}
            datatype = "text"
            column_heading  = "collection"

        elif lookup_name == "#coll_srl" :
            display_params =   {'description': _("The code in the publisher's collection"), 'heading_position': 'hide', 'interpret_as': 'short-text'}
            datatype = "comments"
            column_heading  = "coll_srl"

        if self.creator.must_restart():
            d_ttl  = _("Calibre must restart, sorry")
            d_txt  = "<p>" + _("No more modification cannot be taken into account.")
            d_txt += "</p><p>" + _("Calibre needs to be restarted before proceding") + "</p>"
            do_restart = self.ask_user_now(d_ttl, d_txt)
            if do_restart :
                     self.gui.quit(restart=True)

        result = self.creator.create_column(lookup_name, column_heading, datatype, False, display=display_params, generate_unused_lookup_name=True, freeze_lookup_name=False)
        if DEBUG: prints("result : ", result)
        if result[0] == CreateNewCustomColumn.Result.COLUMN_ADDED:
            if lookup_name == "#collection" :
                self.name_collection.removeItem(self.name_collection.findText(_('Add and select a column'), Qt.MatchFixedString))
                self.name_collection.addItem(result[1])
                self.name_collection.setCurrentIndex(self.name_collection.findText(result[1], Qt.MatchFixedString))
                self.collection_name = result[1]
            elif lookup_name == "#coll_srl" :
                self.name_collection.removeItem(self.name_collection.findText(_('Add and select a column'), Qt.MatchFixedString))
                self.name_coll_srl.addItem(result[1])
                self.name_coll_srl.setCurrentIndex(self.name_coll_srl.findText(result[1], Qt.MatchFixedString))
                self.coll_srl_name = result[1]
        return

    def save_settings(self):
        if DEBUG: prints("in save_settings")
        if DEBUG: prints("self.collection_name : ", self.collection_name)
        if DEBUG: prints("self.coll_srl_name : ", self.coll_srl_name)

        prefs["COLLECTION_NAME"] = self.collection_name
        prefs["COLL_SRL_NAME"] = self.coll_srl_name
        
        d_ttl  = _("Calibre must restart, sorry")
        d_txt  = "<p>" + _("In order to take effect, the choice of column needs a restart...")
        d_txt += "</p><p>" + _("The name of publisher's collection will be under")
        d_txt += ": <strong>{}</strong>".format(self.collection_name)
        d_txt += "</p><p>" + _("The code in the publisher collection's will be under")
        d_txt += ": <strong>{}</strong>".format(self.coll_srl_name) + "</p>"
        do_restart = self.ask_user_now(d_ttl, d_txt)
        if do_restart :
                 self.gui.quit(restart=True)

    def ask_user_now(self, d_ttl, d_txt):
        if DEBUG: prints("in ask_user_now")

        d = info_dialog(self.gui, d_ttl, d_txt, show_copy_button=False)
        b = d.bb.addButton(_('&Restart calibre now'), QDialogButtonBox.ButtonRole.AcceptRole)
        b.setIcon(QIcon.ic('lt.png'))
        d.do_restart = False

        def rf():
            d.do_restart = True
        b.clicked.connect(rf)
        d.set_details('')
        d.exec()
        b.clicked.disconnect()

        return d.do_restart
        


