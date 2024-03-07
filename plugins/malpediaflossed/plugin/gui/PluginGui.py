import io
import os
import re
import csv
import time
import json
import math
import requests
from sys import modules
from copy import deepcopy


if "idaapi" in modules:
    # We are running inside IDA
    from PyQt5 import QtWidgets
    from PyQt5 import QtGui, QtCore
else:
    # We are running inside Cutter, Binary Ninja or Ghidra
    try:
        import PySide2.QtWidgets as QtWidgets
        import PySide2.QtGui as QtGui
        import PySide2.QtCore as QtCore
    except:
        import PySide6.QtWidgets as QtWidgets
        import PySide6.QtGui as QtGui
        import PySide6.QtCore as QtCore




# Define location for the FLOSSed file
THIS_FILE_PATH = str(os.path.abspath(__file__))
PROJECT_ROOT = str(os.path.abspath(os.sep.join([THIS_FILE_PATH, "..", "..", "..", "..", ".."])))
FLOSSED_FILEPATH = os.sep.join([PROJECT_ROOT, "data", "malpedia_flossed.json"])
# Run analysis immediately when plugin is started
AUTO_ANALYZE = False
# If you set FLOSSED_SERVICE, this will be used instead of the local file
# e.g. use our hosted
# FLOSSED_SERVICE = "https://strings.malpedia.io/api/query"
# ... or if you have your own local setup
# FLOSSED_SERVICE = "http://127.0.0.1:8000/api/query"
# leaving this empty means local mode, i.e. loading the JSON specified above instead
FLOSSED_SERVICE = "https://strings.malpedia.io/api/query"






