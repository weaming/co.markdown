rundev:
	DEBUG=1 python index.py

uwsgi:
	DEBUG=1 uwsgi uwsgi.ini
