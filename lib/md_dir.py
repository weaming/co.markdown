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
        self.count_read_key = 'md:count:read'

    def _path(self, id):
        return id + ".md"

    def get_path(self, id: str):
        _path = self._path(id)
        if self.redis:
            return "md:" + _path
        return os.path.join(self.root, _path)

    def descons_path(self, path: str):
        if self.redis:
            return path[len("md:") :]
        return path

    def get_password_path(self, id, for_read=False):
        _path = self._path(id)
        if self.redis:
            if for_read:
                return "pw:read:" + _path
            return "pw:write:" + _path
        return None

    def read_md(self, id):
        path = self.get_path(id)
        if self.redis:
            v = self.redis.get(path)
            if v is not None:
                self.redis.expire(path, self.expire)
                self.redis.zincrby(self.count_read_key, 1, path)
                return v.decode("utf8")
        else:
            if not os.path.isfile(path):
                return None
            with open(path) as f:
                return f.read()
        return None

    def count_top_n(self, n=0):
        def gen():
            got = 0
            for i, x in enumerate(
                self.redis.zrange(
                    self.count_read_key, 0, -1, desc=True, withscores=True
                )
            ):
                if got >= n:
                    return
                path = x[0].decode('utf8')
                v = self.redis.get(path)
                if v is None:
                    self.redis.zrem(self.count_read_key, path)
                    continue

                got += 1
                yield {
                    'key': self.descons_path(path),
                    'count': int(x[1]),
                    'index': i + 1,
                }

        return list(gen())

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
            self.redis.delete(self.get_password_path(id, for_read=True))
            self.redis.zrem(self.count_read_key, path)
            return self.redis.delete(path)
        else:
            if os.path.isfile(path):
                try:
                    os.remove(path)
                    return True
                except Exception as e:
                    print(e)
            return False

    def get_user_password(self, id, for_read=False):
        u, p = None, None
        if self.redis:
            pw_key = self.get_password_path(id, for_read)
            v = self.redis.get(pw_key)
            if v is not None:
                self.redis.expire(pw_key, self.expire)
                p = v.decode("utf8")
        return u, p

    def set_user_password(self, id, user: str, pw: str, for_read=False):
        if self.redis:
            pw_key = self.get_password_path(id, for_read)
            pw_secret = self.hash_password(pw)

            self.redis.set(pw_key, pw_secret.encode("utf8"))
            self.redis.expire(pw_key, self.expire)
            return True
        return False

    @staticmethod
    def hash_password(password):
        return md5(password)
