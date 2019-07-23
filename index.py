import os
import time
import random
import traceback
from functools import wraps
from flask import (
    Flask,
    __version__,
    jsonify,
    make_response,
    url_for,
    redirect,
    Response,
    request,
    render_template,
)
import emoji
from lib.common import md5, read_file
from md.patch import mdir, patch_renderer

patch_renderer()
app = Flask(__name__)
DEBUG = bool(os.getenv("DEBUG"))
example_md_path = os.path.join(os.path.dirname(__file__), "templates/example.md")


def dict_as_json(fn):
    @wraps(fn)
    def _fn(*args, **kwargs):
        return jsonify(**fn(*args, **kwargs))

    return _fn


def wrap_exception(fn):
    @wraps(fn)
    def _fn(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            response = make_response(
                {"exception": {"str": str(e), "type": str(type(e))}}
            )
            response.headers["Content-Type"] = "application/json"
            response.status_code = 500
            return response

    return _fn


def rv_as_mime(mime):
    def decorator(fn):
        @wraps(fn)
        def _fn(*args, **kwargs):
            rv = fn(*args, **kwargs)
            if isinstance(rv, Response):
                response = rv
            else:
                response = make_response(rv)
            response.headers["Content-Type"] = mime
            return response

        return _fn

    return decorator


@app.route("/")
def index():
    return redirect("/md/hello/edit")


@app.route("/sitemap")
@dict_as_json
def site_map():
    links = {}
    for rule in app.url_map.iter_rules():
        if rule.endpoint != "static":
            url = url_for(rule.endpoint, **(rule.defaults or {"id": "readme"}))
            links[rule.endpoint] = {"url": url, "methods": list(rule.methods)}
    return {"urls": links}


@app.route("/robots.txt")
@rv_as_mime("text/plain; charset=utf-8")
def robots():
    return """User-agent: *
Disallow: /"""


@app.route("/status")
@dict_as_json
def status():
    return {
        "flask": {"version": __version__},
        "status": "healthy",
        "files": os.listdir("/tmp"),
    }


def get_response(status_code, msg: str, mime="text/plain; charset=utf-8"):
    if mime == "application/json":
        res = jsonify(**{"status_code": status_code, "data": msg})
    else:
        res = make_response(msg)
    res.status_code = status_code
    return res


@app.route("/md/<id>/html", methods=["GET"])
@rv_as_mime("text/html")
def read_md_as_html(id):
    html = mdir.read_md_as_html(id)
    if html is None:
        return get_response(404, "FILE NOT FOUND")
    return emoji.emojize(html, use_aliases=True)


@app.route("/md/<id>/markdown", methods=["GET"])
@rv_as_mime("text/plain; charset=utf-8")
def read_md(id):
    md = mdir.read_md(id)
    if md is None:
        return get_response(404, "FILE NOT FOUND")
    return md


def new_with_example(id):
    example_md = read_file(example_md_path)
    mdir.save_md(id, example_md)
    return example_md


@app.route("/md/<id>/edit", methods=["GET"])
@rv_as_mime("text/html")
def edit_md(id):
    md = mdir.read_md(id)
    if md is None:
        example_md = new_with_example(id)
        return render_template("edit2.html", md=example_md, id=id)
    return render_template("edit2.html", md=md, id=id)


@app.route("/md/<id>", methods=["DELETE", "POST"])
@rv_as_mime("application/json")
def update_or_delete_md(id):
    if request.method == "DELETE":
        mdir.rm_md(id)
        return {"message": "deleted"}

    if request.method == "POST":
        md = request.stream.read().decode("utf8")
        mdir.save_md(id, md)
        return {"message": "updated"}

    return get_response(405, "method not allowed", "application/json")


@app.route("/md/", methods=["POST", "GET"])
@rv_as_mime("application/json")
def create_md():
    id = md5(str(time.time()) + str(random.randrange(0, 1000)))
    if request.method == "GET":
        new_with_example(id)
        return redirect(f"/md/{id}/edit")

    if request.method == "POST":
        md = request.stream.read().decode("utf8")
        mdir.save_md(id, md)
        return {"id": id}
    return get_response(405, "method not allowed", "application/json")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=DEBUG)
