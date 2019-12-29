from functools import wraps

from flask import g, Response, request
from flask_basicauth import BasicAuth

from lib.md_dir import MDir


class BasicAuth4MarkdownID(BasicAuth):
    mdir: MDir = None

    def check_credentials(self, username, password, for_read):
        """
        Check if the given username and password are correct.

        :param username: a username provided by the client
        :param password: a password provided by the client
        :returns: `True` if the username and password combination was correct,
            and `False` otherwise.
        """
        u, p = self.mdir.get_user_password(g.id, for_read)
        return self.mdir.hash_password(password) == p

    def required(self, view_func, password=None, for_read=False):
        """
        A decorator that can be used to protect specific views with HTTP
        basic access authentication.
        """

        @wraps(view_func)
        def wrapper(*args, **kwargs):
            # set id for check_credentials()
            g.id = kwargs.get("id")
            if self.authenticate(for_read):
                return view_func(*args, **kwargs)
            else:
                return self.challenge(for_read)

        return wrapper

    def challenge(self, for_read):
        """
        Challenge the client for username and password.
        """
        return Response(
            status=401,
            headers={
                "WWW-Authenticate": 'Basic realm="protected markdown %s for %s"'
                % (g.id, 'read' if for_read else 'write')
            },
        )

    def authenticate(self, for_read):
        u, p = self.mdir.get_user_password(g.id, for_read)
        if g.id and p:
            auth = request.authorization
            return (
                auth
                and auth.type == 'basic'
                and self.check_credentials(auth.username, auth.password, for_read)
            )
        return True

    def set_mdir(self, mdir):
        self.mdir = mdir
