#!/bin/bash

# Keluar jika ada perintah yang gagal
set -e

# Pastikan pip tersedia dan perbarui
python3.12 -m ensurepip
python3.12 -m pip install --upgrade pip

# Install dependensi Python
python3.12 -m pip install -r requirements.txt

python3.12 manage.py tailwind build

# Kumpulkan file statis
python3.12 manage.py collectstatic --no-input --clear

# Jalankan migrasi database
python3.12 manage.py migrate
