# Instagram DM Otomasyon (Hackathon Demo)

Bu branch/?al??ma alan?, **Python + Selenium** ile Instagram DM otomasyonu i?in g?venli ve mod?ler bir ba?lang?? mimarisi i?erir.

## ?zellikler
- Instagram login (.env ile g?venli kimlik bilgisi y?netimi)
- DM okuma altyap?s?
- Otomatik yan?t (handler + service katman?)
- Mod?ler yap? (ileride Telegram/WhatsApp kanallar? i?in geni?letilebilir)

## Dizin Yap?s?
```text
project_root/
?
??? channels/
?   ??? instagram/
?       ??? bot.py
?       ??? login.py
?       ??? message_reader.py
?       ??? message_sender.py
?       ??? handlers.py
?
??? services/
?   ??? order_service.py
?   ??? support_service.py
?   ??? cargo_service.py
?
??? .env.example
??? .gitignore
??? requirements.txt
??? main.py
```

## Kurulum
1. Sanal ortam olu?turun ve aktif edin.
2. Ba??ml?l?klar? kurun:
   ```bash
   pip install -r requirements.txt
   ```
3. `.env.example` dosyas?n? kopyalay?p `.env` olu?turun:
   ```bash
   copy .env.example .env
   ```
4. `.env` dosyas?n? doldurun:
   ```env
   INSTAGRAM_USERNAME=your_username
   INSTAGRAM_PASSWORD=your_password
   INSTAGRAM_HEADLESS=false
   INSTAGRAM_AUTO_REPLY_ENABLED=true
   INSTAGRAM_AUTO_REPLY_TEXT=Merhaba, mesaj?n?z al?nd?. En k?sa s?rede d?n?? yapaca??z.
   ```

## ?al??t?rma
```bash
python main.py
```

## G?venlik Notlar?
- Instagram kullan?c? ad?/?ifre **koda hardcode edilmez**.
- T?m gizli bilgiler `.env` dosyas?ndan okunur.
- `.env` dosyas? `.gitignore` i?inde yer al?r.
- Uygulama loglar?nda hassas bilgi yazd?r?lmaz.

## Geni?letme Plan?
- `services/` katman? mevcut backend API?leriyle entegre edilebilir.
- `channels/` alt?na `telegram/`, `whatsapp/` benzeri yeni kanallar eklenebilir.
- Selector stabilitesi i?in ileride merkezi `selectors.py` veya test katman? eklenebilir.
