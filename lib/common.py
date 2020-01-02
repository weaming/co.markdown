import os
import time
import datetime
import hashlib
import json
import requests
import pytz
from jsonkv import JsonKV

from bs4 import BeautifulSoup


def get_root_dir():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_now():
    TIMEZONE = os.getenv("TZ") or "Asia/Hong_Kong"
    TZ = pytz.timezone(TIMEZONE)
    return datetime.datetime.now(tz=TZ)


UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_5) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/69.0.3497.100 Safari/537.36"
)


def expired_for_seconds(name, seconds):
    # path = os.path.join(get_root_dir(), "db.json")
    path = os.path.join("/tmp/", "db.json")
    db = JsonKV(path, release_force=True)

    now = time.time()
    with db:
        ts = db[name]
        if now - (ts or 0) > seconds:
            db[name] = now
            return True
    return False


def http_get_url(
    url,
    is_json=False,
    headers=None,
    params=None,
    data=None,
    encoding="utf8",
    browser=True,
):
    if browser:
        headers = headers or {}
        headers["User-Agent"] = UA
    if data:
        res = requests.post(url, params=params, headers=headers, data=data)
    else:
        res = requests.get(url, params=params, headers=headers, timeout=30)
    if encoding:
        res.encoding = encoding

    err = False if res.status_code == 200 else res.status_code
    try:
        data = res.json() if is_json else res.text
    except Exception as e:
        return str(e), res.text
    return err, data


def rm_file(path):
    if os.path.isfile(path):
        os.remove(path)


def read_file(path, is_json=False):
    path = expand_user_vars(path)
    if not os.path.isfile(path):
        return None

    with open(path) as f:
        text = f.read()
        if is_json:
            return json.loads(text)
        return text


def prepare_dir(path):
    if not path.endswith("/"):
        path = os.path.dirname(path)
    if path and not os.path.isdir(path):
        os.makedirs(path)


def write_file(path, data, indent=2):
    if isinstance(data, (dict, list, tuple)):
        data = json.dumps(data, ensure_ascii=False, indent=indent)

    prepare_dir(path)
    with open(path, "w") as f:
        f.write(data)


def url2soup(url, params=None, encoding="utf8"):
    # print(soup.prettify())
    # soup.find_all('p', class_='chorus')
    # soup.find_all(id='third')
    _, html = http_get_url(
        url,
        params=params,
        is_json=False,
        headers={"Referer": url, "User-Agent": UA},
        encoding=encoding,
    )
    return html2soup(html)


def html2soup(html):
    soup = BeautifulSoup(html, "html.parser")
    return soup


def expand_user_vars(text, user=True, variable=True):
    if not text:
        return text
    if user:
        text = os.path.expanduser(text)
    if variable:
        text = os.path.expandvars(text)
    return text


def md5(text):
    m = hashlib.md5()
    m.update(text.encode("utf8"))
    return m.hexdigest()


def sha256(text: str):
    return hashlib.sha256(text.encode('utf8')).hexdigest()
