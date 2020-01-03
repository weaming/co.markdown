import os
import time
import random
import traceback
from functools import wraps, partial
import pdfkit
import imgkit
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
from werkzeug.wrappers.response import Response as Response2

from lib.auth import BasicAuth4MarkdownID
from lib.common import md5, read_file
from md.patch import mdir, patch_renderer, emojize, MARKDOWN_ROOT

patch_renderer()
app = Flask(__name__)
DEBUG = bool(os.getenv("DEBUG"))
HOT_MAX = int(os.getenv("HOT_MAX", '100'))
# example_md_path = os.path.join(os.path.dirname(__file__), "templates/example.md")
example_md_path = os.path.join(os.path.dirname(__file__), "templates/example_simple.md")

# https://www.w3.org/2005/10/howto-favicon
icon = "https://i.loli.net/2019/07/23/5d372848883f339418.png"
# icon = "https://i.loli.net/2019/07/23/5d3729d9d3aef58565.png"
icon_tag = f'<link rel="shortcut icon" href="{icon}">'
# https://stackoverflow.com/questions/8091996/http-header-stylesheets
# http://test.greenbytes.de/tech/tc/httplink/
# https://www.iana.org/assignments/message-headers/message-headers.xhtml
# https://tools.ietf.org/html/rfc8288
icon_header = f'<{icon}>; rel="shortcut icon"'

basic_auth = BasicAuth4MarkdownID(app)
basic_auth.set_mdir(mdir)


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
            if isinstance(rv, (Response, Response2)):
                response = rv
            elif isinstance(rv, dict):
                response = jsonify(**rv)
                assert mime == "application/json"
            else:
                if isinstance(rv, tuple) and len(rv) == 2:
                    rv, status_code = rv
                else:
                    status_code = 200
                if mime == "text/html":
                    rv = icon_tag + rv
                response = make_response(rv)
                response.status_code = status_code
            response.headers["Content-Type"] = mime
            response.headers["Link"] = icon_header
            return response

        return _fn

    return decorator


@app.route("/")
def index():
    return redirect("/md/readme.html")


