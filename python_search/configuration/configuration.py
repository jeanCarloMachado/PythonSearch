import datetime
from typing import Optional, List, Tuple, Literal

from python_search.entries_group import EntriesGroup
from python_search.features import PythonSearchFeaturesSupport


class PythonSearchConfiguration(EntriesGroup):
    """
    The main _configuration of Python Search
    Everything to customize about the application is configurable via code through this class
    """

    APPLICATION_TITLE = "PythonSearchWindow"
    commands: dict
    simple_gui_theme = "SystemDefault1"
    simple_gui_font_size = 14
    _default_tags = None
    tags_dependent_inserter_marks = None
    _initialization_time = None
    _default_text_editor = "vim"
    _default_fzf_theme = None


    def __init__(
        self,
        *,
        entries: Optional[dict] = None,
        entries_groups: Optional[List[EntriesGroup]] = None,
        supported_features: Optional[PythonSearchFeaturesSupport] = None,
        default_tags=None,
        tags_dependent_inserter_marks: Optional[dict[str, Tuple[str, str]]] = None,
        default_text_editor: Optional[str] = None,
        default_fzf_theme: Optional[Literal["light"]] = None,
        custom_window_size: Optional[Tuple[int, int]] = None,
    ):
        """

        :param entries:
        :param entries_groups:
        :param supported_features:
        :param default_tags:
        :param tags_dependent_inserter_marks:
        :param default_text_editor:
        :param default_fzf_theme: the theme to use for fzf
        :param custom_window_size: the size of the fzf window
        """
        if entries:
            self.commands = entries

        if entries_groups:
            self.aggregate_commands(entries_groups)

        if supported_features:
            self.supported_features: PythonSearchFeaturesSupport = supported_features
        else:
            self.supported_features: PythonSearchFeaturesSupport = (
                PythonSearchFeaturesSupport.default()
            )

        if default_tags:
            self._default_tags = default_tags

        self.tags_dependent_inserter_marks = tags_dependent_inserter_marks

        self._initialization_time = datetime.datetime.now()
        self._default_text_editor = default_text_editor
        self._default_fzf_theme = default_fzf_theme
        if custom_window_size:
            self._custom_window_size = custom_window_size



    def get_text_editor(self):
        return self._default_text_editor

    def get_default_tags(self):
        return self._default_tags

    def get_fzf_theme(self):
        return self._default_fzf_theme

    def get_window_size(self):
        if hasattr(self, "_custom_window_size"):
            return self._custom_window_size