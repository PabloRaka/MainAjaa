# main/views.py

# Imports dari Django
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.contrib import messages
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from datetime import timedelta
from django.contrib.admin.views.decorators import staff_member_required
from cryptography.fernet import Fernet
import midtransclient
import json
from .models import AkunGaming, Pembelian, Kupon, TopUpProduct, TopUpPembelian 

def topup_detail_view(request, pk):
    produk = get_object_or_404(TopUpProduct, pk=pk)
    
    # Mengambil 5 produk lain dari game yang sama sebagai rekomendasi
    nominal_lainnya = TopUpProduct.objects.filter(game=produk.game).exclude(pk=pk)[:5]
    
    context = {
        'produk': produk,
        'nominal_lainnya': nominal_lainnya,
    }
    return render(request, 'main/topup_detail.html', context)

def topup_index_view(request):
    semua_produk_topup = TopUpProduct.objects.all().order_by('game', 'harga')
    
    context = {
        'produk_list': semua_produk_topup,
    }
    return render(request, 'main/topup_index.html', context)

@login_required
def buat_transaksi_api(request, pk):
    if request.method == 'POST':
        akun = get_object_or_404(AkunGaming, pk=pk)
        if akun.is_sold:
            return JsonResponse({'error': 'Maaf, akun ini sudah tidak tersedia.'}, status=400)

        pembelian_pending = Pembelian.objects.filter(akun=akun, pembeli=request.user, status='PENDING').first()
        if pembelian_pending and pembelian_pending.midtrans_token:
            return JsonResponse({'token': pembelian_pending.midtrans_token})

        pembelian = Pembelian.objects.create(
            akun=akun, pembeli=request.user, harga_pembelian=akun.harga, status='PENDING'
        )
        try:
            snap = midtransclient.Snap(
                is_production=settings.MIDTRANS_IS_PRODUCTION,
                server_key=settings.MIDTRANS_SERVER_KEY,
                client_key=settings.MIDTRANS_CLIENT_KEY
            )
            transaction_details = {
                'order_id': str(pembelian.kode_transaksi),
                'gross_amount': int(pembelian.harga_pembelian)
            }
            transaction = snap.create_transaction({'transaction_details': transaction_details})
            pembelian.midtrans_token = transaction['token']
            pembelian.save()
            return JsonResponse({'token': pembelian.midtrans_token})
        except Exception as e:
            pembelian.delete()
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@login_required
def apply_coupon_api(request, kode_transaksi):
    if request.method == 'POST':
        pembelian = get_object_or_404(Pembelian, kode_transaksi=kode_transaksi, pembeli=request.user)
        data = json.loads(request.body)
        kode_kupon = data.get('kode_kupon')
        try:
            kupon = Kupon.objects.get(kode__iexact=kode_kupon, aktif=True)
            if not pembelian.harga_asli:
                pembelian.harga_asli = pembelian.harga_pembelian
            
            diskon_amount = (pembelian.harga_asli * kupon.diskon_persen) / 100
            harga_baru = pembelian.harga_asli - diskon_amount
            pembelian.harga_pembelian = harga_baru
            pembelian.kupon = kupon
            
            snap = midtransclient.Snap(
                is_production=settings.MIDTRANS_IS_PRODUCTION,
                server_key=settings.MIDTRANS_SERVER_KEY,
                client_key=settings.MIDTRANS_CLIENT_KEY
            )
            transaction_details = {
                'order_id': str(pembelian.kode_transaksi),
                'gross_amount': int(pembelian.harga_pembelian)
            }
            transaction = snap.create_transaction({'transaction_details': transaction_details})
            pembelian.midtrans_token = transaction['token']
            pembelian.save()
            
            return JsonResponse({
                'success': True,
                'message': f"Kupon '{kupon.kode}' berhasil diterapkan!",
                'new_token': pembelian.midtrans_token,
                'harga_asli': f'{pembelian.harga_asli:,.0f}'.replace(',', '.'),
                'diskon_amount': f'{diskon_amount:,.0f}'.replace(',', '.'),
                'harga_baru': f'{pembelian.harga_pembelian:,.0f}'.replace(',', '.'),
            })
        except Kupon.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Kupon tidak valid atau sudah tidak aktif.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

# =====================================================================
# VIEWS HALAMAN STANDAR
# =====================================================================

