#!/bin/bash

# Keluar jika ada error
set -e

python3.9 -m ensurepip
python3.9 -m pip install --upgrade pip


# Install dependencies
python3.9 -m pip install -r requirements.txt

# Kumpulkan file statis
python manage.py collectstatic --no-input --clear

# Jalankan migrasi database
python manage.py migrate
