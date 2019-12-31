# Co.Markdown

Collaboration with Markdown. Filesystem or redis as storage.

## Environments

- `REDIS_HOST`: default `127.0.0.1`
- `REDIS_PORT`: default `6379`
- `REDIS_DB`: default `0`
- `MARKDOWN_ROOT`: default `/tmp/markdown`
- `HOSTNAME`: link will be open in new tab if link target does not contains `HOSTNAME`
- `HOT_MAX`: max limit of API `api/top/<limit>`

## API

- `/md/`
  - GET: create one with random id and default content
  - POST: create one with random id
- `/md/<id>`
  - DELETE: delete
  - POST: update
  - GET: same as `/md/<id>.html`
- `/md/<id>/set_write_password`
  - POST: update or set write password
- `/md/<id>/set_read_password`
  - POST: update or set read password
- `/md/<id>`
  - `/edit`: edit markdown, need write password if set
  - `.html`: view as html, need read password if set
  - `.md`: view as markdown raw text, need read password if set
  - `.pdf`: view as PDF, need read password if set
- `/render`
  - POST: render the markdown you posted
- `/api`
  - `/top/10`
    - GET: get the top 10 hottest notes

## What you can use it for

Apply to the scene when you want to shared something to public temporarily,
and would like to be updated by someone has the password if you have set.

## Dependencies

- [`wkhtml2pdf`](https://github.com/wkhtmltopdf/wkhtmltopdf/releases): render as PDF in `/md/<id>.pdf`

## Fonts used in rendering PDF

- [Problem with emoji icons](https://github.com/wkhtmltopdf/wkhtmltopdf/issues/2913)
  - [Setup fonts on ubuntu](https://md.drink.cafe/md/fonts.html)

## TODO

- [x] 修复渲染子列表异常
  - [x] 4 空格缩进渲染异常，2 空格正常
  - [x] 列表栈 pop 回到上一级渲染异常
- [x] 微信字符编码未指定，渲染异常
- [x] 手机字体调整，隐藏快捷键帮助信息
- [x] 支持渲染 TODO
- [x] h3 竟然居中了？！配置决定。
- [x] 更完美的 MD 编辑器
- [x] 改成 Ctrl+S 保存
- [x] 添加文章修改密码 （Basic Auth)
  - [x] 在浏览器为不同文章分别保存密码
- [ ] 添加文章最近 20 次修改历史
- [x] 添加网站图标
- [x] better emoji implement
- [x] fix tooltip size on mobile
- [x] 统计访问频次以获取热门笔记
  - [ ] 从热门笔记中隐藏
- [x] 渲染成 PDF

## Screenshot

![](assets/screenshot.jpg)
