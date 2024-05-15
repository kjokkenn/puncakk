from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import Http404, JsonResponse, HttpResponse
from django.urls import reverse
from . import models
from django.db.models import Sum
from urllib.parse import quote
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta, date


# Create your views here.
# RND
def gethargafg(penyusunobj):
    konversiobj = models.KonversiMaster.objects.get(
        KodePenyusun=penyusunobj.IDKodePenyusun
    )
    konversialowance = konversiobj.Kuantitas + (konversiobj.Kuantitas * 0.025)
    detailsjpembelian = models.DetailSuratJalanPembelian.objects.filter(
        KodeProduk=penyusunobj.KodeProduk
    )
    print("ini detailsjpembelian", detailsjpembelian)
    hargatotalkodeproduk = 0
    jumlahtotalkodeproduk = 0
    for m in detailsjpembelian:
        hargatotalkodeproduk += m.Harga * m.Jumlah
        jumlahtotalkodeproduk += m.Jumlah
    print("ini jumlah harga total ", hargatotalkodeproduk)
    rataratahargakodeproduk = hargatotalkodeproduk / jumlahtotalkodeproduk
    print("selesai")
    print(rataratahargakodeproduk)
    nilaifgperkodeproduk = rataratahargakodeproduk * konversialowance
    print("Harga Konversi : ", nilaifgperkodeproduk)
    return nilaifgperkodeproduk


def dashboard(request):
    dataspk = models.SPK.objects.filter(Tanggal=date.today())
    print(dataspk)
    for i in dataspk:
        detailspk = models.DetailSPK.objects.filter(NoSPK=i.id)
        i.detailspk = detailspk

    dataproduk = models.Produk.objects.filter(TanggalPembuatan=date.today())
    print(dataproduk)
    datasppb = models.SPPB.objects.filter(Tanggal=date.today())
    print(datasppb)
    for i in datasppb:
        detailsppb = models.DetailSPPB.objects.filter(NoSPPB=i.id)
        i.detailsppb = detailsppb
    return render(
        request,
        "rnd/dashboard.html",
        {"dataspk": dataspk, "dataproduk": dataproduk, "datasppb": datasppb},
    )


def views_artikel(request):
    datakirim = []
    data = models.Artikel.objects.all()
    for item in data:
        detailartikelobj = models.Penyusun.objects.filter(KodeArtikel=item.id).filter(
            Status=1
        )
        if detailartikelobj.exists():
            datakirim.append([item, detailartikelobj[0]])
        else:
            datakirim.append([item, "Belum diset"])
    return render(request, "rnd/views_artikel.html", {"data": datakirim})


def tambahdataartikel(request):
    if request.method == "GET":
        return render(request, "rnd/tambah_artikel.html")
    if request.method == "POST":
        # print(dir(request))
        kodebaru = request.POST["kodeartikel"]
        keterangan = request.POST["keterangan"]
        data = models.Artikel.objects.filter(KodeArtikel=kodebaru).exists()
        if data:
            messages.error(request, "Kode Artikel sudah ada")
            return redirect("tambahdataartikel")
        else:
            if keterangan == "":
                keterangan = "-"
            newdataobj = models.Artikel(KodeArtikel=kodebaru, keterangan=keterangan)
            models.transactionlog(
                user="RND",
                waktu=datetime.now(),
                jenis="Create",
                pesan=f"Artikel : {newdataobj.KodeArtikel} Keterangan : {newdataobj.keterangan}",
            ).save()
            newdataobj.save()
            messages.success(request, "Data berhasil disimpan")
            return redirect("views_artikel")


def updatedataartikel(request, id):
    data = models.Artikel.objects.get(id=id)
    if request.method == "GET":
        return render(request, "rnd/update_artikel.html", {"artikel": data})
    else:
        kodeartikel = request.POST["kodeartikel"]
        keterangan = request.POST["keterangan"]
        if keterangan == "":
            keterangan = "-"
        cekkodeartikel = models.Artikel.objects.filter(KodeArtikel=kodeartikel).exists()
        if cekkodeartikel:
            messages.error(request, "Kode Artikel telah terdaftar pada database")
            return redirect("update_artikel", id=id)
        else:
            transaksilog = models.transactionlog(
                user="RND",
                waktu=datetime.now(),
                jenis="Update",
                pesan=f"Artikel Lama : {data.KodeArtikel} Keterangan Lama : {data.keterangan} Artikel Baru : {kodeartikel} Keterangan Baru : {keterangan}",
            )
            data.KodeArtikel = kodeartikel
            data.keterangan = keterangan
            data.save()
            transaksilog.save()
            messages.success(request, "Data Berhasil diupdate")
        return redirect("views_artikel")


