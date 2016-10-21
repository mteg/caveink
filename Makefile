
INKPATH=/usr/share/inkscape

all:
	@echo ""
	@echo "These extensions do not need building."
	@echo "You can, however, do one of the following:"
	@echo "  sudo make install"
	@echo "  make test"
	@echo "  make clean"
	@echo ""
	@echo "Please adjust your inkscape installation path in Makefile (default is /usr/share/inkscape)"
	@echo ""

test:
	PYTHONPATH="../extensions:../../extensions:/usr/share/inkscape/extensions" make -C tests

clean:
	make -C tests clean
	rm -f extensions/*~ extensions/*.pyc symbols/*~

install:
	cp extensions/*.py $(INKPATH)/extensions
	cp extensions/*.inx $(INKPATH)/extensions
	cp patterns/*.svg $(INKPATH)/patterns
	cp templates/*.svg $(INKPATH)/templates
	cp symbols/*.svg $(INKPATH)/symbols
	cp keys/*.xml $(INKPATH)/keys
