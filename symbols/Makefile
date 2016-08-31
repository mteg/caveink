
unstyled:
	cat cave_symbols.svg  | sed 's/id="/id="gr/g;s/>Cave plan</>Cave plan - Unstyled</;s/#000000/inherit/g;s/xlink:href="#/xlink:href="#gr/g;s/stroke-width:[0-9.]\+\(;\|"\)/stroke-width:inherit\1/' > cave_symbols_unstyled.svg
	cat cave_rocks.svg  | sed 's/id="/id="un/g;s/>Cave rocks</>Cave rocks - Unstyled</;s/\(#000000\|none\)/inherit/g;s/xlink:href="#/xlink:href="#un/g;s/stroke-width:[0-9.]\+\(;\|"\)/stroke-width:inherit\1/' > cave_rocks_unstyled.svg
	sh mklist.sh cave_symbols.svg > symbol_list.txt
	sh mklist.sh cave_symbols_unstyled.svg " (Unstyled)" >>symbol_list.txt
	awk < symbol_list.txt -F '\t' '{ printf "<item value=\"%s\">%s</item>\n", $$1, $$2}' > symbol_list.xml
	