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

### :brain: Otonom AI Ajanı (LangGraph & LLM)
```text
Sistemin kalbinde yer alan AI ajanı, statik menülerin ötesine geçer:
   - Doğal Dil Anlama: Kullanıcıların "Hangi ürünün stoğu bitiyor?" veya "Geçen haftanın en çok satanlarını raporla"
     gibi karmaşık isteklerini anlar.
   - Fonksiyonel Entegrasyon (Tool-Calling): Ajan, veritabanına doğrudan erişerek sipariş oluşturabilir, stok
     güncelleyebilir veya kargo sorgusu yapabilir.
   - Akıllı Yönlendirme: Gelen mesajın basit bir komut mu yoksa derinlemesine bir analiz mi gerektirdiğine karar vererek
     kullanıcıyı asiste eder.
```


### :bar_chart: Tahminlemeli Analitik (ML Katmanı)
```text

Veri odaklı karar verme mekanizmaları:
   - Talep Tahminleme (Demand Forecasting): Geçmiş satış trendlerini analiz ederek, hangi dönemde hangi üründen ne kadar
     stok bulundurulması gerektiğini hesaplar.
   - Fiyat Danışmanı (Price Advisor): Stok maliyeti, talep yoğunluğu ve ürün tazeliği gibi verileri kullanarak karlılığı
     maksimize edecek dinamik fiyat önerileri sunar.
```

### 🤖 Çok Fonksiyonlu Telegram Botu
```text
Farklı kullanıcı tipleri için özelleşmiş tek bir iletişim kanalı:
   - Müşteri Arayüzü: Ürün listeleme, sepet yönetimi, kolay sipariş ve canlı kargo takibi.
   - Yönetici/Personel Arayüzü: Mobil cihazdan stok girişi, anlık satış raporları, destek taleplerini (tickets) yönetme
     ve AI asistan ile doğrudan konuşma.
```


### 🎙️ Sesli Komut ve Sipariş Yönetimi
```text
STT (Speech-to-Text) Entegrasyonu: Kullanıcı deneyimini artırmak amacıyla Web Speech API kullanılmıştır. 
Bu sayede kullanıcılar, metin yazmak yerine sesli komutlar vererek sistemle doğal bir şekilde etkileşime girebilirler.

Dinamik Sipariş Yönlendirmesi: Telegram botu üzerinden verilen siparişler, kullanıcıyı doğrudan güvenli bir sipariş verme linkine yönlendirerek işlemin web tabanlı arayüz üzerinden hızlıca tamamlanmasını sağlar.
```

### :computer: 4. Modern Yönetici Paneli (Dashboard)
```text
Kooperatif yöneticileri için merkezi kontrol merkezi:
   - Veri Görselleştirme: Satışların, stokların ve müşteri büyümesinin grafiksel analizi.
   - AI Chat Interface: Dashboard üzerinden AI ajanı ile yazışarak hızlı aksiyon alma.
```

## 🛠 Teknoloji Yığını
- Backend: Python 3.10+, FastAPI (Asenkron API yapısı)
- AI/LLM: LangChain, LangGraph, OpenAI GPT-4o-mini
- Veri & ML: Scikit-learn, Pandas, NumPy
- Veritabanı: PostgreSQL, SQLAlchemy (ORM), Alembic (Migrations)
- Bot: python-telegram-bot (Long-polling & Webhook desteği)
- Frontend: HTML5, CSS3 (Vanilla), JavaScript (ES6+)
- Deployment: Railway (Web + Worker mimarisi)


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
- Python 3.10+ yüklü olduğundan emin olun.
- Bir PostgreSQL veritabanı oluşturun.
- OpenAI API Key ve Telegram Bot Token edinin.
```

## 2. Kurulum Adımları
```text
# Depoyu klonlayın
    git clone https://github.com/kullaniciadi/nexus-coop.git
    cd nexus-coop
# Bağımlılıkları yükleyin
   pip install -r backend/requirements.txt
# .env dosyasını oluşturun ve doldurun
# DATABASE_URL, OPENAI_API_KEY, TELEGRAM_BOT_TOKEN
```

## 3. Çalıştırma
```text
# Veritabanını güncelleyin
  cd backend
  alembic upgrade head
# Uygulamayı başlatın
  uvicorn main:app --reload
```

## 🚀 Canlıya Alma (Deployment)
```text
Bu proje Railway üzerinde aktif olarak çalışmaktadır.
Otomatik Süreç: API ve Bot, Procfile sayesinde aynı anda çalışır.
CI/CD: Ana şubeye yapılan her push otomatik olarak canlıya yansır.
```
