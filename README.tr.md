# CODE/X HQ

Proje klasörünüz için CRT terminal görünümlü bir
başlatıcı. Tüm projeleri listeler, onları Claude veya Codex ile açar, yeni
projeler oluşturur, adlarını değiştirir ve siler.

**Diller:** [Deutsch](README.md) · [English](README.en.md) ·
[Bosanski / Hrvatski / Srpski](README.bhs.md) · Türkçe ·
[Español](README.es.md)

Esas alınan metin Almanca README'dir; bu çeviri onu takip eder.

## Başlatma

**Hazır sürüm:** [Releases](https://github.com/DAHDO47/CODE-X-HQ/releases/latest) sayfasından
`CODE-X-HQ-windows-x64.zip` dosyasını indirin, açın ve
`ProjectHQ\ProjectHQ.exe` dosyasını çalıştırın — Python gerekmez. İlk
başlatmada **Ayarlar** altında proje klasörünüzü seçin (varsayılan:
`%USERPROFILE%\Projekte`). `claude` veya `codex` kurulu ve PATH içinde
olmalıdır.

Kaynaktan derlendiğinde `.exe` burada bulunur:

```
dist\ProjectHQ\ProjectHQ.exe
```

`.exe` dosyasını görev çubuğuna sabitleyin veya masaüstüne bir kısayol
koyun. Açılış dizisi bir tıklama veya tuşla atlanır;
`ProjectHQ.exe --no-boot` onu her zaman atlar.

## Kullanım

Her şeye fareyle ulaşılabilir: çift tıklama bir projeyi başlatır, sağ
tıklama tüm işlemleri içeren menüyü açar, soldaki yan menü seçili öğe için
aynı işlemleri sunar.

| Tuş | İşlem |
|-----|-------|
| Çift tıklama / F5 | Projeyi başlat |
| Ctrl+N | Yeni proje oluştur |
| F2 | Adını değiştir |
| Del | Sil (geri dönüşüm kutusuna) |
| F4 | Proje klasöründe terminal |
| F6 | Projenin görevleri Not Defteri'nde |
| Shift+F4 | Yönetici olarak terminal |
| Ctrl+D | Favori olarak sabitle veya çıkar |
| Ctrl+R | Listeyi yeniden oku, tarih ve ajanı yeniden hesapla |
| Ctrl+F | Aramaya git |
| Esc | Aramayı temizle, boşsa kapat |

Arama, yazarken canlı olarak ad **ve** türe göre filtreler: `node` tüm
Node projelerini gösterir. Bir sütun başlığına tıklamak listeyi ona göre
sıralar.

Listede altı sütun vardır:

```
 ►  PROJE             TÜR    AJAN       NOT     OLUŞTURMA    DÜZENLEME
 *  Tarkov            node   ■ CLAUDE     ≡     28.08.2026   05.09.2026
 ►  Webshop           py     ● CODEX      ≡     24.05.2026   02.08.2026
 ►  Homepage          web    –            ·     22.06.2026   27.07.2026
```

Liste `Ctrl+R` ile yeniden okunur — ve pencere tekrar öne geldiğinde
otomatik olarak. Bu arada Gezgin'de oluşan bir klasör böylece hemen
listede görünür. Seçim korunur.

İkisi arasında bir fark var: `DÜZENLEME` ve `AJAN` değerlerini hesaplamak
24 proje için yaklaşık 320 ms sürer — her Alt-Tab için fazla. Bu yüzden
otomatik tarama hatırlanan değerleri kullanır (yaklaşık 40 ms);
**`Ctrl+R` onları yeniden hesaplar**. HQ'nun hiç görmediği bir proje her
zaman hesaplanır; yeni bir klasör böylece hemen doğru tarihle görünür.

## Nasıl başlatılır

Başlatırken bir iletişim kutusu neyle başlatılacağını sorar:

```
┌─ NEYLE BAŞLATILSIN? ────────────┐
│  > PROJE:  Tarkov               │
│                                 │
│   ■  CLAUDE   Claude Code       │
│   □  CODEX    OpenAI Codex CLI  │
│                                 │
│  > KONSOL                       │
│   ■  CMD     □  POWERSHELL      │
│                                 │
│   □  YÖNETİCİ OLARAK            │
│   □  ONAY SORMADAN              │
│                                 │
│           [İPTAL]  [BAŞLAT]     │
└─────────────────────────────────┘
```

Son seçim önceden işaretlidir ve `BAŞLAT` varsayılan düğmedir —
**Enter'a basmak yeterlidir**, iletişim kutusu ek bir tıklamaya mal olmaz.
`Esc` iptal eder ve hiçbir şey başlatmaz.

Ardından proje klasörünü çalışma dizini olarak kullanan bir konsol açılır
ve seçilen ajan onun içinde çalışır. Komut özünde her zaman şudur:

```
cmd /K claude      ya da      cmd /K codex
```

`/K`, ajan kapandığında pencereyi açık tutar — çıktılar ve hatalar
okunabilir kalır. Klasörde ne olduğu önemli değildir: bir `start.bat` veya
`npm run dev` artık çalıştırılmaz.

Her yol aynı şekilde sorar — çift tıklama, `F5`, `BAŞLAT` düğmesi ve
`+ YENİ` sonrasında doğrudan başlatma. Seçilen ajan PATH içinde yoksa, bir
Windows hatası içeren konsol açmak yerine terminal görünümlü bir mesaj
bunu söyler.

Altında konsolu hangi kabuğun sağlayacağı seçilir: `CMD` veya
`POWERSHELL`. Ajanın kendisi için bu neredeyse hiçbir şeyi değiştirmez —
araçlarını kendisi seçer. Ancak PowerShell kendi profilinizi
(`$PROFILE`) yükler, `cmd` yüklemez.

Seçim `config.json` içinde `last_agent` ve `last_shell` olarak saklanır.
`YÖNETİCİ OLARAK` onay kutusu ise saklanmaz — her başlatmada yeniden
boştur. Hatırlanması, sonraki her başlatmanın sessizce bir UAC iletişim
kutusu açması anlamına gelirdi; yükseltilmiş haklar bir istisnadır, bir
ayar değil.

Konsolun nasıl görüneceğine [Ayarlar](#ayarlar) altındaki konsol tasarımı
karar verir.

Yeni konsol, başlatıcının ortamını devralır — çalışan bir Claude
oturumunun işaretleri hariç (`CLAUDE_CODE_CHILD_SESSION`,
`CLAUDE_CODE_SESSION_ID` ve `runner.SESSION_MARKERS` içindeki diğerleri).
ProjectHQ bir gün bir Claude oturumunun içinden başlatılırsa bunları
devralır ve yeni konsoldaki Claude kendini bir alt oturum sanıp transkript
yazmayı bırakırdı. Liste isim bazlıdır, `CLAUDE*` ile başlayan her şeyi
silmez: `ANTHROPIC_API_KEY` gibi kendi kalıcı ayarlarınız konsola ulaşmaya
devam eder.

`TÜR` sütunu hâlâ neyle ilgili olduğunu gösterir (`py`, `node`, `bat`,
`docker`, `web`, `dotnet`, `docs` veya geri kalan her şey için `-`). Bu
yalnızca bilgidir ve başlatmayı etkilemez.

## Onay sormadan

`ONAY SORMADAN` onay kutusu, seçilen ajana artık soru sormamasını sağlayan
parametreleri ekler (`runner.FREE_FLAGS`):

| Ajan | Parametreler |
|------|--------------|
| Claude | `--dangerously-skip-permissions` |
| Codex | `--sandbox danger-full-access --ask-for-approval never` |

Claude bundan sonra hiçbir dosya değişikliğinden veya komuttan önce
sormaz; Codex ayrıca sandbox'ı olmadan çalışır. Onay kutusu, neye izin
verdiğinizi görmeniz için o anda seçili ajanın parametrelerini gösterir.

Onay kutusu kabuğa bağlı değildir: `cmd`'de de PowerShell'de de çalışır.
PowerShell'de `-NoExit`, `cmd`'deki `/K` gibi pencereyi açık tutar; CRT
tasarımında PowerShell kendi giriş komutuyla renklenir
(`runner.ps_crt_prolog`), çünkü `cmd` giriş komutu PowerShell'de başarısız
olur: orada `&` kullanılamaz.

Yönetici onay kutusu gibi hatırlanmaz — aksi halde sonraki her başlatma
sessizce onay sormadan çalışırdı. PowerShell'de yönetici olarak,
yükseltilmiş konsol `Set-Location` ile proje klasörüne geçer
(`_elevated_ps_params`). Claude'un yükseltilmiş bir konsolda parametreyi
kabul edip etmediği henüz denenmedi.

## Yönetici olarak

Onay kutusu işaretliyse Windows önce sorar — aynı konsol, sadece
yükseltilmiş haklarla. İçindeki komut değişmez. Oraya giden yol değişir:
`subprocess.Popen` hakları yükseltemez, çünkü yeni süreç eskisinin
belirtecini devralır. Windows'ta bunun tek yolu `runas` fiiliyle
`ShellExecuteW`'dir ve o bir liste yerine komut satırı alır. Satır
`_elevated_params` içinde, `list2cmdline` yerine elle oluşturulur: o, içteki
tırnakları ters eğik çizgiyle korur, `cmd` ise bunu koruma olarak değil
karakter olarak okur. Dıştaki tırnakları ise `cmd` kaldırabilir — ikiden
fazla tırnak varsa tam olarak ilkini ve sonuncusunu siler ve kalanını
çalıştırır.

UAC iletişim kutusuna `Hayır` cevabı verilirse, terminal görünümlü bir
mesaj bunu söyler. Aksi halde düğme sessizce hiçbir şey yapmazdı.

Yükseltilmiş bir süreç artık üst süreç olarak ProjectHQ'ya değil,
Windows'un hak yükseltmesine bağlıdır: ortamını bizden almaz, bu yüzden
yukarıdaki oturum işaretlerini ayıklama orada işlemez. Bu nedenle
konsolun kendisinde silinirler — değersiz `set AD=` bir değişkeni kaldırır.
Hiçbiri devralınmadıysa, ki normal durum budur, komut değişmeden kalır.

Proje klasörü de aynı yolu izler. `ShellExecuteW` onu alır ama `runas`
fiilinde kullanmaz: süreci biz değil, hak yükseltmenin arkasındaki hizmet
başlatır ve o kendi dizinini belirler. Ölçüldü: her yükseltilmiş konsol
hangi proje kastedilirse edilsin `C:\Windows\System32` içinde açıldı. Bu
yüzden dizin değişikliği komutun kendisinde, zincirin ilk halkası olarak
yer alır: `cd /d "<proje klasörü>"`. `/d` klasörü ve sürücüyü tek seferde
değiştirir; projeler `D:` üzerindedir. İşaretlerin temizlenmesi ancak
bundan sonra gelir, böylece daha sonra çalışılacak yerde gerçekleşir.

Ajansız terminal de yönetici haklarıyla açılabilir: `Shift+F4` veya sağ
tıklama menüsünde `Burada terminal (yönetici)`.

## Ayarlar

Başlığın sağ üstündeki dişli her şeyi tek bir yerde açar: konsol
tasarımı, arayüz tasarımı, dil ve proje klasörü. `TAMAM`'a basılana kadar
hiçbir şeye dokunulmaz.

**Konsol tasarımı**, bir proje başlatılırken açılan pencerenin nasıl
görüneceğini belirler — `F4` terminalini de. İkisi de aynı konsolu açar;
`F4`'te içinde ajan çalışmaz:

| Tasarım | Ne olur |
|---------|---------|
| `CRT` (varsayılan) | Konsol başlatıcının renklerini alır: arka plan `#050b05`, yazı `#33ff66` |
| `KLASİK` | Windows varsayılan renkleri, elle açılmış bir konsolla aynı |

CRT tasarımında ajandan önce kısa bir giriş komutu gelir:

```
cmd /K echo <OSC 11 arka plan><OSC 10 yazı>&cls&claude
```

Konsol kendini iki ANSI dizisiyle renklendirir. Bu, Windows'ta veya
Windows Terminal ayarlarında hiçbir şeyi değiştirmez; dizileri anlamayan
bir konsol onları metin olarak yazar — ardından gelen `cls` metni hemen
siler. Renkler `projecthq/theme.py` dosyasından gelir: oradaki yeşil
değişirse konsol da değişir.

Her zaman `cmd` açılır, asla Windows Terminal değil — `wt` kurulu olsa
bile. `wt` kendisine verilen komut satırını kendi ayrıştırır ve giriş
komutunun ESC dizileriyle başa çıkamaz: basit bir komut geçer, `&`
zinciri de geçer, giriş komutu geçmez. Bu fark edilene kadar `F4` CRT
tasarımında hiç pencere açmıyordu.

Konsolun **yazı tipi** ayarlanamaz — bunun için Windows Terminal'de ayrı
bir profil gerekirdi. Ajanın kendi yazdığı renkler de değişmez; yalnızca
arka plan ve varsayılan yazı rengi yeşile döner.

**Dil** arayüzü değiştirir: Almanca (varsayılan), İngilizce,
Boşnakça/Hırvatça/Sırpça, Türkçe veya İspanyolca. Değişiklik yeniden
başlatmadan hemen etkili olur — düğmeler, sütun başlıkları, menüler,
iletişim kutuları, mesajlar ve açılış ekranı. `AUFGABEN.md` notu ve
ajanların kendi yazdıkları çevrilmez.

Metinler `projecthq/i18n.py` içindedir. Almanca metin orada aynı zamanda
anahtardır: `tr("Löschen")` çeviriyi döndürür, çeviri eksikse boş bir düğme
yerine Almanca görünür. `tests/test_i18n.py`, her dilin her metni
bildiğini, aynı yer tutucuları kullandığını ve sütun başlıklarının
sütunlarına sığdığını denetler. Yeni bir dil, kodunu `LANGUAGES`'e, adını
`LANGUAGE_LABELS`'e ve her metin için bir çeviri ekleyerek oluşturulur.

**Proje klasörü**, eskiden `YOL ...` arkasında duran yolun aynısıdır. Yeni
bir klasör listeyi hemen yeniden yükler.

Her şey `config.json` dosyasına yazılır ve bir sonraki başlatmada da
geçerlidir.

## Otomatik kapatma

Sol alttaki `⏻ KAPAT`, bilgisayarın seçilebilir bir süre sonra
kapanmasını planlar: `15`, `30`, `60` veya `120` dakika ya da kendi
belirlediğiniz dakika sayısı. Planlama Windows aracı `shutdown /t` ile
yapılır — bu yüzden geri sayım HQ arada kapatılsa bile devam eder ve
yeniden başlatılan HQ onu tekrar gösterir.

Bir kapatma bekliyorken düğme kırmızıdır ve durum satırı kalan süreyi ve
kapanış saatini gösterir. Kırmızı düğmeye tıklamak, iptal edilip
edilmeyeceğini sorar.

## Yeni proje

`+ YENİ` veya `Ctrl+N` bir ad sorar, klasörü `projects_root` altında
oluşturur ve hemen başlatır — neyle başlatılacağı sorusuyla birlikte.
Klasör boş kalır; geri kalan her şeyi ajan oluşturur. Geçersiz veya
kullanılmış adlar, hiçbir şey oluşturulmadan reddedilir.

## Proje başına görevler

`NOT` sütunu, bir proje için bir şey not edilip edilmediğini söyler: `≡`
evet, `·` henüz bir şey yok demektir. **Simgeye tıklamak** notu Not
Defteri'nde açar — `F6` ve sağ tıklama menüsündeki `Görevleri aç` da
öyle. Bu sütuna çift tıklamak projeyi **başlatmaz**; satırın diğer her
yerinde her zamanki gibi başlatır.

Not, **proje klasörünün kendisinde** bulunan `AUFGABEN.md` adlı sıradan
bir dosyadır, yapılandırmanın yanında değil. Böylece projeyle birlikte
taşınır, Gezgin'de bulunur ve Git'e eklenebilir. Henüz yoksa ilk açılışta
oluşturulur — boş değil, **dolu** olarak:

```markdown
# Aufgaben — HQ

## Stand vom 07.09.2026, 03:10

**Woran gearbeitet wurde**
- 07.09. 02:49 · Claude · Spalten für letzte Aufgaben und verwendetes Modell
- 06.09. 23:26 · Codex · Ladezeit der Startseite halbieren

**Letzte Commits**
- 81ea5fe Erhoehte Konsole startete in System32 statt im Projekt

**Nicht committet** — 9 geändert, 5 neu

**Zuletzt geändert**
- 07.09. 02:44 · projecthq/activity.py
```

Not, arayüz dili ne olursa olsun Almanca yazılır. İçeriğin nereden
geldiği [HQ durumu nereden bilir](#hq-durumu-nereden-bilir) altında
anlatılır.

Altında dosya sizindir: bir sonraki görev, açık sorular, ne isterseniz.
Başlatıcı içeriği asla okumaz; yalnızca dosyanın var olup olmadığını
görür. Var olan bir dosyaya açılırken **asla** dokunulmaz — aksi halde her
bakışta büyürdü. Dosyayı silmek sütunu `·` durumuna geri döndürür.

### Sonradan güncel bir durum eklemek

Sağ tıklama → **Durumu ekle**, başlığın hemen altına yeni bir blok yazar;
önceki her şey aşağı kayar. Not Defteri'nde en yenisi kaydırmadan görünür
ve sizin yazdıklarınızdan hiçbir şey kaybolmaz. Dosya böylece projenin
küçük bir geçmişine dönüşür.

## En son neyle çalışıldı

`AJAN` sütunu her proje için en son neyle çalışıldığını gösterir:
`■ CLAUDE` veya `● CODEX`. `–`, hiçbir şey bulunamadığı anlamına gelir.

Belirleyici olan yalnızca HQ üzerinden yapılan başlatmalar değil,
**oturum arşivleridir**. Kendi açtığınız bir konsol da aynı şekilde
sayılır — aksi halde şu anda yazdığınız bir projede bir çizgi görünürdü.
Arşivlerin nereden geldiği
[HQ durumu nereden bilir](#hq-durumu-nereden-bilir) altında anlatılır.

HQ'nun kendi başlattıkları boşluğu doldurur: `config.json` içinde
`project_agents` altında saklanır ve arşiv bir şey bilmediği sürece
geçerlidir — örneğin eski bir transkript silindiğinde. Yalnızca başlatma
başarılı olduğunda hatırlanır; ajan PATH içinde olmadığı için başarısız
olursa sütun olduğu gibi kalır.

## Proje başına iki tarih

Liste `OLUŞTURMA` ve `DÜZENLEME` gösterir. `OLUŞTURMA`, klasörün
oluşturulma zamanıdır ve ad değiştirmede korunur.

`DÜZENLEME`, **tüm projedeki en son değişikliktir** — klasörün değişiklik
zamanı değil. O bunun için işe yaramaz: Windows onu yalnızca doğrudan
içine bir öğe eklendiğinde, kaldırıldığında veya adı değiştirildiğinde
günceller. Bir dosyada yazmak, hele bir alt klasörde, ona dokunmaz.

`Webshop` üzerinde ölçüldü: klasör 02.08. diyordu, en yeni
dosya 07.09. tarihliydi — 35 gün fark. Liste varsayılan olarak bu alana
göre sıraladığı için proje, üzerinde çalışılırken en altta duruyordu.

HQ'nun kendi `AUFGABEN.md` dosyası **sayılmaz**. Aksi halde görevlere bir
bakış bile projeyi yukarı iterdi ve liste sizin nerede çalıştığınızı değil,
HQ'nun nereye yazdığını gösterirdi.

## Sıralama

Bir sütun başlığına tıklamak ona göre sıralar: `PROJE`, `TÜR`, `AJAN`,
`NOT`, `OLUŞTURMA` veya `DÜZENLEME`. Etkin sütun parlar ve `▲` veya `▼`
ile hangi yönde sıralandığını gösterir; aynı sütuna tekrar tıklamak yönü
tersine çevirir.

Bir tarih sütununa ilk tıklama en yeni öğeyle, `PROJE` veya `TÜR`'e ilk
tıklama A ile başlar. `AJAN` ve `NOT`, bir öğesi olan projelerle başlar —
artan sırada önce boş olanlar gelirdi, yani sütuna tıklayan birinin tam
olarak aramadığı projeler. Eşit değerler her zaman ada göre alfabetik
olarak çözülür.

Seçim `config.json` dosyasına yazılır ve bir sonraki başlatmada da
geçerlidir. Kayıt yoksa `DÜZENLEME`'ye göre azalan sıralanır; en son
düzenlenen proje en üstte olur.

## Yalnızca bir pencere

CODE/X HQ yalnızca bir kez çalışır. İkinci kez başlatılırsa — zaten
açıkken kısayola tıklamak —, bu başlatma mevcut pencereyi öne getirir ve
kendini kapatır. Görev çubuğundan da geri getirir.

Bu kendi başına bir amaç değildir: yan yana iki başlatıcının her biri
`config.json` dosyasının kendi kopyasını tutar ve kaydederken dosyanın
tamamını yazardı. Son kaydeden kazanır — diğeri sıralamayı, proje
klasörünü veya konsol tasarımını kaybederdi.

Nasıl yapıldığı: `projecthq/ui/instance.py`. Zaten bir tanesinin çalışıp
çalışmadığını adlandırılmış bir Windows mutex'i yanıtlar; öne getirme
adlandırılmış bir Qt borusu üzerinden yapılır. Tek başına `QLocalServer`
yetmez — bir boru aynı ada sahip birden fazla sunucuya izin verir, yani
ikinci bir `listen` de başarılı olur.

Bu geliştirme sırasında da geçerlidir: `.exe` çalışıyorsa,
`py -3.12 main.py` ikinci bir pencere açmak yerine onun penceresini öne
getirir.

## Favoriler

`Ctrl+D` veya sağ tıklama menüsündeki öğe, seçili projeyi en üste
sabitler. Sabitlenmiş projeler, sıralama ne olursa olsun her zaman
diğerlerinin önünde durur ve ok yerine yıldız işareti taşır:

```
 *  Tarkov            py        01.09.2026    06.09.2026
 ►  Spielwiese        node      28.08.2026    05.09.2026
```

Bilerek `★` değil `*` kullanılmıştır: Consolas'ta yıldız yoktur ve yedek
yazı tipi onu 7 yerine 13 px genişliğinde çizer — bu yüzden bir favori
satırının sütunları kayıyordu. Bkz.
[Izgaradaki karakterler](#izgaradaki-karakterler).

Kendi aralarında aşağıdakiyle aynı sıralama geçerlidir — `PROJE`'ye
tıklamak hem üstte hem altta alfabetik sıralar. Aynı kısayol sabitlemeyi
yeniden kaldırır.

Adlar `config.json` içinde `favorites` altında saklanır ve ad değiştirmeyi
ve yeniden başlatmayı atlatır. Bir proje silindiğinde kaydı da kaybolur.

## config.json

Kullanıcı profilinde bulunur:

```
%APPDATA%\ProjectHQ\config.json
```

`.exe`'nin yanında değil — orada `dist\ProjectHQ` içinde olurdu ve
PyInstaller tam olarak bu klasörü her derlemede `--noconfirm` ile boşaltır;
ayarlar her yeniden derlemeden sonra kaybolurdu. Hâlâ eski yerde duran bir
dosya ilk başlatmada bir kez devralınır (kopyalanır, taşınmaz).

İçerik:

```json
{
  "projects_root": "D:\\Projekte",
  "favorites": [],
  "sort_key": "mtime",
  "sort_desc": true,
  "console_style": "crt",
  "app_theme": "green",
  "language": "de",
  "last_agent": "claude",
  "last_shell": "cmd",
  "project_agents": {
    "Tarkov": "codex"
  }
}
```

`sort_key` sütunlardan biridir (`name`, `kind`, `agent`, `has_note`,
`created`, `mtime`), `sort_desc` yöndür. Orada bilinmeyen bir şey varsa
ikisi de atlanır ve yeniden `DÜZENLEME`'ye göre azalan sıralanır.

`console_style`, `crt` veya `classic`'tir; başka bir şey varsa `crt`
kullanılır. `last_agent`, `claude` veya `codex`'tir ve başlatma iletişim
kutusunda en son neyin seçildiğini kaydeder; bilinmeyen değer `claude`'a
döner. `last_shell` de aynı şekilde `cmd` veya `powershell`'dir.
`language`, `de`, `en`, `bhs`, `tr` veya `es`'dir; bilinmeyen değer `de`'ye
döner.

`project_agents`, her projeyi en son çalıştığı ajanla eşler. Bilinmeyen bir
ajan içeren kayıt yüklenirken atılır — yalnızca o, tüm tablo değil; proje
o zaman bir `–` gösterir.

`projects_root`, `console_style`, `app_theme` ve `language` programda
`AYARLAR` altında değiştirilebilir. Dosya bozuksa veya yoksa program
varsayılanlarla başlar. Eski bir sürümden kalan `commands` bloğu
yüklenirken atlanır.

## Silme

Silme, proje klasörünü **Windows geri dönüşüm kutusuna** taşır, asla
kalıcı olarak silmez. Öncesinde ad, yol ve boyut içeren bir onay iletişim
kutusu görünür. Geri dönüşüm kutusundan her şey geri yüklenebilir.

## Pencere çerçevesi

Tüm pencereler çerçevesiz çalışır ve kendi başlık çubuklarını getirir;
aksi halde terminal görünümünün üstünde gri bir Windows çubuğu dururdu.
Bu, iletişim kutuları ve açılış dizisi için de geçerlidir; `QMessageBox`
yerine kendi küçük mesaj kutusu vardır.

Windows hareketleri yine de çalışır, çünkü taşıma ve yeniden boyutlandırma
`startSystemMove` ve `startSystemResize` üzerinden yapılır:

| Hareket | Etki |
|---------|------|
| Çubuğu sürüklemek | Pencereyi taşımak, ekran kenarına yaslamak |
| Çubuğa çift tıklamak | Büyütmek ve geri almak |
| Kenarı veya köşeyi sürüklemek | Boyutu değiştirmek (6 px tutma alanı) |
| `─` `□` `×` | Simge durumuna küçültmek, büyütmek, kapatmak |

Çerçeve, pencere etkin olduğu sürece yeşil parlar, aksi halde soluk
yeşile döner. Platform sistem hareketlerini reddederse — örneğin
testlerdeki offscreen platformunda —, `frame.py` geometriyi kendisi
hesaplar; pencere böylece kullanılabilir kalır.

## HQ durumu nereden bilir

Dört kaynak, her biri `projecthq/activity.py` içinde. Hiçbir şey vermeyen
kaynak notta görünmez — boş bir bölüm, eksik bir bölümden daha kötü
olurdu.

| Kaynak | Nereden | Kapsar |
|--------|---------|--------|
| Ne üzerinde çalışıldı | Claude ve Codex oturumları | 24 projeden 14'ü |
| Son commit'ler | `git log -5 --oneline` | 24'ten 7'si |
| Commit edilmemiş | `git status --porcelain` | 24'ten 7'si |
| Son değişenler | klasördeki en yeni dosyalar | hepsi |

**Claude** oturumlarını `~/.claude/projects/<yol>/` altında saklar ve her
birine kendisi bir başlık verir — *„Yönetici başlatma seçenekleri"*. Bu,
mevcut en iyi özettir. Yepyeni bir oturumun henüz başlığı yoktur; o zaman
orada ilk soru durur.

**Codex** projeye göre değil, tarihe göre saklar. Bir oturumun hangi
klasöre ait olduğu ilk satırında yazar — bu yüzden dosyanın gerçekten
kastedilip kastedilmediği belli olana kadar yalnızca o satır okunur. Codex
başlık vermez, bu yüzden orada ilk soru durur.

Eşleme klasör adıyla değil, kaydedilen çalışma diziniyle yapılır:
`Benim Projem` ve `Benim-Projem` aynı ada dönüşür ve her biri diğerinin
notunu alırdı.

### Bunda belirsiz olan

**Biçim belgelenmemiştir.** Codex kaydını Mayıs ile Eylül 2026 arasında
değiştirdi; iki biçim arşivde yan yana durur ve HQ ikisini de okur. Bir
şey yeniden değişirse etkilenen bölüm sessizce düşer — not yine de açılır.

**Oturumlar kaybolur.** `.claude/projects` içinde bazı projeler için
yalnızca boş klasörler kalmıştır. Bu bir arşiv değil, kayan bir penceredir.
Bu yüzden durum **dosyaya yazılır** ve her açılışta yeniden hesaplanmaz:
bir kez yazılan kalır.

**Notta sizin girdileriniz bulunur.** Claude ve Codex'e yazdıklarınızdan
alıntılar. Bu yüzden `AUFGABEN.md`, HQ'nun `.gitignore` dosyasındadır.
Diğer projelerde buna kendiniz karar vermelisiniz — HQ başka projelerin
`.gitignore` dosyalarına dokunmaz.

### Çalışma süresi

24 projenin tamamında ölçüldü: toplam 2,6 s, proje başına 0,03 ile
0,57 s arası. Bu **yalnızca** bir not oluşturulurken ve „Durumu ekle"de
çalışır — listeyi tararken asla; aksi halde pencere her pencere
değişiminde donardı. Ayrıca, silme iletişim kutusundaki `folder_size`
gibi, zaman bütçeleri aramayı sınırlar.

## Izgaradaki karakterler

Listenin sütunları bir tabloda değil, eşit genişlikteki karakterlerden
oluşan bir metin satırındadır. Bu, her karakter tam olarak bir karakter
genişliğinde olduğu sürece işler — Consolas 13 px'te bu 7 px'tir.

Sorun şu: kullanılan simgelerin **hiçbiri** Consolas'ta yoktur. Onları
Windows'un yedek olarak devreye soktuğu yazı tipi çizer ve o ızgaraya
uymaz. Ölçüldü:

| Genişlik | Karakterler |
|----------|-------------|
| 7 px (doğru) | `►` `*` `≡` `·` `–` `●` `○` `■` `□` `▪` `▬` `▒` `─` |
| 8 px | `▶` `◆` `◇` `▤` `▣` |
| 13 px | `★` `☆` `✱` `✦` `☰` |

Fazla geniş bir karakter, satırındaki tüm sütunları sağa iter. Favori
satırının ilk yıldızı `★` tam olarak bunu altı piksel kadar yapıyordu — ve
fark edilmedi, çünkü test karakterleri *ölçmek* yerine yalnızca
*sayıyordu*.

Bu yalnızca gerçek bir yazı tipi veritabanıyla ölçülebilir. Testler
`QT_QPA_PLATFORM=offscreen` ile çalışır ve orada her karakter için aynı
genişliği alır — yani bunu denetleyemez. Bunun için şu araç vardır:

```
py -3.12 tools/messe_zeichen.py
```

Araç, kullanılan her simgeyi tamamen stillendirilmiş bir listede ölçer ve
biri uymazsa çıkış kodu 1 döndürür. Testler yalnızca hiçbir simgenin bu
ölçümü atlayarak girmediğini garanti eder: izin verilen,
`projecthq/ui/window.py` içindeki `GRID_MARKS`'ta yazanlardır. Yeni bir
simge kullanmak isteyen önce onu ölçer, sonra oraya ekler.

## Simge

`assets/projecthq.ico`, `.exe`'nin simgesi ve aynı zamanda çalışırken
pencere ve görev çubuğu simgesidir. Görev çubuğu ve Gezgin'in kendileri
küçültmek zorunda kalmaması için 16'dan 256 piksele kadar tüm boyutları
içerir.

Elle çizilmez, şununla oluşturulur:

```
py -3.12 tools/make_icon.py
```

Betik 1024 pikselde işler ve küçültür. Motifi değiştirmek isteyen,
`tools/make_icon.py` içindeki 16x16 `SKULL` ızgarasını değiştirir ve
betiği bir kez çalıştırır; ardından yeni bir `.exe` için `build.ps1`.

Windows simgeleri inatla önbelleğe alır. Gezgin derlemeden sonra hâlâ eski
resmi gösteriyorsa `ie4uinit.exe -show` veya Gezgin'i yeniden başlatmak
yardımcı olur.

## Yeniden derleme

```
powershell -ExecutionPolicy Bypass -File build.ps1
```

Betik önce testleri çalıştırır ve biri başarısız olursa durur. Ardından
PyInstaller `dist\ProjectHQ\` içine paketler. Derleme bilerek onefile
değil onedir'dir: hiçbir şeyin açılması gerekmediği için dört yerine
yaklaşık bir saniyede başlar.

**Bu sırada ProjectHQ kapalı olmalıdır.** Çalışan bir `.exe`
DLL'lerini kilitler; PyInstaller o zaman `dist\ProjectHQ`'yu değiştiremez
ve temizliğin ortasında durur — yarı boşaltılmış bir klasörle. Bu olursa

```
Remove-Item -Recurse -Force build, dist
```

ve yeniden çalıştırmak yardımcı olur. Aksi halde analiz bozuk klasörün
kalıntılarını bir sonraki derlemeye taşır.

Yalnızca testleri çalıştırmak:

```
py -3.12 -m pytest -q
```

## Yapı

```
assets/
  projecthq.ico uygulama simgesi (CRT görünümlü kafatası)
tools/
  make_icon.py  simgeyi yeniden çizer
  messe_zeichen.py  liste simgelerinin ızgaraya uyup uymadığını ölçer
projecthq/
  config.py     ayarlar, config.json
  scanner.py    projeleri bulma, türü belirleme, zaman damgalarını
                okuma, sıralama
  activity.py   bir projenin durumu: Claude ve Codex oturumları,
                commit'ler, son değişen dosyalar
  runner.py     başlatma, oluşturma, ad değiştirme, silme,
                Gezgin/Terminal/VS Code, not (AUFGABEN.md)
  theme.py      renk paleti ve Qt stil sayfası
  i18n.py       arayüz dilleri, tr()
  ui/
    window.py     ana pencere
    dialogs.py    yeni proje, ad değiştirme, silme, ayarlar,
                  başlatma iletişim kutusu (neyle?)
    boot.py       açılış dizisi
    crt.py        tarama çizgisi ve vinyet katmanı
    frame.py      başlık çubuklu kendi pencere çerçevesi
    appicon.py    pencere ve görev çubuğu simgesi
main.py
```

`config.py`, `scanner.py`, `activity.py` ve `runner.py` Qt içermez. Bu
kasıtlıdır: tüm mantık çalışan bir arayüz olmadan test edilebilir.
`tests/` altındaki testler bu modülleri doğrudan kapsar; ayrıca gerçek ana
pencereyi offscreen kuran uçtan uca testler vardır.

## Lisans

[MIT](LICENSE)
