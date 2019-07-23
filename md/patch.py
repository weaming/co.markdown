import os

import emoji
import maxpress
import redis
from maxpress.renderer import MRender, MDown

from lib.md_dir import MDir


def get_redis():
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0"))
    print("redis config:", host, port, db)
    rd = redis.Redis(host=host, port=port, db=db)
    return rd


mdir = MDir(os.getenv("MARKDOWN_ROOT", "/tmp/markdown"), redis=get_redis())
config, styles = None, None


def m2html(md: str, title):
    global config, styles
    if config is None:
        config, styles = maxpress.load_config_and_css(None)
        # config["poster_url"] = "https://bitsflow.org/favicon.png"
    return maxpress.convert_markdown(md, title, config, styles)


class EmojiMRender(MRender):
    def emojize(self, text):
        return emoji.emojize(text, use_aliases=True)


def patch_renderer():
    mdir.md2html = m2html
    maxpress.export["markdown"] = MDown(renderer=EmojiMRender())
