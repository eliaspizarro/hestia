#!/bin/bash
#
# Hestia unified IPv4 ipset generator
# Combina todos los ipsets v4 existentes en uno solo (sin duplicados)
# STDOUT: solo IPv4/CIDR válidos
#

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export PATH

set -u
umask 077

SELF_IPSET="all.ipset"
V_LIST="/usr/local/hestia/bin/v-list-firewall-ipset"
[[ -x "$V_LIST" ]] || exit 0

TMP_ALL=$(mktemp)
trap 'rm -f "$TMP_ALL"' EXIT

# Obtener todos los ipsets v4 excepto el propio
mapfile -t SOURCES < <(
	"$V_LIST" 2>/dev/null \
	| awk -v self="$SELF_IPSET" '
		NR>1 && $2=="v4" && $1!=self {
			src=""
			for (i=5; i<=NF-2; i++) src=src $i (i<NF-2?" ":"")
			if (src!="") print src
		}'
)

[[ ${#SOURCES[@]} -eq 0 ]] && exit 0

for src in "${SOURCES[@]}"; do
	if [[ "$src" == script:* ]]; then
		script="${src#script:}"
		[[ -x "$script" ]] || continue

		bash "$script" 2>/dev/null \
		| grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}(/[0-9]{1,2})?' \
		>> "$TMP_ALL" || true
	else
		TMP_SRC=$(mktemp)
		HTTP_RC=$(curl -L -s --connect-timeout 10 --max-time 20 \
			-o "$TMP_SRC" -w "%{http_code}" "$src" 2>/dev/null || echo 0)

		if [[ "$HTTP_RC" == "200" || "$HTTP_RC" == "302" || "$HTTP_RC" == "000" || "$HTTP_RC" == "0" ]]; then
			grep -oE '([0-9]{1,3}\.){3}[0-9]{1,3}(/[0-9]{1,2})?' "$TMP_SRC" \
			>> "$TMP_ALL"
		fi

		rm -f "$TMP_SRC"
	fi
done

# Normalización, filtrado y deduplicación final

sed -r '
	s/^0*([0-9]+)\.0*([0-9]+)\.0*([0-9]+)\.0*([0-9]+)/\1.\2.\3.\4/
' "$TMP_ALL" \
| sed -r '/^(0\.0\.0\.0|10\.|127\.|169\.254\.|172\.1[6-9]\.|172\.2[0-9]\.|172\.3[0-1]\.|192\.168\.|22[4-9]\.|23[0-9]\.)/d' \
| sort -u
