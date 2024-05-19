from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404
from django.urls import reverse
from . import models
from django.db.models import Sum
from datetime import datetime
from datetime import timedelta
from django.db.models.functions import ExtractYear


def view_gudang(request):
    getretur = (
        models.TransaksiGudang.objects.filter(KeteranganACC=False)
        .filter(jumlah__lt=0)
        .order_by("tanggal")
    )

    getkeluar = (
        models.TransaksiGudang.objects.filter(KeteranganACC=False)
        .filter(jumlah__gt=0)
        .order_by("tanggal")
    )

    akhir = datetime.now()

    mulai = akhir - timedelta(days=30)
    print(mulai)
    allspk = models.SPK.objects.filter(
        Tanggal__range=(mulai, akhir), StatusAktif = True
    ).order_by("Tanggal")

    for i in allspk :
        if i.StatusDisplay == 0 :
            detailspk = models.DetailSPK.objects.filter(NoSPK = i.id)
            i.detailspk = detailspk
        else :
            detailspk = models.DetailSPKDisplay.objects.filter(NoSPK = i.id)
            i.detailspk = detailspk

    for a in getretur:
        a.jumlah = a.jumlah * -1
    for i in getretur:
        i.tanggal = i.tanggal.strftime("%d-%m-%Y")
    for i in getkeluar:
        i.tanggal = i.tanggal.strftime("%d-%m-%Y")
    for i in allspk:
        i.Tanggal = i.Tanggal.strftime("%d-%m-%Y")

    if len(getretur) == 0:
        messages.info(request, "Tidak ada barang retur yang belum ACC")
    if len(getkeluar) == 0:
        messages.info(request, "Tidak ada barang keluar yang belum ACC")
    if len(allspk) == 0:
        messages.warning(request, "Tidak ada SPK selama 30 hari terakhir")

    return render(
        request,
        "gudang/viewgudang.html",
        {
            "getkeluar": getkeluar,
            "getretur": getretur,
            "allspk": allspk,
        },
    )


def masuk_gudang(request):
    datasjb = models.DetailSuratJalanPembelian.objects.all().order_by(
        "NoSuratJalan__Tanggal"
    )
    date = request.GET.get("date")
    if date is not None:
        datasjb = models.DetailSuratJalanPembelian.objects.filter(
            NoSuratJalan__Tanggal=date
        ).order_by("NoSuratJalan__Tanggal")

    for i in datasjb:
        i.NoSuratJalan.Tanggal = i.NoSuratJalan.Tanggal.strftime("%d-%m-%Y")

    if len(datasjb) == 0:
        messages.info(request, "Tidak ada barang masuk ke gudang")

    return render(
        request,
        "gudang/baranggudang.html",
        {
            "datasjb": datasjb,
            "date": date,
        },
    )


def add_gudang(request):
    if request.method == "GET":
        detailsjp = models.DetailSuratJalanPembelian.objects.all()
        detailsj = models.SuratJalanPembelian.objects.all()
        getproduk = models.Produk.objects.all()

        return render(
            request,
            "gudang/addgudang.html",
            {"detailsjp": detailsjp, "detailsj": detailsj, "getproduk": getproduk},
        )
    if request.method == "POST":
        print(request.POST)
        kode = request.POST.getlist("kodeproduk")
        # print(kode[1])
        # print(type(request.POST['kodeproduk']))
        nosuratjalan = request.POST["nosuratjalan"]
        tanggal = request.POST["tanggal"]
        supplier = request.POST["supplier"]
        nomorpo = request.POST["nomorpo"]
        if nomorpo == "":
            nomorpo = "-"
        if supplier == "":
            supplier = "-"
        nosuratjalanobj = models.SuratJalanPembelian(
            NoSuratJalan=nosuratjalan, Tanggal=tanggal, supplier=supplier, PO=nomorpo
        )
        nosuratjalanobj.save()
        nosuratjalanobj = models.SuratJalanPembelian.objects.get(
            NoSuratJalan=nosuratjalan
        )
        for kodeproduk, jumlah in zip(
            request.POST.getlist("kodeproduk"), request.POST.getlist("jumlah")
        ):
            # print(kodeproduk)
            newprodukobj = models.DetailSuratJalanPembelian(
                KodeProduk=models.Produk.objects.get(KodeProduk=kodeproduk),
                Jumlah=jumlah,
                KeteranganACC=0,
                Harga=0,
                NoSuratJalan=nosuratjalanobj,
            )
            models.transactionlog(
                user="Gudang",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"No Surat Jalan : {newprodukobj.NoSuratJalan} Kode Barang : {newprodukobj.KodeProduk}",
            ).save()
            newprodukobj.save()

        return redirect("baranggudang")


