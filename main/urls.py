# main/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ===================================================
    # URL HALAMAN UTAMA & PENELUSURAN
    # ===================================================
    path('', views.landing_page, name='landing_page'),
    path('semua-akun/', views.semua_akun_view, name='semua_akun'),
    path('akun/<int:pk>/', views.akun_detail_view, name='akun_detail'),
    path('kategori/<str:nama_game>/', views.kategori_view, name='kategori'),
    path('search/', views.search_results_view, name='search_results'),

    # ===================================================
    # URL FITUR TOP UP
    # ===================================================
    path('top-up/', views.topup_index_view, name='topup_index'),
    path('top-up/<int:pk>/', views.topup_detail_view, name='topup_detail'),
    path('top-up/beli/<int:pk>/', views.beli_topup_view, name='beli_topup'), 
    path('top-up/bayar/<uuid:kode_transaksi>/', views.pembayaran_topup_view, name='pembayaran_topup'),
    path('api/apply-coupon-topup/<uuid:kode_transaksi>/', views.apply_coupon_topup_api, name='apply_coupon_topup_api'),

    # ===================================================
    # URL PROFIL & AKSI PENGGUNA
    # ===================================================
    path('profil/', views.profil_view, name='profil'),
    path('favorit/', views.favorit_view, name='favorit'),
    path('favorit/tambah/<int:pk>/', views.tambah_ke_favorit, name='tambah_ke_favorit'),
    path('favorit/hapus/<int:pk>/', views.hapus_dari_favorit, name='hapus_dari_favorit'),
    path('pembelian/riwayat/', views.riwayat_pembelian_view, name='riwayat_pembelian'),
    path('pembelian/lihat/<uuid:kode_transaksi>/', views.lihat_akun_dibeli_view, name='lihat_akun_dibeli'),
    path('pembelian/ulasan/<uuid:kode_transaksi>/', views.tambah_ulasan_view, name='tambah_ulasan'),
    
    # ===================================================
    # URL PROSES PEMBAYARAN (HALAMAN & WEBHOOK)
    # ===================================================
    path('pembelian/beli/<int:pk>/', views.beli_akun_view, name='beli_akun'),
    path('pembelian/bayar/<uuid:kode_transaksi>/', views.pembayaran_view, name='pembayaran'),
    path('webhook/', views.webhook_view, name='webhook'),
    
    # ===================================================
    # API ENDPOINTS (UNTUK JAVASCRIPT/AJAX)
    # ===================================================
    path('api/buat-transaksi/<int:pk>/', views.buat_transaksi_api, name='buat_transaksi_api'),
    path('api/apply-coupon/<uuid:kode_transaksi>/', views.apply_coupon_api, name='apply_coupon_api'),
    path('api/validate-game-id/', views.validate_game_id_api, name='validate_game_id_api'),

    # ===================================================
    # URL DASHBOARD ADMIN
    # ===================================================
    path('dashboard/', views.dashboard_view, name='dashboard'),
]