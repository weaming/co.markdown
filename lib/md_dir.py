import os
import mistune
import redis

from .common import prepare_dir, md5

month = 60 * 60 * 24 * 31
quarter = month * 3


def extract_user_id_from_md_id(id: str):
    if '/' in id:
        return id.split('/', 1)[0]
    return None


def parse_md_id_under_user(id: str) -> (bool, str):
    user_id = extract_user_id_from_md_id(id)
    if user_id:
        # all markdowns under an user are protected using same password
        return True, user_id
    return False, id


class MDir:
    def __init__(self, root="/tmp/markdown", redis: redis.Redis = None, expire=quarter):
        self.root = root
        self.redis = redis
        self.expire = expire
        self.count_read_key = 'md:count:read'

    def _md_id(self, id):
        return id + ".md"

    def _user_id(self, user_id):
        return user_id + '/'

    def get_redis_md_key(self, id: str):
        _path = self._md_id(id)
        if self.redis:
            return "md:" + _path
        return os.path.join(self.root, _path)

    def descons_path(self, path: str):
        if self.redis:
            return path[len("md:") :]
        return path

    def get_redis_password_key(self, id, for_read=False):
        for_user, user_id = parse_md_id_under_user(id)
        # only write passwords of one user are same
        if for_user and not for_read:
            md_id = self._user_id(user_id)
        else:
            md_id = self._md_id(id)
        if self.redis:
            if for_read:
                return "pw:read:" + md_id
            return "pw:write:" + md_id
        return None

    def read_md(self, id):
        path = self.get_redis_md_key(id)
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
        path = self.get_redis_md_key(id)
        if self.redis:
            self.redis.set(path, text.encode("utf8"))
            self.redis.expire(id, self.expire)
            self.redis.bgsave()
        else:
            prepare_dir(path)
            with open(path, "w") as f:
                f.write(text)

    def rm_md(self, id):
        path = self.get_redis_md_key(id)
        if self.redis:
            self.redis.delete(self.get_redis_password_key(id))
            self.redis.delete(self.get_redis_password_key(id, for_read=True))
            self.redis.zrem(self.count_read_key, path)
            self.redis.bgsave()
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
            pw_key = self.get_redis_password_key(id, for_read)
            v = self.redis.get(pw_key)
            if v is not None:
                self.redis.expire(pw_key, self.expire)
                p = v.decode("utf8")
        return u, p

    def delete_user_password(self, id, user: str, for_read=False):
        if self.redis:
            pw_key = self.get_redis_password_key(id, for_read)
            self.redis.delete(pw_key)
            return True
        # default no password
        return True

    def set_user_password(self, id, user: str, pw: str, for_read=False):
        if self.redis:
            pw_key = self.get_redis_password_key(id, for_read)
            pw_secret = self.hash_password(pw)

            self.redis.set(pw_key, pw_secret.encode("utf8"))
            self.redis.expire(pw_key, self.expire)
            self.redis.bgsave()
            return True
        return False

    @staticmethod
    def hash_password(password):
        return md5(password)
