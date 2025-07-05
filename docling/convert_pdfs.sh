#!/bin/bash
set -e

echo "📄 Starting batch conversion with Docling..."

for file in /pdfs/*.pdf; do
  filename=$(basename "$file" .pdf)
  echo "➡️  Converting $filename.pdf ..."
  docling "$file" --from pdf --to html --output /htmls/
done

echo "✅ All PDFs converted."