def deleteartikel(request, id):
    dataobj = models.Artikel.objects.get(id=id)
    models.transactionlog(
        user="RND",
        waktu=datetime.now(),
        jenis="Delete",
        pesan=f"Artikel : {dataobj.kodebaru} Keterangan : {dataobj.keterangan}",
    ).save()
    dataobj.delete()
    messages.success(request, "Data Berhasil dihapus")
    return redirect("views_artikel")


def views_penyusun(request):
    print(request.GET)
    data = request.GET
    if len(request.GET) == 0:
        data = models.Artikel.objects.all()

        return render(request, "rnd/views_penyusun.html", {"dataartikel": data})
    else:
        kodeartikel = request.GET["kodeartikel"]

        try:
            get_id_kodeartikel = models.Artikel.objects.get(KodeArtikel=kodeartikel)
            data = models.Penyusun.objects.filter(KodeArtikel=get_id_kodeartikel.id)
            dataversi = data.values_list("versi", flat=True).distinct()
            print(dataversi)
            try:
                if request.GET["versi"] == "":
                    versiterpilih = dataversi.order_by("-versi").first()
                    print("ini versi terbaru", versiterpilih)
                    versiterpilih = versiterpilih.strftime("%Y-%m-%d")
                else:
                    versiterpilih = request.GET["versi"]
            except:
                versiterpilih = dataversi.order_by("-versi").first()
                print("ini versi terbaru", versiterpilih)
                versiterpilih.strftime("%Y-%m-%d")

            data = data.filter(versi=versiterpilih)
            dataversi = [date.strftime("%Y-%m-%d") for date in dataversi]
            print(dataversi)
            datakonversi = []
            nilaifg = 0
            print(data)
            if data.exists():
                for item in data:
                    print(item, item.IDKodePenyusun)
                    konversidataobj = models.KonversiMaster.objects.get(
                        KodePenyusun=item.IDKodePenyusun
                    )
                    # print(konversidataobj.Kuantitas)
                    masukobj = models.DetailSuratJalanPembelian.objects.filter(
                        KodeProduk=item.KodeProduk
                    )
                    # print("ini detail sjp", masukobj)
                    tanggalmasuk = masukobj.values_list(
                        "NoSuratJalan__Tanggal", flat=True
                    )
                    keluarobj = models.TransaksiGudang.objects.filter(
                        jumlah__gte=0, KodeProduk=item.KodeProduk
                    )
                    tanggalkeluar = keluarobj.values_list("tanggal", flat=True)
                    # print(item)
                    saldoawalobj = (
                        models.SaldoAwalBahanBaku.objects.filter(
                            IDBahanBaku=item.KodeProduk.KodeProduk
                        )
                        .order_by("-Tanggal")
                        .first()
                    )
                    if saldoawalobj:
                        # print(saldoawalobj)
                        saldoawal = saldoawalobj.Jumlah
                        hargasatuanawal = saldoawalobj.Harga
                        hargatotalawal = saldoawal * hargasatuanawal
                    else:
                        saldoawal = 0
                        hargasatuanawal = 0
                        hargatotalawal = saldoawal * hargasatuanawal

                    hargaterakhir = 0
                    listdata = []
                    listtanggal = sorted(list(set(tanggalmasuk.union(tanggalkeluar))))
                    # print("inii", listtanggal)
                    for i in listtanggal:
                        jumlahmasukperhari = 0
                        hargamasuktotalperhari = 0
                        hargamasuksatuanperhari = 0
                        jumlahkeluarperhari = 0
                        hargakeluartotalperhari = 0
                        hargakeluarsatuanperhari = 0
                        sjpobj = masukobj.filter(NoSuratJalan__Tanggal=i)
                        if sjpobj.exists():
                            for j in sjpobj:
                                hargamasuktotalperhari += j.Harga * j.Jumlah
                                jumlahmasukperhari += j.Jumlah
                            hargamasuksatuanperhari += (
                                hargamasuktotalperhari / jumlahmasukperhari
                            )
                        else:
                            hargamasuktotalperhari = 0
                            jumlahmasukperhari = 0
                            hargamasuksatuanperhari = 0

                        transaksigudangobj = keluarobj.filter(tanggal=i)
                        # print(transaksigudangobj)
                        if transaksigudangobj.exists():
                            for j in transaksigudangobj:
                                jumlahkeluarperhari += j.jumlah
                                hargakeluartotalperhari += j.jumlah * hargasatuanawal
                            hargakeluarsatuanperhari += (
                                hargakeluartotalperhari / jumlahkeluarperhari
                            )
                        else:
                            hargakeluartotalperhari = 0
                            hargakeluarsatuanperhari = 0
                            jumlahkeluarperhari = 0

                        saldoawal += jumlahmasukperhari - jumlahkeluarperhari
                        hargatotalawal += (
                            hargamasuktotalperhari - hargakeluartotalperhari
                        )
                        hargasatuanawal = hargatotalawal / saldoawal

                        # print("ini hargasatuan awal : ", hargasatuanawal)

                    hargaterakhir += hargasatuanawal
                    kuantitaskonversi = konversidataobj.Kuantitas
                    kuantitasallowance = kuantitaskonversi + kuantitaskonversi * 0.025
                    hargaperkotak = hargaterakhir * kuantitasallowance
                    # print("\n", hargaterakhir, "\n")
                    nilaifg += hargaperkotak

                    datakonversi.append(
                        {
                            "HargaSatuan": round(hargaterakhir, 2),
                            "Penyusunobj": item,
                            "Konversi": round(kuantitaskonversi, 5),
                            "Allowance": round(kuantitasallowance, 5),
                            "Hargakotak": round(hargaperkotak, 2),
                        }
                    )

                # print(data)
                print(versiterpilih)
                # print(dasdatakonversi)

                return render(
                    request,
                    "rnd/views_penyusun.html",
                    {
                        "data": datakonversi,
                        "kodeartikel": get_id_kodeartikel,
                        "nilaifg": nilaifg,
                        "versiterpilih": versiterpilih,
                        "dataversi": dataversi,
                    },
                )
            else:
                messages.error(request, "Kode Artikel Belum memiliki penyusun")
                return render(
                    request,
                    "rnd/views_penyusun.html",
                    {"kodeartikel": get_id_kodeartikel},
                )
        except models.Artikel.DoesNotExist:
            messages.error(request, "Kode Artikel Tidak ditemukan")
            return render(
                request,
                "rnd/views_penyusun.html",
                {"dataartikel": models.Artikel.objects.all()},
            )


