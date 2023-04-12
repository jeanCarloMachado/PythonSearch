
# Customizing Python Search

The customization is done by customizing your instance of the PythonSearchConfiguration class.
In your entries_main.py

```py
from python_search.configuration.configuration import PythonSearchConfiguration
configuration = PythonSearchConfiguration(
    custom_pysimple_gui_theme="DarkAmber",
)
```



# Adding new customizations in python search

If you need to change the code of python search to add a new customization you do the folling:

1. Add the new customization as options in the PythonSearchConfiguration class.


2. In the code where you need the new option, get the configuration as showned below and use it.


```py
from python_search.configuration.loader import ConfigurationLoader
 configuration = ConfigurationLoader().load_config()
```