def add_gudang2(request):
    if request.method == "GET":
        detailsjb = models.SuratJalanPembelian.objects.all()
        return render(request, "gudang/addgudang2.html", {"detailsj": detailsjb})
    if request.method == "POST":
        no_surat = request.POST["no_surat"]
        tanggal = request.POST["Tanggal"]
        supplier = request.POST["supplier"]
        datasjb = models.SuratJalanPembelian(
            NoSuratJalan=no_surat,
            Tanggal=tanggal,
            supplier=supplier,
        ).save()
        return redirect("baranggudang")


def accgudang(request, id):
    datagudang = models.TransaksiGudang.objects.get(IDDetailTransaksiGudang=id)
    datagudang.KeteranganACC = True
    datagudang.save()
    return redirect("viewgudang")


def update_gudang(request, id):
    datasjp = models.DetailSuratJalanPembelian.objects.get(IDDetailSJPembelian=id)
    datasjp2 = models.DetailSuratJalanPembelian.objects.all()
    datasj = models.SuratJalanPembelian.objects.all()
    getproduk = models.Produk.objects.all()
    datasjp_getobj = models.SuratJalanPembelian.objects.get(
        NoSuratJalan=datasjp.NoSuratJalan.NoSuratJalan
    )
    detailsjp_filtered = models.DetailSuratJalanPembelian.objects.filter(
        NoSuratJalan=datasjp_getobj.NoSuratJalan
    )
    if request.method == "GET":
        # tanggal = datetime.strftime(datasjp.NoSuratJalan.Tanggal, '%Y-%m-%d')
        # jumlah = datasjp.Jumlah
        # kodeproduk = datasjp.KodeProduk
        # print(kodeproduk)
        # print(getproduk)
        # return render(request, 'gudang/updategudang.html', {
        #     'datasjp' : datasjp,
        #     'datasjp2' : datasjp2,
        #     'datasj' : datasj,
        #     'getproduk' : getproduk,
        #     'kodeproduk' : kodeproduk,
        #     'tanggal' : tanggal,
        #     'jumlah' : jumlah,
        # })

        return render(
            request,
            "gudang/updategudang2.html",
            {
                "datasjp": datasjp_getobj,
                "detailsjp": datasjp,
                "datasj": datasj,
                "detailsj": datasjp2,
                "tanggal": datetime.strftime(datasjp_getobj.Tanggal, "%Y-%m-%d"),
            },
        )

    else:
        tanggal = request.POST["tanggal"]
        print(request.POST)
        kode_produk = request.POST.get("kodeproduk")
        kode_produkobj = models.Produk.objects.get(KodeProduk=kode_produk)
        jumlah = request.POST["jumlah"]

        datasjp.KodeProduk = kode_produkobj
        datasjp.Jumlah = jumlah
        datasjp.KeteranganACC = datasjp.KeteranganACC
        datasjp.Harga = datasjp.Harga
        datasjp.NoSuratJalan = datasjp.NoSuratJalan
        datasjp.NoSuratJalan.Tanggal = tanggal
        datasjp.save()
        datasjp.NoSuratJalan.save()
        models.transactionlog(
                user="Gudang",
                waktu=datetime.now(),
                jenis="Update",
                pesan=f"Kode Barang Lama : {datasjp.KodeProduk} Jumlah Lama : {datasjp.Jumlah} Kode Barang Baru : {kode_produk} Jumlah Baru : {jumlah}",
            ).save()

        return redirect("baranggudang")


