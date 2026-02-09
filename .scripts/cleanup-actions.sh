#!/bin/bash

# Limpa workflow runs antigos do GitHub Actions
# Requer: gh CLI instalado e autenticado

echo "=== Limpando Workflow Runs Antigos ==="
echo ""

# Lista workflows disponíveis
echo "Workflows disponíveis:"
gh workflow list
echo ""

# Opção 1: Deletar runs com mais de 30 dias
echo "Deletando runs com mais de 30 dias..."
gh run list --limit 1000 --json databaseId,createdAt,status \
  --jq '.[] | select(.createdAt < (now - 2592000)) | .databaseId' \
  | xargs -I {} gh run delete {} 2>/dev/null

# Opção 2: Deletar runs completados (manter apenas os últimos 10)
echo ""
echo "Deletando runs completados (mantendo últimos 10)..."
gh run list --limit 1000 --status completed --json databaseId \
  --jq '.[10:] | .[].databaseId' \
  | xargs -I {} gh run delete {} 2>/dev/null

echo ""
echo "=== Limpeza Concluída ==="
