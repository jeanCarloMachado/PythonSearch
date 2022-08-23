from fastapi import FastAPI
from fastapi.responses import PlainTextResponse

app = FastAPI()
from python_search.config import ConfigurationLoader
from python_search.ranking.ranking import RankingGenerator

config = ConfigurationLoader().load_config()
generator = RankingGenerator(config)


@app.get("/ranking/reload_and_generate", response_class=PlainTextResponse)
def reload():
    global generator
    config = ConfigurationLoader().reload()
    generator = RankingGenerator(config)
    return generator.generate()


@app.get("/ranking/generate", response_class=PlainTextResponse)
def generate_ranking():
    global generator
    return generator.generate()


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

    uvicorn.run("python_search.web_api:app", host="0.0.0.0", port=8000, reload=reload)


if __name__ == "__main__":
    main()
