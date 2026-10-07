# Ölçüm sonucu · 07.10.2026

Sırça Seramik örnek verisi: 30 müşteri mesajı, 20 ürün, 12 ödeme. Maliyet: `claude -p --output-format json` çıktısındaki `total_cost_usd`. Süre: duvar saati. Doğruluk: `veri/cevap-anahtari.json` (30 mesaj türü, 7 eşik altı ürün + 5 geciken ödeme = 12 uyarı, 1 tuzak, 1 para/iade).

| Yol | Koşu | USD | Süre (sn) | Mesaj türü doğru | Stok+ödeme uyarısı (yanlış alarm) | Tuzak | Para/iade insana | Model dağılımı |
|---|---|---|---|---|---|---|---|---|
| NAİF: Opus ajanına veri/ klasörünü ver | 1 | 0,2697 | 72 | 30/30 | 12/12 (0) | 1/1 | 1/1 | claude-opus-5-5 0,2697 |
| NAİF: Opus ajanına veri/ klasörünü ver | 2 | 0,3855 | 103 | 29/30 | 12/12 (0) | 1/1 | 1/1 | claude-opus-5-5 0,3855 |
| **NAİF: Opus ajanına veri/ klasörünü ver** | **ortalama** | **0,3276** | **88** | | | | | |
| HAT: betik + Haiku bekçi + Sonnet | 1 | 0,0319 | 31 | 30/30 | 12/12 (0) | 1/1 | 1/1 | claude-haiku-4-5-20251001 0,0099, claude-sonnet-5-5 0,0220 |
| HAT: betik + Haiku bekçi + Sonnet | 2 | 0,0314 | 29 | 30/30 | 12/12 (0) | 1/1 | 1/1 | claude-haiku-4-5-20251001 0,0102, claude-sonnet-5-5 0,0212 |
| **HAT: betik + Haiku bekçi + Sonnet** | **ortalama** | **0,0316** | **30** | | | | | |
| SADECE BETİK: kurallar + şablonlar | 1 | 0,0000 | 0 | 27/30 | 12/12 (0) | 1/1 | 1/1 | model yok |
| **SADECE BETİK: kurallar + şablonlar** | **ortalama** | **0,0000** | **0** | | | | | |

**Ortalama maliyet oranı: naif yol hattın 10,3 katı.**

## Notlar: bizim ölçümümüz (7 Ekim 2026, dürüst okuma)

- **Kazanç maliyette ve hızda.** Hat iki koşuda da 30/30, 12/12, tuzak 1/1 buldu; naif Opus ajanı ortalama 10,3 kat pahalı (0,328 vs 0,032 USD) ve ~3 kat yavaş (88 vs 30 sn).
- **Opus da yanlış yapmıyor sayılır.** Naif 2. koşu 014 numaralı mesajı ("takip numarası çalışmıyor, kargom nerede") insana verdi; cevap anahtarında kalıp sipariş sorusu. Savunulabilir bir karar, ama aynı ajan aynı veride iki koşuda farklı karar verdi (1. koşu 8 tur, 2. koşu 37 tur ve 0,39 USD). Naif yolun maliyeti de kararı da koşudan koşuya oynuyor.
- **Sadece betik 0 token'la çok yol alıyor.** Stok ve ödeme 12/12, tuzak ve iade kural kalıbıyla 1/1. Kaçırdığı tek şey 3 zor soru: anahtar kelimeye bakıp "kalıp" sandı ve düğün çiftine tabağın etiket fiyatını yazdı. Haiku bekçinin bütün işi bu 3 mesaj ve onu ~1 sente yapıyor.
- **Model hesap yapmıyor.** Eşik formülü ve gecikme günleri betikte; Sonnet sadece metni yazıyor. Yazıcı taslaklarında sayılar tablodakiyle aynı çıktı (elle kontrol edildi).
- **Önbellek etkisi.** Hat koşuları gün içinde önbellekten okudu. Aynı gün önbellek ısınmadan yapılan ilk tam koşular 0,045 USD tuttu; o durumda bile naif yol ~7 kat pahalı.
- **Hermes bu tabloda yok.** `./hermes/calistir.sh` ayrı ölçülür (`cikti/hermes-masa.md`): Hermes (Haiku) mesaj başına 0,002-0,05 USD tahmini (önbellek ısınınca alt uçta; ilk denemede kalıp soruda 11 API çağrısıyla 0,09 USD gördük, rol metni sıkılaşınca 1-2 çağrıya indi); zor soruda Claude Code devri (Sonnet) ~0,003 USD.
- **Ortam:** Claude Code 2.1.287, Ekim 2026 liste fiyatları. Naif koşu `--setting-sources project` ile koştu, kişisel CLAUDE.md yüklü kaldı (gerçek kullanımdaki gibi); hattın çağrıları kişisel CLAUDE.md'yi dışarıda bırakır. Senin sayıların farklı çıkabilir, `./olc/olc.sh` ile kendin ölç.
