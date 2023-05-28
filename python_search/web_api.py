from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from python_search.entry_type.classifier_inference import (
    EntryData,
    PredictEntryTypeInference,
)
from python_search.events.latest_used_entries import RecentKeys
from python_search.events.run_performed import EntryExecuted
from python_search.events.run_performed.writer import RunPerformedWriter
from python_search.configuration.loader import ConfigurationLoader
from python_search.search.search import Search

import pyroscope

pyroscope.configure(
    application_name="my.python.app",  # replace this with some name for your application
    server_address="http://host.docker.internal:4040",  # replace this with the address of your pyroscope server
    sample_rate=1,  # default is 100
)
PORT = 8000

app = FastAPI()

search = Search(ConfigurationLoader().load_config())
results = search.search()
entry_type_inference = PredictEntryTypeInference()


def reload_ranking():
    global search
    global results
    results = Search(ConfigurationLoader().reload()).search()
    return results


@app.get("/ranking/generate", response_class=PlainTextResponse)
def generate_ranking(skip_model: bool = False, base_rank=False, get_latest=True):
    global results
    if get_latest and not base_rank:
        return results
    print("Skip model api level: ", skip_model)
    results = search.search(skip_model=skip_model, base_rank=base_rank)
    return results


@app.get("/ranking/reload", response_class=PlainTextResponse)
def reload():
    reload_ranking()


@app.get("/ranking/reload_and_generate", response_class=PlainTextResponse)
def reload_and_generate():
    return reload_ranking()


@app.get("/_health")
def health():
    global search

    from python_search.events.latest_used_entries import RecentKeys

    entries = RecentKeys().get_latest_used_keys()

    return {
        "keys_count": len(ConfigurationLoader().load_config().commands.keys()),
        "latest_used_entries": entries,
        "initialization_time": ConfigurationLoader().load_config()._initialization_time,
    }


@app.post("/log_run")
def log_run(event: EntryExecuted):
    RecentKeys.add_latest_used(event.key)
    RunPerformedWriter().write(event)
    # regenerate the search after running a key
    reload()

    return event


@app.post("/entry_type/classify")
def predict_entry_type_endpoint(entry: EntryData):
    type, uuid = entry_type_inference.predict_entry_type(entry)
    return {"predicted_type": type, "prediction_uuid": uuid}



@app.get("/recent_history")
def recent_history_endpoint():
    return {"history": RecentKeys().get_latest_used_keys()}


def main():
    import os

    import uvicorn

    os.putenv("WEB_CONCURRENCY", "0")
    reload = False
    if "PS_DEBUG" in os.environ:
        print("Debug mode is ON, enabling reload")
        reload = True
    else:
        print("Debug mode is OFF")

    uvicorn.run("python_search.web_api:app", host="0.0.0.0", port=PORT, reload=reload)


if __name__ == "__main__":
    main()
