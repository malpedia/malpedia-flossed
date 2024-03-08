IS_BINJA_ENV = False
try:
    from binaryninjaui import DockHandler, DockContextHandler, UIActionHandler
    IS_BINJA_ENV = True
except:
    pass

if IS_BINJA_ENV:
    # TODO adjust this to your plugin name
    from malpediaflossed.plugin.apis.BinaryNinjaApi import BinaryNinjaApi
    from malpediaflossed.plugin.gui.PluginGui import PluginGui
    import malpediaflossed.config as config

    from binaryninjaui import DockHandler, DockContextHandler, UIActionHandler
    import PySide6.QtWidgets as QtWidgets
    from PySide6.QtCore import Qt


class PluginDockWidget(QtWidgets.QWidget, DockContextHandler):
    def __init__(self, parent, name, data):
        QtWidgets.QWidget.__init__(self, parent)
        DockContextHandler.__init__(self, self, name)

        self.actionHandler = UIActionHandler()
        self.actionHandler.setupActionHandler(self)

        self.api_proxy = BinaryNinjaApi()
        self.plugin_gui = PluginGui(self.api_proxy, config)

        self.setLayout(self.plugin_gui.layout)

    def shouldBeVisible(self, view_frame):
        if view_frame is None:
            return False
        else:
            return True

    def notifyViewChanged(self, view_frame):
        pass

    @staticmethod
    def create_widget(name, parent, data=None):
        return PluginDockWidget(parent, name, data)


if IS_BINJA_ENV:
    dock_handler = DockHandler.getActiveDockHandler()
    dock_handler.addDockWidget(
        "MalpediaFlossed",
        PluginDockWidget.create_widget,
        Qt.RightDockWidgetArea,
        Qt.Horizontal,
        False,
    )
