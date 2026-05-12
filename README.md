# 🚀 Nexus: Yapay Zeka Destekli Akıllı Kooperatif Ekosistemi
Nexus, geleneksel kooperatifçilik modellerini günümüz teknolojileriyle harmanlayan uçtan uca bir yönetim ve operasyon platformudur. Küçük üreticilerin ve kooperatiflerin, dev e-ticaret platformlarıyla rekabet edebilecek analitik güce ve operasyonel hıza ulaşmasını sağlar.



## 📝 Genel Bakış
Nexus, sadece bir stok takip programı değildir. Veriyi işleyen, geleceği tahmin eden ve kullanıcıyla doğal dilde etkileşime giren entegre bir ekosistemdir.



## Sistem Bileşenleri:

FastAPI tabanlı güçlü bir backend
LangGraph ile güçlendirilmiş bir AI ajanı
Scikit-learn tabanlı ML modelleri
Çok kanallı bir Telegram arayüzü

## ✨ Temel Özellikler

1. Otonom AI Ajanı (LangGraph & LLM)
Sistemin kalbinde yer alan AI ajanı, statik menülerin ötesine geçer:
Doğal Dil Anlama: Kullanıcıların karmaşık isteklerini (örn: "Hangi ürünün stoğu bitiyor?") anlar.
Fonksiyonel Entegrasyon: Veritabanına doğrudan erişerek sipariş oluşturabilir veya stok güncelleyebilir.
Akıllı Yönlendirme: Gelen mesajın analiz mi yoksa basit bir komut mu gerektirdiğine karar verir.


2. Tahminlemeli Analitik (ML Katmanı)
Talep Tahminleme: Geçmiş satış trendlerini analiz ederek gereken stok miktarını hesaplar.
Fiyat Danışmanı: Stok maliyeti ve ürün tazeliğine göre dinamik fiyat önerileri sunar.


3. Çok Fonksiyonlu Telegram & WhatsApp Botu
Müşteri Arayüzü: Ürün listeleme, sepet yönetimi ve canlı kargo takibi.
Yönetici/Personel Arayüzü: Mobil stok girişi, anlık satış raporları ve AI asistan ile konuşma.

## 🛠 Teknoloji Yığını
Backend: Python 3.10+, FastAPI

AI/LLM: LangChain, LangGraph, OpenAI GPT-4o-mini

Veri & ML: Scikit-learn, Pandas, NumPy

Veritabanı: PostgreSQL, SQLAlchemy, Alembic

Deployment: Railway


## 📂 Proje Yapısı
```text
├── backend/
│   ├── ai_agent/        # LangGraph ajan mimarisi
│   ├── api/             # FastAPI router yapıları
│   ├── database/        # Veri modelleri
│   ├── services/        # İş mantığı ve ML modelleri
│   └── main.py          # Uygulama giriş noktası
├── frontend/            # Dashboard dosyaları
├── railway.toml         # Deployment ayarları
└── requirements.txt     # Bağımlılıklar
```

## ⚙️ Kurulum ve Yerel Çalıştırma
## 1. Hazırlık
```text
Python 3.10+ ve PostgreSQL kurulu olmalıdır.
OpenAI API Key ve Telegram Bot Token hazır olmalıdır.
```
## 2. Kurulum Adımları
```text
Depoyu klonlayın
git clone [https://github.com/kullaniciadi/nexus-coop.git](https://github.com/kullaniciadi/nexus-coop.git)
cd nexus-coop
Bağımlılıkları yükleyin
pip install -r backend/requirements.txt
.env dosyasını oluşturun ve şu bilgileri ekleyin:
DATABASE_URL, OPENAI_API_KEY, TELEGRAM_BOT_TOKEN
```

## 3. Çalıştırma
```text
cd backend
alembic upgrade head
uvicorn main:app --reload
```
## 🚀 Canlıya Alma (Deployment)
```text
Bu proje Railway üzerinde aktif olarak çalışmaktadır.
Otomatik Süreç: API ve Bot, Procfile sayesinde aynı anda çalışır.
CI/CD: Ana şubeye yapılan her push otomatik olarak canlıya yansır.
```

## 🔮 Gelecek Vizyonu
```text
📸 Görüntü İşleme: Fotoğraf ile otomatik stok girişi.
⛓ Blockchain: Şeffaf tedarik zinciri takibi.
💳 Ödeme Entegrasyonu: Bot üzerinden ödeme alma.
```
