all:
	sh ../test.sh ../../extensions/speleo_grid.py "--spacing=100 --id=ref --draw-coords=rotate --type=cross" moved
	sh ../test.sh ../../extensions/speleo_grid.py "--spacing=50 --id=ref --draw-coords=plain" confined-grid
	sh ../test.sh ../../extensions/speleo_grid.py "--spacing=50 --id=ref --id=page --draw-coords=plain" confined-grid
	sh ../test.sh ../../extensions/speleo_grid.py "--spacing=50 --id=page --id=ref --origin-x=1000 --origin-y=1000 --units=ft --draw-coords=plain" confined-grid
	sh ../test.sh ../../extensions/speleo_grid.py "--spacing=50 --id=page --id=orrect --origin-x=1000 --origin-y=1000 --units=ft --draw-coords=plain" confined-grid
