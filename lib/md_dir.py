import os
import mistune
import redis

from .common import prepare_dir, md5

month = 60 * 60 * 24 * 31
quarter = month * 3


class MDir:
    def __init__(self, root="/tmp/markdown", redis: redis.Redis = None, expire=quarter):
        self.root = root
        self.redis = redis
        self.expire = expire

    def _path(self, id):
        return id + ".md"

    def get_path(self, id: str):
        _path = self._path(id)
        if self.redis:
            return "md:" + _path
        return os.path.join(self.root, _path)

    def get_password_path(self, id):
        _path = self._path(id)
        if self.redis:
            return "pw:" + _path
        return None

    def read_md(self, id):
        path = self.get_path(id)
        if self.redis:
            v = self.redis.get(path)
            if v is not None:
                self.redis.expire(path, self.expire)
                return v.decode("utf8")
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
            self.redis.set(path, text.encode("utf8"))
            self.redis.expire(id, self.expire)
        else:
            prepare_dir(path)
            with open(path, "w") as f:
                f.write(text)

    def rm_md(self, id):
        path = self.get_path(id)
        if self.redis:
            self.redis.delete(self.get_password_path(id))
            return self.redis.delete(path)
        else:
            if os.path.isfile(path):
                try:
                    os.remove(path)
                    return True
                except Exception as e:
                    print(e)
            return False

    def get_user_password(self, id):
        u, p = None, None
        if self.redis:
            pw_key = self.get_password_path(id)
            v = self.redis.get(pw_key)
            if v is not None:
                self.redis.expire(pw_key, self.expire)
                p = v.decode("utf8")
        return u, p

    def set_user_password(self, id, user: str, pw: str):
        if self.redis:
            pw_key = self.get_password_path(id)
            pw_secret = self.hash_password(pw)

            self.redis.set(pw_key, pw_secret.encode("utf8"))
            self.redis.expire(pw_key, self.expire)
            return True
        return False

    @staticmethod
    def hash_password(password):
        return md5(password)
