# 🌿 Nexus — Kooperatif Yönetim Sistemi

> SQL yazmadan, Excel açmadan, veritabanına bakmadan.  
> Türkçe yaz, AI agent halleder.

**Production'da çalışıyor** · FastAPI + Supabase · GPT-4o-mini + LangGraph · Railway'de deploy · Trendyol & Hepsiburada entegrasyonu

---

## Neden Nexus?

Kooperatiflerde operasyonel bilgiye ulaşmak genellikle şöyle görünür: Excel açılır, filtre uygulanır, kargo firmasının sitesine girilir, muhtemelen birisi WhatsApp'tan aranır. Nexus bu döngüyü kesiyor.

**Nexus'un çekirdeği bir AI agent.** "Toplam ciro ne kadar?", "kritik stok var mı?", "Trendyol'dan kaç sipariş geldi?" — bunları sormak için ne SQL bilmek ne Excel açmak ne de herhangi bir rapora tıklamak gerekiyor. Agent, LangGraph üzerinde çalışır; doğal dil mesajını anlayıp doğru servisi çağırır ve sonucu düz Türkçe olarak geri verir.

Müşteri tarafında da aynı mantık geçerli: Telegram botu ürün bilgisi verir, kargo takip eder, destek alır ve sipariş için web sitesine yönlendirir — hiçbir şey manuel olarak girilmez.

---

## Ne Yapabilir?

### 🤖 AI Agent — Sistemin Çekirdeği
LangGraph üzerinde çalışan GPT-4o-mini tabanlı agent, 18 farklı tool'a sahip. Doğal Türkçe komutları anlayıp doğrudan veritabanı servislerini çağırır — ne SQL ne Excel, sadece yaz ve cevap al.

```
"toplam ciro ne kadar"              → sipariş verilerini çekip hesaplar
"kritik stokta hangi ürünler var"   → stok servisini çağırır, listeler
"zeytinyağının fiyatını 180 tl yap" → fiyatı günceller
"son 10 siparişi göster"            → formatlanmış sipariş listesi
"domates salçası stoğunu 50 artır"  → stok hareketi oluşturur
```

İki katmanlı mimari çalışır: sık kullanılan komutlar kural tabanlı intent parser tarafından milisaniyede karşılanır, geri kalanlar LLM agent'a devredilir.

### 💬 Telegram Botu
Müşteriler Telegram'dan ürün bilgisi alır, kargo takip eder, destek talebi oluşturur; sipariş için web sitesine yönlendirilir. Satıcılar aynı bot üzerinden stok sorgular, kargoya verilecekleri listeler.

### 📦 Operasyon Paneli
Web panelinden tüm operasyonu yönetin: sipariş durumlarını güncelleyin, kritik stok uyarılarını görün, kargoya verilecekleri listeleyin, müşteri geçmişine bakın.

### 🛒 Marketplace Entegrasyonu
Trendyol ve Hepsiburada siparişlerini tek tıkla çekip sisteme aktarın. Stok çakışmaları otomatik uyarılır, kanal bazlı satış dağılımı raporlanır.

### 🔮 ML Tahmin Motoru
Geçmiş sipariş verilerine göre haftalık talep tahmini üretir. Hangi ürünü ne zaman sipariş etmeniz gerektiğini önceden görün, stok krizini yaşamadan önleyin.

### 📊 Raporlama
Ürünler, siparişler, müşteriler ve envanter hareketlerini tek tıkla Excel'e aktarın.

---

## Ekran Görüntüleri

| Dashboard | AI Asistan | Stok Yönetimi |
|-----------|-----------|---------------|
| ![Dashboard](assets/dashboard.png) | ![AI Asistan](assets/ai-asistan.png) | ![Stok Yönetimi](assets/stok-yonetimi.png) |

---

## Hızlı Başlangıç

**Gereksinimler:** Python 3.10+, Supabase hesabı, OpenAI API anahtarı

