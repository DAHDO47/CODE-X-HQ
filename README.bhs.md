# CODE/X HQ

Pokretač za tvoju mapu projekata u izgledu CRT terminala.
Prikazuje sve projekte, otvara ih u Claudeu ili Codexu, kreira nove,
preimenuje ih i briše.

**Jezici:** [Deutsch](README.md) · [English](README.en.md) ·
Bosanski / Hrvatski / Srpski · [Türkçe](README.tr.md) ·
[Español](README.es.md)

Njemački README je mjerodavan; ovaj prijevod ga prati.

## Pokretanje

**Gotova verzija:** preuzmi `CODE-X-HQ-windows-x64.zip` sa
[Releases](https://github.com/DAHDO47/CODE-X-HQ/releases/latest), raspakuj i pokreni `ProjectHQ\ProjectHQ.exe` — Python
nije potreban. Pri prvom pokretanju u **Postavkama** odaberi svoju mapu
projekata (zadano: `%USERPROFILE%\Projekte`). `claude` ili `codex` moraju
biti instalirani i u PATH-u.

Kad se gradi iz izvornog koda, `.exe` je ovdje:

```
dist\ProjectHQ\ProjectHQ.exe
```

Prikači `.exe` na traku zadataka ili stavi prečac na radnu površinu.
Sekvenca pokretanja se preskače klikom ili tipkom;
`ProjectHQ.exe --no-boot` je trajno preskače.

## Upotreba

Sve je dostupno mišem: dvostruki klik pokreće projekat, desni klik otvara
meni sa svim radnjama, a bočni meni lijevo nudi iste radnje za odabrani
unos.

| Tipka | Radnja |
|-------|--------|
| Dvostruki klik / F5 | Pokreni projekat |
| Ctrl+N | Kreiraj novi projekat |
| F2 | Preimenuj |
| Del | Obriši (u koš za smeće) |
| F4 | Terminal u mapi projekta |
| F6 | Zadaci projekta u Notepadu |
| Shift+F4 | Terminal kao administrator |
| Ctrl+D | Prikači ili ukloni iz favorita |
| Ctrl+R | Ponovo učitaj listu, ponovo izračunaj datum i agenta |
| Ctrl+F | Skoči u pretragu |
| Esc | Isprazni pretragu, inače zatvori |

Pretraga filtrira uživo dok tipkaš, po nazivu **i** tipu: `node` prikazuje
sve Node projekte. Klik na zaglavlje kolone sortira listu po njoj.

Lista ima šest kolona:

```
 ►  PROJEKAT          TIP    AGENT      BILJ.   KREIRANO     IZMIJENJENO
 *  Tarkov            node   ■ CLAUDE     ≡     28.08.2026   05.09.2026
 ►  Webshop           py     ● CODEX      ≡     24.05.2026   02.08.2026
 ►  Homepage          web    –            ·     22.06.2026   27.07.2026
```

Lista se ponovo učitava sa `Ctrl+R` — i automatski čim se prozor vrati u
prvi plan. Mapa koja je u međuvremenu nastala u Exploreru tako se odmah
pojavi na listi. Odabir ostaje sačuvan.

Jedna razlika između to dvoje: izračunati `IZMIJENJENO` i `AGENT` košta
oko 320 ms za 24 projekta — previše za svaki Alt-Tab. Automatsko
skeniranje zato koristi zapamćene vrijednosti (oko 40 ms);
**`Ctrl+R` ih ponovo izračunava**. Projekat koji HQ nikad nije vidio uvijek
se izračunava, pa nova mapa odmah ima tačan datum.

## Kako se pokreće

Pri pokretanju dijalog pita sa čim:

```
┌─ POKRENUTI SA? ─────────────────┐
│  > PROJEKAT:  Tarkov            │
│                                 │
│   ■  CLAUDE   Claude Code       │
│   □  CODEX    OpenAI Codex CLI  │
│                                 │
│  > KONZOLA                      │
│   ■  CMD     □  POWERSHELL      │
│                                 │
│   □  KAO ADMINISTRATOR          │
│   □  BEZ POTVRDE                │
│                                 │
│        [ODUSTANI]  [POKRENI]    │
└─────────────────────────────────┘
```

Posljednji izbor je unaprijed označen, a `POKRENI` je zadano dugme —
**dovoljan je pritisak na Enter**, dijalog ne košta nijedan klik. `Esc`
prekida i ništa ne pokreće.

Zatim se otvara konzola s mapom projekta kao radnim direktorijem, i u njoj
radi odabrani agent. Naredba je u suštini uvijek

```
cmd /K claude      odnosno      cmd /K codex
```

`/K` drži prozor otvorenim kad se agent završi — ispis i greške ostaju
čitljivi. Šta se nalazi u mapi nije bitno: `start.bat` ili `npm run dev` se
više ne izvršavaju.

Svaki put pita jednako — dvostruki klik, `F5`, dugme `POKRENI` i pokretanje
odmah nakon `+ NOVO`. Ako odabrani agent nije u PATH-u, to kaže poruka u
izgledu terminala, umjesto da se otvori konzola s Windows greškom.

Ispod toga se bira koji shell daje konzolu: `CMD` ili `POWERSHELL`. Za
samog agenta to gotovo ništa ne mijenja — on sam bira svoje alate. Ali
PowerShell učitava tvoj profil (`$PROFILE`), `cmd` ne.

Izbor se čuva kao `last_agent` i `last_shell` u `config.json`. Kvačica
`KAO ADMINISTRATOR` se ne čuva — pri svakom pokretanju je ponovo prazna.
Pamćenje bi značilo da svako kasnije pokretanje tiho otvara UAC dijalog;
povišena prava su izuzetak, a ne postavka.

Kako konzola izgleda određuje dizajn konzole u
[Postavkama](#postavke).

Nova konzola nasljeđuje okruženje pokretača — osim oznaka aktivne Claude
sesije (`CLAUDE_CODE_CHILD_SESSION`, `CLAUDE_CODE_SESSION_ID` i ostale iz
`runner.SESSION_MARKERS`). Ako se ProjectHQ ikad pokrene iz Claude sesije,
naslijedi ih, i Claude u novoj konzoli bi mislio da je podsesija i ne bi
više pisao transkript. Lista je po imenima, a ne čišćenje svega što počinje
s `CLAUDE*`: tvoje trajne postavke poput `ANTHROPIC_API_KEY` i dalje stižu
do konzole.

Kolona `TIP` i dalje pokazuje o čemu se radi (`py`, `node`, `bat`,
`docker`, `web`, `dotnet`, `docs`, ili `-` za sve ostalo). To je samo
informacija i ne utiče na pokretanje.

## Bez potvrde

Kvačica `BEZ POTVRDE` dodaje odabranom agentu prekidače s kojima više ne
pita (`runner.FREE_FLAGS`):

| Agent | Prekidači |
|-------|-----------|
| Claude | `--dangerously-skip-permissions` |
| Codex | `--sandbox danger-full-access --ask-for-approval never` |

Claude tada više ne pita prije nijedne izmjene datoteke ni naredbe; Codex
dodatno radi bez svog sandboxa. Kvačica navodi prekidače trenutno
odabranog agenta, da se vidi šta se dozvoljava.

Kvačica ne ovisi o shellu: radi i u `cmd` i u PowerShellu. U PowerShellu
`-NoExit` drži prozor otvorenim kao `/K` u `cmd`, a u CRT dizajnu se
PowerShell boji vlastitim uvodom (`runner.ps_crt_prolog`), jer `cmd` uvod u
PowerShellu ne radi: tamo `&` nije dozvoljen.

Kao i administratorska kvačica, ne pamti se — inače bi svako kasnije
pokretanje tiho radilo bez potvrde. Kao administrator u PowerShellu
povišena konzola prelazi u mapu projekta sa `Set-Location`
(`_elevated_ps_params`). Da li Claude prihvata prekidač u povišenoj
konzoli još nije isprobano.

## Kao administrator

S postavljenom kvačicom Windows prvo pita — ista konzola, samo s povišenim
pravima. Naredba u njoj se ne mijenja. Put do nje da: `subprocess.Popen` ne
može povisiti prava, jer novi proces nasljeđuje token starog. Na Windowsu
jedini izlaz je `ShellExecuteW` s glagolom `runas`, a on prima komandnu
liniju umjesto liste. Gradi se u `_elevated_params`, ručno umjesto sa
`list2cmdline`: ono štiti unutrašnje navodnike obrnutom kosom crtom, a
`cmd` je ne čita kao zaštitu nego kao znak. Vanjske navodnike `cmd` smije
skinuti — kod više od dva navodnika uklanja tačno prvi i posljednji i
izvršava ostatak.

Ako se na UAC dijalog odgovori sa `Ne`, to kaže poruka u izgledu
terminala. Inače dugme ne bi uradilo ništa bez objašnjenja.

Povišeni proces visi o Windows povišenju prava, a više ne o ProjectHQ kao
roditeljskom procesu: okruženje ne dobija od nas, pa filtriranje oznaka
sesije odozgo tamo ne djeluje. Zato se brišu u samoj konzoli —
`set IME=` bez vrijednosti uklanja varijablu. Ako nijedna nije
naslijeđena, što je uobičajeno, naredba ostaje ista.

Isti put ide i mapa projekta. `ShellExecuteW` je dobija, ali je kod
glagola `runas` ne koristi: proces ne pokrećemo mi, nego servis iza
povišenja prava, a on postavlja svoj direktorij. Izmjereno: svaka povišena
konzola završila je u `C:\Windows\System32` — bez obzira na projekat. Zato
je promjena direktorija u samoj naredbi, kao prva karika lanca:
`cd /d "<mapa projekta>"`. `/d` mijenja mapu i disk odjednom; projekti su
na `D:`. Tek nakon toga se čiste oznake, da se to desi tamo gdje se poslije
radi.

I terminal bez agenta postoji s pravima: `Shift+F4`, ili
`Terminal ovdje (administrator)` u meniju desnog klika.

## Postavke

Zupčanik gore desno otvara sve na jednom mjestu: dizajn konzole, izgled
sučelja, jezik i mapu projekata. Ništa se ne dira dok se ne pritisne `OK`.

**Dizajn konzole** određuje kako izgleda prozor koji se otvara pri
pokretanju projekta — i terminal na `F4`. Oba otvaraju istu konzolu; na
`F4` u njoj ne radi agent:

| Dizajn | Šta se dešava |
|--------|---------------|
| `CRT` (zadano) | Konzola dobija boje pokretača: pozadina `#050b05`, tekst `#33ff66` |
| `KLASIČNO` | Standardne Windows boje, tačno kao ručno otvorena konzola |

U CRT dizajnu prije agenta stoji kratak uvod:

```
cmd /K echo <OSC 11 pozadina><OSC 10 tekst>&cls&claude
```

Konzola se dakle sama boji, pomoću dvije ANSI sekvence. To ne mijenja ništa
u Windowsu ni u postavkama Windows Terminala, a konzola koja ne razumije
sekvence ispisuje ih kao tekst — sljedeći `cls` ga odmah briše. Boje dolaze
iz `projecthq/theme.py`: ako se tamo promijeni zelena, mijenja se i
konzola.

Uvijek se otvara `cmd`, nikad Windows Terminal — čak i ako je `wt`
instaliran. `wt` sam parsira proslijeđenu komandnu liniju i ne snalazi se
sa ESC sekvencama uvoda: jednostavna naredba prolazi, lanac sa `&` također,
uvod ne. Zato `F4` u CRT dizajnu nije otvarao nijedan prozor dok to nije
primijećeno.

**Font** konzole se ne može podesiti — za to bi trebao poseban profil u
Windows Terminalu. A boje koje agent sam ispisuje ostaju iste; samo
pozadina i zadana boja teksta postaju zelene.

**Jezik** mijenja sučelje: njemački (zadano), engleski,
bosanski/hrvatski/srpski, turski ili španski. Promjena djeluje odmah, bez
ponovnog pokretanja — dugmad, zaglavlja kolona, meniji, dijalozi, poruke i
ekran pokretanja. Ne prevode se bilješka `AUFGABEN.md` i ono što agenti
sami ispisuju.

Tekstovi su u `projecthq/i18n.py`. Njemački tekst je tamo ujedno ključ:
`tr("Löschen")` vraća prijevod, a ako nedostaje, pojavi se njemački umjesto
praznog dugmeta. `tests/test_i18n.py` provjerava da svaki jezik zna svaki
tekst, koristi iste rezervisane oznake i da zaglavlja staju u svoje kolone.
Novi jezik se dodaje upisom njegove oznake u `LANGUAGES`, naziva u
`LANGUAGE_LABELS` i prijevoda za svaki tekst.

**Mapa projekata** je ista putanja koja je ranije bila iza `PUTANJA ...`.
Nova mapa odmah ponovo učitava listu.

Sve se sprema u `config.json` i važi i pri sljedećem pokretanju.

## Automatsko gašenje

`⏻ GAŠENJE` dolje lijevo zakazuje gašenje računara nakon odabranog
vremena: `15`, `30`, `60` ili `120` minuta, ili vlastiti broj minuta.
Zakazuje se Windows alatom `shutdown /t` — zato odbrojavanje teče i ako se
HQ u međuvremenu zatvori, a ponovo pokrenuti HQ ga opet prikazuje.

Dok je gašenje zakazano, dugme je crveno, a statusna linija pokazuje
preostalo vrijeme i vrijeme gašenja. Klik na crveno dugme pita da li se
gašenje otkazuje.

## Novi projekat

`+ NOVO` ili `Ctrl+N` pita za naziv, kreira mapu u `projects_root` i odmah
je pokreće — s istim pitanjem sa čim. Mapa ostaje prazna; sve ostalo kreira
agent. Nevažeći ili već zauzeti nazivi se odbijaju prije nego što išta
nastane.

## Zadaci po projektu

Kolona `BILJ.` kaže da li je za projekat nešto zabilježeno: `≡` znači da,
`·` znači još ništa. **Klik na znak** otvara bilješku u Notepadu — isto kao
`F6` i `Otvori zadatke` u meniju desnog klika. Dvostruki klik na ovu kolonu
**ne** pokreće projekat; svugdje drugdje u redu da, kao i obično.

Bilješka je obična datoteka `AUFGABEN.md` **u samoj mapi projekta**, a ne
pored konfiguracije. Tako se seli s projektom, vidi se u Exploreru i može
u Git. Ako još ne postoji, kreira se pri prvom otvaranju — i to
**popunjena**, ne prazna:

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

Bilješka se piše na njemačkom, bez obzira na jezik sučelja. Odakle dolazi
sadržaj piše pod [Odakle HQ zna stanje](#odakle-hq-zna-stanje).

Ispod toga datoteka je tvoja: sljedeći zadatak, otvorena pitanja, šta god
želiš. Pokretač nikad ne čita sadržaj; vidi samo da li datoteka postoji.
Postojeća datoteka se pri otvaranju **nikad** ne dira — inače bi rasla sa
svakim pogledom. Brisanje datoteke vraća kolonu na `·`.

### Kasnije dodati svježe stanje

Desni klik → **Umetni stanje** piše novi blok odmah ispod naslova, sve
prethodno se pomjera dolje. U Notepadu se najnovije vidi bez skrolanja, i
ništa tvoje se ne gubi. Datoteka tako postaje mala historija projekta.

## Sa čim se zadnji put radilo

Kolona `AGENT` pokazuje za svaki projekat sa čim se u njemu zadnji put
radilo: `■ CLAUDE` ili `● CODEX`. `–` znači da se ništa nije našlo.

Mjerodavne su **arhive sesija**, ne samo pokretanja preko HQ-a. Konzola
koju si sam otvorio računa se jednako — inače bi projekat u kojem upravo
tipkaš pokazivao crticu. Odakle dolaze arhive piše pod
[Odakle HQ zna stanje](#odakle-hq-zna-stanje).

Ono što je HQ sam pokrenuo popunjava prazninu: stoji u `config.json` pod
`project_agents` i važi dok arhiva ništa ne zna — npr. kad je stari
transkript uklonjen. Pamti se tek kad je pokretanje uspjelo; ako ne uspije
jer agent nije u PATH-u, kolona ostaje kakva je bila.

## Dva datuma po projektu

Lista pokazuje `KREIRANO` i `IZMIJENJENO`. `KREIRANO` je vrijeme kreiranja
mape i ostaje pri preimenovanju.

`IZMIJENJENO` je **najnovija izmjena u cijelom projektu** — ne vrijeme
izmjene mape. Ono za to ne valja: Windows ga podiže samo kad se direktno u
mapi doda, ukloni ili preimenuje unos. Tipkanje u datoteci, a pogotovo u
podmapi, ga ne dira.

Izmjereno na `Webshop`: mapa je govorila 02.08., najnovija
datoteka je bila od 07.09. — 35 dana razlike. A pošto lista po zadanom
sortira po ovom polju, projekat je bio skroz dolje dok se na njemu radilo.

Vlastita `AUFGABEN.md` se **ne** računa. Inače bi već pogled na zadatke
pogurao projekat gore, a lista bi pokazivala gdje je HQ pisao umjesto gdje
si ti radio.

## Sortiranje

Klik na zaglavlje kolone sortira po njoj: `PROJEKAT`, `TIP`, `AGENT`,
`BILJ.`, `KREIRANO` ili `IZMIJENJENO`. Aktivna kolona svijetli i sa `▲` ili
`▼` pokazuje smjer; još jedan klik na istu kolonu okreće smjer.

Prvi klik na kolonu datuma počinje od najnovijeg unosa, prvi klik na
`PROJEKAT` ili `TIP` od A. `AGENT` i `BILJ.` počinju s projektima koji
imaju unos — uzlazno bi prvo bili prazni, baš oni koje niko ne traži kad
klikne kolonu. Jednake vrijednosti se uvijek rješavaju abecedno po nazivu.

Izbor se sprema u `config.json` i važi i pri sljedećem pokretanju. Bez
unosa sortira se po `IZMIJENJENO` silazno, pa je zadnji uređivani projekat
na vrhu.

## Samo jedan prozor

CODE/X HQ radi samo jednom. Ako se pokrene drugi put — klik na prečac dok
je već otvoren —, to pokretanje dovodi postojeći prozor naprijed i samo se
gasi. I s trake zadataka.

To nije samo sebi svrha: dva pokretača uporedo bi svaki imao svoju kopiju
`config.json` i pri spremanju pisao cijelu datoteku. Ko zadnji spremi,
pobjeđuje — drugi bi izgubio sortiranje, mapu projekata ili dizajn
konzole.

Kako je urađeno: `projecthq/ui/instance.py`. Da li već jedan radi
odgovara imenovani Windows mutex; dovođenje naprijed ide preko imenovane
Qt cijevi. Sam `QLocalServer` nije dovoljan — cijev dozvoljava više
servera istog imena, pa i drugi `listen` uspijeva.

To važi i pri razvoju: ako `.exe` radi, `py -3.12 main.py` dovodi njegov
prozor naprijed umjesto da otvori drugi.

## Favoriti

`Ctrl+D` ili unos u meniju desnog klika prikači odabrani projekat na vrh.
Prikačeni projekti su uvijek ispred svih ostalih, bez obzira na
sortiranje, i umjesto strelice nose zvjezdicu:

```
 *  Tarkov            py        01.09.2026    06.09.2026
 ►  Spielwiese        node      28.08.2026    05.09.2026
```

Namjerno je `*`, a ne `★`: Consolas nema zvijezdu, a zamjenski font je
crta široku 13 px umjesto 7 — kolone reda favorita su zbog toga bile
pomaknute. Vidi [Znakovi na rasteru](#znakovi-na-rasteru).

Među sobom važi isto sortiranje kao dolje — klik na `PROJEKAT` sortira
abecedno i gore i dolje. Isti prečac ponovo uklanja prikačivanje.

Nazivi stoje u `config.json` pod `favorites` i preživljavaju preimenovanje
i ponovno pokretanje. Kad se projekat obriše, nestaje i njegov unos.

## config.json

Nalazi se u korisničkom profilu:

```
%APPDATA%\ProjectHQ\config.json
```

Ne pored `.exe` — tamo bi bio u `dist\ProjectHQ`, a upravo tu mapu
PyInstaller prazni sa `--noconfirm` pri svakom buildu; postavke bi nakon
svakog ponovnog builda nestale. Datoteka koja je još na starom mjestu
preuzima se jednom pri prvom pokretanju (kopira se, ne premješta).

Sadržaj:

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

`sort_key` je jedna od kolona (`name`, `kind`, `agent`, `has_note`,
`created`, `mtime`), `sort_desc` smjer. Ako tu stoji nešto nepoznato, oboje
se preskače i ponovo se sortira po `IZMIJENJENO` silazno.

`console_style` je `crt` ili `classic`; sve drugo koristi `crt`.
`last_agent` je `claude` ili `codex` i bilježi šta je zadnje odabrano u
dijalogu pokretanja; nepoznato se vraća na `claude`. `last_shell` je
isto tako `cmd` ili `powershell`. `language` je `de`, `en`, `bhs`, `tr` ili
`es`; nepoznato se vraća na `de`.

`project_agents` dodjeljuje svakom projektu agenta s kojim je zadnji put
radio. Unos s nepoznatim agentom se pri učitavanju odbacuje — samo taj, ne
cijela tabela; projekat tada pokazuje `–`.

`projects_root`, `console_style`, `app_theme` i `language` mogu se
promijeniti u programu pod `POSTAVKE`. Ako je datoteka oštećena ili
nedostaje, program se pokreće sa zadanim vrijednostima. Blok `commands` iz
ranije verzije se pri učitavanju preskače.

## Brisanje

Brisanje premješta mapu projekta u **Windows koš za smeće**, nikad
trajno. Prije toga se pojavi dijalog potvrde s nazivom, putanjom i
veličinom. Iz koša se sve može vratiti.

## Okvir prozora

Svi prozori rade bez okvira i donose vlastitu naslovnu traku, inače bi
iznad izgleda terminala stajala siva Windows traka. To važi i za dijaloge i
sekvencu pokretanja; umjesto `QMessageBox` postoji vlastiti mali okvir za
poruke.

Windows geste ipak ostaju, jer pomicanje i promjena veličine idu preko
`startSystemMove` i `startSystemResize`:

| Gesta | Učinak |
|-------|--------|
| Povući traku | Pomjeriti prozor, pristati uz rub ekrana |
| Dvostruki klik na traku | Maksimizirati i nazad |
| Povući rub ili ugao | Promijeniti veličinu (zona hvata 6 px) |
| `─` `□` `×` | Minimizirati, maksimizirati, zatvoriti |

Okvir svijetli zeleno dok je prozor aktivan, a inače pada na prigušenu
zelenu. Ako platforma odbije sistemske geste — npr. pod offscreen
platformom u testovima —, `frame.py` sam računa geometriju, pa prozor
ostaje upotrebljiv.

## Odakle HQ zna stanje

Četiri izvora, svaki u `projecthq/activity.py`. Šta ništa ne daje ne
pojavljuje se u bilješci — prazan odjeljak bio bi gori od nepostojećeg.

| Izvor | Odakle | Pokriva |
|-------|--------|---------|
| Na čemu se radilo | sesije Claudea i Codexa | 14 od 24 projekta |
| Zadnji commitovi | `git log -5 --oneline` | 7 od 24 |
| Nije commitovano | `git status --porcelain` | 7 od 24 |
| Zadnje izmijenjeno | najnovije datoteke u mapi | sve |

**Claude** sprema svoje sesije u `~/.claude/projects/<putanja>/` i svakoj
sam daje naslov — *„Opcije pokretanja kao administrator"*. To je najbolji
sažetak koji postoji. Potpuno nova sesija ga još nema; tada tu stoji prvo
pitanje.

**Codex** sprema po datumu, a ne po projektu. Kojoj mapi sesija pripada
stoji u njenom prvom redu — zato se čita samo on dok nije jasno da li je
datoteka uopšte tražena. Codex ne daje naslov, pa tu stoji prvo pitanje.

Dodjela ide preko zabilježenog radnog direktorija, a ne naziva mape:
`Moj Projekat` i `Moj-Projekat` bi dali isti naziv, i svaki bi dobio
bilješku drugog.

### Šta je tu nesigurno

**Format nije dokumentovan.** Codex je promijenio svoj zapis između maja i
septembra 2026; oba oblika stoje jedan pored drugog u arhivi, i HQ čita
oba. Ako se nešto opet promijeni, pogođeni odjeljak tiho otpada —
bilješka se ipak otvara.

**Sesije nestaju.** U `.claude/projects` za neke projekte stoje još samo
prazne mape. To je klizni prozor, a ne arhiva. Zato se stanje **upisuje u
datoteku** i ne računa se ponovo pri svakom otvaranju: šta jednom uđe,
ostaje.

**U bilješci su tvoji unosi.** Isječci onoga što si pisao Claudeu i
Codexu. Zato je `AUFGABEN.md` u `.gitignore` HQ-a. U drugim projektima to
moraš sam odlučiti — HQ ne dira tuđe `.gitignore` datoteke.

### Trajanje

Izmjereno na svih 24 projekta: ukupno 2,6 s, od 0,03 do 0,57 s po
projektu. To se izvršava **samo** pri kreiranju bilješke i kod „Umetni
stanje" — nikad pri skeniranju liste, inače bi prozor zastao pri svakoj
promjeni prozora. Dodatno vremenski budžeti ograničavaju pretragu, kao kod
`folder_size` u dijalogu brisanja.

## Znakovi na rasteru

Kolone liste nisu u tabeli, nego u redu teksta od jednako širokih znakova.
To funkcioniše dok svaki znak mjeri tačno jednu širinu znaka — kod
Consolas 13 px to je 7 px.

Kvaka: **nijedan** od korištenih simbola nije u Consolasu. Crta ih font
koji Windows koristi kao zamjenu, a on se ne drži rastera. Izmjereno:

| Širina | Znakovi |
|--------|---------|
| 7 px (ispravno) | `►` `*` `≡` `·` `–` `●` `○` `■` `□` `▪` `▬` `▒` `─` |
| 8 px | `▶` `◆` `◇` `▤` `▣` |
| 13 px | `★` `☆` `✱` `✦` `☰` |

Preširok znak gura sve kolone svog reda udesno. Upravo to je radila
prvobitna zvijezda `★` reda favorita, šest piksela — i nije se primijetilo
jer je test samo *brojao* znakove umjesto da ih *mjeri*.

To se može izmjeriti samo pravom bazom fontova. Testovi rade sa
`QT_QPA_PLATFORM=offscreen` i tamo za svaki znak dobijaju istu širinu —
dakle to ne mogu provjeriti. Za to postoji

```
py -3.12 tools/messe_zeichen.py
```

Alat mjeri svaki korišteni simbol na potpuno stiliziranoj listi i vraća
izlazni kod 1 ako neki ne odgovara. Testovi samo osiguravaju da nijedan
simbol ne uđe mimo ovog mjerenja: dozvoljeno je ono što stoji u
`GRID_MARKS` u `projecthq/ui/window.py`. Ko želi novi simbol, prvo ga
izmjeri, pa ga onda tamo upiše.

## Ikona

`assets/projecthq.ico` je ikona `.exe` i ujedno ikona prozora i trake
zadataka tokom rada. Sadrži sve veličine od 16 do 256 piksela, da traka
zadataka i Explorer ne moraju sami smanjivati.

Ne crta se ručno, nego sa

```
py -3.12 tools/make_icon.py
```

Skripta renderuje na 1024 piksela i smanjuje. Ko želi promijeniti motiv,
mijenja raster 16x16 `SKULL` u `tools/make_icon.py` i jednom pokrene
skriptu; zatim `build.ps1` za novi `.exe`.

Windows agresivno pamti ikone. Ako Explorer nakon builda i dalje pokazuje
staru sliku, pomaže `ie4uinit.exe -show` ili ponovno pokretanje Explorera.

## Ponovni build

```
powershell -ExecutionPolicy Bypass -File build.ps1
```

Skripta prvo pokreće testove i prekida ako neki ne uspije. Zatim
PyInstaller pakuje u `dist\ProjectHQ\`. Build je namjerno onedir, a ne
onefile: pokreće se za oko jednu sekundu umjesto četiri, jer se ništa ne
mora raspakovati.

**ProjectHQ mora pri tome biti zatvoren.** Pokrenut `.exe` zaključava
svoje DLL-ove; PyInstaller tada ne može zamijeniti `dist\ProjectHQ` i
prekida usred čišćenja — s napola ispražnjenom mapom. Ako se to desi,
pomaže

```
Remove-Item -Recurse -Force build, dist
```

i ponovno pokretanje. Inače analiza povuče ostatke pokvarene mape u
sljedeći build.

Pokrenuti samo testove:

```
py -3.12 -m pytest -q
```

## Struktura

```
assets/
  projecthq.ico ikona aplikacije (lobanja u CRT izgledu)
tools/
  make_icon.py  ponovo crta ikonu
  messe_zeichen.py  mjeri da li simboli liste staju u raster
projecthq/
  config.py     postavke, config.json
  scanner.py    pronalazak projekata, određivanje tipa, čitanje
                vremenskih oznaka, sortiranje
  activity.py   stanje projekta: sesije Claudea i Codexa,
                commitovi, zadnje izmijenjene datoteke
  runner.py     pokretanje, kreiranje, preimenovanje, brisanje,
                Explorer/Terminal/VS Code, bilješka (AUFGABEN.md)
  theme.py      paleta boja i Qt stylesheet
  i18n.py       jezici sučelja, tr()
  ui/
    window.py     glavni prozor
    dialogs.py    novi projekat, preimenovanje, brisanje, postavke,
                  dijalog pokretanja (sa čim?)
    boot.py       sekvenca pokretanja
    crt.py        sloj linija skeniranja i vinjete
    frame.py      vlastiti okvir prozora s naslovnom trakom
    appicon.py    ikona za prozor i traku zadataka
main.py
```

`config.py`, `scanner.py`, `activity.py` i `runner.py` ne sadrže Qt. To je
namjerno: sva logika se može testirati bez pokrenutog sučelja. Testovi u
`tests/` direktno pokrivaju ove module, a uz to postoje testovi s kraja na
kraj koji grade pravi glavni prozor offscreen.

## Licenca

[MIT](LICENSE)
