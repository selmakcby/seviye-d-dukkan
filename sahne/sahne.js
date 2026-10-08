// Dükkan sahnesi: cikti/olaylar.jsonl'u 1 sn'de bir okur, ajanları istasyon istasyon gösterir.
// Yeni rol eklemek: betik tarafında olay("<rol>", ...) çağır, buraya bir İSTASYON satırı ekle.
(function () {
'use strict';

/* ---------- İSTASYONLAR: sahnedeki her durak (x = merkez, 1920×1080 tuval) ---------- */
const SATIR_Y = 240, RAY_Y = 690;
const SUTUN = (i) => 160 + i * 267;
const ISTASYONLAR = [
  { id: 'gelen', ad: 'GELEN KUTUSU', renk: 'dim', x: SUTUN(0), cizim: 'zarflar', bos: 'sabah kutusu dolu' },
  { id: 'betik', ad: 'BETİK · 0 TOKEN', renk: 'amber', x: SUTUN(1), gorsel: 'poz-insaat.png', roller: ['betik'] },
  { id: 'bekci', ad: 'BEKÇİ · HAIKU', renk: 'cyan', x: SUTUN(2), gorsel: 'poz-kontrol.png', roller: ['bekci'] },
  { id: 'masa', ad: 'MASA · SONNET', renk: 'violet', x: SUTUN(3), gorsel: 'poz-selam.png', roller: ['masa', 'claude'] },
  { id: 'yazici', ad: 'YAZICI · SONNET', renk: 'violet', x: SUTUN(4), gorsel: 'poz-belge.png', roller: ['yazici'] },
  { id: 'yonetici', ad: 'YÖNETİCİ', renk: 'green', x: SUTUN(5), gorsel: 'poz-fikir.png', roller: ['yonetici'] },
  { id: 'rapor', ad: 'RAPOR', renk: 'ink', x: SUTUN(6), cizim: 'kagit', bos: 'sabah-raporu.md bekliyor' },
  { id: 'hermes', ad: 'HERMES · HAIKU', renk: 'cyan', x: 184, y: 760, gorsel: 'clawd-duz.png', roller: ['hermes'], yan: true },
];
const ROL_ADI = { betik: 'BETİK', bekci: 'BEKÇİ', masa: 'MASA', yazici: 'YAZICI', yonetici: 'YÖNETİCİ', hermes: 'HERMES', claude: 'CLAUDE' };
const ROL_RENK = { betik: 'amber', bekci: 'cyan', masa: 'violet', yazici: 'violet', yonetici: 'green', hermes: 'cyan', claude: 'violet' };
const SAYACLAR = [['mesaj', 'mesaj', 'ink'], ['kalip', 'kalıp', 'green'], ['zor', 'zor', 'violet'],
  ['tuzak', 'tuzak', 'red'], ['insana', 'insana', 'amber']];
const DEVIR_X = SUTUN(3), DEVIR_Y = 845, HERMES_SAG = 760;
const ADIM_CANLI = 700, ADIM_TEKRAR = 1000, SORGU_MS = 1000, KAYIT_SATIR = 6;

const $ = (id) => document.getElementById(id);
const rolIstasyonu = (rol) => ISTASYONLAR.find((i) => (i.roller || []).includes(rol));

/* ---------- durum: saf fonksiyonlar, her olay yeni bir durum döndürür ---------- */
function bosDurum() {
  const ist = Object.fromEntries(ISTASYONLAR.map((i) => [i.id, { durum: 'bekliyor', satirlar: [], usd: 0 }]));
  return { ist, sayac: { mesaj: 0, kalip: 0, zor: 0, tuzak: 0, insana: 0 }, usd: 0, kayit: [], aktif: null, devir: false };
}

function satirlariGuncelle(eski, olay) {
  if (olay.rol === 'hermes' || olay.rol === 'claude') {
    const en = olay.rol === 'hermes' ? 3 : 2;  // devir masanın özetini silmesin, altına eklensin
    const sonDegisir = (olay.rol === 'hermes' && olay.durum === 'not') || (olay.rol === 'claude' && olay.durum === 'bitti');
    if (sonDegisir) return [...eski.slice(0, -1), olay.detay].slice(-en);
    return olay.durum === 'basladi' ? [...eski, olay.detay].slice(-en) : eski;
  }
  if (olay.durum === 'not') return [...eski, olay.detay].slice(-2);
  return [olay.detay];
}

const MODELLI = ['bekci', 'masa', 'yazici'];
function kuralMi(ist, olay) {
  if (olay.durum === 'basladi') return /kural|şablon|sadece/.test(olay.detay || '');
  if (olay.durum === 'bitti' && MODELLI.includes(olay.rol)) return (olay.maliyet_usd || 0) === 0 && !(ist.usd > 0);
  return !!ist.kural;
}
function istasyonGuncelle(ist, olay) {
  const yeniDurum = olay.durum === 'bitti' ? 'bitti' : 'calisiyor';
  return { durum: yeniDurum, satirlar: satirlariGuncelle(ist.satirlar, olay), usd: ist.usd + (olay.maliyet_usd || 0), kural: kuralMi(ist, olay) };
}

function turetilmis(ist, olay, sayac) {
  const ek = {};
  if (olay.rol === 'betik' && olay.durum === 'basladi') ek.gelen = { durum: 'calisiyor', satirlar: ['betiğe gidiyor'], usd: 0 };
  if (olay.rol === 'betik' && olay.durum === 'bitti') {
    ek.gelen = { durum: 'bitti', satirlar: [sayac.mesaj + ' mesaj · 20 ürün · 12 fatura'], usd: 0 };
  }
  if (olay.rol === 'yonetici' && olay.durum === 'bitti') {
    ek.rapor = { durum: 'bitti', satirlar: ['cikti/sabah-raporu.md', 'insana ' + (sayac.tuzak + sayac.insana) + ' · en üstte'], usd: 0 };
  }
  return { ...ist, ...ek };
}

function uygula(d, olay) {
  const hedef = rolIstasyonu(olay.rol);
  if (!hedef) return d;
  const sayac = { ...d.sayac, ...(olay.sayac || {}) };
  const ist = turetilmis({ ...d.ist, [hedef.id]: istasyonGuncelle(d.ist[hedef.id], olay) }, olay, sayac);
  const devir = olay.rol === 'claude' ? olay.durum === 'basladi' : (olay.rol === 'hermes' ? d.devir : false);
  return { ist, sayac, usd: d.usd + (olay.maliyet_usd || 0), kayit: [...d.kayit, olay].slice(-KAYIT_SATIR),
    aktif: olay.rol === 'claude' ? 'devir' : hedef.id, devir };
}

/* ---------- çizim: iskelet bir kez, sonra yalnız değişen alanlar ---------- */
const CIZIMLER = {
  zarflar: '<svg viewBox="0 0 200 150" width="200" height="150">' + [0, 1, 2].map((k) =>
    '<g transform="translate(' + (30 + k * 12) + ',' + (78 - k * 26) + ') rotate(' + (k * 5 - 5) + ')">' +
    '<rect width="120" height="80" rx="6" fill="#fffdf8" stroke="#2b2a27" stroke-width="4"/>' +
    '<path d="M4 6 L60 46 L116 6" fill="none" stroke="#2b2a27" stroke-width="4"/></g>').join('') + '</svg>',
  kagit: '<svg viewBox="0 0 150 150" width="150" height="150"><path d="M30 6 H100 L124 30 V144 H30 Z" fill="#fffdf8" stroke="#2b2a27" stroke-width="4"/>' +
    '<path d="M100 6 V30 H124" fill="none" stroke="#2b2a27" stroke-width="4"/>' +
    [46, 64, 82, 100, 118].map((y, i) => '<rect x="44" y="' + y + '" width="' + (i % 2 ? 50 : 66) + '" height="7" rx="3" fill="' +
    (i === 0 ? '#b8322a' : '#c9bfa9') + '"/>').join('') + '</svg>',
};

function istasyonHtml(i) {
  const gorsel = i.cizim ? CIZIMLER[i.cizim] : '<img src="/gorseller/' + i.gorsel + '" alt="">';
  const sol = '<div class="kare">' + gorsel + '<span class="tik">✓</span></div>' +
    '<div class="rol">' + i.ad + '</div><div class="usd"></div>';
  const balon = '<div class="balon"></div>';
  const ic = i.yan ? '<div class="sol">' + sol + '</div>' + balon : balon + sol;
  return '<div class="ist bekliyor c-' + i.renk + (i.yan ? ' yan' : '') + '" id="ist-' + i.id + '" style="left:' +
    (i.x - 120) + 'px;top:' + (i.y || SATIR_Y) + 'px">' + ic + '</div>';
}

function yollarSvg() {
  const oklar = ISTASYONLAR.filter((i) => !i.yan).slice(0, -1).map((i) =>
    '<text x="' + (i.x + 133) + '" y="' + (SATIR_Y + 255) + '" text-anchor="middle" font-family="JetBrains Mono" font-weight="700" font-size="46" fill="#8b867b">→</text>');
  return '<path class="ray" d="M' + SUTUN(0) + ' ' + RAY_Y + ' H' + SUTUN(6) + '"/>' + oklar.join('') +
    '<defs><marker id="uc" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto">' +
    '<path d="M0 0 L10 5 L0 10 Z" fill="#6a4597"/></marker></defs>' +
    '<path id="devir" class="devir" marker-end="url(#uc)" d="M' + HERMES_SAG + ' ' + DEVIR_Y + ' H' + DEVIR_X + ' V' + (RAY_Y - 16) + '"/>' +
    '<text id="devir-yazi" class="devir-yazi" x="' + (DEVIR_X + 18) + '" y="' + (DEVIR_Y - 30) + '">claude -p</text>';
}

function iskeletKur() {
  $('istasyonlar').innerHTML = ISTASYONLAR.map(istasyonHtml).join('');
  $('yollar').innerHTML = yollarSvg();
  $('sayac').innerHTML = SAYACLAR.map(([k, ad, r]) => '<span class="c-' + r + '" id="s-' + k + '">' + ad + ' <b>0</b></span>').join('') +
    '<span class="c-violet" id="s-usd">maliyet <b>0,00 USD</b></span>';
}

const kacis = (s) => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const usdYaz = (x, b) => x.toFixed(b).replace('.', ',') + ' USD';

function istasyonCiz(i, d) {
  const el = $('ist-' + i.id), s = d.ist[i.id];
  const kural = !!s.kural && (i.roller || []).some((r) => MODELLI.includes(r));
  el.className = 'ist ' + s.durum + ' c-' + (kural ? 'dim' : i.renk) + (i.yan ? ' yan' : '') + (kural ? ' kural' : '');
  el.querySelector('.rol').textContent = kural ? i.ad.split(' · ')[0] + ' · KURAL' : i.ad;
  if (i.id === 'hermes') {
    const gizli = s.durum === 'bekliyor';
    el.style.display = gizli ? 'none' : '';
    ['devir', 'devir-yazi'].forEach((k) => { const e = $(k); if (e) e.style.display = gizli ? 'none' : ''; });
  }
  const satirlar = s.satirlar.length ? s.satirlar : [i.bos || 'bekliyor…'];
  const bos = !s.satirlar.length;
  const html = satirlar.map((t) => '<p' + (bos ? ' class="bos"' : '') + '>' + kacis(t) + '</p>').join('');
  const balon = el.querySelector('.balon');
  if (balon.innerHTML !== html) balon.innerHTML = html;
  el.querySelector('.usd').textContent = s.usd > 0 ? usdYaz(s.usd, 4) : '';
}

function sayacCiz(d) {
  const degerler = [...SAYACLAR.map(([k]) => [k, String(d.sayac[k] || 0)]), ['usd', usdYaz(d.usd, 2)]];
  degerler.forEach(([k, v]) => {
    const b = $('s-' + k).querySelector('b');
    if (b.textContent === v) return;
    b.textContent = v;
    $('s-' + k).classList.add('oynadi');
    setTimeout(() => $('s-' + k).classList.remove('oynadi'), 260);
  });
}

function zarfCiz(d) {
  const hedef = d.aktif === 'devir' ? [DEVIR_X, DEVIR_Y] : d.aktif === 'hermes' ? [HERMES_SAG, DEVIR_Y]
    : [(ISTASYONLAR.find((i) => i.id === d.aktif) || ISTASYONLAR[0]).x, RAY_Y];
  $('zarf').style.transform = 'translate(' + (hedef[0] - 26) + 'px,' + (hedef[1] - 19) + 'px)';
  $('devir').classList.toggle('acik', d.devir);
  $('devir-yazi').classList.toggle('acik', d.devir);
}

function kayitCiz(d) {
  $('kayit').innerHTML = d.kayit.slice().reverse().map((o) => {
    const saat = new Date(o.t * 1000).toTimeString().slice(0, 8);
    return '<li class="c-' + (ROL_RENK[o.rol] || 'dim') + '"><i>' + saat + '</i><b>' + (ROL_ADI[o.rol] || o.rol) + '</b>' +
      kacis(o.detay || o.durum) + '</li>';
  }).join('') || '<li><i>--:--:--</i>henüz olay yok · ./calistir.sh</li>';
}

function ciz(d) {
  ISTASYONLAR.forEach((i) => istasyonCiz(i, d));
  sayacCiz(d);
  zarfCiz(d);
  kayitCiz(d);
}

/* ---------- akış: sorgu → kuyruk → adım adım uygula ---------- */
let durum = bosDurum(), okunan = 0, kuyruk = [], tekrarda = false, bagli = true;

async function sorgula() {
  try {
    const cevap = await fetch('/olaylar?since=' + okunan, { cache: 'no-store' });
    bagli = cevap.ok;
    if (!cevap.ok) return;
    const veri = await cevap.json();
    if (veri.sifirla) { durum = bosDurum(); kuyruk = []; ciz(durum); }
    okunan = veri.toplam;
    kuyruk = [...kuyruk, ...veri.olaylar];
  } catch (hata) {
    bagli = false;
  }
}

function adimAt() {
  if (kuyruk.length) {
    const [ilk, ...kalan] = kuyruk;
    kuyruk = kalan;
    durum = uygula(durum, ilk);
    ciz(durum);
  } else if (tekrarda) {
    tekrarda = false;
  }
  $('mod').className = 'mod' + (tekrarda ? ' tekrar' : '');
  $('mod').textContent = !bagli ? 'sunucu yok' : tekrarda ? 'tekrar oynatılıyor' : 'canlı';
  setTimeout(adimAt, tekrarda ? ADIM_TEKRAR : ADIM_CANLI);
}

async function tekrarOynat() {
  const cevap = await fetch('/olaylar?since=0', { cache: 'no-store' });
  const veri = await cevap.json();
  okunan = veri.toplam;
  kuyruk = veri.olaylar;
  durum = bosDurum();
  tekrarda = true;
  ciz(durum);
}

async function baslat() {
  iskeletKur();
  await sorgula();
  durum = kuyruk.reduce(uygula, bosDurum());  // sayfa açılınca eski koşu anında yerine otursun
  kuyruk = [];
  ciz(durum);
  const olcekle = () => {
    const k = Math.min(innerWidth / 1920, innerHeight / 1080);
    $('sahne').style.transform = 'translate(-50%,-50%) scale(' + k + ')';
  };
  olcekle();
  addEventListener('resize', olcekle);
  $('tekrar').addEventListener('click', () => { tekrarOynat().catch(() => { bagli = false; }); });
  setInterval(sorgula, SORGU_MS);
  setTimeout(adimAt, ADIM_CANLI);
  if (new URLSearchParams(location.search).has('tekrar')) tekrarOynat();
}

baslat();
})();