def landing_page(request):
    akun_unggulan = AkunGaming.objects.filter(is_unggulan=True, is_sold=False).first()
    stats = {'akun_terjual': '15,000+', 'kepuasan': '98%', 'support': '24/7'}
    context = {'akun_unggulan': akun_unggulan, 'stats': stats}
    return render(request, 'main/landing_page.html', context)

def semua_akun_view(request):
    semua_akun = AkunGaming.objects.filter(is_sold=False)
    game_filter = request.GET.get('game', '') 
    sort_by = request.GET.get('sort', 'terbaru') 
    if game_filter:
        semua_akun = semua_akun.filter(game=game_filter)
    if sort_by == 'termurah':
        semua_akun = semua_akun.order_by('harga')
    elif sort_by == 'termahal':
        semua_akun = semua_akun.order_by('-harga')
    else: 
        semua_akun = semua_akun.order_by('-id')
    daftar_game = AkunGaming.objects.values_list('game', flat=True).distinct()
    context = {
        'semua_akun': semua_akun, 'daftar_game': daftar_game,         
        'game_filter_aktif': game_filter, 'sort_by_aktif': sort_by,         
    }
    return render(request, 'main/semua_akun.html', context)

def akun_detail_view(request, pk):
    akun = get_object_or_404(AkunGaming, pk=pk)
    akun_serupa = AkunGaming.objects.filter(game=akun.game, is_sold=False).exclude(pk=pk)[:4]

    ulasan_game = Pembelian.objects.filter(
        akun__game=akun.game, 
        status='COMPLETED'
    ).exclude(rating__isnull=True).order_by('-tanggal_pembelian')
    
    context = { 
        'akun': akun, 
        'akun_serupa': akun_serupa,
        'ulasan_list': ulasan_game, # Kirim daftar ulasan yang baru
        'midtrans_client_key': settings.MIDTRANS_CLIENT_KEY
    }
    return render(request, 'main/akun_detail.html', context)

def kategori_view(request, nama_game):
    akun_list = AkunGaming.objects.filter(game=nama_game, is_sold=False)
    paginator = Paginator(akun_list, 8)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'judul_halaman': f"Kategori: {nama_game}",
        'nama_game_kategori': nama_game,
    }
    return render(request, 'main/kategori.html', context)

def search_results_view(request):
    query = request.GET.get('q')
    if query:
        hasil_list = AkunGaming.objects.filter(is_sold=False).filter(Q(nama_akun__icontains=query) | Q(deskripsi__icontains=query)).distinct()
    else:
        hasil_list = AkunGaming.objects.none()
    paginator = Paginator(hasil_list, 8)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'query': query}
    return render(request, 'main/search_results.html', context)

# =====================================================================
# VIEWS PEMBELIAN & PROFIL PENGGUNA
# =====================================================================

@login_required
def profil_view(request):
    return render(request, 'main/profil.html')

@login_required
def favorit_view(request):
    akun_favorit_pengguna = request.user.akun_favorit.filter(is_sold=False).order_by('-dibuat_pada')
    paginator = Paginator(akun_favorit_pengguna, 8)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'judul_halaman': "Akun Favorit Saya"}
    return render(request, 'main/semua_akun.html', context)

@login_required
def tambah_ke_favorit(request, pk):
    akun = get_object_or_404(AkunGaming, pk=pk)
    akun.favorit.add(request.user)
    messages.success(request, f'"{akun.nama_akun}" telah ditambahkan ke favorit Anda.')
    return redirect('akun_detail', pk=pk)

@login_required
def hapus_dari_favorit(request, pk):
    akun = get_object_or_404(AkunGaming, pk=pk)
    akun.favorit.remove(request.user)
    messages.success(request, f'"{akun.nama_akun}" telah dihapus dari favorit Anda.')
    return redirect('akun_detail', pk=pk)

@login_required
def riwayat_pembelian_view(request):
    # 1. Ambil riwayat pembelian AKUN
    pembelian_akun = list(Pembelian.objects.filter(pembeli=request.user))
    
    # 2. Ambil riwayat pembelian TOP UP
    pembelian_topup = list(TopUpPembelian.objects.filter(pembeli=request.user))
    
    # 3. Gabungkan kedua daftar menjadi satu
    semua_pembelian = pembelian_akun + pembelian_topup
    
    # 4. Urutkan daftar gabungan berdasarkan tanggal pembelian (dari yang terbaru)
    semua_pembelian.sort(key=lambda x: x.tanggal_pembelian, reverse=True)
    
    context = {
        'daftar_pembelian': semua_pembelian, # Kirim daftar yang sudah digabung
        'midtrans_client_key': settings.MIDTRANS_CLIENT_KEY
    }
    return render(request, 'main/riwayat_pembelian.html', context)

