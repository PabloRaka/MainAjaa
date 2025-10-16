#!/bin/bash

# Keluar jika ada error
set -e

# Pastikan pip terinstall
python3.12 -m ensurepip
python3.12 -m pip install --upgrade pip

# Install dependencies
python3.12 -m pip install -r requirements.txt

# Kumpulkan file statis
python3.12 manage.py collectstatic --no-input --clear

# Jalankan migrasi database
python3.12 manage.py migrate