def delete_gudang(request, id):
    datasbj = models.DetailSuratJalanPembelian.objects.get(IDDetailSJPembelian=id)
    models.transactionlog(
                user="Gudang",
                waktu=datetime.now(),
                jenis="Delete",
                pesan=f"No Surat Jalan : {datasbj.NoSuratJalan} Kode Barang : {datasbj.KodeProduk}",
            ).save()
    datasbj.delete()
    return redirect("baranggudang")


def rekap_gudang(request):
    dict_semua = []
    listproduk = []
    listjumlah = []
    listnama = []
    satuan = []
    dataproduk = models.Produk.objects.all()
    datenow = datetime.now()
    tahun = datenow.year
    mulai = datetime(year=tahun, month=1, day=1)

    for i in dataproduk :
        listproduk.append(i.KodeProduk)
        listnama.append(i.NamaProduk)
        satuan.append(i.unit)

        datasjb = (
        models.DetailSuratJalanPembelian.objects.filter(NoSuratJalan__Tanggal__range = (mulai, datenow),KodeProduk = i).values(
            "KodeProduk",
            "KodeProduk__NamaProduk",
            "KodeProduk__unit",
        )
        .annotate(kuantitas=Sum("Jumlah"))
        .order_by()
    )

        datagudang = (
                models.TransaksiGudang.objects.filter(tanggal__range = (mulai, datenow) ,KodeProduk = i).values("KodeProduk")
                .annotate(kuantitas=Sum("jumlah"))
                .order_by()
            )
        date = request.GET.get("date")

        if date is not None:
            datasjb = (
                models.DetailSuratJalanPembelian.objects.filter(
                    NoSuratJalan__Tanggal__range=(mulai, date),
                    KodeProduk = i
                )
                .values(
                    "KodeProduk",
                    "KodeProduk__NamaProduk",
                    "KodeProduk__unit",
                )
                .annotate(kuantitas=Sum("Jumlah"))
                .order_by()
            )

            datagudang = (
                models.TransaksiGudang.objects.filter(tanggal__range = (mulai, date), KodeProduk = i).values("KodeProduk")
                .annotate(kuantitas=Sum("jumlah"))
                .order_by()
            )
        if len(datasjb) == 0 and len(datagudang) == 0:
            listjumlah.append(0)
        # print(datasjb)
        # print(datagudang)

        if len(datasjb) > 0 or len(datagudang) > 0 :    
            for item in datasjb:
                kode_produk = item["KodeProduk"]
                try:
                    corresponding_gudang_item = datagudang.get(KodeProduk=kode_produk)
                    item["kuantitas"] -= corresponding_gudang_item["kuantitas"]
                    
                    listjumlah.append(item["kuantitas"])
                    
                    if item["kuantitas"] + corresponding_gudang_item["kuantitas"] < 0:
                        messages.info("Kuantitas gudang menjadi minus")

                except models.TransaksiGudang.DoesNotExist:
                    listjumlah.append(item["kuantitas"])
        
            if len(datasjb) == 0 :
                for item in datagudang :
                    listjumlah.append(item["kuantitas"])
                    print("adaaaa")

    # print(listproduk)
    print(listjumlah)
    for produk,jumlah,nama,unit in zip(listproduk, listjumlah, listnama, satuan) :
        dict_semua.append(
            {
                "produk" : produk,
                "jumlah" : jumlah,
                "nama" : nama,
                "unit" : unit   
            }
        )

    return render(
        request,
        "gudang/rekapgudang.html",
        {
            "datasjb": datasjb,
            "date": date,
            "dict_semua" : dict_semua
        },
    )


