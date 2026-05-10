# yzta-kobi

# 🚀 NexusAI: Otonom KOBİ Operasyon Merkezi

NexusAI, KOBİ'lerin ve kooperatiflerin operasyonel yükünü sıfıra indirmeyi hedefleyen, yapay zeka ajanları tarafından yönetilen uçtan uca bir otomasyon sistemidir.

## 📋 Problem Tanımı
KOBİ'ler günlük 2-3 saatlerini manuel sipariş takibi ve müşteri sorularıyla kaybetmektedir. NexusAI, bu süreci otonom hale getirerek verimliliği artırır.

## ✨ Temel Özellikler
*   **Müşteri İletişim Otomasyonu:** Telegram/WhatsApp üzerinden doğal dil ile sipariş ve stok sorgulama.
*   **Proaktif Kargo Takibi:** Gecikmeleri müşteri sormadan tespit edip bildirme.
*   **Akıllı Stok Yönetimi:** Kritik eşik analizi ve otomatik tedarikçi mail taslağı hazırlama.
*   **Sabah Raporu:** Yöneticiye her sabah operasyonel özet sunumu.

## 🛠 Teknik Mimari
*   **LLM:** GPT-4o / Claude 3.5 Sonnet
*   **Orchestration:** CrewAI / LangChain
*   **Database/API:** Airtable (Stok ve Sipariş Yönetimi)
*   **Interface:** Telegram Bot API & Streamlit Dashboard

## 🚀 Kurulum
1. Repoyu klonlayın: `git clone https://github.com/kullanici/nexus-ai.git`
2. Bağımlılıkları yükleyin: `pip install -r requirements.txt`
3. `.env` dosyasını oluşturun ve API keylerinizi girin.
4. Uygulamayı başlatın: `python src/main.py`
