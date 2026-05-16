# indoor_drone_gas_demo

Basit, sunulabilir ve adim adim gelistirilebilir ROS2/Gazebo/PX4/MAVSDK tabanli drone gaz algilama demo prototipi.

## 1. Projenin Amaci

Bu projenin amaci, kapali alan benzeri basit bir koridor/oda ortaminda drone simülasyonu yaparak:

- Drone kalkis gorevini baslatmak,
- On taraftaki engeli lidar veya range sensor ile algilamak,
- Basit reaktif kontrol ile engelden kacmak,
- Gaz bolgesinde simule gaz olcumu almak,
- Konum ve gaz verisini CSV dosyasina kaydetmek,
- 2B heatmap ve sonraki asamada basit 3B gorsellestirme uretmek,
- Gorev sonunda inis veya gorev bitis durumuna gecmek.

Bu ilk surum, tam otonom magara kesfi veya SLAM cozumu degil; bitirme projesi sunumu icin calisan ve anlatilabilir bir prototip temelidir.

Gorev, koridor sonunda inis yapmak degildir. Drone guvenli baslangic/cikis noktasindan iceri girer, odalari tarar, olcum alir, haritalama yapar ve ayni guvenli cikis noktasina geri donerek inis yapar.

## 2. Bitirme Projesi Kapsami

Proje, "Drone Simulasyonu" onerisiyle uyumlu olacak sekilde su basliklari kapsar:

- ROS2 Humble ile dugum tabanli yazilim mimarisi,
- Gazebo Classic ile simule kapali alan ortami,
- PX4 SITL ile drone simülasyonu,
- MAVSDK Python ile gorev ve hareket komutlari,
- Simulasyon tabanli lidar/range, IMU ve gaz sensoru verileri,
- Python agirlikli veri isleme ve kayit,
- 2B ve ileride 3B gorsellestirme.

Bu iskelet, once basit ve saglam bir demo kurmayi hedefler. Daha gelismis SLAM, gercekci magara haritasi ve sensor fuzyonu sonraki asamalara birakilmistir.

## 3. Neden Sade Demo Secildi?

Tam magara kesfi, SLAM, dinamik gaz yayilimi ve gelismis sensor fuzyonu ayni anda ele alindiginda proje karmasik, kirilgan ve sunum icin riskli hale gelir.

Bu nedenle ilk demo su prensiplerle sade tutulur:

- Ortam basit koridor/oda geometrlisi ile sinirlanir.
- Drone gorevi finite-state-machine ile anlatilir.
- Engel kacma reaktif ve kural tabanli olur.
- Gaz verisi once simule edilir.
- CSV kaydi ve heatmap gibi somut ciktilar onceliklendirilir.

Boylece bitirme sunumunda sistemin amaci, veri akisi ve gelistirme yolu net bicimde gosterilebilir.

World icindeki possible gas zone markerlari sadece aday bolgeleri gosterir. Aktif gaz kaynagi Python tarafinda rastgele veya senaryo bazli secilecektir.

## 4. Kullanilan Teknolojiler

- Ubuntu 22.04
- ROS2 Humble
- Gazebo Classic
- PX4 SITL
- MAVSDK Python
- Python 3
- Matplotlib / NumPy / Pandas
- Opsiyonel sonraki asama: RViz2, Open3D veya Plotly

## 5. Calistirma Adimlari

Bu bolum ilk asamada placeholder olarak birakilmistir. PX4, Gazebo ve ROS2 entegrasyonu eklendikce netlestirilecektir.

Ornek hedef akis:

```bash
cd indoor_drone_gas_demo

# Gazebo Classic ile sadece world dosyasini acmak icin
gazebo worlds/simple_corridor_room.world

# Demo ortamini baslatmak icin
./scripts/start_demo.sh

# Gaz haritalama dugumunu veya simule mapper akisini baslatmak icin
./scripts/run_mapper.sh

# Gaz haritalama smoke test icin senaryo secerek calistirmak icin
./scripts/run_mapper.sh random
./scripts/run_mapper.sh no_gas
./scripts/run_mapper.sh possible_gas_zone_1
./scripts/run_mapper.sh possible_gas_zone_2
./scripts/run_mapper.sh random_multi
./scripts/run_mapper.sh multi_all

# Gorev sonunda CSV sonucunu gorsellestirmek icin
python3 scripts/plot_results.py results/gas_samples.csv

# Simulated mission FSM test icin
python3 src/mission_manager.py --mode sim
```

