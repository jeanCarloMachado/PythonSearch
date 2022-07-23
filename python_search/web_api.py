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
def root():
    global generator
    return generator.generate()


@app.get("/about")
def root():
    global generator
    return {"run_id": generator.inference.PRODUCTION_RUN_ID}


def main():
    import os

    import uvicorn

    os.putenv("WEB_CONCURRENCY", "1")
    uvicorn.run("python_search.web_api:app", host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
