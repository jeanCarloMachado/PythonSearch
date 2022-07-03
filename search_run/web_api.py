from fastapi import FastAPI
from fastapi.responses import PlainTextResponse


app = FastAPI()
from search_run.ranking.ranking import RankingGenerator
from search_run.config import ConfigurationLoader

config = ConfigurationLoader().load()
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


if __name__ == "__main__":
    import uvicorn
    import os
    os.putenv('WEB_CONCURRENCY', '1')
    uvicorn.run("web_api:app", host="0.0.0.0", port=8000)