import json
import requests
from bs4 import BeautifulSoup
from typing import List


class TagsNotFound(Exception):
    pass


class API:
    TAGS_URL: str = "https://atcoder-tags.herokuapp.com/check/"
    SUBMISSIONS_URL: str = "https://kenkoooo.com/atcoder/atcoder-api/results"

    def __init__(self):
        pass

    def get_tags(self, problem_id: str) -> List[str]:
        r = requests.get(self.TAGS_URL + problem_id)
        if not r.ok:
            raise TagsNotFound

        soup = BeautifulSoup(r.text, 'html.parser')

        tags = []
        try:
            tags = [soup.find(id=f'tag{i}').text for i in range(4)]
            tags = [t for t in tags if t != "None"]
            if len(tags) == 0:
                raise TagsNotFound
        except Exception:
            raise TagsNotFound
        return tags

    def get_submissions(self, user_id: str, limit=None):
        r = requests.get(self.SUBMISSIONS_URL, {"user": user_id})
        submissions = r.json()
        if limit is not None:
            submissions = submissions[:limit]
        return submissions

    def get_enriched_submissions(self, user_id: str, limit=10):
        submissions = self.get_submissions(user_id, limit)
        tags = {}
        for submission in submissions:
            problem_id = submission["problem_id"]
            if problem_id not in tags:
                try:
                    tags[problem_id] = self.get_tags(problem_id)
                except TagsNotFound:
                    tags[problem_id] = []
                submission["tags"] = tags[problem_id]
        return submissions

    def cache_enriched_submissions(self, user_id: str) -> str:
        submissions = self.get_enriched_submissions(user_id, None)
        with open(f"{user_id}.json", "w", encoding='utf-8') as f:
            json.dump(submissions, f, ensure_ascii=False, indent=4)
        return f"{user_id}.json"