@app.route("/sitemap")
@rv_as_mime("application/json")
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
Allow: /"""


@app.route("/status")
@rv_as_mime("application/json")
def status():
    return {"flask": {"version": __version__}, "files": os.listdir(MARKDOWN_ROOT)}


def get_response(status_code, msg: str, mime="text/plain; charset=utf-8"):
    if mime == "application/json":
        res = jsonify(**{"status_code": status_code, "data": msg})
    else:
        res = make_response(msg)
    res.status_code = status_code
    return res


@app.route("/api/top/<int:limit>", methods=["GET"])
@rv_as_mime("application/json")
def top_hot(limit):
    if limit > HOT_MAX:
        return get_response(404, f"limit is bigger than {HOT_MAX}")
    rv = mdir.count_top_n(limit)

    def to_url(x):
        x['url'] = f'/md/{x["key"][:-len(".md")]}.html'
        return x

    return {'data': list(map(to_url, rv))}


@app.route("/md/<path:id>.html", methods=["GET"])
@partial(basic_auth.required, for_read=True)
@rv_as_mime("text/html")
def read_md_as_html(id):
    html = mdir.read_md_as_html(id)
    if html is None:
        return get_response(404, "FILE NOT FOUND")
    return html


@app.route("/md/<path:id>.md", methods=["GET"])
@partial(basic_auth.required, for_read=True)
@rv_as_mime("text/plain; charset=utf-8")
def read_md(id):
    md = mdir.read_md(id)
    if md is None:
        return get_response(404, "FILE NOT FOUND")
    return md


@app.route("/md/<path:id>.pdf", methods=["GET"])
@partial(basic_auth.required, for_read=True)
@rv_as_mime("application/pdf")
def read_md_as_pdf(id):
    html = mdir.read_md_as_html(id)
    if html is None:
        return get_response(404, "FILE NOT FOUND")
    try:
        return pdfkit.from_string(
            html,
            False,
            # https://github.com/wkhtmltopdf/wkhtmltopdf/issues/3424
            options={
                '--disable-javascript': '',
                # '--javascript-delay': 5,
                '--encoding': 'utf-8',
                '--quiet': '',
            },
        )
    except Exception as e:
        traceback.print_exc()
        return get_response(500, str(e))


@app.route("/md/<path:id>.png", methods=["GET"])
@partial(basic_auth.required, for_read=True)
@rv_as_mime("image/png")
def read_md_as_png(id):
    html = mdir.read_md_as_html(id)
    if html is None:
        return get_response(404, "FILE NOT FOUND")
    try:
        return imgkit.from_string(
            html,
            False,
            # https://github.com/wkhtmltopdf/wkhtmltopdf/issues/3424
            options={
                '--format': 'png',
                '--disable-javascript': '',
                # '--javascript-delay': 5,
                '--encoding': 'utf-8',
                '--quiet': '',
            },
        )
    except Exception as e:
        traceback.print_exc()
        return get_response(500, str(e))


def new_with_example(id):
    example_md = read_file(example_md_path)
    mdir.save_md(id, example_md)
    return example_md


@app.route("/md/<user_id>/", methods=["GET"])
@rv_as_mime("text/html")
def list_md(user_id):
    # user_id maybe a markdown id
    md = mdir.read_md(user_id)
    if md is not None:
        return redirect(f"/md/{user_id}.html")

    mds = mdir.list_md(user_id)
    title = f'Notes of user {user_id}'
    md = f'# Notes of user {user_id}\n\n' + '\n'.join(
        f'* [{x}](/md/{x}.html)' for x in sorted(mds)
    )
    return mdir.md2html(md, title)


@app.route("/md/<path:id>/edit", methods=["GET"])
@basic_auth.required
@rv_as_mime("text/html")
def edit_md(id):
    md = mdir.read_md(id)
    if '/' in id:
        user_id = id.split('/', 1)[0]
        md_with_user_id_as_id = mdir.read_md(user_id)
        if md_with_user_id_as_id:
            return (
                f'User id "{user_id}" is used as markdown id. Please choose another one.',
                400,
            )
    else:
        mds = mdir.list_md(user_id)
        if mds:
            return (
                f'Markdown id "{id}" is used as user id. Please choose another one.',
                400,
            )

    if md is None:
        example_md = new_with_example(id)
        return render_template("edit.html", md=example_md, id=id)
    write_u, write_p = mdir.get_user_password(id, for_read=False)
    read_u, read_p = mdir.get_user_password(id, for_read=True)
    return render_template(
        "edit.html",
        md=md,
        id=id,
        write_user=write_u,
        write_password=write_p,
        read_user=read_u,
        read_password=read_p,
    )


@app.route("/md/<path:id>/set_write_password", methods=["POST"])
@partial(basic_auth.required, for_read=False)
@rv_as_mime("application/json")
def set_md_write_password(id):
    return set_password_for_md(id, for_read=False)


@app.route("/md/<path:id>/set_read_password", methods=["POST"])
@partial(basic_auth.required, for_read=True)
@rv_as_mime("application/json")
def set_md_read_password(id):
    return set_password_for_md(id, for_read=True)


def set_password_for_md(id, for_read):
    md = mdir.read_md(id)
    type = 'read' if for_read else 'write'
    if md is not None:
        data = request.get_json()
        pw = data.get("password")
        if not pw:
            mdir.delete_user_password(id, None, for_read)
            return {"message": f"succeed removing {type} password", "id": id}
        if mdir.set_user_password(id, None, pw, for_read,):
            return {"message": f"succeed setting {type} password", "id": id}
        else:
            return {"message": f"failed setting {type} password", "id": id}
    return {"message": "NOT FOUND", "id": id}


@app.route("/md/<path:id>", methods=["DELETE", "POST"])
@basic_auth.required
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


@app.route("/render", methods=["POST", "GET"])
@rv_as_mime("text/html")
def render():
    if request.method == "GET":
        md = "POST your markdown text to this endpoint to render instantly! :smile:"
        title = ":joy:"

    elif request.method == "POST":
        md = request.stream.read().decode("utf8")
        if not md.strip():
            md = "You markdown is blank! :smile:"
            title = ":smile:"
        else:
            title = md.split("\n")[0].lstrip("# ").strip() if md.strip() else ""

    return mdir.md2html(md, emojize(title))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")), debug=DEBUG)