def updatepenyusun(request, id):
    data = models.Penyusun.objects.get(IDKodePenyusun=id)
    if request.method == "GET":
        datakonversi = models.KonversiMaster.objects.get(
            KodePenyusun=data.IDKodePenyusun
        )
        datakonversi.allowance = datakonversi.Kuantitas + (
            datakonversi.Kuantitas * 0.025
        )
        kodebahanbaku = models.Produk.objects.all()
        lokasiobj = models.Lokasi.objects.all()
        return render(
            request,
            "rnd/update_penyusun.html",
            {
                "kodestok": kodebahanbaku,
                "data": data,
                "lokasi": lokasiobj,
                "konversi": datakonversi,
            },
        )
    else:
        print(request.POST)
        kodeproduk = request.POST["kodeproduk"]
        lokasi = request.POST["lokasi"]
        status = request.POST["status"]
        kuantitas = request.POST["kuantitas"]
        produkobj = models.Produk.objects.get(KodeProduk=kodeproduk)
        lokasiobj = models.Lokasi.objects.get(IDLokasi=lokasi)
        konversiobj = models.KonversiMaster.objects.get(KodePenyusun=id)
        data.KodeProduk = produkobj
        data.Lokasi = lokasiobj
        data.Status = status
        data.save()
        konversiobj.Kuantitas = kuantitas
        konversiobj.save()
        transaksilog = models.transactionlog(
                user="RND",
                waktu=datetime.now(),
                jenis="Update",
            pesan=f"Penyusun Baru. Kode Artikel : {data.KodeArtikel}, Kode produk : {data.KodeProduk}-{data.NamaProduk}, Status Utama : {data} versi : {data.versi}, Kuantitas Konversi : {  konversiobj.Kuantitas}",
            )
        transaksilog.save()
        return redirect("penyusun_artikel")


def tambahdatapenyusun(request, id, versi):
    dataartikelobj = models.Artikel.objects.get(id=id)
    print(versi)
    if request.method == "GET":
        dataprodukobj = models.Produk.objects.all()

        return render(
            request,
            "rnd/tambah_penyusun.html",
            {
                "kodeartikel": dataartikelobj,
                "dataproduk": dataprodukobj,
                "versiterpilih": versi,
            },
        )
    else:
        kodeproduk = request.POST["kodeproduk"]
        statusproduk = request.POST["Status"]
        if statusproduk == "True":
            statusproduk = True
        else:
            statusproduk = False
        lokasi = request.POST["lokasi"]

        newprodukobj = models.Produk.objects.get(KodeProduk=kodeproduk)
        lokasiobj = models.Lokasi.objects.get(NamaLokasi=lokasi)

        datapenyusunobj = (
            models.Penyusun.objects.filter(KodeArtikel=id)
            .filter(Status=True, versi=versi)
            .exists()
        )
        if datapenyusunobj and statusproduk:
            messages.error(
                request, "Artikel telah memiliki Bahan baku utama sebelumnya"
            )
            return redirect("tambah_data_penyusun", id=id, versi=versi)
        penyusunobj = models.Penyusun(
            Status=statusproduk,
            KodeArtikel=dataartikelobj,
            KodeProduk=newprodukobj,
            Lokasi=lokasiobj,
            versi=versi,
        )
        penyusunobj.save()
        kuantitas = request.POST["kuantitas"]
        konversimasterobj = models.KonversiMaster(
            KodePenyusun=penyusunobj, Kuantitas=kuantitas, lastedited=datetime.now()
        ).save()
        messages.success(request, "Data penyusun berhasil ditambahkan")
        models.transactionlog(
            user="RND",
            waktu=datetime.now(),
            jenis="Create",
            pesan=f"Penyusun. Kode Artikel : {dataartikelobj.KodeArtikel}, Kode produk : {newprodukobj.KodeProduk}-{newprodukobj.NamaProduk}, Status Utama : {statusproduk} versi : {versi}, Kuantitas Konversi : {kuantitas}",
        ).save()
        return redirect(
            f"/rnd/penyusun?kodeartikel={quote(dataartikelobj.KodeArtikel)}"
        )