def detail_barang(request):
    datagudang = models.TransaksiGudang.objects.all()
    dataproduk = models.Produk.objects.all()
    if len(request.GET) == 0:
        return render(
            request,
            "gudang/detailbarang.html",
            {
                "datagudang": datagudang,
                "dataproduk": dataproduk,
            },
        )

    else:
        dict_semua = []
        list_masuk = []
        list_keluar = []
        list_sisa = []
        input_kode = request.GET.get("input_kode")
        input_tahun = request.GET.get("input_tahun")
        datagudang2 = (
            models.TransaksiGudang.objects.filter(KodeProduk=input_kode)
            .filter(tanggal__year=input_tahun)
            .order_by("tanggal")
        )
        saldo_awal = (
            models.SaldoAwalBahanBaku.objects.filter(IDBahanBaku=input_kode)
            .filter(Tanggal__year=input_tahun)
            .order_by("Tanggal")
        )
        datasjp = (
            models.DetailSuratJalanPembelian.objects.filter(KodeProduk=input_kode)
            .filter(NoSuratJalan__Tanggal__year=input_tahun)
            .order_by("NoSuratJalan__Tanggal")
        )
        tanggalgudang = list(datagudang2.values_list("tanggal", flat=True).distinct())
        tanggalgudang2 = list(
            datasjp.values_list("NoSuratJalan__Tanggal", flat=True).distinct()
        )
        tanggalgudang3 = list(saldo_awal.values_list("Tanggal", flat=True).distinct())

        tanggaltotal = tanggalgudang + tanggalgudang2
        tanggaltotal = sorted(list(set(tanggaltotal)))

        if len(tanggaltotal) == 0:
            messages.error(
                request, "Tidak ada barang masuk ke gudang, keluar, dan retur"
            )

        saldo_awal = 0
        data_saldoawal = models.SaldoAwalBahanBaku.objects.filter(
            IDBahanBaku=input_kode
        )
        for i in data_saldoawal:
            print(i.Jumlah)
            saldo_awal += i.Jumlah

        saldo_dummy = saldo_awal
        for i in tanggaltotal:
            keluar = 0
            masuk = 0

            data_gudangobj = models.TransaksiGudang.objects.filter(tanggal=i).filter(
                KodeProduk=input_kode
            )
            data_sjp = models.DetailSuratJalanPembelian.objects.filter(
                NoSuratJalan__Tanggal=i
            ).filter(KodeProduk=input_kode)
            data_saldoawal = models.SaldoAwalBahanBaku.objects.filter(Tanggal=i).filter(
                IDBahanBaku=input_kode
            )

            if len(data_gudangobj) > 0:
                for j in data_gudangobj:
                    if j.jumlah > 0:
                        keluar += j.jumlah
                    else:
                        masuk += j.jumlah * -1

            if len(data_sjp) > 0:
                for j in data_sjp:
                    masuk += j.Jumlah

            saldo_dummy += masuk - keluar

            if saldo_dummy + masuk - keluar < 0:
                messages.warning(
                    request,
                    "Sisa stok menjadi negatif pada tanggal {}.\nCek kembali mutasi barang".format(
                        i
                    ),
                )

            list_keluar.append(keluar)
            list_masuk.append(masuk)
            list_sisa.append(saldo_dummy)

        for tanggal, masuk, keluar, sisa in zip(
            tanggaltotal, list_masuk, list_keluar, list_sisa
        ):
            tanggal = tanggal.strftime("%d-%m-%Y")
            dict_semua.append(
                {
                    "tanggaltotal": tanggal,
                    "masuk": masuk,
                    "keluar": keluar,
                    "sisa": sisa,
                }
            )

        return render(
            request,
            "gudang/detailbarang.html",
            {
                "datagudang2": datagudang2,
                "dataproduk": dataproduk,
                "list_keluar": list_keluar,
                "dict_semua": dict_semua,
                "kodeproduk": input_kode,
                "saldoawal": saldo_awal,
                "input_tahun": input_tahun,
                "datasjp": datasjp,
            },
        )


