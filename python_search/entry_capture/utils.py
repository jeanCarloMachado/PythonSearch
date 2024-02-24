def get_page_title(url):
    from bs4 import BeautifulSoup
    import requests

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.title.string
    except Exception:
        return ""


if __name__ == "__main__":
    import fire

    fire.Fire()
