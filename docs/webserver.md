
# Web UI

Python Search comes with a stream lit based interface with much richer options than the standard desktop application.

### Running the Web UI

```bash
PS_DISABLE_PASSWORD=True streamlit run python_search/web_ui/main.py
```
Then access the web UI at http://localhost:8501

## The API


The webservice is FastAPI system for smart ranking of search queries.
It is by default disabled, but can be enabled by running the docker container.
Once enabled, the webservice will log all calls and store them in disk.
This data is then used to inform the reranking model.

To run the webservice, the following steps must be followed:

1. Build the docker container: "ps_container build"
2. Run the webservice: "ps_container run_webserver"

Once the webservice is running, it will log all calls and store them in disk. This data will then be used to inform the reranking model. The webservice can be disabled by running the command "ps_container stop_webserver".
