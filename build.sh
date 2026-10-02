#!/usr/bin/env bash
set -e

pip install --upgrade pip
if [ -f requirements.txt ]; then
  pip install --prefer-binary -r requirements.txt
elif [ -f backend/requirements.txt ]; then
  pip install --prefer-binary -r backend/requirements.txt
fi
