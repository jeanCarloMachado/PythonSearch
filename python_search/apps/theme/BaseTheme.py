class BaseTheme:
    colors = None

    def get_colorful(self):
        import colorful as cf

        cf.update_palette(self.colors)
        return cf

    def __init__(self):
        self.backgroud = self.colors["backgroud"]
        self.text = self.colors["text"]

        self.font_size = 19
        self.font = "SF Pro"