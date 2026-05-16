# Demo Plan

Bu dokuman, `indoor_drone_gas_demo` prototipi icin sade finite-state-machine gorev akisini tanimlar. Amac, ilk asamada tam SLAM veya karmasik magara kesfi yapmak degil; drone'un kapali ortama girip odalari taramasini, gaz olcumu almasini, harita uretmesini ve guvenli cikis noktasina geri donmesini gostermektir.

## Gorev Mantigi

Drone koridorun sonuna gidip orada inmez. `START / SAFE_EXIT` alani hem kalkis, hem donus, hem de inis alanidir.

World icindeki `possible_gas_zone_*` markerlari aktif gaz kaynagi degildir. Bunlar sadece aday senaryo noktalarini gosterir. Aktif gaz kaynagi daha sonra `gas_sensor_node.py` icinde her calistirmada rastgele veya senaryo bazli olarak secilecektir. Drone gazin nerede oldugunu onceden biliyor gibi davranmaz; odalara ve koridor noktalarina girip olcum alarak gaz yogunluk haritasi uretir.

## Finite-State-Machine

```text
TAKEOFF
  -> ENTER_ENVIRONMENT
  -> EXPLORE_CORRIDOR
  -> ENTER_ROOM
  -> SAMPLE_GAS
  -> MAP_UPDATE
  -> EXPLORE_CORRIDOR
  -> RETURN_TO_SAFE_EXIT
  -> LAND
  -> FINISH
```

State gecisleri ilk asamada basit rota noktalarina, zamanlayicilara ve lidar/range tabanli engel kontrolune baglanabilir. Daha sonra ROS2 topic, MAVSDK telemetry ve Gazebo sensor verileriyle daha gercek zamanli hale getirilebilir.

## TAKEOFF

Drone `START / SAFE_EXIT` alaninda goreve baslar.

Sorumluluklar:

- PX4/MAVSDK baglantisinin hazir oldugunu kontrol etmek,
- Drone'u arm etmek,
- Guvenli bir hedef irtifaya kalkis yapmak,
- Kalkis tamamlaninca `ENTER_ENVIRONMENT` state'ine gecmek.

Basit demo kosulu:

- Baslangic koordinati yaklasik `x=0, y=0`.
- Hedef irtifa: 1.5-2.0 metre.

## ENTER_ENVIRONMENT

Drone guvenli cikis alanindan ana koridora girer.

Sorumluluklar:

- Yavas ve kontrollu ileri hareket baslatmak,
- Koridor merkez hattina yerlesmek,
- Ilk engel ve duvar mesafelerini range/lidar verisiyle kontrol etmek,
- Koridor icine guvenli sekilde girildiginde `EXPLORE_CORRIDOR` state'ine gecmek.

## EXPLORE_CORRIDOR

Drone ana koridor boyunca ilerler ve oda girislerini ziyaret edilecek hedefler olarak ele alir.

Sorumluluklar:

- Koridor uzerindeki ara noktalara gitmek,
- Ana koridordaki olcum noktalarinda gaz ornegi almak,
- Engel goruldugunde basit reaktif kacinma yapmak,
- Siradaki oda girisine ulasildiginda `ENTER_ROOM` state'ine gecmek,
- Tum odalar ve koridor olcumleri tamamlandiysa `RETURN_TO_SAFE_EXIT` state'ine gecmek.

Basit demo rotasi:

- Baslangic alani,
- Sol oda girisi,
- Sag oda girisi,
- Ileri kucuk oda girisi,
- Koridor orta noktasi,
- Guvenli cikisa donus.

## ENTER_ROOM

Drone secilen odaya girer ve kisa bir tarama hareketi yapar.

Sorumluluklar:

- Oda girisinden iceri kontrollu gecmek,
- Oda merkezine veya belirlenen 1-2 ara noktaya ilerlemek,
- Odadaki kucuk engellerden kacmak,
- Olcum alinacak noktaya ulasildiginda `SAMPLE_GAS` state'ine gecmek.

Not:

- Sag oda normal bir odadir; "gaz odasi" olarak kabul edilmez.
- Gazin aktif konumu Python tarafinda secilecegi icin her oda aday olcum bolgesi gibi ele alinir.

## SAMPLE_GAS

Drone bulundugu oda veya koridor noktasinda gaz olcumu alir.

Sorumluluklar:

- Anlik drone konumunu almak,
- Simule gaz konsantrasyonunu `gas_sensor_node.py` tarafindan uretilen modele gore okumak,
- Olcumu zaman damgasi ve pozisyonla birlikte gecici veri yapisina eklemek,
- Yeterli ornek alindiginda `MAP_UPDATE` state'ine gecmek.

Basit demo kosulu:

- Gaz degeri aktif secilen possible zone'a uzakliga bagli Gaussian benzeri fonksiyonla uretilebilir.
- Her oda veya koridor noktasinda 5-10 ornek alinabilir.

## MAP_UPDATE

Toplanan gaz olcumleri kaydedilir ve haritalama ciktisi icin hazirlanir.

Sorumluluklar:

- `results/gas_samples.csv` dosyasina zaman, x, y, z ve gaz degerini yazmak,
- 2B heatmap icin grid veri uretmek,
- Ileride 3B gorsellestirme icin veri formatini korumak,
- Siradaki kesif noktasi varsa `EXPLORE_CORRIDOR` veya `ENTER_ROOM` state'ine donmek,
- Kesif tamamlandiysa `RETURN_TO_SAFE_EXIT` state'ine gecmek.

Basit demo ciktisi:

```text
timestamp,x,y,z,gas_ppm
```

## RETURN_TO_SAFE_EXIT

Drone gorev sonunda koridoru takip ederek baslangic/guvenli cikis alanina geri doner.

Sorumluluklar:

- Oda veya koridor icindeki son konumdan ana koridor merkezine donmek,
- Baslangic noktasi civarina geri ilerlemek,
- Donus sirasinda engellerden reaktif olarak kacmak,
- `START / SAFE_EXIT` alanina ulasildiginda `LAND` state'ine gecmek.

Basit demo kosulu:

- Hedef donus koordinati yaklasik `x=0, y=0`.

## LAND

Drone `START / SAFE_EXIT` alaninda guvenli sekilde inis yapar.

Sorumluluklar:

- Ileri/yanal hareketi durdurmak,
- MAVSDK veya PX4 komutu ile land komutu gondermek,
- Inis tamamlandiginda `FINISH` state'ine gecmek.

## FINISH

Gorev tamamlanir ve raporlanabilir ciktılar kontrol edilir.

Sorumluluklar:

- Gorev durumunu terminalde raporlamak,
- CSV dosyasinin olustugunu kontrol etmek,
- Plot scriptinin calistirilabilecegini belirtmek,
- Gerekirse log dosyalarini saklamak.

Beklenen ciktilar:

- `results/gas_samples.csv`
- `results/gas_heatmap.png`
- Ileride: 3B gorsellestirme ciktisi.
