#!/bin/bash

# Keluar jika ada perintah yang gagal
set -e

# Install dependensi Python
python3.12 -m pip install -r requirements.txt

# ===============================================
# PERBAIKAN DI SINI: Gunakan npm untuk membuat CSS
# ===============================================
npm run build:css

# Kumpulkan file statis
python3.12 manage.py collectstatic --no-input --clear

# Jalankan migrasi database
python3.12 manage.py migrate
