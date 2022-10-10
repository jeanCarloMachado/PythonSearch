from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

from python_search.data_collector import GenericDataCollector
from python_search.events.events import SearchRunPerformed

PORT = 8000

app = FastAPI()
from python_search.config import ConfigurationLoader
from python_search.ranking.ranking import RankingGenerator

generator = RankingGenerator(ConfigurationLoader().load_config())
ranking_result = generator.generate()


def reload_ranking():
    global generator
    global ranking_result
    generator = RankingGenerator(ConfigurationLoader().reload())
    ranking_result = generator.generate()
    return ranking_result


@app.get("/ranking/generate", response_class=PlainTextResponse)
def generate_ranking():
    global ranking_result
    return ranking_result


@app.get("/ranking/reload", response_class=PlainTextResponse)
def reload():
    reload_ranking()


@app.get("/ranking/reload_and_generate", response_class=PlainTextResponse)
def reload():
    return reload_ranking()


@app.get("/_health")
def health():
    global generator

    from python_search.events.latest_used_entries import LatestUsedEntries

    entries = LatestUsedEntries().get_latest_used_keys()

    return {
        "keys_count": len(ConfigurationLoader().load_config().commands.keys()),
        "run_id": generator.inference.PRODUCTION_RUN_ID,
        "latest_used_entries": entries,
    }

recent_history = []

@app.post("/log_run")
def log_run(event: SearchRunPerformed):
    global recent_history

    recent_history = [event.key] + recent_history
    GenericDataCollector().write(data=event.__dict__, table_name='searches_performed')

    # regenerate the ranking after running a key
    reload()

    return event

@app.get("/recent_history")
def recent_history_endpoint():
    global recent_history
    return recent_history


def main():
    import os

    import uvicorn

    os.putenv("WEB_CONCURRENCY", "1")
    reload = False
    if "PS_DEBUG" in os.environ:
        print("Debug mode is ON, enabling reload")
        reload = True
    else:
        print("Debug mode is OFF")

    uvicorn.run("python_search.web_api:app", host="0.0.0.0", port=PORT, reload=reload)


if __name__ == "__main__":
    main()
