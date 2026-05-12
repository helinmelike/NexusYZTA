Nexus: Yapay Zeka Destekli Akıllı Kooperatif Ekosistemi

  Nexus, geleneksel kooperatifçilik modellerini günümüz teknolojileriyle harmanlayan uçtan uca bir yönetim ve
  operasyon platformudur. Küçük üreticilerin ve kooperatiflerin, dev e-ticaret platformlarıyla rekabet
  edebilecek analitik güce ve operasyonel hıza ulaşmasını sağlar.

  ---

  Genel Bakış

  Nexus, sadece bir stok takip programı değildir. Veriyi işleyen, geleceği tahmin eden ve kullanıcıyla doğal dilde
  etkileşime giren entegre bir ekosistemdir. Sistem; FastAPI tabanlı güçlü bir backend, LangGraph ile güçlendirilmiş bir
  AI ajanı, Scikit-learn tabanlı ML modelleri ve çok kanallı bir Telegram arayüzünden oluşur.

  ---

  Temel Özellikler

  1. Otonom AI Ajanı (LangGraph & LLM)
  Sistemin kalbinde yer alan AI ajanı, statik menülerin ötesine geçer:
   - Doğal Dil Anlama: Kullanıcıların "Hangi ürünün stoğu bitiyor?" veya "Geçen haftanın en çok satanlarını raporla"
     gibi karmaşık isteklerini anlar.
   - Fonksiyonel Entegrasyon (Tool-Calling): Ajan, veritabanına doğrudan erişerek sipariş oluşturabilir, stok
     güncelleyebilir veya kargo sorgusu yapabilir.
   - Akıllı Yönlendirme: Gelen mesajın basit bir komut mu yoksa derinlemesine bir analiz mi gerektirdiğine karar vererek
     kullanıcıyı asiste eder.

  2. Tahminlemeli Analitik (ML Katmanı)
  Veri odaklı karar verme mekanizmaları:
   - Talep Tahminleme (Demand Forecasting): Geçmiş satış trendlerini analiz ederek, hangi dönemde hangi üründen ne kadar
     stok bulundurulması gerektiğini hesaplar.
   - Fiyat Danışmanı (Price Advisor): Stok maliyeti, talep yoğunluğu ve ürün tazeliği gibi verileri kullanarak karlılığı
     maksimize edecek dinamik fiyat önerileri sunar.

  3. Çok Fonksiyonlu Telegram & WhatsApp Botu
  Farklı kullanıcı tipleri için özelleşmiş tek bir iletişim kanalı:
   - Müşteri Arayüzü: Ürün listeleme, sepet yönetimi, kolay sipariş ve canlı kargo takibi.
   - Yönetici/Personel Arayüzü: Mobil cihazdan stok girişi, anlık satış raporları, destek taleplerini (tickets) yönetme
     ve AI asistan ile doğrudan konuşma.

  4. Modern Yönetici Paneli (Dashboard)
  Kooperatif yöneticileri için merkezi kontrol merkezi:
   - Veri Görselleştirme: Satışların, stokların ve müşteri büyümesinin grafiksel analizi.
   - AI Chat Interface: Dashboard üzerinden AI ajanı ile yazışarak hızlı aksiyon alma.

  ---

  Teknoloji Yığını

   - Backend: Python 3.10+, FastAPI (Asenkron API yapısı)
   - AI/LLM: LangChain, LangGraph, OpenAI GPT-4o-mini
   - Veri & ML: Scikit-learn, Pandas, NumPy
   - Veritabanı: PostgreSQL, SQLAlchemy (ORM), Alembic (Migrations)
   - Bot: python-telegram-bot (Long-polling & Webhook desteği)
   - Frontend: HTML5, CSS3 (Vanilla), JavaScript (ES6+)
   - Deployment: Railway (Web + Worker mimarisi)

  ---

  Proje Yapısı

    1 ├── backend/
    2 │   ├── ai_agent/           # LangGraph ajan mimarisi ve araçlar
    3 │   ├── api/                # FastAPI modüler router yapıları
    4 │   ├── core/               # Konfigürasyon ve bağımlılık yönetimi
    5 │   ├── database/           # Veri modelleri ve repository katmanı
    6 │   ├── services/           # İş mantığı (Business Logic)
    7 │   │   └── ml/             # Makine öğrenimi modelleri (Talep & Fiyat)
    8 │   ├── telegram_bot/       # Bot menüleri ve AI Router mantığı
    9 │   └── main.py             # Uygulama giriş noktası
   10 ├── frontend/               # Statik Dashboard dosyaları
   11 ├── railway.toml            # Railway orkestrasyon dosyası
   12 ├── Procfile                # Çoklu süreç (Web + Bot) yönetim dosyası
   13 └── requirements.txt        # Bağımlılık listesi

  ---

  Kurulum ve Yerel Çalıştırma

  1. Hazırlık
   - Python 3.10+ yüklü olduğundan emin olun.
   - Bir PostgreSQL veritabanı oluşturun.
   - OpenAI API Key ve Telegram Bot Token edinin.

  2. Adımlar

   1 # Depoyu klonlayın
   2 git clone https://github.com/kullaniciadi/nexus-coop.git
   3 cd nexus-coop
   4
   5 # Bağımlılıkları yükleyin
   6 pip install -r backend/requirements.txt
   7
   8 # .env dosyasını oluşturun ve doldurun
   9 # DATABASE_URL, OPENAI_API_KEY, TELEGRAM_BOT_TOKEN

  3. Çalıştırma

   1 # Veritabanını güncelleyin
   2 cd backend
   3 alembic upgrade head
   4
   5 # Uygulamayı başlatın
   6 uvicorn main:app --reload

  ---

  Canlıya Alma (Deployment)

  Bu proje Railway üzerinde aktif olarak çalışmaktadır.

   - Otomatik Süreç Yönetimi: Railway, railway.toml ve Procfile sayesinde hem API'yi hem de Telegram Botu'nu iki ayrı
     servis olarak aynı anda çalıştırır.
   - Veritabanı: Railway PostgreSQL eklentisi üzerinden yönetilir.
   - CI/CD: Ana şubeye (main branch) yapılan her push işlemi otomatik olarak canlıya yansır.

  ---

  Gelecek Vizyonu

   - Görüntü İşleme: Üreticilerin ürün fotoğraflarını çekerek otomatik stok girişi yapabilmesi.
   - Blockchain Entegrasyonu: Ürünlerin tarladan sofraya takibini sağlayan şeffaf tedarik zinciri.
   - Ödeme Entegrasyonu: Bot üzerinden doğrudan ödeme alma (Stripe/Iyzico).

  ---
  Bu proje, kooperatifçilik ruhunu teknolojiyle buluşturmak amacıyla geliştirilmiştir.
