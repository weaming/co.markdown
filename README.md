# Co.Markdown

Collaboration with Markdown. Filesystem or redis as storage.

## Environments

* `REDIS_HOST`: default `127.0.0.1`
* `REDIS_PORT`: default `6379`
* `REDIS_DB`: default `0`
* `MARKDOWN_ROOT`: default `/tmp/markdown`

## API

* /md/
    * GET:  create one with ramdom id and default content
    * POST: create one with ramdom id
* `/md/<id>`
    * DELETE: delete
    * POST: update
* `/md/<id>`
    * /edit
    * /html
    * /markdown

## What you can use it for

No write lock, no instant synchronization.

Apply to the scene when you want to shared something to public temporarily and would like to be updated by anyone.