@login_required
def pembayaran_view(request, kode_transaksi):
    pembelian = get_object_or_404(Pembelian, kode_transaksi=kode_transaksi, pembeli=request.user)
    if not pembelian.midtrans_token:
        messages.error(request, "Token pembayaran untuk transaksi ini tidak valid.")
        return redirect('riwayat_pembelian')
    diskon_aktif = 0
    if pembelian.kupon and pembelian.harga_asli:
        diskon_aktif = pembelian.harga_asli - pembelian.harga_pembelian
    context = {
        'pembelian': pembelian,
        'midtrans_client_key': settings.MIDTRANS_CLIENT_KEY,
        'diskon_aktif': diskon_aktif,
    }
    return render(request, 'main/pembayaran.html', context)

@login_required
def lihat_akun_dibeli_view(request, kode_transaksi):
    pembelian = get_object_or_404(Pembelian, kode_transaksi=kode_transaksi, pembeli=request.user)
    if pembelian.status != 'COMPLETED':
        messages.error(request, "Pembelian ini belum selesai.")
        return redirect('riwayat_pembelian')

    # PERUBAHAN DI SINI: Tambahkan pengecekan sebelum mendekripsi
    decrypted_password = "" # Siapkan variabel kosong
    if pembelian.akun and pembelian.akun.akun_password:
        try:
            f = Fernet(settings.ENCRYPTION_KEY)
            decrypted_password = f.decrypt(pembelian.akun.akun_password.encode()).decode()
        except Exception as e:
            # Jika ada error saat dekripsi (misal: format salah)
            decrypted_password = "Error: Password tidak dapat didekripsi."
    else:
        # Jika password memang kosong di database
        decrypted_password = "Password tidak diatur untuk akun ini."

    context = {'pembelian': pembelian, 'decrypted_password': decrypted_password}
    return render(request, 'main/lihat_akun_dibeli.html', context)

@login_required
def tambah_ulasan_view(request, kode_transaksi):
    pembelian = get_object_or_404(Pembelian, kode_transaksi=kode_transaksi, pembeli=request.user)
    if pembelian.status != 'COMPLETED':
        messages.error(request, "Anda hanya bisa memberi ulasan untuk transaksi yang sudah selesai.")
        return redirect('riwayat_pembelian')
    if pembelian.rating is not None:
        messages.error(request, "Anda sudah memberikan ulasan untuk transaksi ini.")
        return redirect('riwayat_pembelian')
    if request.method == 'POST':
        rating = request.POST.get('rating')
        ulasan = request.POST.get('ulasan')
        if rating:
            pembelian.rating = int(rating)
            pembelian.ulasan = ulasan
            pembelian.save()
            messages.success(request, "Terima kasih atas ulasan Anda!")
            return redirect('riwayat_pembelian')
    context = {'pembelian': pembelian}
    return render(request, 'main/tambah_ulasan.html', context)
    
# =====================================================================
# WEBHOOK & DASHBOARD
# =====================================================================

@csrf_exempt
def webhook_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            order_id = data.get('order_id')
            transaction_status = data.get('transaction_status')
            fraud_status = data.get('fraud_status')

            # Cek dulu di tabel Pembelian Akun
            pembelian = Pembelian.objects.filter(kode_transaksi=order_id).first()
            # Jika tidak ada, cek di tabel Pembelian Top Up
            pembelian_topup = TopUpPembelian.objects.filter(kode_transaksi=order_id).first()

            transaksi = pembelian or pembelian_topup # Ambil mana yang ditemukan

            if not transaksi:
                return HttpResponse("Transaksi tidak ditemukan.", status=404)

            if transaction_status in ['capture', 'settlement'] and fraud_status == 'accept' and transaksi.status == 'PENDING':
                transaksi.status = 'COMPLETED'
                transaksi.save()

                # Jika ini adalah pembelian akun, tandai akun sebagai terjual
                if isinstance(transaksi, Pembelian) and transaksi.akun:
                    transaksi.akun.is_sold = True
                    transaksi.akun.save()
                
                # ===================================================
                #         CATAT PENGGUNAAN KUPON DI SINI
                # ===================================================
                if transaksi.kupon:
                    transaksi.kupon.digunakan_oleh.add(transaksi.pembeli)
                # ===================================================

            elif transaction_status in ['cancel', 'expire', 'deny']:
                transaksi.status = 'CANCELED'
                transaksi.save()
            
            return HttpResponse("OK", status=200)
        except Exception as e:
            return HttpResponse(f"Webhook Error: {e}", status=400)
    return HttpResponse("Metode tidak diizinkan.", status=405)
    
