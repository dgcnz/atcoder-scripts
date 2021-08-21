from api import API
import json
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np

api = API()


def accepted_pie(user_id: str, user_cache: str = None):
    if user_cache is None:
        submissions = api.get_enriched_submissions(user_id, 10)
    else:
        with open(user_cache, "r") as f:
            submissions = json.load(f)
    submissions = [s for s in submissions if s["result"] == "AC"]
    problems_solved = set()
    tag_cnt = Counter()
    for s in submissions:
        if s["result"] != "AC":
            continue
        problem_id = s["problem_id"]
        if problem_id not in problems_solved:
            problems_solved.add(problem_id)
            if "tags" in s and len(s["tags"]) > 0:
                main_tag = s["tags"][0]
                tag_cnt[main_tag] += 1

    tags = tag_cnt.keys()
    cnt = list(tag_cnt.values())

    fig, ax = plt.subplots(figsize=(6, 3), subplot_kw=dict(aspect="equal"))

    def func(pct, allvals):
        absolute = int(pct / 100. * np.sum(allvals))
        return "{:.1f}%\n({:d})".format(pct, absolute)

    wedges, texts, autotexts = ax.pie(cnt,
                                      autopct=lambda pct: func(pct, cnt),
                                      textprops=dict(color="w"))

    ax.legend(wedges,
              tags,
              title=f"Tags (from {sum(cnt)} problems)",
              loc="center left",
              bbox_to_anchor=(1, 0, 0.5, 1))

    plt.setp(autotexts, size=8, weight="bold")

    ax.set_title(f"{user_id}'s accepted count per problem tag")

    plt.show()


# api.cache_enriched_submissions("dgcnz")
# accepted_pie("dgcnz", "dgcnz.json")

api.cache_enriched_submissions("pulsatio")
accepted_pie("pulsatio", "pulsatio.json")