def barang_keluar(request):
    datalokasi = models.Lokasi.objects.all()
    data = models.TransaksiGudang.objects.filter(jumlah__gt=0).order_by("tanggal")
    for i in data:
        i.tanggal = i.tanggal.strftime("%d-%m-%Y")
    print(data)
    if len(request.GET) == 0:
        return render(
            request,
            "gudang/barangkeluar.html",
            {
                "datalokasi": datalokasi,
                "data": data,
            },
        )
    else:
        date = request.GET.get("mulai")
        date2 = request.GET.get("akhir")
        lok = request.GET.get("lokasi")
        if date is not None:
            data = data.filter(
                tanggal__range=(date, date2), Lokasi__NamaLokasi=lok, jumlah__gt=0
            ).order_by("tanggal")

        for i in data:
            i.tanggal = i.tanggal.strftime("%d-%m-%Y")

        if len(data) == 0:
            messages.error(request, "Tidak ada barang keluar dari gudang")

        return render(
            request,
            "gudang/barangkeluar.html",
            {
                "datalokasi": datalokasi,
                "data": data,
                "date": date,
                "date2": date2,
                "lok": lok,
            },
        )


def barang_retur(request):
    datalokasi = models.Lokasi.objects.all()
    data = models.TransaksiGudang.objects.filter(jumlah__lt=0).order_by("tanggal")
    for i in data:
        i.tanggal = i.tanggal.strftime("%d-%m-%Y")
    print(data)
    if len(request.GET) == 0:
        return render(
            request,
            "gudang/barangretur.html",
            {
                "datalokasi": datalokasi,
                "data": data,
            },
        )
    else:
        date = request.GET.get("mulai")
        date2 = request.GET.get("akhir")
        lok = request.GET.get("lokasi")
        if date is not None:
            data = data.filter(
                tanggal__range=(date, date2), Lokasi__NamaLokasi=lok, jumlah__lt=0
            ).order_by("tanggal")

        for i in data:
            i.jumlah = i.jumlah * -1
            i.tanggal = i.tanggal.strftime("%d-%m-%Y")

        if len(data) == 0:
            messages.error(request, "Tidak ada barang keluar dari gudang")

        return render(
            request,
            "gudang/barangretur.html",
            {
                "datalokasi": datalokasi,
                "data": data,
                "date": date,
                "date2": date2,
                "lok": lok,
            },
        )


def accgudang2(request, id, date, date2, lok):
    datagudang = models.TransaksiGudang.objects.get(IDDetailTransaksiGudang=id)
    datagudang.KeteranganACC = True
    datagudang.save()

    return redirect(f"/gudang/barangretur/?mulai={date}&akhir={date2}&lokasi={lok}")


def accgudang3(request, id, date, date2, lok):
    datagudang = models.TransaksiGudang.objects.get(IDDetailTransaksiGudang=id)
    datagudang.KeteranganACC = True
    datagudang.save()

    return redirect(f"/gudang/barangkeluar/?mulai={date}&akhir={date2}&lokasi={lok}")


def spk(request):
    dataspk = models.SPK.objects.all().order_by("-Tanggal")
    for i in dataspk:
        i.Tanggal = i.Tanggal.strftime("%d-%m-%Y")
    return render(request, "gudang/spkgudang.html", {"dataspk": dataspk})


