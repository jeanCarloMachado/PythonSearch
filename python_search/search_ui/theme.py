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
    foreground: str
    background: str
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
    prompt_query: str

    def inclusivity(self):

        self.name = 'inclusivity'
        # Base Colors
        self.background = "#F8F4F1"  # Creamy pastel base for a soft, neutral background
        self.foreground = "#ACA092"  # Almost black for the primary text to ensure contrast

        self.hl = "#6F8B9D"
        self.hl_plus = "#6F8B9D"  # A muted taupe for differentiation
        self.fg_plus = "#565B64"  # A soft charcoal for secondary text elements
        self.bg_plus = "#E9E4E1"  # A hue that's between the primary background and highlight

        # Auxiliary colors for better visibility
        self.info = "#81A1C1"  # Subdued cerulean, a hint of sophisticated blue
        self.prompt_arrows = "#D19B86"  # Pastel terracotta for a hint of earthiness
        self.pointer_current_line = "#ECD8C6"  # A light apricot shade
        self.marker = "#F28F77"  # Pastel coral, striking yet soft
        self.spinner = "#8A98A6"  # Muted steel blue
        self.header = "#949AAD"  # Subdued periwinkle for distinction
        self.prompt_query = "#3E434A"  # A dark gray, ensuring text elements pop
        self.label = "#6B6E78"  # Medium gray to differentiate from other text
        self.border = self.background # Muted taupe, again for consistent differentiation

        # Adjusted colors for "key," "value," and "type"
        self.key = "#D1A8A1"  # Muted rose, soft yet distinguishable
        self.value = "#6F8B9D"  # Pastel slate blue, offering contrast against the creamy background
        self.type = "#F4AA5F"  # Soft tangerine to break the monotony and bring warmth

        return self

    def solarized(self):
        self.name = 'solarized'

        # Base Solarized Dark Colors
        base03 = "#002b36"
        base02 = "#073642"
        base01 = "#586e75"
        base00 = "#657b83"
        base0 = "#839496"
        base1 = "#93a1a1"
        base2 = "#eee8d5"
        base3 = "#fdf6e3"
        yellow = "#b58900"
        orange = "#cb4b16"
        red = "#dc322f"
        magenta = "#d33682"
        violet = "#6c71c4"
        blue = "#268bd2"
        cyan = "#2aa198"
        green = "#859900"

        # Refactored Variables
        self.foreground = cyan
        lighter_blue = base02
        self.background = base03
        self.hl = yellow
        self.fg_plus = violet
        self.bg_plus = lighter_blue
        self.hl_plus = blue
        self.info = magenta
        self.prompt_arrows = lighter_blue

        self.pointer_current_line = violet
        self.marker = blue
        self.spinner = cyan
        self.header = blue
        self.prompt_query = orange
        self.key = orange
        self.label = self.background
        self.value = cyan
        self.border = base02
        self.type = red

        return self