def delete_penyusun(request, id):
    penyusunobj = models.Penyusun.objects.get(IDKodePenyusun=id)
    penyusunobj.delete()
    print(penyusunobj)
    print(id)
    return redirect("penyusun_artikel")


# Update Delete Penyusun belum masuk
def konversi(request):
    data = request.GET
    if len(data) == 0:
        return render(request, "views_konversi.html")
    else:
        kodeartikel = request.GET["kodeartikel"]
        try:
            get_id_kodeartikel = models.Artikel.objects.get(KodeArtikel=kodeartikel)
        except models.Artikel.DoesNotExist:
            messages.error(request, "Data Artikel tidak ditemukan")
            return redirect("konversi")
        data = models.Penyusun.objects.filter(KodeArtikel=get_id_kodeartikel.id)
        if data.exists():
            listdata = []
            for i in data:
                allowance = models.KonversiMaster.objects.get(
                    KodePenyusun=i.IDKodePenyusun
                )
                listdata.append(
                    [i, allowance, allowance.Kuantitas + allowance.Kuantitas * 0.025]
                )
            return render(
                request,
                "views_konversi.html",
                {"data": listdata, "kodeartikel": kodeartikel},
            )
        else:
            return render(request, "rnd/views_konversi.html")


def konversimaster_update(request, id):
    dataobj = models.Penyusun.objects.get(IDKodePenyusun=id)
    if request.method == "GET":
        return render(request, "rnd/update_konversimaster.html", {"data": dataobj})
    else:
        konversimasterobj = models.KonversiMaster.objects.get(IDKodeKonversiMaster=id)
        print(konversimasterobj)
        konversimasterobj.Kuantitas = float(request.POST["kuantitas"])
        konversimasterobj.save()
        return redirect("konversi")


def konversimaster_delete(request, id):
    dataobj = models.KonversiMaster.objects.get(IDKodeKonversiMaster=id)
    dataobj.Kuantitas = 0
    dataobj.save()
    return redirect("konversi")


def views_sppb(request):
    data = models.SPPB.objects.all()
    for sppb in data:
        detailsppb = models.DetailSPPB.objects.filter(NoSPPB=sppb.id)
        sppb.detailsppb = detailsppb
    return render(request, "rnd/views_sppb.html", {"data": data})


def view_spk(request):
    dataspk = models.SPK.objects.all()
    for spk in dataspk:
        detailspk = models.DetailSPK.objects.filter(NoSPK=spk.id)
        spk.detailspk = detailspk
        spk.Tanggal = spk.Tanggal.strftime("%d-%m-%Y")

    return render(request, "rnd/views_spk.html", {"dataspk": dataspk})


def hariterakhirdatetime(tahun):
    next_year = datetime(tahun + 1, 1, 1)
    last_day = next_year - timedelta(days=1)
    return last_day


