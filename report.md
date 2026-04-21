# Laporan UTS Sistem Terdistribusi

## Ringkasan Sistem dan Arsitektur

Sistem ini adalah Pub-Sub log aggregator yang menerima event dari publisher, memprosesnya melalui consumer yang idempotent, dan melakukan deduplication. Arsitektur menggunakan FastAPI untuk API, asyncio untuk concurrency, dan SQLite untuk persistent dedup store.

Diagram sederhana:
```
Publisher -> POST /publish -> Queue -> Consumer -> Dedup Store -> Processed Events
                                      |
                                      v
                                   GET /events, /stats
```

## Keputusan Desain

### Idempotency & Deduplication
- Dedup store menggunakan SQLite dengan primary key (topic, event_id)
- Consumer memeriksa duplikasi sebelum processing
- Logging untuk setiap duplikasi terdeteksi

### Ordering
- Total ordering tidak diperlukan karena aggregator hanya mengumpulkan log tanpa dependensi urutan ketat
- Menggunakan timestamp untuk informasi waktu

### Retry & Reliability
- At-least-once delivery dengan simulasi duplikasi
- Persistent store tahan terhadap restart container

## Analisis Performa
- Skala uji: 5000+ events dengan 20% duplikasi
- Responsif dengan asyncio dan in-memory queue
- Metrik: throughput, latency, duplicate rate

## Keterkaitan ke Bab 1-7

### T1 (Bab 1): Karakteristik Sistem Terdistribusi
Sistem terdistribusi memiliki karakteristik seperti concurrency, no global clock, dan independent failures. Trade-off pada Pub-Sub aggregator adalah kompleksitas vs scalability (Tanenbaum & Van Steen, 2020).

### T2 (Bab 2): Arsitektur Client-Server vs Publish-Subscribe
Publish-Subscribe lebih cocok untuk decoupling producer-consumer, memungkinkan multiple subscribers tanpa coupling langsung (Tanenbaum & Van Steen, 2020).

### T3 (Bab 3): At-Least-Once vs Exactly-Once
At-least-once dapat menyebabkan duplikasi; idempotent consumer memastikan exactly-once semantic melalui deduplication (Tanenbaum & Van Steen, 2020).

### T4 (Bab 4): Penamaan
Event_id unik menggunakan UUID; skema penamaan collision-resistant memastikan dedup efektif (Tanenbaum & Van Steen, 2020).

### T5 (Bab 5): Ordering
Total ordering tidak diperlukan; menggunakan timestamp + counter untuk partial ordering (Tanenbaum & Van Steen, 2020).

### T6 (Bab 6): Toleransi Kegagalan
Failure modes: duplikasi, crash. Mitigasi: retry dengan backoff, durable store (Tanenbaum & Van Steen, 2020).

### T7 (Bab 7): Konsistensi
Eventual consistency dicapai melalui idempotency dan dedup, memastikan state akhir konsisten (Tanenbaum & Van Steen, 2020).

### T8 (Bab 1-7): Metrik Evaluasi
Throughput, latency, duplicate rate; keputusan desain memprioritaskan reliability over strict ordering (Tanenbaum & Van Steen, 2020).

## Sitasi
Tanenbaum, A. S., & Van Steen, M. (2020). *Distributed systems: Principles and paradigms* (3rd ed.). Pearson.