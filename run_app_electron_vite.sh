#!/bin/bash
cd frontend || exit 1
./build.sh
cd - || exit 1
cd electron-vite || exit 1
./run.sh