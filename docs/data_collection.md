# Data collection

Python search optionally can collect the data you create.
This data can then be later used to customize your ranking.

To enable it, you need to enable it in your PythonSearchConfiguration:

```py
configuration = PythonSearchConfig(...collect_data=False)
```

Your data can then be found inside:

```
 $HOME/.python_search/data/
 ```