def views_ksbj(request):
    if len(request.GET) == 0:
        dataartikel = models.Artikel.objects.all()
        return render(request, "rnd/view_ksbj.html", {"dataartikel": dataartikel})
    else:
        print(request.GET)
        lokasi = request.GET["lokasi"]
        tahun = request.GET["tahun"]
        kodeartikel = request.GET["kodeartikel"]
        lokasiobj = models.Lokasi.objects.get(NamaLokasi=lokasi)
        saldoawalobj = models.SaldoAwalArtikel.objects.filter(
            IDArtikel__KodeArtikel=kodeartikel, IDLokasi=lokasiobj.IDLokasi
        )

        # Cek apabila Kode Artikel user tidak ada
        try:
            artikel = models.Artikel.objects.get(KodeArtikel=kodeartikel)
        except:
            messages.error(request, "Kode Artikel Tidak ditemukan")
            return redirect("views_ksbj")
        # Cek apabila penyusun utama belum di setting
        try:
            getbahanbakuutama = models.Penyusun.objects.get(
                KodeArtikel=artikel.id, Status=1
            )
        except models.Penyusun.DoesNotExist:
            messages.error(request, "Bahan Baku utama belum di set")
            return redirect("views_ksbj")

        data = models.TransaksiProduksi.objects.filter(KodeArtikel=artikel.id)
        # if lokasi == "WIP":
        # # print(tanggallist)
        listdata = []

        if lokasi == "WIP":
            data = data.filter(Lokasi=lokasiobj.IDLokasi)
            try:
                saldoakhirgte = (
                    saldoawalobj.filter(Tanggal__year__gt=tahun)
                    .order_by("Tanggal")
                    .first()
                )
                saldoawallte = (
                    saldoawalobj.filter(Tanggal__year__lte=tahun)
                    .order_by("-Tanggal")
                    .first()
                )
                print("Ini saldo gte : ", saldoakhirgte)
                print("Ini Saldo LTE : ", saldoawallte)
                print("Tahun saat ini : ", tahun)
                print("Saldo Awal Tahun : ", saldoawallte)
                print("Saldo Akhir Tahun : ", saldoakhirgte)
            except:
                saldoawallte = None
                saldoakhirgte = None
            print(saldoawalobj)

            if saldoawallte and saldoakhirgte:
                tanggalawal = saldoawallte.Tanggal
                tanggalakhir = saldoakhirgte.Tanggal
            elif saldoawallte and not saldoakhirgte:
                tanggalawal = saldoawallte.Tanggal
                tanggalakhir = datetime.max
            elif not saldoawallte and saldoakhirgte:
                print("data awal tidak ditemukan")
                tanggalawal = datetime.min
                tanggalakhir = saldoakhirgte.Tanggal
            else:
                print("Tidak ditemukan data awal dan akhir")
                tanggalawal = datetime.min
                tanggalakhir = datetime.max

            tanggallist = (
                data.filter(Tanggal__range=(tanggalawal, tanggalakhir))
                .values_list("Tanggal", flat=True)
                .order_by("Tanggal")
                .distinct()
            )

            saldoawalobj = saldoawallte

            if saldoawalobj:
                saldoawal = saldoawalobj.Jumlah
            else:
                saldoawal = 0
            # print('ini WIP')
            saldoawaltaun = saldoawal
            for i in tanggallist:

                jumlahhasil = 0
                jumlahmasuk = 0
                # print(data)
                print(i)
                filtertanggal = data.filter(Tanggal=i)
                print(filtertanggal)
                if filtertanggal:
                    jumlahmasuk = filtertanggal.filter(Jenis="Produksi").aggregate(
                        total=Sum("Jumlah")
                    )["total"]
                    print(jumlahmasuk)
                    if jumlahmasuk is None:
                        jumlahmasuk = 0
                    jumlahhasil = filtertanggal.filter(Jenis="Mutasi").aggregate(
                        total=Sum("Jumlah")
                    )["total"]
                    if jumlahhasil is None:
                        jumlahhasil = 0
                    print(jumlahhasil)

                    # Cari data konversi bahan baku utama pada artikel terkait

                konversimasterobj = models.KonversiMaster.objects.get(
                    KodePenyusun=getbahanbakuutama.IDKodePenyusun
                )
                # print('Konversi', konversimasterobj.Kuantitas + ( konversimasterobj.Kuantitas*0.025))
                masukpcs = round(
                    jumlahmasuk
                    / (
                        (
                            konversimasterobj.Kuantitas
                            + (konversimasterobj.Kuantitas * 0.025)
                        )
                    )
                    * 0.893643879
                )
                # Cari data penyesuaian
                saldoawal = saldoawal - jumlahhasil + masukpcs
                if saldoawal < 0:
                    messages.warning(
                        request,
                        "Sisa stok menjadi negatif pada tanggal {}.\nCek kembali mutasi barang".format(
                            i
                        ),
                    )
                # listdata.append([i,getbahanbakuutama,jumlahmasuk,jumlahhasil,masukpcs,sisa])
                listdata.append(
                    {
                        "Tanggal": i.strftime("%d-%m-%Y"),
                        "Bahanbakuutama": getbahanbakuutama,
                        "Jumlahmasuk": jumlahmasuk,
                        "Jumlahhasil": jumlahhasil,
                        "Masukpcs": masukpcs,
                        "Sisa": saldoawal,
                    }
                )
            if saldoawalobj:
                saldoawalobj.Tanggal = saldoawalobj.Tanggal.strftime("%d-%m-%Y")

            stockopname = 0
            if saldoakhirgte:
                stockopname = saldoakhirgte.Jumlah - saldoawal
            print(saldoakhirgte)

            return render(
                request,
                "rnd/view_ksbj.html",
                {
                    "data": data,
                    "kodeartikel": kodeartikel,
                    "lokasi": lokasi,
                    "listdata": listdata,
                    "saldoawal": saldoawalobj,
                    "tahun": tahun,
                    "stockopname": stockopname,
                    "saldoakhir": saldoakhirgte,
                },
            )

            #     print(getbahanbakuutama)

        else:
            data = data.filter(Lokasi=1)
            saldoawalperiode = (
                saldoawalobj.values_list("Tanggal__year", flat=True)
                .distinct()
                .order_by("-Tanggal")
            )
            print(saldoawalperiode)
            try:
                saldoakhirgte = (
                    saldoawalobj.filter(Tanggal__year__gt=tahun)
                    .order_by("Tanggal")
                    .first()
                )
                saldoawallte = (
                    saldoawalobj.filter(Tanggal__year__lte=tahun)
                    .order_by("-Tanggal")
                    .first()
                )
                print("Ini saldo gte : ", saldoakhirgte)
                print("Ini Saldo LTE : ", saldoawallte)
                print("Tahun saat ini : ", tahun)
                print("Saldo Awal Tahun : ", saldoawallte)
                print("Saldo Akhir Tahun : ", saldoakhirgte)
            except ValueError:
                saldoawallte = None
                saldoakhirgte = None

            # IF Saldo awal LTE kosong --> Data saldoawal belum di set --> Harusnya di set semua pertahun
            if saldoawallte and saldoakhirgte:
                tanggalawal = saldoawallte.Tanggal
                tanggalakhir = saldoakhirgte.Tanggal
            elif saldoawallte and not saldoakhirgte:
                tanggalawal = saldoawallte.Tanggal
                tanggalakhir = datetime.max
            elif not saldoawallte and saldoakhirgte:
                print("data awal tidak ditemukan")
                tanggalawal = datetime.min
                tanggalakhir = saldoakhirgte.Tanggal
            else:
                print("Tidak ditemukan data awal dan akhir")
                tanggalawal = datetime.min
                tanggalakhir = datetime.max
            # IF Saldo Akhir GT kosong --> Data filter data tahun saat ini
            tanggallist = (
                data.filter(Tanggal__range=(tanggalawal, tanggalakhir))
                .values_list("Tanggal", flat=True)
                .distinct()
            )

            saldoawalobj = saldoawallte

            if saldoawalobj:
                saldoawal = saldoawalobj.Jumlah
            else:
                saldoawal = 0
            sppb = models.DetailSPPB.objects.filter(
                DetailSPK__KodeArtikel__KodeArtikel=kodeartikel,
                NoSPPB__Tanggal__range=(tanggalawal, tanggalakhir),
            )
            tanggalsppb = sppb.values_list("NoSPPB__Tanggal", flat=True).distinct()
            # print(tanggalsppb)
            tanggallist = sorted(list(set(tanggallist.union(tanggalsppb))))
            # print(tanggallist)

            # print('ini FG')
            saldoawaltaun = saldoawal
            for i in tanggallist:
                jumlahhasil = 0
                jumlahmasuk = 0
                totalmasuk = 0
                totalkeluar = 0
                nosppb = []
                nospk = []
                jumlah = []
                listsppbobj = []

                penyerahanwip = models.TransaksiProduksi.objects.filter(
                    Tanggal=i,
                    KodeArtikel__KodeArtikel=kodeartikel,
                    Jenis="Mutasi",
                    Lokasi__NamaLokasi="WIP",
                )
                detailsppbobj = sppb.filter(NoSPPB__Tanggal=i)
                # print(detailsppbobj)
                if penyerahanwip:
                    # print('data penyerahan ada ',i)
                    totalmasuk = penyerahanwip.aggregate(total=Sum("Jumlah"))["total"]

                    # print(totalmasuk)
                if detailsppbobj:
                    # print('data Pengiriman Ada',i)
                    totalkeluar = detailsppbobj.aggregate(total=Sum("Jumlah"))["total"]
                    # print(totalkeluar)
                    for j in detailsppbobj:
                        nosppb.append(j.NoSPPB)
                        nospk.append(j.DetailSPK.NoSPK)
                        jumlah.append(j.Jumlah)
                saldoawal += totalmasuk - totalkeluar
                if saldoawal < 0:
                    messages.warning(
                        request,
                        "Sisa stok menjadi negatif pada tanggal {}.\nCek kembali mutasi barang".format(
                            i
                        ),
                    )
                # print('Tanggal : ',i)
                # print('Jumlah Penyerahan dari WIP : ',totalmasuk)
                # print('SPPB : ', nosppb)
                # print('SPK : ',nospk)
                # print('Jumlah Kirim : ',jumlah)
                # print('Sisa : ')
                # print('\n')

                listdata.append(
                    {
                        "Tanggal": i.strftime("%d-%m-%Y"),
                        "JumlahPenyerahan": totalmasuk,
                        "SPPB": nosppb,
                        "SPK": nospk,
                        "Jumlahkirim": jumlah,
                        "Sisa": saldoawal,
                    }
                )

            print("ini saldo awal", saldoawalobj)
            # print('saldoakhir ', saldoakhirgte.Jumlah)
            stockopname = 0
            if saldoakhirgte:
                stockopname = saldoakhirgte.Jumlah - saldoawal
                print(stockopname)

            if saldoawalobj:
                saldoawalobj.Tanggal = saldoawalobj.Tanggal.strftime("%d-%m-%Y")
            return render(
                request,
                "rnd/view_ksbj.html",
                {
                    "data": data,
                    "kodeartikel": kodeartikel,
                    "lokasi": "FG",
                    "listdata": listdata,
                    "saldoawal": saldoawalobj,
                    "tahun": tahun,
                    "saldoakhir": saldoakhirgte,
                    "stockopname": stockopname,
                },
            )


