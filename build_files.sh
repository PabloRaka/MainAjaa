#!/bin/bash

# Keluar jika ada error
set -e

# Install dependencies (dengan perintah yang sudah benar)
python3.9 -m pip install -r requirements.txt

# Kumpulkan file statis
python manage.py collectstatic --no-input

# (Opsional) Jalankan migrasi database
python manage.py migrate
