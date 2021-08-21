from tags_api import TagsAPI

api = TagsAPI('problems.json', 'tags.json')
api.update_all_tags(chunk_size=100, chunk_index=22)