@staff_member_required
def dashboard_view(request):
    hari_ini = timezone.now().date()

    # 1. Hitung data dari penjualan AKUN
    penjualan_akun_hari_ini = Pembelian.objects.filter(status='COMPLETED', tanggal_pembelian__date=hari_ini)
    jumlah_akun_terjual_hari_ini = penjualan_akun_hari_ini.count()
    pendapatan_akun_hari_ini = penjualan_akun_hari_ini.aggregate(Sum('harga_pembelian'))['harga_pembelian__sum'] or 0

    # 2. Hitung data dari penjualan TOP UP
    penjualan_topup_hari_ini = TopUpPembelian.objects.filter(status='COMPLETED', tanggal_pembelian__date=hari_ini)
    jumlah_topup_hari_ini = penjualan_topup_hari_ini.count()
    pendapatan_topup_hari_ini = penjualan_topup_hari_ini.aggregate(Sum('harga_pembelian'))['harga_pembelian__sum'] or 0

    # 3. Gabungkan total pendapatan
    total_pendapatan_hari_ini = pendapatan_akun_hari_ini + pendapatan_topup_hari_ini
    
    # 4. Statistik lainnya
    akun_tersedia = AkunGaming.objects.filter(is_sold=False).count()
    
    context = {
        'total_pendapatan_hari_ini': total_pendapatan_hari_ini,
        'jumlah_akun_terjual_hari_ini': jumlah_akun_terjual_hari_ini, # Data spesifik untuk akun
        'jumlah_topup_hari_ini': jumlah_topup_hari_ini,               # Data spesifik untuk top up
        'akun_tersedia': akun_tersedia,
    }
    return render(request, 'main/dashboard.html', context)

# =====================================================================
# VIEWS LAMA (BISA DIHAPUS JIKA SUDAH TIDAK DIPAKAI DI URLS.PY)
# =====================================================================

@login_required
def beli_akun_view(request, pk):
    akun = get_object_or_404(AkunGaming, pk=pk)
    if akun.is_sold:
        messages.error(request, "Maaf, akun ini sudah tidak tersedia.")
        return redirect('akun_detail', pk=pk)

    # Cek jika sudah ada transaksi PENDING, langsung arahkan ke pembayaran
    pembelian_pending = Pembelian.objects.filter(akun=akun, pembeli=request.user, status='PENDING').first()
    if pembelian_pending:
        return redirect('pembayaran', kode_transaksi=pembelian_pending.kode_transaksi)

    # Jika belum ada, buat transaksi baru
    pembelian = Pembelian.objects.create(
        akun=akun, pembeli=request.user, harga_pembelian=akun.harga, status='PENDING'
    )

    try:
        # Buat token Midtrans
        snap = midtransclient.Snap(
            is_production=settings.MIDTRANS_IS_PRODUCTION,
            server_key=settings.MIDTRANS_SERVER_KEY,
            client_key=settings.MIDTRANS_CLIENT_KEY
        )
        transaction_details = {
            'order_id': str(pembelian.kode_transaksi),
            'gross_amount': int(pembelian.harga_pembelian)
        }
        transaction = snap.create_transaction({'transaction_details': transaction_details})
        
        # Simpan token ke database
        pembelian.midtrans_token = transaction['token']
        pembelian.save()
        
        # Arahkan ke halaman pembayaran
        return redirect('pembayaran', kode_transaksi=pembelian.kode_transaksi)
        
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan saat membuat transaksi: {e}")
        pembelian.delete()
        return redirect('akun_detail', pk=pk)

@login_required
def apply_coupon_view(request, kode_transaksi):
    # Logika lama ini bisa dihapus jika semua kupon sudah lewat API
    messages.info(request, "Silakan gunakan form kupon interaktif.")
    return redirect('pembayaran', kode_transaksi=kode_transaksi)

