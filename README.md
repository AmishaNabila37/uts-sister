# UTS Sistem Terdistribusi - Pub-Sub Log Aggregator

## Deskripsi
Implementasi layanan Pub-Sub log aggregator dengan idempotent consumer dan deduplication menggunakan Python FastAPI, berjalan dalam Docker.

## Cara Build dan Run

### Build Docker Image
```bash
docker build -t uts-aggregator .
```

### Run Container
```bash
docker run -p 8080:8080 uts-aggregator
```

## API Endpoints

- `POST /publish`: Menerima batch atau single event
- `GET /events?topic=...`: Mengembalikan daftar event unik
- `GET /stats`: Menampilkan statistik sistem

## Asumsi
- Semua komponen berjalan lokal dalam container
- Deduplication berdasarkan (topic, event_id)
- Store persistent menggunakan SQLite

## Unit Tests
Jalankan dengan:
```bash
pytest tests/
```

## Laporan
Lihat [report.md](report.md) untuk penjelasan detail.

## Video Demo
[Link YouTube Demo](https://youtube.com/watch?v=example) - Durasi 5-8 menit mendemonstrasikan build, run, dedup, dan persistensi.