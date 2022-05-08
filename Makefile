VER=$(shell grep __version__ negar_gui/constants.py|cut -d= -f2|tr -d '\" ')

.ONESHELL:

ver:
	@echo negar-gui ver. $(VER)

setup: ver
	python setup.py sdist
	python setup.py bdist_wheel

lins: ver
	python setup.py install

pins: ver
	pip install negar-gui==$(VER)

upypi: setup
	twine upload "dist/negar-gui-$(VER).tar.gz"

utest: setup
	twine upload -r testpypi "dist/negar-gui-$(VER).tar.gz"

upload: setup upypi utest

nuCompile: ver
	nuitka3 negar_gui/gui.py --standalone --onefile --linux-onefile-icon=negar_gui/logo.png \
	--include-data-dir=.negar/lib/python3.10/site-packages/pyuca=pyuca \
	--include-data-dir=.negar/lib/python3.10/site-packages/negar=negar/data \
	-o dist/negar-gui-v$(VER).bin \
	--output-dir=dist --remove-output --enable-plugin=pyqt5
	# --include-data-file=negar/data/untouchable.dat=data/untouchable.dat \

	ls -lh dist

piCompile: ver
	rm build/gui/ -rfv
	. .negar/bin/activate
	pyinstaller -p negar_gui --onefile --clean \
	--collect-data pyuca --noupx negar_gui/gui.py -n negar-gui-v$(VER) \
	--add-data ../python-negar/negar/data/untouchable.dat:data
	ls -lh dist

trans: ver
	pylupdate5 -verbose negar_gui/Ui_mwin.py -ts negar_gui/ts/fa-uimwin.ts
	pylupdate5 -verbose negar_gui/Ui_uwin.py -ts negar_gui/ts/fa-uiuwin.ts
	pylupdate5 -verbose negar_gui/main.py -ts negar_gui/ts/fa-main.ts
	lrelease negar_gui/ts/fa-*.ts -qm negar_gui/ts/fa.qm

res: ver
	pyrcc5 negar_gui/resource.qrc -o negar_gui/resource_rc.py

ui: ver
	pyuic5 --from-imports negar_gui/mwin.ui -o negar_gui/Ui_mwin.py
	pyuic5 --from-imports negar_gui/uwin.ui -o negar_gui/Ui_uwin.py

sres: ver
	pyside2-rcc negar_gui/resource.qrc -o negar_gui/resource_rc.py

sui: ver
	pyside2-uic --from-imports negar_gui/mwin.ui -o negar_gui/Ui_mwin.py
	pyside2-uic --from-imports negar_gui/uwin.ui -o negar_gui/Ui_uwin.py

strans: ver
	pyside2-lupdate -verbose negar_gui/Ui_mwin.py -ts negar_gui/ts/fa-uimwin.ts
	pyside2-lupdate -verbose negar_gui/Ui_uwin.py -ts negar_gui/ts/fa-uiuwin.ts
	pyside2-lupdate -verbose negar_gui/main.py -ts negar_gui/ts/fa-main.ts
	pyside2-lrelease negar_gui/ts/fa-*.ts -qm negar_gui/ts/fa.qm

clean: ver
	rm negar_gui.egg-info/ -rfv
	rm build/ -rfv
	rm dist/ -rfv
	rm gui.build/ -rfv
	rm gui.dist/ -rfv
	rm negar*.spec -rfv
