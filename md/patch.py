import os

import maxpress
import redis
import emoji

from lib.md_dir import MDir


def get_redis():
    host = os.getenv("REDIS_HOST", "localhost")
    port = int(os.getenv("REDIS_PORT", "6379"))
    db = int(os.getenv("REDIS_DB", "0"))
    print("redis config:", host, port, db)
    rd = redis.Redis(host=host, port=port, db=db)
    return rd


MARKDOWN_ROOT = os.getenv("MARKDOWN_ROOT", "/tmp/markdown")
mdir = MDir(MARKDOWN_ROOT, redis=get_redis())
config, styles = None, None


def m2html(md: str, title):
    global config, styles
    if config is None:
        config, styles = maxpress.load_config_and_css(None)
        # config["poster_url"] = "https://bitsflow.org/favicon.png"
    return maxpress.convert_markdown(md, title, config, styles)


def emojize(text):
    return emoji.emojize(text, use_aliases=True)


def patch_renderer():
    mdir.md2html = m2html
