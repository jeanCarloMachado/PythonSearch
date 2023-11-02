class Theme:
    """
       fg                  Text
         preview-fg        Preview window text
       bg                  Background
         preview-bg        Preview window background
       hl                  Highlighted substrings
       fg+                 Text (current line)
       bg+                 Background (current line)
         gutter            Gutter on the left
       hl+                 Highlighted substrings (current line)
       query               Query string
         disabled          Query string when search is disabled (--disabled)
       info                Info line (match counters)
       border              Border around the window (--border and --preview)
         scrollbar         Scrollbar
         preview-border    Border around the preview window (--preview)
         preview-scrollbar Scrollbar
         separator         Horizontal separator on info line
       label               Border label (--border-label and --preview-label)
         preview-label     Border label of the preview window (--preview-label)
       prompt              Prompt
       pointer             Pointer to the current line
       marker              Multi-select marker
       spinner             Streaming input indicator
       header              Header
    """
    fg: str
    bg: str
    hl: str
    fg_plus: str
    bg_plus: str
    hl_plus: str
    info: str
    prompt_arrows: str
    # the pointer of hte current line
    pointer_current_line: str
    marker: str
    spinner: str
    header: str
    query: str

    def solarized(self):
        self.name = 'solarized'
        self.fg = "#2aa198"
        lighter_blue = "#073642"
        self.bg = "#002b36"
        self.hl = "#b58900"
        self.fg_plus = "#6c71c4"
        self.bg_plus = lighter_blue
        self.hl_plus = "#268bd2"
        self.info = "#d33682"
        self.prompt_arrows = lighter_blue

        self.pointer_current_line = "#6c71c4"
        self.marker = "#268bd2"
        self.spinner = "#2aa198"
        self.header = "#268bd2"
        self.query = "#cb4b16"
        self.label = self.bg
        self.border = "#073642"

        return self

    def light(self):

        self.name = 'light'
        self.fg = "#383838"  # Soft Black (Primary text)
        self.bg = "#FAFAFA"  # Almost White Background
        self.hl = "#D3BAA4"  # Muted Taupe (Highlight) - Neutral, yet distinct

        self.fg_plus = "#606060"  # Darker Gray (Secondary text)
        self.bg_plus = "#E0E0E0"  # Light Gray
        self.hl_plus = "#A9CCE3"  # Soft Light Blue (Highlight Plus)

        self.info = "#5687A5"  # Deep Sky Blue
        self.prompt_arrows = "#89A478"  # Muted Olive Green

        self.pointer_current_line = "#D38250"  # Burnt Sienna - Deeper shade for better contrast
        self.marker = "#D47F70"  # Muted Coral
        self.spinner = "#4A8AB0"  # Steel Blue
        self.header = "#8C8EB3"  # Muted Lavender
        self.query = "#5A6D7E"  # Blue Gray
        self.label = "#C2C2C2"  # Lighter Gray
        self.border = "#FAFAFA"  # Medium Gray for borders
        self.cyan = "#8C8EB3"
        self.green = "#5687A5"
        self.red = "#D47F70"

        return self
