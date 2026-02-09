#!/bin/bash

for chart_dir in charts/*/; do
    chart_yaml="${chart_dir}Chart.yaml"
    
    if [ -f "$chart_yaml" ]; then
        chart_name=$(basename "$chart_dir")
        current_version=$(grep '^version:' "$chart_yaml" | awk '{print $2}')
        
        # Incrementa patch version
        IFS='.' read -ra VERSION <<< "$current_version"
        major=${VERSION[0]}
        minor=${VERSION[1]}
        patch=${VERSION[2]}
        new_patch=$((patch + 1))
        new_version="${major}.${minor}.${new_patch}"
        
        echo "Bumping $chart_name: $current_version -> $new_version"
        sed -i "s/^version: .*/version: $new_version/" "$chart_yaml"
    fi
done

echo ""
echo "Todas as versões foram atualizadas!"
