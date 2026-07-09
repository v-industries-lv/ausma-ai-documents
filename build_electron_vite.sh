#!/bin/bash

# Build frontend
cd frontend || exit 1
./build.sh
cd - || exit 1

# Build backend
cd backend || exit 1
./build_bundled.sh
cd - || exit 1

# Ensure pdftopng
FILE="backend/bin/linux/pdftopng"
if [[ ! -f "$FILE" ]]; then
  mkdir -p backend/bin/linux
  url="https://dl.xpdfreader.com/xpdf-tools-linux-4.06.tar.gz"
  archive="xpdf-tools-linux-4.06.tar.gz"
  archive_root="xpdf-tools-linux-4.06"
  curl -LO "$url"

  bits=$(getconf LONG_BIT | tr -d '[:space:]')
  if [[ "$bits" == "32" ]]; then
   pdftopng_bin="$archive_root/bin32/pdftopng"
  elif [[ "$bits" == "64" ]]; then
   pdftopng_bin="$archive_root/bin64/pdftopng"
  else
   echo "Unknown architecture: $bits"
   exit 1
  fi

tar -xzf "$archive" "$pdftopng_bin" || { echo "Extraction has failed"; exit 1; }
mv "$pdftopng_bin" "backend/bin/linux/pdftopng" || { echo "Failed to move file"; exit 1; }
rm $archive_root -r
else
  echo "pdftopng exists"
fi
# Build app
cd electron-vite || exit 1
./build.sh