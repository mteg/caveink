
tr < $1 '\n' ' ' | sed 's/<symbol/\n<symbol/g;s/<\/title>/<\/title>\n/g' | sed 's/^.*<symbol *id="\([a-z_0-9-]\+\)" *> *<title[^<>]*>\([^<>]\+\)<\/title>.*$/===\t\1\t\2/' | awk -v suffix="$2" -F '\t' '/^===/ {printf "%s\t%s%s\n", $2, $3, suffix}'

