from apis.CutterApi import CutterApi
from gui.PluginGui import PluginGui

import PySide2.QtWidgets as QtWidgets
import cutter


class PluginWidget(cutter.CutterDockWidget):
    def __init__(self, parent):
        super(PluginWidget, self).__init__(parent)
        self.main = parent
        self.setObjectName("MalpediaFlossed")
        self.setWindowTitle("MalpediaFlossed")

        self.api_proxy = CutterApi()
        self.plugin_gui = PluginGui(self.api_proxy)
        content = QtWidgets.QWidget()
        self.setWidget(content)
        content.setLayout(self.plugin_gui.layout)


class HyaraPlugin(cutter.CutterPlugin):
    name = "MalpediaFlossed"
    description = "This plugin matches strings in the given target binary with data from malpedia-flossed.json"
    version = "1.0"
    author = "Daniel Plohmann"
    plugin_widget = None

    def setupPlugin(self):
        pass

    def nop(self):
        return

    def setupActions(self):
        self.dummyAction = QtWidgets.QAction("Dummy Action")

        # context menu extensions / actions need to be registered here
        menu = self.plugin_widget.main.getContextMenuExtensions(
            cutter.MainWindow.ContextMenuType.Disassembly
        )
        menu.addSeparator()
        menu.addAction(self.dummyAction)
        self.startAddrAction.triggered.connect(self.nop)

    def setupInterface(self, main):
        self.plugin_widget = PluginWidget(main)
        self.setupActions()
        main.addPluginDockWidget(self.plugin_widget)

    def terminate(self):
        pass
