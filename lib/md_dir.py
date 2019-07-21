import os
import mistune
from .common import prepare_dir


class MDir:
    def __init__(self, root="/tmp/markdown"):
        self.root = root

    def get_path(self, id: str):
        return os.path.join(self.root, id + ".md")

    def read_md(self, id):
        path = self.get_path(id)
        if not os.path.isfile(path):
            return None
        with open(path) as f:
            return f.read()

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
        prepare_dir(path)
        with open(path, "w") as f:
            f.write(text)

    def rm_md(self, id):
        path = self.get_path(id)
        if os.path.isfile(path):
            try:
                os.remove(path)
                return True
            except Exception as e:
                print(e)
        return False
