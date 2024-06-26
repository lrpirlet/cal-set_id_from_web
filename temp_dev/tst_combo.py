# spin_combo_boxes.py
# Import necessary modules
import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QLabel, QComboBox, QSpinBox, QHBoxLayout, QVBoxLayout)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt
class SelectItems(QWidget):

    def __init__(self):
        # super().__init__()
        QWidget.__init__(self)
        self.initializeUI()

    def initializeUI(self):
        """
        Initialize the window and display its contents to the screen
        """
        self.setGeometry(100, 100, 300, 200)
        # self.setWindowTitle('ComboBox and SpinBox')
        self.columns_name()
        self.show()

    def columns_name(self):
        """
        Create the widgets so users can select or create a column from the combo boxes
        """
        info_label = QLabel("Select the columns to expand the overloaded publisher")
        info_label.setFont(QFont('Arial', 12))
        info_label.setAlignment(Qt.AlignCenter)
        # self.display_total_label = QLabel("Total Spent: $")
        # self.display_total_label.setFont(QFont('Arial', 16))
        # self.display_total_label.setAlignment(Qt.AlignRight)
        # Create list of food items and add those items to two separate combo boxes
        lunch_list = ["egg", "turkey sandwich", "ham sandwich", "cheese", "hummus", "yogurt", "apple", "banana", "orange", "waffle", "baby carrots", "bread", "pasta", "crackers", "pretzels", "pita chips", "coffee", "soda", "water"]
        
        label_collection = QLabel("#collection name")
        name_collection = QComboBox()
        name_collection.addItems(lunch_list)

        label_coll_srl = QLabel("#coll_srl name")
        name_coll_srl = QComboBox()
        name_coll_srl.addItems(lunch_list)
        # # Create two separate price spin boxes
        # self.price_sb1 = QSpinBox()
        # self.price_sb1.setRange(0,100)
        # self.price_sb1.setPrefix("$")
        # self.price_sb1.valueChanged.connect(self.calculateTotal)
        # self.price_sb2 = QSpinBox()
        # self.price_sb2.setRange(0,100)
        # self.price_sb2.setPrefix("$")
        # self.price_sb2.valueChanged.connect(self.calculateTotal)
        # Create horizontal boxes to hold combo boxes and spin boxes
        h_box1 = QHBoxLayout()
        h_box2 = QHBoxLayout()
        h_box1.addWidget(label_collection)
        h_box1.addWidget(name_collection)
        h_box2.addWidget(label_coll_srl)
        h_box2.addWidget(name_coll_srl)
        # Add widgets and layouts to QVBoxLayout
        v_box = QVBoxLayout()
        v_box.addWidget(info_label)
        v_box.addLayout(h_box1)
        v_box.addLayout(h_box2)
        # v_box.addWidget(self.display_total_label)
        self.setLayout(v_box)

    # def calculateTotal(self):
    #     """
    #     Calculate and display total price from spin boxes and change value shown in QLabel
    #     """
    #     total = self.price_sb1.value() + self.price_sb2.value()
    #     self.display_total_label.setText("Total Spent: ${}".format(str(total)))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SelectItems()
    sys.exit(app.exec_())
