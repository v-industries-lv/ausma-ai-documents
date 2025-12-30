#!/bin/bash
cd frontend || exit 1
./setup_linux.sh
cd - || exit 1

cd electron || exit 1
./setup_linux.sh
cd - || exit 1

cd backend || exit 1
./setup_linux.sh