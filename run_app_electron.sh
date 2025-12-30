#!/bin/bash
cd frontend || exit 1
./build.sh
cd - || exit 1
cd electron || exit 1
./run.sh