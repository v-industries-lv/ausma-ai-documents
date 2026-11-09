#!/bin/bash
cd frontend || exit 1
./build.sh
cd - || exit 1
cd backend || exit 1
./run_app.sh --frontend_path "../frontend/dist"