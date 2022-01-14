import json

from search_run.core_entities import Ranking


class ReadProjection:
    def create(ranking: Ranking, extra: dict = None) -> str:
        """ Froma  list of entries returns a string that is optimized for reading in fzf"""
        fzf_lines = ""
        position = 1
        for entry in ranking.entries:
            content = entry.value
            try:
                content["key_name"] = entry.name
                content["rank_position"] = position
                if extra:
                    content["extra"] = extra

                content_str = json.dumps(content, default=tuple, ensure_ascii=True)
            except BaseException:
                content_str = str(content)

            position = position + 1
            fzf_lines += f"{entry.name.lower()}: " + content_str + "\n"

        fzf_lines = fzf_lines.replace("\\", "\\\\")
        return fzf_lines
