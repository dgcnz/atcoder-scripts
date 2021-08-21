from ratelimit import sleep_and_retry
from ratelimit import limits
from bs4 import BeautifulSoup
from typing import List
from tqdm import tqdm
import requests
import itertools
import time
import json


class TagsNotFound(Exception):
    pass


class ProblemCacheOutOfDate(Exception):
    pass


class KenkooApiError(Exception):
    pass


def chunks(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]


class TagsAPI:
    TAGS_URL: str = "https://atcoder-tags.herokuapp.com/check/"
    PROBLEMS_URL: str = "https://kenkoooo.com/atcoder/resources/problems.json"
    MERGED_PROBLEMS_URL: str = "https://kenkoooo.com/atcoder/resources/merged-problems.json"
    PROBLEM_MODELS_URL: str = "https://kenkoooo.com/atcoder/resources/problem-models.json"
    tags = dict()
    problems = dict()
    problem_ids = []

    def __init__(self, problems_path: str, tags_path: str):
        self.problems_path = problems_path
        self.tags_path = tags_path
        with open(self.tags_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if len(content) > 0:
                self.tags = {
                    problem['id']: problem['tags']
                    for problem in json.loads(content)
                }
        with open(self.problems_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.problems = json.loads(content) if len(content) > 0 else []
            self.problem_ids = [problem['id'] for problem in self.problems]

    def commit(self):
        # TODO: only commit if changes are done
        with open(self.tags_path, 'w', encoding='utf-8') as f:
            json.dump([{
                'id': problem_id,
                'tags': problem_tags
            } for problem_id, problem_tags in self.tags.items()],
                      f,
                      ensure_ascii=False,
                      indent=4)
        with open(self.problems_path, 'w', encoding='utf-8') as f:
            json.dump(self.problems, f, ensure_ascii=False, indent=4)

    @sleep_and_retry
    @limits(calls=1, period=60)
    def update_problems(self) -> None:
        r = requests.get(self.PROBLEMS_URL)
        if not r.ok:
            raise KenkooApiError
        self.problems = r.json()
        self.problem_ids = [problem['id'] for problem in self.problems]

    def update_all_tags(self, chunk_size=100, chunk_index=0) -> None:
        # TODO check if chunk_index fits in range
        t = tqdm(chunks(self.problem_ids, chunk_size)[chunk_index:],
                 desc='Overall progress')
        for chunk in t:
            t.set_description('Updating Chunk')
            self.update_tags(chunk)
            t.set_description('Saving Chunk')
            self.commit()
            t.set_description('Saved')

    def update_tags(self, problem_ids: List[str]) -> None:
        t = tqdm(problem_ids)
        for problem_id in t:
            t.set_description(desc=f'Updating {problem_id}')
            if problem_id not in problem_ids:
                raise ProblemCacheOutOfDate
            problem_tags = []
            try:
                problem_tags = self.crawl_tag(problem_id)
            except TagsNotFound:
                pass
            self.tags[problem_id] = problem_tags

    @sleep_and_retry
    @limits(calls=2, period=1)
    def crawl_tag(self, problem_id: str) -> List[str]:
        r = requests.get(self.TAGS_URL + problem_id)
        if not r.ok:
            raise TagsNotFound
        soup = BeautifulSoup(r.text, 'html.parser')
        html_tags = [soup.find(id=f'tag{i}') for i in range(4)]
        problem_tags = [tag.text for tag in html_tags if tag is not None]

        problem_tags = [t for t in problem_tags if t != "None"]
        if len(problem_tags) == 0:
            raise TagsNotFound
        return problem_tags
