
BASEFILES = app.yaml google_user_challenger.py google_user_extractor.py googledata.py main.py tiddlywebconfig.py static

clean: cleango cleangotmp

cleango:
	rm -rf go || true

cleangotmp:
	rm -rf go.tmp || true

installenv:
	virtualenv --no-site-packages go.tmp
	( cd go.tmp && source bin/activate && \
	pip install -U tiddlywebwiki tiddlywebplugins.wimporter)

go: installenv fill

fill:
	mkdir go
	( cd go ; \
	for file in $(BASEFILES); do ln -s ../$$file . ; done ; \
	for file in ../go.tmp/lib/python*/site-packages/* ; do ln -s $$file . ; done ;\
	ln -s tiddlywebplugins/templates templates ;\
	touch tiddlywebplugins/__init__.py )

.DEFAULT:
	echo $@
