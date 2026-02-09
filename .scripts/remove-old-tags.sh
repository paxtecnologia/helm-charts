#!/bin/bash

echo "=== REMOVENDO TAGS ANTIGAS (mantendo últimas 5 de cada chart) ==="
echo ""

for chart in $(git tag | sed 's/-[0-9].*//' | sort -u); do
    tags=($(git tag | grep "^${chart}-" | sort -V))
    total=${#tags[@]}
    
    if [ $total -gt 5 ]; then
        keep=$((total - 5))
        echo "Chart: $chart (removendo $keep tags)"
        for tag in "${tags[@]:0:$keep}"; do
            echo "  Removendo: $tag"
            git tag -d "$tag"
            git push origin ":refs/tags/$tag"
        done
        echo ""
    fi
done

echo "=== CONCLUÍDO ==="
