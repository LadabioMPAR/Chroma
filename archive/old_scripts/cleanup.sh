#!/bin/bash

echo "🧹 Limpando projeto Chroma..."

# Limpar diretórios (manter as pastas, remover conteúdo)
echo "📁 Limpando raw_data/"
rm -rf raw_data/*

echo "📁 Limpando cromatogramas/"
rm -rf cromatogramas/*

echo "📁 Limpando plots/"
rm -rf plots/*

# Remover arquivos específicos
echo "📄 Removendo resumo.csv"
rm -f resumo.csv

# Remover arquivos .cdf soltos na raiz
echo "📄 Removendo arquivos .cdf da raiz"
rm -f *.cdf

echo "🎉 Limpeza concluída!"
echo ""
echo "💡 Para usar novamente:"
echo "   1. Coloque arquivos .cdf em raw_data/"
echo "   2. Execute: python ler.py"