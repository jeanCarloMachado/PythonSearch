import datetime
import os
from typing import Optional, List, Tuple, Literal

from python_search.entries_group import EntriesGroup
from python_search.features import PythonSearchFeaturesSupport


class PythonSearchConfiguration(EntriesGroup):
    """
    The main configuration of Python Search
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
    _fzf_theme = None
    use_webservice = False
    _rerank_via_model_enabled = None
    entry_generation = False
    privacy_sensitive_terms = None

    def __init__(
        self,
        *,
        entries: Optional[dict] = None,
        entries_groups: Optional[List[EntriesGroup]] = None,
        default_tags=None,
        tags_dependent_inserter_marks: Optional[dict[str, Tuple[str, str]]] = None,
        default_text_editor: Optional[str] = None,
        fzf_theme: Literal["light", "solarized"] = "light",
        custom_window_size: Optional[Tuple[int, int]] = None,
        use_webservice=False,
        rerank_via_model=None,
        collect_data: bool = False,
        entry_generation=False,
        privacy_sensitive_terms: Optional[List[str]] = None,
    ):
        """

        :param entries:
        :param entries_groups:
        :param default_tags:
        :param tags_dependent_inserter_marks:
        :param default_text_editor:
        :param fzf_theme: the theme to use for fzf
        :param custom_window_size: the size of the fzf window
        :param use_webservice: if True, the ranking will be generated via a webservice
        :param collect_data: if True, we will collect data about the entries you run in your machine
        """
        if entries:
            self.commands = entries

        if entries_groups:
            self.aggregate_commands(entries_groups)

        self.supported_features: PythonSearchFeaturesSupport = (
            PythonSearchFeaturesSupport.default()
        )

        if default_tags:
            self._default_tags = default_tags

        self.tags_dependent_inserter_marks = tags_dependent_inserter_marks

        self._rerank_via_model_enabled = rerank_via_model

        self._initialization_time = datetime.datetime.now()
        self._default_text_editor = default_text_editor
        self._fzf_theme = fzf_theme
        if custom_window_size:
            self._custom_window_size = custom_window_size

        self.use_webservice = use_webservice
        self.collect_data = collect_data
        self.entry_generation = entry_generation
        self.privacy_sensitive_terms = privacy_sensitive_terms

    def get_text_editor(self):
        return self._default_text_editor

    def is_rerank_via_model_enabled(self):
        home = os.path.expanduser("~")

        if self._rerank_via_model_enabled is False:
            return False

        if os.path.exists(f"{home}/.python_search/feature_enable_next_item_predictor"):
            return True

        return self._rerank_via_model_enabled

    def get_default_tags(self):
        return self._default_tags

    def get_fzf_theme(self) -> str:
        return self._fzf_theme

    def get_window_size(self):
        if hasattr(self, "_custom_window_size"):
            return self._custom_window_size