def csv_encode(list_of_strings):
    output = io.StringIO()
    writer = csv.writer(output, quotechar='"', delimiter=",", quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(list_of_strings)
    return output.getvalue().strip()

def filter_string(string):
    if re.match("^[ -~\t\r\n]+$", string):
        return string
    return ""

def filter_strings(list_of_strings):
    cleaned_strings = []
    for string in list_of_strings:
        if re.match("^[ -~\t\r\n]+$", string):
            cleaned_strings.append(string)
    return cleaned_strings

def get_color_for_string(flossed_string):
    score_to_color = {
        # cyan
        0: (0x00, 0xff, 0xff),
        # green
        1: (0x00, 0xff, 0x00),
        # lime
        5: (0xc0, 0xff, 0x00),
        # yellow
        10: (0xff, 0xff, 0x00),
        # orange
        20: (0xff, 0xc0, 0x00),
        # dark orange
        50: (0xff, 0x80, 0x00),
        # red-orange
        100: (0xff, 0x40, 0x00),
        # red
        2000: (0xff, 0x00, 0x00)
    }
    if flossed_string[4]:
        # we start with red
        result_color = (0xff, 0x00, 0x00)
        if "family_count" in flossed_string[3]:
            for color_score, color_tuple in sorted(score_to_color.items(), reverse=True):
                if flossed_string[3]["family_count"] <= color_score:
                    result_color = color_tuple
            return QtGui.QColor(result_color[0], result_color[1], result_color[2])
        else:
            return QtGui.QColor(0x00, 0xff, 0xff)
    # string didn't pass filtering due to special chars, no lookup possible
    return QtGui.QColor(0x99, 0x99, 0x99)


class NumberQTableWidgetItem(QtWidgets.QTableWidgetItem):
    """
    A simple helper class that allows sorting by numeric values.
    """

    def __lt__(self, other):
        """
        Redefine function from QTableWidgetItem to allow sorting by numeric value instead of string value.
        @param other: another item of the same type
        @type other: I{NumberQTableWidgetItem}
        @return: (boolean) the numeric comparison of the items.
        """
        return float(self.text()) < float(other.text())


class PluginGui():

    def __init__(self, api_proxy) -> None:
        self.layout = QtWidgets.QVBoxLayout()
        self.api_proxy = api_proxy
        self._createGui()
        if AUTO_ANALYZE:
            self._analyzeStrings()

    def _createGui(self):
        """
        defines widget layout 
        """
        ##### top part
        self.controls_widget = QtWidgets.QWidget()
        controls_layout = QtWidgets.QHBoxLayout()
        # actual widgets
        self.cb_show_invalid = QtWidgets.QCheckBox("Show invalid strings")
        self.cb_show_invalid.setEnabled(True)
        self.cb_show_invalid.setChecked(False)
        self.cb_show_invalid.clicked.connect(self._onCheckBoxClicked)
        # deduplicate button
        self.cb_deduplicate = QtWidgets.QCheckBox("Deduplicate strings")
        self.cb_deduplicate.setEnabled(True)
        self.cb_deduplicate.setChecked(True)
        self.cb_deduplicate.clicked.connect(self._onCheckBoxClicked)
        # analyze button
        self.b_analyze = QtWidgets.QPushButton("Analyze")
        self.b_analyze.clicked.connect(self._onBAnalyzeClicked)
        self.b_analyze.setEnabled(True)
        # overview button
        self.b_overview = QtWidgets.QPushButton("Show Overview")
        self.b_overview.clicked.connect(self._onBOverviewClicked)
        self.b_overview.setEnabled(True)
        # filter trash
        self.cb_filter_trash = QtWidgets.QCheckBox("Show potential trash strings")
        self.cb_filter_trash.setEnabled(True)
        self.cb_filter_trash.setChecked(False)
        self.cb_filter_trash.clicked.connect(self._onCheckBoxClicked)
        # filter wheel
        self.sb_score_threshold = QtWidgets.QSpinBox()
        self.sb_score_threshold.setRange(0, 100)
        self.sb_score_threshold.setValue(50)
        self.sb_score_threshold.valueChanged.connect(self.handleSpinScoreChange)
        self.label_sb_score = QtWidgets.QLabel("Min. Score: ")
        # checkboxes
        self.menu_left_widget = QtWidgets.QWidget()
        menu_left_layout = QtWidgets.QVBoxLayout()
        menu_left_layout.addWidget(self.cb_show_invalid)
        menu_left_layout.addWidget(self.cb_deduplicate)
        # buttons for analysis and overview
        two_buttons_widget = QtWidgets.QWidget()
        two_buttons_layout = QtWidgets.QHBoxLayout()
        two_buttons_layout.addWidget(self.b_analyze)
        two_buttons_layout.addWidget(self.b_overview)
        two_buttons_widget.setLayout(two_buttons_layout)
        # glue together
        menu_left_layout.addWidget(two_buttons_widget)
        self.menu_left_widget.setLayout(menu_left_layout)
        # threshold spinbox and label
        self.menu_right_widget = QtWidgets.QWidget()
        threshold_layout = QtWidgets.QVBoxLayout()
        threshold_layout.addWidget(self.cb_filter_trash)
        threshold_layout.addWidget(self.label_sb_score)
        threshold_layout.addWidget(self.sb_score_threshold)
        self.menu_right_widget.setLayout(threshold_layout)
        # glue controls
        controls_layout.addWidget(self.menu_left_widget)
        controls_layout.addWidget(self.menu_right_widget)
        self.controls_widget.setLayout(controls_layout)
        ##### bottom part
        self.table_flossed_strings = QtWidgets.QTableWidget()
        self.table_flossed_strings.doubleClicked.connect(self._onTableDoubleClicked)
        self.layout.addWidget(self.controls_widget)
        self.layout.addWidget(self.table_flossed_strings)

    def _analyzeStrings(self):
        # do stuff
        self.use_query_service = FLOSSED_SERVICE not in [None, ""]
        if not self.use_query_service:
            print("No FLOSSed webservice specified.")
            if os.path.exists(FLOSSED_FILEPATH):
                print("Loading FLOSSed JSON file.")
                time.sleep(0.5)
                self.load_json()
            else:
                raise("Configured to not use a web service for queries but FLOSSED_FILEPATH is not pointing to a valid file - did you unpack the zip file in ./data yet?")
        self.info_by_string = {}
        self.flossed_strings = self.process_strings()
        option_compatible_strings = self.filter_by_options(self.flossed_strings)
        self.update_table(option_compatible_strings)


    def _onCheckBoxClicked(self, mi):
        """ If the filter is altered, we refresh the table. """
        option_compatible_strings = self.filter_by_options(self.flossed_strings)
        self.update_table(option_compatible_strings)

    def _onBAnalyzeClicked(self, mi):
        self._analyzeStrings()

    def _onBOverviewClicked(self, mi):
        # calculate some statistics
        family_to_score = {}
        for entry in self.flossed_strings:
            if entry[3]:
                for family in entry[3]["families"]:
                    if family not in family_to_score:
                        family_to_score[family] = 0
                    family_to_score[family] += entry[5]
        num_families_shown = 0
        print("-" * 50)
        print("    |                         Family |  agg. score")
        print("-" * 50)
        for family, score in sorted(family_to_score.items(), key=lambda x: x[1], reverse=True):
            num_families_shown +=1
            print(f"{num_families_shown:>2}. | {family:>30} | {score:>11.2f}")
            if num_families_shown >= 20:
                break

    def handleSpinScoreChange(self, mi):
        """ If the filter is altered, we refresh the table. """
        option_compatible_strings = self.filter_by_options(self.flossed_strings)
        self.update_table(option_compatible_strings)

    def filter_by_options(self, input_strings):
        start_strings = deepcopy(input_strings)
        filtered_strings = []
        deduplicated_strings = set([])
        for string in sorted(start_strings):
            if not string[4]:
                if not self.cb_show_invalid.isChecked():
                    continue
            if string[5] < self.sb_score_threshold.value():
                continue
            if not self.cb_filter_trash.isChecked() and string[6] >= 40:
                continue
            if self.cb_deduplicate.isChecked() and string[2] in deduplicated_strings:
                continue
            filtered_strings.append(string)
            deduplicated_strings.add(string[2])
        return filtered_strings

    def get_local_string_info(self, needle):
        return self._flossed_dict["strings"].get(needle, {})

    def load_json(self):
        flossed_dict = {}
        with open(FLOSSED_FILEPATH, "r") as fin:
            flossed_dict = json.load(fin)
        # translate family_ids to families
        self._family_id_to_family = {value: key for key, value in flossed_dict["family_to_id"].items()}
        for _, string_doc in flossed_dict["strings"].items():
            string_doc["families"] = [self._family_id_to_family[family_id] for family_id in string_doc["families"]]
        self._flossed_dict = flossed_dict

    def get_string_score(self, string):
        score = 0
        if string not in self.info_by_string:
            score = 0
        else:
            if "family_count" in self.info_by_string[string]:
                # just some random function that slopes nicely :D
                score = round(max(1, (2000 / (self.info_by_string[string]["family_count"] + 20))), 2)
            else:
                # string is not known, so probably pretty rate/unique
                score = 100
        return score
    
    def get_trash_score(self, string):
        # possibly subject to change
        score = 0
        for char in string:
            if not re.match("^[ A-Za-z0-9()\._\-]$", char):
                score += 1
        return math.ceil(100 * score / len(string))

    def process_strings(self):
        self.info_by_string = {}
        flossed_strings = []
        if self.use_query_service:
            # check all strings at once
            all_strings = set([])
            for string_item in self.api_proxy.Strings():
                string_offset, string_type, plain_string = string_item
                all_strings.add(plain_string)
            filtered_strings = filter_strings(all_strings)
            if len(filtered_strings) < len(all_strings):
                print(f"Filtered strings from {len(all_strings)} to {len(filtered_strings)}.")
            print(f"Performing lookup for {len(filtered_strings)} strings...")
            if any([s for s in filtered_strings if ("\n" in s or "\r" in s)]):
                print("contains evil chars")
            if len(filtered_strings) == 0:
                print("It seems we have not found any queriable strings, so we have to abort.")
                return flossed_strings
            response = requests.post(FLOSSED_SERVICE, data=csv_encode(filtered_strings))
            if response.status_code == 200:
                for entry in response.json()["data"]:
                    self.info_by_string[entry["string"]] = entry if entry["matched"] else {}
            else:
                print(f"No results, server returned status code: {response.status_code}.")
        else:
            for string_item in self.api_proxy.Strings():
                string_offset, string_type, plain_string = string_item
                if filter_string(plain_string):
                    self.info_by_string[plain_string] = self.get_local_string_info(plain_string)
        # run a second time over strings and format consistenly
        for string_item in self.api_proxy.Strings():
            string_offset, string_type, plain_string = string_item
            string_score = self.get_string_score(plain_string)
            trash_score = self.get_trash_score(plain_string)
            flossed_strings.append((
                string_offset, 
                string_type, 
                plain_string, 
                self.info_by_string[plain_string] if plain_string in self.info_by_string else {}, 
                plain_string in self.info_by_string, 
                string_score,
                trash_score
            ))
        return flossed_strings

    def update_table(self, flossed_strings):
        self.table_flossed_strings.setSortingEnabled(False)
        self.local_function_header_labels = ["Offset", "Type", "String", "Families", "Score", "Tags"]
        if self.cb_filter_trash.isChecked():
            self.local_function_header_labels = ["Offset", "Type", "String", "Families", "Score", "Tags", "Trash Score"]
        self.table_flossed_strings.clear()
        self.table_flossed_strings.setColumnCount(len(self.local_function_header_labels))
        self.table_flossed_strings.setHorizontalHeaderLabels(self.local_function_header_labels)
        # Identify number of table entries and prepare addresses to display
        self.table_flossed_strings.setRowCount(len(flossed_strings))
        self.table_flossed_strings.resizeRowToContents(0)
        row = 0
        for flossed_string in sorted(flossed_strings, key=lambda x: (x[5], len(x[2])), reverse=True):
            for column, column_name in enumerate(self.local_function_header_labels):
                tmp_item = None
                if column == 0:
                    tmp_item = QtWidgets.QTableWidgetItem("0x%x" % flossed_string[0])
                elif column == 1:
                    tmp_item = QtWidgets.QTableWidgetItem(flossed_string[1])
                elif column == 2:
                    tmp_item = QtWidgets.QTableWidgetItem(flossed_string[2])
                elif column == 3:
                    tmp_item = NumberQTableWidgetItem("%d" % (flossed_string[3]["family_count"] if flossed_string[3] else 0))
                elif column == 4:
                    tmp_item = NumberQTableWidgetItem("%5.2f" % flossed_string[5])
                elif column == 5:
                    tmp_item = QtWidgets.QTableWidgetItem(",".join(sorted(flossed_string[3]["tags"])) if (flossed_string[3] and "tags" in flossed_string[3]) else "")
                elif column == 6:
                    tmp_item = NumberQTableWidgetItem("%5.2f" % flossed_string[6])
                tmp_item.setFlags(tmp_item.flags() & ~QtCore.Qt.ItemIsEditable)
                tmp_item.setTextAlignment(QtCore.Qt.AlignHCenter)
                tmp_item.setForeground(QtGui.QBrush(QtGui.QColor(0x10, 0x10, 0x10)))
                self.table_flossed_strings.setItem(row, column, tmp_item)
                # colorize cell
                self.table_flossed_strings.item(row, column).setBackground(get_color_for_string(flossed_string))
            self.table_flossed_strings.resizeRowToContents(row)
            row += 1
        
        self.table_flossed_strings.resizeColumnsToContents()
        self.table_flossed_strings.resizeRowsToContents()
        self.table_flossed_strings.setSortingEnabled(True)
        # self.table_flossed_strings.setColumnWidth(2, 600)
        header = self.table_flossed_strings.horizontalHeader()
        for header_id in range(0, len(self.local_function_header_labels), 1):
            try:
                header.setSectionResizeMode(header_id, QtWidgets.QHeaderView.Interactive)
                if header_id == 2:
                    header.setSectionResizeMode(header_id, QtWidgets.QHeaderView.Stretch)
                    header.setMaximumSectionSize(600)
            except:
                header.setResizeMode(header_id, QtWidgets.QHeaderView.Stretch)

    def _onTableDoubleClicked(self, mi):
        """
        Use the row with that was double clicked to import the function_name to the current function
        """
        column_id = int(mi.column())
        row_id = mi.row()
        if column_id == 0:
            clicked_address = self.table_flossed_strings.item(row_id, 0).text()
            # print("double clicked_block_address", clicked_block_address)
            self.api_proxy.jump_to(int(clicked_address, 16))
        if column_id > 0:
            clicked_string = self.table_flossed_strings.item(row_id, 2).text()
            if clicked_string in self.info_by_string and self.info_by_string[clicked_string]:
                string_info = self.info_by_string[clicked_string]
                tag_string = ', '.join(sorted(string_info['tags'])) if "tags" in string_info else ""
                print(f"Info: '{string_info['string']}' - tags: [{tag_string}] - families ({string_info['family_count']}):  [{', '.join(sorted(string_info['families']))}]")
            else:
                print("Info: not available.")
    