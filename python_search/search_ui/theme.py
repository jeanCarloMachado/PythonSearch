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
        self.key= "#2aa198"
        self.label = self.bg
        self.value = '#2aa198'
        self.border = "#073642"
        self.type= "#dc322f"

        return self


    def inclusivity(self):
        self.name = 'inclusivity'

        self.bg = "#F3F4F6"  # Soft grayish-white, a neutral background
        self.fg = "#373B3F"  # Darker charcoal, for primary text

        # Highlight and Secondary colors
        self.hl = "#CCD0D6"  # A more defined gray-blue for highlighting
        self.hl_plus = "#B2B8BE"  # An even deeper shade for differentiation
        self.fg_plus = "#646A70"  # Darkened gray for secondary text
        self.bg_plus = "#E1E3E6"  # Adjusted background for UI elements

        # Auxiliary colors for better visibility
        self.info = "#6A7F9B"  # Darker blue for clarity
        self.prompt_arrows = "#7F9A88"  # Adjusted sage green
        self.pointer_current_line = "#FFDCAA"  # A more noticeable beige
        self.marker = "#FF9F87"  # Brightened coral for better visibility
        self.spinner = "#8E89C7"  # Darkened lilac
        self.header = "#949BAD"  # More defined blue-gray
        self.query = "#3C4145"  # Darkened to improve visibility
        self.label = "#575C61"  # Darker gray for clarity
        self.border = "#C8CCD1"  # Darkened border for structure

        # Adjusted colors for "key," "value," and "type" for better readability
        self.key = "#A57680"  # Further deepened blush
        self.value = "#637A90"  # More defined blue
        self.type = "#FF8E58"  # A clearer shade of apricot

        return self


