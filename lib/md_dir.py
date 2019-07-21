import os
import mistune
import redis
from .common import prepare_dir

year = 60 * 60 * 24 * 365


class MDir:
    def __init__(self, root="/tmp/markdown", redis: redis.Redis = None, expire=year):
        self.root = root
        self.redis = redis
        self.expire = expire

    def get_path(self, id: str):
        if self.redis:
            return "md:" + id + ".md"
        return os.path.join(self.root, id + ".md")

    def read_md(self, id):
        path = self.get_path(id)
        if self.redis:
            v = self.redis.get(path)
            if v is not None:
                self.redis.expire(path, self.expire)
                return v.decode('utf8')
        else:
            if not os.path.isfile(path):
                return None
            with open(path) as f:
                return f.read()
        return None

    @staticmethod
    def md2html(md, id):
        return mistune.markdown(md)

    def read_md_as_html(self, id):
        md = self.read_md(id)
        if md is not None:
            return self.md2html(md, id)
        return None

    def save_md(self, id, text):
        path = self.get_path(id)
        if self.redis:
            self.redis.set(path, text.encode('utf8'))
            self.redis.expire(id, self.expire)
        else:
            prepare_dir(path)
            with open(path, "w") as f:
                f.write(text)

    def rm_md(self, id):
        path = self.get_path(id)
        if self.redis:
            return self.redis.delete(path)
        else:
            if os.path.isfile(path):
                try:
                    os.remove(path)
                    return True
                except Exception as e:
                    print(e)
            return False
