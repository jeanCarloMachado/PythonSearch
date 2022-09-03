"""
run it like this:

"""
import wx.adv

from python_search.infrastructure.infrastructure import Infrastructure

TRAY_TOOLTIP = "Tray Demo"
TRAY_ICON = "icon.svg.png"


class TaskBarIcon(wx.adv.TaskBarIcon):
    def __init__(self, frame):
        self.frame = frame

        super(TaskBarIcon, self).__init__()
        icon = wx.Icon(wx.Bitmap(TRAY_ICON, wx.BITMAP_TYPE_ANY))

        self.SetIcon(icon, TRAY_TOOLTIP)
        self.Bind(wx.adv.EVT_TASKBAR_LEFT_DOWN, self.on_left_down)

        self.infra = Infrastructure()
        self.infra.all()

    def CreatePopupMenu(self):
        menu = wx.Menu()
        self.create_menu_item(menu, "Data UI", self.data_ui)
        self.create_menu_item(menu, "Infra Status", self.infra_status)
        self.create_menu_item(menu, "Webservice", self.web_api)
        self.create_menu_item(menu, "Redis consumer", self.latest_redis_consumer)
        self.create_menu_item(menu, "Kafka", self.kafka)
        self.create_menu_item(menu, "Redis", self.redis)
        self.create_menu_item(menu, "Zookeeper", self.zookeeper)
        menu.AppendSeparator()
        self.create_menu_item(menu, "Exit", self.on_exit)
        return menu

    def create_menu_item(self, menu, label, func):
        item = wx.MenuItem(menu, -1, label)
        menu.Bind(wx.EVT_MENU, func, id=item.GetId())
        menu.AppendItem(item)
        return item

    def set_icon(self, path):
        icon = wx.Icon(wx.Bitmap(path))
        self.SetIcon(icon, TRAY_TOOLTIP)

    def on_left_down(self, event):
        print("Tray icon was left-clicked.")

    def data_ui(self, event):
        from subprocess import Popen

        Popen(
            'python_search run_key "pythonsearch entries app ui run new evaluator streamlit main"',
            shell=True,
            stdin=None,
            stdout=None,
            stderr=None,
            close_fds=True,
        )

    def infra_status(self, event):
        self.infra.status_window()

    def web_api(self, event):
        self.infra.run_service("web_api")

    def latest_redis_consumer(self, event):
        self.infra.run_service("latest_redis_consumer")

    def kafka(self, event):
        self.infra.run_service("kafka")

    def zookeeper(self, event):
        self.infra.run_service("zookeeper")

    def redis(self, event):
        self.infra.run_service("redis")

    def on_exit(self, event):
        wx.CallAfter(self.Destroy)
        self.frame.Close()


class App(wx.App):
    def OnInit(self):
        frame = wx.Frame(None)
        self.SetTopWindow(frame)
        TaskBarIcon(frame)
        return True


def main():
    app = App(False)
    app.MainLoop()


if __name__ == "__main__":
    main()
