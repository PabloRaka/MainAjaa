import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Kupon(models.Model):
    kode = models.CharField(max_length=50, unique=True)
    diskon_persen = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    aktif = models.BooleanField(default=True)
    digunakan_oleh = models.ManyToManyField(User, related_name='kupon_yang_digunakan', blank=True)
    
    def __str__(self):
        return f"{self.kode} ({self.diskon_persen}%)"
    
class TopUpProduct(models.Model):
    GAME_CHOICES = [
        ('Mobile Legends', 'Mobile Legends'),
        ('PUBG Mobile', 'PUBG Mobile'),
        # Tambahkan game lain jika perlu
    ]
    CATEGORY_CHOICES = [
        ('Diamonds', 'Diamonds'),
        ('UC', 'UC'),
    ]
    game = models.CharField(max_length=50, choices=GAME_CHOICES)
    nama_paket = models.CharField(max_length=100)
    kategori = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Diamonds')
    deskripsi = models.TextField(blank=True, null=True, help_text="Contoh: Bonus 10 Diamonds, Proses 1-5 Menit, dll.")
    harga = models.DecimalField(max_digits=10, decimal_places=2)
    gambar = models.ImageField(upload_to='topup_images/', blank=True, null=True)

    def __str__(self):
        return f"{self.game} - {self.nama_paket}"
    
class TopUpPembelian(models.Model):
    # Model ini mirip dengan 'Pembelian' tapi khusus untuk Top Up
    STATUS_CHOICES = [
        ('PENDING', 'Menunggu Pembayaran'),
        ('COMPLETED', 'Selesai'),
        ('CANCELED', 'Dibatalkan'),
    ]
    produk = models.ForeignKey(TopUpProduct, on_delete=models.SET_NULL, null=True)
    pembeli = models.ForeignKey(User, on_delete=models.CASCADE)
    kode_transaksi = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    tanggal_pembelian = models.DateTimeField(auto_now_add=True)
    harga_pembelian = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    midtrans_token = models.CharField(max_length=255, null=True, blank=True)
    kupon = models.ForeignKey(Kupon, on_delete=models.SET_NULL, null=True, blank=True)
    harga_asli = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Data game yang diisi pembeli
    game_user_id = models.CharField(max_length=100)
    game_zone_id = models.CharField(max_length=50, blank=True, null=True) # Khusus ML

    def __str__(self):
        return f"TopUp {self.kode_transaksi} oleh {self.pembeli.email}"
    

    
class AkunGaming(models.Model):
    NAMA_GAME_CHOICES = [
        ('Mobile Legends', 'Mobile Legends'),
        ('PUBG Mobile', 'PUBG Mobile'),
        ('Genshin Impact', 'Genshin Impact'),
        ('Haikyuu', 'Haikyuu'),
        ('Black Desert', 'Black Desert'),
    ]

    nama_akun = models.CharField(max_length=100)
    game = models.CharField(max_length=50, choices=NAMA_GAME_CHOICES)
    deskripsi = models.TextField()
    harga = models.DecimalField(max_digits=10, decimal_places=2)
    gambar = models.ImageField(upload_to='akun_images/', blank=True, null=True, help_text="Ini akan menjadi gambar utama atau thumbnail.")
    is_unggulan = models.BooleanField(default=False, help_text="Tandai jika ini adalah akun unggulan untuk ditampilkan di landing page.")
    is_sold = models.BooleanField(default=False)
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    favorit = models.ManyToManyField(User, related_name='akun_favorit', blank=True)
    akun_email = models.CharField(max_length=255, blank=True, null=True)
    akun_password = models.CharField(max_length=255, blank=True, null=True)
    level = models.PositiveIntegerField(default=1, null=True, blank=True)
    highlight = models.TextField(blank=True, null=True, help_text="Isi dengan poin-poin utama, pisahkan dengan baris baru (Enter).")

    def __str__(self):
        return f"{self.nama_akun} - {self.game}"

class GambarAkun(models.Model):
    akun = models.ForeignKey(AkunGaming, on_delete=models.CASCADE, related_name='gambar_tambahan')
    gambar = models.ImageField(upload_to='akun_images/tambahan/')

    def __str__(self):
        return f"Gambar untuk {self.akun.nama_akun}"

class Pembelian(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Menunggu Pembayaran'),
        ('VERIFYING', 'Verifikasi Pembayaran'),
        ('COMPLETED', 'Selesai'),
        ('CANCELED', 'Dibatalkan'),
    ]
    
    akun = models.ForeignKey(AkunGaming, on_delete=models.SET_NULL, null=True)
    pembeli = models.ForeignKey(User, on_delete=models.CASCADE)
    kode_transaksi = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    tanggal_pembelian = models.DateTimeField(auto_now_add=True)
    harga_pembelian = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    bukti_pembayaran = models.ImageField(upload_to='bukti_pembayaran/', blank=True, null=True)
    midtrans_token = models.CharField(max_length=255, null=True, blank=True)
    rating = models.IntegerField(null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)])
    ulasan = models.TextField(blank=True, null=True)
    kupon = models.ForeignKey(Kupon, null=True, blank=True, on_delete=models.SET_NULL)
    harga_asli = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Transaksi {self.kode_transaksi} oleh {self.pembeli.email}"