def tracking_spk(request, id):
    dataartikel = models.Artikel.objects.all()
    dataspk = models.SPK.objects.get(id=id)
    datadetail = models.DetailSPK.objects.filter(NoSPK=dataspk.id)

    # Data SPK terkait yang telah di request ke Gudang
    transaksigudangobj = models.TransaksiGudang.objects.filter(
        DetailSPK__NoSPK=dataspk.id, jumlah__gte=0
    )

    # Data SPK Terkait yang telah jadi di FG
    transaksiproduksiobj = models.TransaksiProduksi.objects.filter(
        DetailSPK__NoSPK=dataspk.id, Jenis="Mutasi"
    )

    # Data SPK Terkait yang telah dikirim
    sppbobj = models.DetailSPPB.objects.filter(DetailSPK__NoSPK=dataspk.id)

    if request.method == "GET":
        tanggal = datetime.strftime(dataspk.Tanggal, "%Y-%m-%d")

        return render(
            request,
            "gudang/trackingspk.html",
            {
                "data": dataartikel,
                "dataspk": dataspk,
                "datadetail": datadetail,
                "tanggal": tanggal,
                "transaksigudang": transaksigudangobj,
                "transaksiproduksi": transaksiproduksiobj,
                "transaksikeluar": sppbobj,
            },
        )


def cobaform(request):
    databahanbaku = models.Produk.objects.all()
    if request.method == "POST":
        print(request.POST)
        nomor_nota = request.POST.get("nomor_nota")
        produk_list = request.POST.getlist("produk[]")
        print(len(produk_list))
        print(produk_list)

    return render(request, "gudang/cobaform.html", {"data": databahanbaku})


def addgudang3(request):
    if request.method == "GET":
        detailspk = models.DetailSPK.objects.all()
        getproduk = models.Produk.objects.all()
        getlokasi = models.Lokasi.objects.all()
        return render(
            request,
            "gudang/addgudang3.html",
            {"detailspk": detailspk, "getproduk": getproduk, "getlokasi": getlokasi},
        )
    if request.method == "POST":
        kode = request.POST["kodeproduk"]
        tanggal = request.POST["tanggal"]
        keterangan = request.POST["keterangan"]
        jumlah = request.POST["jumlah"]
        acc = True
        lokasi = request.POST["lokasi"]
        print(lokasi)

        savetrans = models.TransaksiGudang(
            KodeProduk=models.Produk.objects.get(KodeProduk=kode),
            keterangan=keterangan,
            jumlah=jumlah,
            tanggal=tanggal,
            KeteranganACC=acc,
            Lokasi=models.Lokasi.objects.get(NamaLokasi=lokasi),
            DetailSPK=None,
        )
        models.transactionlog(
                user="Gudang",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"Kode Barang : {savetrans.KodeProduk} Jumlah : {savetrans.jumlah} Lokasi : {lokasi}",
            ).save()
        savetrans.save()

        return redirect("barangkeluar")


def read_produk(request):
    produkobj = models.Produk.objects.all()
    return render(request, "gudang/read_produk.html", {"produkobj": produkobj})


def update_produk_gudang(request, id):
    produkobj = models.Produk.objects.get(pk=id)
    if request.method == "GET":
        return render(request, "gudang/update_produk.html", {"produkobj": produkobj})
    else:
        print(request.POST)
        keterangan_produk = request.POST["keterangan_produk"]
        jumlah_minimal = request.POST["jumlah_minimal"]
        produkobj.keteranganGudang = keterangan_produk
        produkobj.Jumlahminimal = jumlah_minimal
        produkobj.save()
        models.transactionlog(
                user="Gudang",
                waktu=datetime.now(),
                jenis="Update",
                pesan=f"Jumlah Minimal : {produkobj.Jumlahminimal} Keterangan : {produkobj.keteranganGudang}",
            ).save()
        return redirect("readprodukgudang")

def read_saldoawal(request) :
    dataproduk = models.SaldoAwalBahanBaku.objects.filter(IDLokasi__NamaLokasi = "Gudang").order_by("-Tanggal")
    for i in dataproduk:
        i.Tanggal = i.Tanggal.strftime("%d-%m-%Y")

    return render(
        request, "gudang/read_saldoawalbahan.html", {"dataproduk": dataproduk}
    )