def uploadexcel(request):
    if request.method == "POST":
        excel_file = request.FILES["excel_file"]
        if excel_file.name.endswith(".xlsx"):
            df = pd.read_excel(excel_file)
            print(df["KodeProduk"].tolist())
            # Lakukan operasi yang diperlukan dengan dataframe
            # Misalnya, simpan dataframe ke database atau lakukan analisis
            excel_file = BytesIO()
            # df.to_excel('export data.xlsx',index=False)
            with pd.ExcelWriter(excel_file, engine="xlsxwriter") as writer:
                df.to_excel(writer, index=False)
            excel_file.seek(0)
            response = HttpResponse(
                excel_file.read(),
                content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            response["Content-Disposition"] = 'attachment; filename="data_export.xlsx"'
            return response
        else:
            return HttpResponse("File harus berformat .xlsx")
    return render(request, "rnd/formexcel.html")


def views_rekapharga(request):
    kodeprodukobj = models.Produk.objects.all()
    if len(request.GET) == 0:
        return render(request, "rnd/views_ksbb.html", {"kodeprodukobj": kodeprodukobj})
    else:
        kode_produk = request.GET["kode_produk"]

        try:
            produkobj = models.Produk.objects.get(KodeProduk=kode_produk)
        except models.Produk.DoesNotExist:
            messages.error(request, "Kode bahan baku tidak ditemukan")
            return render(
                request, "rnd/views_ksbb.html", {"kodeprodukobj": kodeprodukobj}
            )
        masukobj = models.DetailSuratJalanPembelian.objects.filter(
            KodeProduk=produkobj.KodeProduk
        )

        tanggalmasuk = masukobj.values_list("NoSuratJalan__Tanggal", flat=True)

        keluarobj = models.TransaksiGudang.objects.filter(
            jumlah__gte=0, KodeProduk=produkobj.KodeProduk
        )
        tanggalkeluar = keluarobj.values_list("tanggal", flat=True)
        print("ini kode bahan baku", keluarobj)
        if not keluarobj.exists():
            messages.error(request, "Tidak ditemukan data Transaksi Barang")
            return redirect("rekapharga")
        saldoawalobj = (
            models.SaldoAwalBahanBaku.objects.filter(
                IDBahanBaku=produkobj.KodeProduk, IDLokasi=1
            )
            .order_by("-Tanggal")
            .first()
        )
        if saldoawalobj:
            print("ada data")
            saldoawal = saldoawalobj.Jumlah
            hargasatuanawal = saldoawalobj.Harga
            hargatotalawal = saldoawal * hargasatuanawal

        else:
            saldoawal = 0
            hargasatuanawal = 0
            hargatotalawal = saldoawal * hargasatuanawal
        saldoawalobj = {
            "saldoawal": saldoawal,
            "hargasatuanawal": hargasatuanawal,
            "hargatotalawal": hargatotalawal,
            "Tanggal": saldoawalobj.Tanggal.strftime("%d-%m-%Y"),
        }
        hargaterakhir = 0
        listdata = []
        print(tanggalmasuk)
        print(tanggalkeluar)
        listtanggal = sorted(list(set(tanggalmasuk.union(tanggalkeluar))))
        print(listtanggal)
        for i in listtanggal:
            jumlahmasukperhari = 0
            hargamasuktotalperhari = 0
            hargamasuksatuanperhari = 0
            jumlahkeluarperhari = 0
            hargakeluartotalperhari = 0
            hargakeluarsatuanperhari = 0
            sjpobj = masukobj.filter(NoSuratJalan__Tanggal=i)
            if sjpobj.exists():
                for j in sjpobj:
                    hargamasuktotalperhari += j.Harga * j.Jumlah
                    jumlahmasukperhari += j.Jumlah
                hargamasuksatuanperhari += hargamasuktotalperhari / jumlahmasukperhari
            else:
                hargamasuktotalperhari = 0
                jumlahmasukperhari = 0
                hargamasuksatuanperhari = 0

            transaksigudangobj = keluarobj.filter(tanggal=i)
            print(transaksigudangobj)
            if transaksigudangobj.exists():
                for j in transaksigudangobj:
                    jumlahkeluarperhari += j.jumlah
                    hargakeluartotalperhari += j.jumlah * hargasatuanawal
                hargakeluarsatuanperhari += (
                    hargakeluartotalperhari / jumlahkeluarperhari
                )
            else:
                hargakeluartotalperhari = 0
                hargakeluarsatuanperhari = 0
                jumlahkeluarperhari = 0

            print("Tanggal : ", i)
            print("Sisa Stok Hari Sebelumnya : ", saldoawal)
            print("harga awal Hari Sebelumnya :", hargasatuanawal)
            print("harga total Hari Sebelumnya :", hargatotalawal)
            print("Jumlah Masuk : ", jumlahmasukperhari)
            print("Harga Satuan Masuk : ", hargamasuksatuanperhari)
            print("Harga Total Masuk : ", hargamasuktotalperhari)
            print("Jumlah Keluar : ", jumlahkeluarperhari)
            print("Harga Keluar : ", hargakeluarsatuanperhari)
            print(
                "Harga Total Keluar : ", hargakeluarsatuanperhari * jumlahkeluarperhari
            )
            if saldoawal + jumlahmasukperhari - jumlahkeluarperhari < 0:
                messages.warning(
                    request,
                    "Sisa stok menjadi negatif pada tanggal {}.\nCek kembali mutasi barang".format(
                        i
                    ),
                )

            dumy = {
                "Tanggal": i.strftime("%d-%m-%Y"),
                "Jumlahstokawal": saldoawal,
                "Hargasatuanawal": round(hargasatuanawal, 2),
                "Hargatotalawal": round(hargatotalawal, 2),
                "Jumlahmasuk": jumlahmasukperhari,
                "Hargamasuksatuan": round(hargamasuksatuanperhari, 2),
                "Hargamasuktotal": round(hargamasuktotalperhari, 2),
                "Jumlahkeluar": jumlahkeluarperhari,
                "Hargakeluarsatuan": round(hargakeluarsatuanperhari, 2),
                "Hargakeluartotal": round(hargakeluartotalperhari, 2),
            }
            """
            Rumus dari Excel KSBB Purchasing
            Sisa = Sisa hari sebelumnya + Jumlah masuk hari ini - jumlah keluar hari ini 
            harga sisa satuan = total sisa / harga total sisa
            Harga keluar = harga satuan hari sebelumnya

            """
            saldoawal += jumlahmasukperhari - jumlahkeluarperhari
            hargatotalawal += hargamasuktotalperhari - hargakeluartotalperhari
            hargasatuanawal = hargatotalawal / saldoawal

            print("Sisa Stok Hari Ini : ", saldoawal)
            print("harga awal Hari Ini :", hargasatuanawal)
            print("harga total Hari Ini :", hargatotalawal, "\n")
            dumy["Sisahariini"] = saldoawal
            dumy["Hargasatuansisa"] = round(hargasatuanawal, 2)
            dumy["Hargatotalsisa"] = round(hargatotalawal, 2)

            listdata.append(dumy)

        hargaterakhir += hargasatuanawal

        return render(
            request,
            "rnd/views_ksbb.html",
            {
                "data": listdata,
                "Hargaakhir": hargaterakhir,
                "Saldoawal": saldoawalobj,
                "kodeprodukobj": kodeprodukobj,
            },
        )


def tambahversi(request, id):
    data = models.Artikel.objects.get(id=id)
    tanggal = date.today().strftime("%Y-%m-%d")
    print(tanggal)
    if request.method == "GET":
        return render(
            request, "rnd/tambah_versi.html", {"data": data, "versi": tanggal}
        )
    else:
        print(request.POST)
        kodeproduk = request.POST.getlist("kodeproduk")
        status = request.POST.getlist("Status")
        lokasi = request.POST.getlist("lokasi")
        kuantitas = request.POST.getlist("kuantitas")
        if status.count("True") > 1:
            messages.error(request, "Terdapat Artikel utama lebih dari 1")
            return redirect("add_versi", id=id)
        dataproduk = list(zip(kodeproduk, status, lokasi, kuantitas))
        print(dataproduk)
        for i in dataproduk:
            newpenyusun = models.Penyusun(
                KodeProduk=models.Produk.objects.get(KodeProduk=i[0]),
                KodeArtikel=data,
                Status=i[1],
                Lokasi=models.Lokasi.objects.get(NamaLokasi=i[2]),
                versi=tanggal,
            ).save()
            datanewpenyusun = models.Penyusun.objects.all().last()
            konversimasterobj = models.KonversiMaster(
                KodePenyusun=datanewpenyusun, Kuantitas=i[3]
            ).save()
            print(newpenyusun)
            print(konversimasterobj)
        return redirect("penyusun_artikel")


def read_produk(request):
    produkobj = models.Produk.objects.all()
    print(produkobj[1].keteranganRND)
    return render(request, "rnd/read_produk.html", {"produkobj": produkobj})
