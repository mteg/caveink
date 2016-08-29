

all:
	export PYTHONPATH="../extensions:../../extensions:/usr/share/inkscape/extensions"
	make -C randstones
	make -C window
	make -C line
	make -C morph
	make -C grid
	make -C pack
	make -C merge
	make -C find2

clean:
	rm -f */*.out.svg */*.out.png
	
	