def addsaldo(request) :
    databarang = models.Produk.objects.all()
    datalokasi = models.Lokasi.objects.all()
    if request.method == "GET":
        return render(
            request,
            "gudang/addsaldobahan.html",
            {"nama_lokasi": datalokasi, "databarang": databarang},
        )
    else:
        kodeproduk = request.POST["produk"]
        lokasi = request.POST["nama_lokasi"]
        jumlah = request.POST["jumlah"]
        harga = request.POST["harga"]
        tanggal = request.POST["tanggal"]

        # Ubah format tanggal menjadi YYYY-MM-DD
        tanggal_formatted = datetime.strptime(tanggal, "%Y-%m-%d")
        # Periksa apakah entri sudah ada
        existing_entry = models.SaldoAwalBahanBaku.objects.filter(
            Tanggal__year=tanggal_formatted.year,
            IDBahanBaku__KodeProduk=kodeproduk,
            IDLokasi__NamaLokasi=lokasi
        ).exists()
        if existing_entry:
            # Jika sudah ada, beri tanggapan atau lakukan tindakan yang sesuai
            messages.warning(request,('Sudah ada Entry pada tahun',tanggal_formatted.year))
            return redirect("read_saldoawalbahan")
        
        produkobj = models.Produk.objects.get(KodeProduk=kodeproduk)
        lokasiobj = models.Lokasi.objects.get(NamaLokasi=lokasi)
        lokasi = str(lokasiobj.IDLokasi)

        pemusnahanobj = models.SaldoAwalBahanBaku(
            Tanggal=tanggal, Jumlah=jumlah, IDBahanBaku=produkobj, IDLokasi_id=lokasi, Harga=harga)
        
        models.transactionlog(
            user="Gudang",
            waktu=datetime.now(),
            jenis="Create",
            pesan=f"Kode Barang : {kodeproduk} Lokasi : {lokasi}",
        ).save()

        pemusnahanobj.save()
        return redirect("read_saldoawalbahan")
    
def delete_saldo(request, id):
    dataobj = models.SaldoAwalBahanBaku.objects.get(IDSaldoAwalBahanBaku=id)
    models.transactionlog(
                user="Gudang",
                waktu=datetime.now(),
                jenis="Delete",
                pesan=f"Kode Barang : {dataobj.IDBahanBaku} Lokasi : {dataobj.IDLokasi}",
            ).save()
    dataobj.delete()
    return redirect("read_saldoawalbahan")


def update_saldo(request,id) :    
    databarang = models.Produk.objects.all()
    dataobj = models.SaldoAwalBahanBaku.objects.get(IDSaldoAwalBahanBaku=id)
    dataobj.Tanggal = dataobj.Tanggal.strftime("%Y-%m-%d")
    lokasiobj = models.Lokasi.objects.all()
    if request.method == "GET":
        return render(
            request,
            "gudang/update_saldobahan.html",
            {"data": dataobj, "nama_lokasi": lokasiobj,"databarang": databarang},
        )

    else:
        kodeproduk = request.POST["produk"]
        lokasi = request.POST["nama_lokasi"]
        jumlah = request.POST["jumlah"]
        harga = request.POST["harga"]
        tanggal = request.POST["tanggal"]
        produkobj = models.Produk.objects.get(KodeProduk=kodeproduk)
        lokasiobj = models.Lokasi.objects.get(NamaLokasi=lokasi)
        lokasi = str(lokasiobj.IDLokasi)

        dataobj.Tanggal = tanggal
        dataobj.Jumlah = jumlah
        dataobj.IDBahanBaku = produkobj
        dataobj.IDLokasi_id = lokasi
        dataobj.Harga = harga
        models.transactionlog(
            user="Gudang",
            waktu=datetime.now(),
            jenis="Update",
            pesan=f"Kode Barang Lama : {dataobj.IDBahanBaku} Jumlah Lama : {dataobj.Jumlah} Harga Lama : {dataobj.Harga} Kode Barang Baru : {kodeproduk} Jumlah Baru : {jumlah} Harga Baru : {harga}",
        ).save()
        dataobj.save()
        return redirect("read_saldoawalbahan")
    
    