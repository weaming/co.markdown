from functools import wraps

from flask import g, Response
from flask_basicauth import BasicAuth

from lib.md_dir import MDir


class BasicAuth4MarkdownID(BasicAuth):
    mdir: MDir = None

    def check_credentials(self, username, password):
        """
        Check if the given username and password are correct.

        :param username: a username provided by the client
        :param password: a password provided by the client
        :returns: `True` if the username and password combination was correct,
            and `False` otherwise.
        """
        u, p = self.mdir.get_user_password(g.id)
        return self.mdir.hash_password(password) == p

    def required(self, view_func):
        """
        A decorator that can be used to protect specific views with HTTP
        basic access authentication.
        """

        @wraps(view_func)
        def wrapper(*args, **kwargs):
            # set id for check_credentials()
            g.id = kwargs.get("id")

            if self.authenticate():
                return view_func(*args, **kwargs)
            else:
                return self.challenge()

        return wrapper

    def challenge(self):
        """
        Challenge the client for username and password.
        """
        return Response(
            status=401, headers={"WWW-Authenticate": 'Basic realm="protected markdown %s"' % g.id}
        )

    def authenticate(self):
        u, p = self.mdir.get_user_password(g.id)
        if g.id and p:
            return super().authenticate()
        return True

    def set_mdir(self, mdir):
        self.mdir = mdir