@login_required
def pembayaran_sukses_view(request, kode_transaksi):
    # View ini tidak lagi dipanggil oleh Snap.js, tapi aman untuk disimpan
    pembelian = get_object_or_404(Pembelian, kode_transaksi=kode_transaksi, pembeli=request.user)
    messages.success(request, f"Pembayaran untuk akun '{pembelian.akun.nama_akun}' berhasil!")
    return redirect('riwayat_pembelian')

@login_required
def instruksi_pembayaran_view(request, kode_transaksi):
    # View ini kemungkinan tidak terpakai jika semua pembayaran lewat Midtrans
    pembelian = get_object_or_404(Pembelian, kode_transaksi=kode_transaksi, pembeli=request.user)
    context = {'pembelian': pembelian}
    return render(request, 'main/instruksi_pembayaran.html', context)

@csrf_exempt
def validate_game_id_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        game = data.get('game')
        user_id = data.get('user_id')
        zone_id = data.get('zone_id')

        # Ini adalah simulasi. Di dunia nyata, Anda akan memanggil API game di sini.
        if game == 'Mobile Legends':
            if user_id and zone_id and user_id.isdigit() and zone_id.isdigit():
                # Berpura-pura berhasil dan mengembalikan nama acak
                return JsonResponse({'success': True, 'username': f'PemainML_{user_id}'})
            else:
                return JsonResponse({'success': False, 'error': 'ID atau Server tidak valid.'}, status=400)
        
        elif game == 'PUBG Mobile':
            if user_id and user_id.isdigit() and len(user_id) > 5:
                # Berpura-pura berhasil
                return JsonResponse({'success': True, 'username': f'PemainPUBG_{user_id}'})
            else:
                return JsonResponse({'success': False, 'error': 'ID Pemain tidak valid.'}, status=400)
        
    return JsonResponse({'success': False, 'error': 'Request tidak valid.'}, status=400)

@login_required
def beli_topup_view(request, pk):
    """
    Menangani form submission dari halaman topup_detail.
    Membuat transaksi TopUpPembelian dan mengarahkan ke halaman pembayaran.
    """
    produk = get_object_or_404(TopUpProduct, pk=pk)
    if request.method == 'POST':
        user_id = request.POST.get('game_user_id')
        zone_id = request.POST.get('game_zone_id', '') # Ambil zone_id jika ada

        if not user_id:
            messages.error(request, "ID Pemain wajib diisi.")
            return redirect('topup_detail', pk=produk.pk)

        # Buat objek pembelian di database
        pembelian = TopUpPembelian.objects.create(
            produk=produk,
            pembeli=request.user,
            harga_pembelian=produk.harga,
            status='PENDING',
            game_user_id=user_id,
            game_zone_id=zone_id
        )

        try:
            # Buat transaksi Midtrans
            snap = midtransclient.Snap(
                is_production=settings.MIDTRANS_IS_PRODUCTION,
                server_key=settings.MIDTRANS_SERVER_KEY,
                client_key=settings.MIDTRANS_CLIENT_KEY
            )
            transaction_details = {
                'order_id': str(pembelian.kode_transaksi),
                'gross_amount': int(pembelian.harga_pembelian)
            }
            transaction = snap.create_transaction({'transaction_details': transaction_details})
            
            pembelian.midtrans_token = transaction['token']
            pembelian.save()
            
            # Arahkan ke halaman pembayaran khusus Top Up
            return redirect('pembayaran_topup', kode_transaksi=pembelian.kode_transaksi)

        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {e}")
            pembelian.delete()
            return redirect('topup_detail', pk=produk.pk)
            
    return redirect('topup_detail', pk=produk.pk)


@login_required
def pembayaran_topup_view(request, kode_transaksi):
    pembelian = get_object_or_404(TopUpPembelian, kode_transaksi=kode_transaksi, pembeli=request.user)
    
    # HITUNG DISKON DI SINI
    diskon_aktif = 0
    if pembelian.kupon and pembelian.harga_asli:
        diskon_aktif = pembelian.harga_asli - pembelian.harga_pembelian

    context = {
        'pembelian': pembelian,
        'midtrans_client_key': settings.MIDTRANS_CLIENT_KEY,
        'diskon_aktif': diskon_aktif, # <-- Kirim hasil perhitungan ke template
    }
    return render(request, 'main/pembayaran_topup.html', context)