```bash
git clone https://github.com/kullanici-adi/nexus-kooperatif.git
cd nexus-kooperatif

python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# .env dosyasını düzenle

alembic upgrade head
uvicorn main:app --reload
```

`.env` dosyası:
```env
# Supabase → Settings > Database > Connection String (Transaction pooler önerilir)
DATABASE_URL=postgresql://postgres.[proje-id]:[sifre]@aws-0-[bolge].pooler.supabase.com:6543/postgres

OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=YOUR_TELEGRAM_BOT_TOKEN   # opsiyonel
```

Sunucu ayağa kalktıktan sonra:
- **API Docs** → `http://localhost:8000/docs`
- **Web Paneli** → `index.html` dosyasını tarayıcıda açın
- **Telegram Bot** → `python telegram_bot.py`

---

## Deploy (Railway)

Proje Railway üzerinde production'da çalışmaktadır. Kendi ortamınıza deploy etmek için:

1. [Railway](https://railway.app)'de yeni bir proje oluşturun
2. Bu repoyu GitHub'dan bağlayın
3. Environment variable'ları Railway dashboard'dan girin (`DATABASE_URL`, `OPENAI_API_KEY`, `TELEGRAM_BOT_TOKEN`)
4. Start command olarak şunu girin:
   ```
   uvicorn main:app --host 0.0.0.0 --port $PORT
   ```
5. Railway otomatik olarak build edip deploy eder

Veritabanı olarak [Supabase](https://supabase.com) kullanılmaktadır. Supabase projenizi oluşturduktan sonra `DATABASE_URL`'i Transaction Pooler bağlantı stringiyle doldurun, ardından migration'ları çalıştırın:
```bash
alembic upgrade head
```

---

## Mimari

Sistem üç katmandan oluşur: bir FastAPI backend, bir web yönetim paneli ve bir Telegram botu. AI tarafında iki aşamalı bir yönlendirme çalışır — sık kullanılan komutlar kural tabanlı intent parser tarafından milisaniyede karşılanır, parser'ın çözemediği mesajlar LangGraph üzerindeki GPT-4o-mini agent'a iletilir. Agent, 18 adet tool ile ürün, sipariş, müşteri ve kargo servislerine doğrudan erişir.

```
Telegram / Web Paneli
        │
   FastAPI Backend
   ├── /orders  /products  /cargo
   ├── /customers  /tickets  /ml
   └── /agent
        │
   ┌────┴──────────────────────┐
   │  Intent Parser            │  ← hızlı, kural tabanlı
   │  LangGraph Agent          │  ← GPT-4o-mini + 18 tool
   └───────────────────────────┘
        │
   PostgreSQL + ML Layer
```

---

## API

Tüm endpoint'ler `http://localhost:8000/docs` üzerinden interaktif olarak test edilebilir.

| Endpoint | Açıklama |
|----------|----------|
| `POST /agent/chat` | AI asistanla konuş |
| `GET /orders` | Sipariş listesi |
| `POST /orders` | Yeni sipariş |
| `GET /cargo/{tracking}` | Kargo takibi |
| `GET /ml/forecast/{product_id}` | Talep tahmini |
| `GET /ml/price-suggest/{product_id}` | Fiyat önerisi |
| `POST /marketplace/sync-trendyol` | Trendyol senkronizasyonu |

---

## Teknoloji Yığını

| | |
|--|--|
| **Backend** | FastAPI, SQLAlchemy, Alembic |
| **Veritabanı** | Supabase (PostgreSQL) |
| **Hosting** | Railway |
| **AI / LLM** | LangGraph, LangChain, GPT-4o-mini |
| **ML** | scikit-learn, NumPy, APScheduler |
| **Bot** | python-telegram-bot 21 |
| **Raporlama** | openpyxl |

---

## Katkı

Pull request'ler açık. Büyük değişiklikler için önce bir issue açın.

---

## Lisans

MIT
