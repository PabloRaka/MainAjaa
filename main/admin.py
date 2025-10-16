# main/admin.py
from django.contrib import admin
from .models import AkunGaming, GambarAkun, Pembelian, Kupon ,TopUpProduct, TopUpPembelian
from django.conf import settings 
from cryptography.fernet import Fernet 


class GambarAkunInline(admin.TabularInline):
    model = GambarAkun
    extra = 1

@admin.register(AkunGaming)
class AkunGamingAdmin(admin.ModelAdmin):
    list_display = ('nama_akun', 'game', 'harga', 'is_unggulan', 'is_sold', 'dibuat_pada')
    list_filter = ('game', 'is_unggulan', 'is_sold')
    search_fields = ('nama_akun', 'deskripsi')
    list_editable = ('harga', 'is_unggulan', 'is_sold') 
    inlines = [GambarAkunInline]
    
    fieldsets = (
        (None, {
            'fields': ('nama_akun', 'game', 'deskripsi', 'harga', 'gambar', 'is_unggulan', 'is_sold')
        }),
        ('Statistik & Highlight', {
            'fields': ('level', 'highlight')
        }),
        ('Kredensial Akun (Sangat Rahasia)', {
            'fields': ('akun_email', 'akun_password'),
            'description': 'Password akan dienkripsi secara otomatis saat disimpan.'
        }),
    )

    def save_model(self, request, obj, form, change):
        if 'akun_password' in form.changed_data and obj.akun_password:
            try:
                Fernet(settings.ENCRYPTION_KEY).decrypt(obj.akun_password.encode())
            except:
                f = Fernet(settings.ENCRYPTION_KEY)
                encrypted_password = f.encrypt(obj.akun_password.encode())
                obj.akun_password = encrypted_password.decode()
        super().save_model(request, obj, form, change)

@admin.register(Pembelian)
class PembelianAdmin(admin.ModelAdmin):
    list_display = ('kode_transaksi', 'akun', 'pembeli', 'status', 'tanggal_pembelian')
    list_filter = ('status', 'tanggal_pembelian')
    list_editable = ('status',)
    search_fields = ('kode_transaksi', 'pembeli__email')
    readonly_fields = ('kode_transaksi', 'akun', 'pembeli', 'tanggal_pembelian', 'harga_pembelian')

@admin.register(Kupon)
class KuponAdmin(admin.ModelAdmin):
    list_display = ('kode', 'diskon_persen', 'aktif')
    list_filter = ('aktif',)
    search_fields = ('kode',)

@admin.register(TopUpProduct)
class TopUpProductAdmin(admin.ModelAdmin):
    list_display = ('game', 'nama_paket', 'kategori', 'harga')
    list_filter = ('game', 'kategori')
    search_fields = ('nama_paket',)
    fieldsets = (
        (None, {
            'fields': ('game', 'kategori', 'nama_paket', 'harga', 'gambar')
        }),
        ('Informasi Tambahan', {
            'fields': ('deskripsi',)
        }),
    )

@admin.register(TopUpPembelian)
class TopUpPembelianAdmin(admin.ModelAdmin):
    list_display = ('kode_transaksi', 'produk', 'pembeli', 'status', 'tanggal_pembelian')
    list_filter = ('status', 'produk__game')
    search_fields = ('kode_transaksi', 'pembeli__email', 'game_user_id')
    readonly_fields = ('kode_transaksi', 'produk', 'pembeli', 'tanggal_pembelian', 'harga_pembelian')