@login_required
def apply_coupon_api(request, kode_transaksi):
    if request.method == 'POST':
        pembelian = get_object_or_404(Pembelian, kode_transaksi=kode_transaksi, pembeli=request.user)
        data = json.loads(request.body)
        kode_kupon = data.get('kode_kupon')

        try:
            kupon = Kupon.objects.get(kode__iexact=kode_kupon, aktif=True)

            # PENGECEKAN BARU: Pastikan kupon belum pernah digunakan oleh user ini
            if kupon.digunakan_oleh.filter(id=request.user.id).exists():
                return JsonResponse({'success': False, 'error': 'Kupon ini sudah pernah Anda gunakan.'}, status=400)

            if not pembelian.harga_asli:
                pembelian.harga_asli = pembelian.harga_pembelian
            
            diskon_amount = (pembelian.harga_asli * kupon.diskon_persen) / 100
            harga_baru = pembelian.harga_asli - diskon_amount
            
            pembelian.harga_pembelian = harga_baru
            pembelian.kupon = kupon
            
            # Buat token Midtrans BARU dengan harga yang sudah didiskon
            snap = midtransclient.Snap(
                is_production=settings.MIDTRANS_IS_PRODUCTION,
                server_key=settings.MIDTRANS_SERVER_KEY,
                client_key=settings.MIDTRANS_CLIENT_KEY
            )
            transaction_details = {
                'order_id': str(pembelian.kode_transaksi),
                'gross_amount': int(pembelian.harga_pembelian)
            }
            transaction = snap.create_transaction({'transaction_details': transaction_details})
            pembelian.midtrans_token = transaction['token']
            pembelian.save()
            
            return JsonResponse({
                'success': True,
                'message': f"Kupon '{kupon.kode}' berhasil diterapkan!",
                'new_token': pembelian.midtrans_token,
                'harga_asli': f'{pembelian.harga_asli:,.0f}'.replace(',', '.'),
                'diskon_amount': f'{diskon_amount:,.0f}'.replace(',', '.'),
                'harga_baru': f'{pembelian.harga_pembelian:,.0f}'.replace(',', '.'),
            })

        except Kupon.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Kupon tidak valid atau sudah tidak aktif.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
            
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@login_required
def apply_coupon_topup_api(request, kode_transaksi):
    if request.method == 'POST':
        pembelian = get_object_or_404(TopUpPembelian, kode_transaksi=kode_transaksi, pembeli=request.user)
        data = json.loads(request.body)
        kode_kupon = data.get('kode_kupon')

        try:
            kupon = Kupon.objects.get(kode__iexact=kode_kupon, aktif=True)
            
            # PENGECEKAN BARU: Pastikan kupon belum pernah digunakan oleh user ini
            if kupon.digunakan_oleh.filter(id=request.user.id).exists():
                return JsonResponse({'success': False, 'error': 'Kupon ini sudah pernah Anda gunakan.'}, status=400)

            if not pembelian.harga_asli:
                pembelian.harga_asli = pembelian.harga_pembelian
            
            diskon_amount = (pembelian.harga_asli * kupon.diskon_persen) / 100
            harga_baru = pembelian.harga_asli - diskon_amount
            
            pembelian.harga_pembelian = harga_baru
            pembelian.kupon = kupon
            
            # Buat token Midtrans BARU dengan harga yang sudah didiskon
            snap = midtransclient.Snap(
                is_production=settings.MIDTRANS_IS_PRODUCTION,
                server_key=settings.MIDTRANS_SERVER_KEY,
                client_key=settings.MIDTRANS_CLIENT_KEY
            )
            transaction_details = {
                'order_id': str(pembelian.kode_transaksi),
                'gross_amount': int(pembelian.harga_pembelian)
            }
            transaction = snap.create_transaction({'transaction_details': transaction_details})
            pembelian.midtrans_token = transaction['token']
            pembelian.save()
            
            return JsonResponse({
                'success': True,
                'message': f"Kupon '{kupon.kode}' berhasil diterapkan!",
                'new_token': pembelian.midtrans_token,
                'harga_asli': f'{pembelian.harga_asli:,.0f}'.replace(',', '.'),
                'diskon_amount': f'{diskon_amount:,.0f}'.replace(',', '.'),
                'harga_baru': f'{pembelian.harga_pembelian:,.0f}'.replace(',', '.'),
            })
            
        except Kupon.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Kupon tidak valid atau sudah tidak aktif.'}, status=400)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
            
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)