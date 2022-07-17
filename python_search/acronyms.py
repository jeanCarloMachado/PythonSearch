from typing import List


def generate_acronyms(name: str) -> List[str]:
    return [generate_acronym(name)]


def generate_acronym(name: str) -> str:
    words = name.split(" ")
    acronyms = [word[0] for word in words]
    return "".join(acronyms)