### Gaz Haritalama Smoke Test

Bu asamada gercek drone/PX4 pozisyonu kullanilmaz. `src/gas_sensor_node.py` simule kesif rotasi uzerinde drone pozisyonlari uretir, aktif gaz kaynagini `possible_gas_zone_1/2/3/4` listesinden secer ve her noktada ppm degeri hesaplar.

Varsayilan calistirma:

```bash
./scripts/run_mapper.sh random
```

Belirli senaryo calistirma:

```bash
./scripts/run_mapper.sh no_gas
./scripts/run_mapper.sh possible_gas_zone_1
./scripts/run_mapper.sh possible_gas_zone_2
./scripts/run_mapper.sh random_multi
./scripts/run_mapper.sh multi_1_2
./scripts/run_mapper.sh multi_all
```

### Gaz Senaryolari

- `no_gas` / `clean_air`: aktif gaz kaynagi yoktur; ppm degeri background seviyesine yakin kalir.
- `possible_gas_zone_1/2/3/4`: tek gaz kacagi senaryosudur.
- `random_single`: possible zone listesinden tek aktif kaynak secer.
- `random_multi`: possible zone listesinden 2 veya 3 aktif kaynak secer.
- `multi_1_2`, `multi_1_3`, `multi_2_3`, `multi_2_4`, `multi_all`: birden fazla gaz kaynagini ayni anda aktif eder.
- `random`: her calistirmada `no_gas`, `random_single` veya `random_multi` durumlarindan birini secer.

Varsayilan olarak seed verilmez ve `random` her calistirmada farkli sonuc uretebilir. Tekrarlanabilir sonuc icin:

```bash
SEED=42 ./scripts/run_mapper.sh random
```

Beklenen ciktilar:

- `results/gas_samples.csv`
- `results/scenario_info.json`
- `results/gas_heatmap.png`
- `results/heatmaps/gas_heatmap_<scenario>_<active_zones>.png`

Heatmap varsayilan olarak sabit `vmin=0`, `vmax=130` renk skalasi ile uretilir. Boylece `no_gas`, tek kaynak ve coklu kaynak senaryolari ayni renk araliginda karsilastirilabilir. Gerekirse:

```bash
VMIN=0 VMAX=180 ./scripts/run_mapper.sh multi_all
```

Not: CSV uretimi Matplotlib/NumPy gerektirmez. Heatmap uretimi icin Matplotlib gerekir; sistemde Matplotlib/NumPy uyumsuzlugu varsa script bunu dependency problemi olarak raporlar.

### Simulated Mission FSM Test

Bu asamada `mission_manager.py` gercek drone, PX4, MAVSDK veya ROS2 baglantisi kurmaz. Sadece gorev state gecislerini ve hedef waypoint'leri terminale yazar.

```bash
python3 src/mission_manager.py --mode sim
```

State gecisleri:

```text
TAKEOFF -> ENTER_ENVIRONMENT -> EXPLORE_CORRIDOR -> ENTER_ROOM -> SAMPLE_GAS -> MAP_UPDATE -> RETURN_TO_SAFE_EXIT -> LAND -> FINISH
```

Beklenen sonraki entegrasyonlar:

- `ros2 launch indoor_drone_gas_demo demo.launch.py`
- PX4 SITL baslatma komutu
- Gazebo world yukleme komutu
- MAVSDK tabanli gorev yonetimi

## 6. Ileri Asama Hedefleri

- ROS2 tabanli SLAM entegrasyonu,
- Daha gercekci magara veya maden galerisi world modeli,
- Lidar, IMU, barometre ve range sensor verilerinin gelismis fuzyonu,
- Dinamik gaz yayilimi modeli,
- RViz2 veya 3B web tabanli gorsellestirme,
- Gercek drone donanimina gecis icin arayuzlerin ayrilmasi,
- Senaryo bazli testler ve raporlanabilir deney sonuclari.

## Proje Yapisi

```text
indoor_drone_gas_demo/
├── README.md
├── scripts/
│   ├── start_demo.sh
│   ├── run_mapper.sh
│   └── plot_results.py
├── worlds/
│   └── simple_corridor_room.world
├── launch/
│   └── demo.launch.py
├── src/
│   ├── gas_sensor_node.py
│   ├── gas_mapper_node.py
│   ├── reactive_controller.py
│   └── mission_manager.py
├── results/
│   └── .gitkeep
└── docs/
    └── demo_plan.md
```
