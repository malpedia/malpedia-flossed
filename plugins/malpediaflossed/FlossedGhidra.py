# Check strings against MalpediaFLOSSed
# @author Daniel Plohmann (daniel.plohmann@fkie.fraunhofer.de)
# @category Python 3

from plugin.apis.GhidraApi import GhidraApi
from plugin.gui.PluginGui import PluginGui

import sys
try:
    import PySide2.QtWidgets as QtWidgets
except:
    import PySide6.QtWidgets as QtWidgets

class PluginWidget(QtWidgets.QWidget):
    def __init__(self):
        QtWidgets.QWidget.__init__(self)

        self.api_proxy = GhidraApi()
        self.plugin_gui = PluginGui(self.api_proxy)
        self.setLayout(self.plugin_gui.layout)

def run():
    if not QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication(sys.argv)
    else:
        app = QtWidgets.QApplication.instance()

    window = PluginWidget()
    window.show()
    app.exec()

if __name__ == "__main__":
    run()

