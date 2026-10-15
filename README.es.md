# CODE/X HQ

Un lanzador para tu carpeta de proyectos con aspecto de
terminal CRT. Muestra todos los proyectos, los abre en Claude o Codex, crea
proyectos nuevos, los renombra y los elimina.

**Idiomas:** [Deutsch](README.md) · [English](README.en.md) ·
[Bosanski / Hrvatski / Srpski](README.bhs.md) · [Türkçe](README.tr.md) ·
Español

El README en alemán es la referencia; esta traducción lo sigue.

## Iniciar

**Versión lista:** descarga `CODE-X-HQ-windows-x64.zip` desde
[Releases](https://github.com/DAHDO47/CODE-X-HQ/releases/latest), descomprímelo y ejecuta `ProjectHQ\ProjectHQ.exe` — no
hace falta Python. En el primer inicio elige tu carpeta de proyectos en
**Ajustes** (por defecto: `%USERPROFILE%\Projekte`). `claude` o `codex`
deben estar instalados y en el PATH.

Si se compila desde el código, la `.exe` está aquí:

```
dist\ProjectHQ\ProjectHQ.exe
```

Ancla el `.exe` a la barra de tareas o crea un acceso directo en el
escritorio. La secuencia de arranque se salta con un clic o una tecla;
`ProjectHQ.exe --no-boot` la omite siempre.

## Manejo

Todo es accesible con el ratón: doble clic inicia un proyecto, el clic
derecho abre el menú con todas las acciones, y el menú lateral de la
izquierda ofrece las mismas acciones para la entrada seleccionada.

| Tecla | Acción |
|-------|--------|
| Doble clic / F5 | Iniciar proyecto |
| Ctrl+N | Crear proyecto nuevo |
| F2 | Renombrar |
| Supr | Eliminar (a la papelera) |
| F4 | Terminal en la carpeta del proyecto |
| F6 | Tareas del proyecto en el Bloc de notas |
| Shift+F4 | Terminal como administrador |
| Ctrl+D | Fijar o quitar de favoritos |
| Ctrl+R | Releer la lista, recalcular fecha y agente |
| Ctrl+F | Saltar a la búsqueda |
| Esc | Vaciar la búsqueda; si está vacía, cerrar |

La búsqueda filtra en vivo mientras se escribe, por nombre **y** tipo:
`node` muestra todos los proyectos Node. Un clic en el encabezado de una
columna ordena la lista por ella.

La lista tiene seis columnas:

```
 ►  PROYECTO          TIPO   AGENTE     NOTA    CREADO       MODIFICADO
 *  Tarkov            node   ■ CLAUDE     ≡     28.08.2026   05.09.2026
 ►  Webshop           py     ● CODEX      ≡     24.05.2026   02.08.2026
 ►  Homepage          web    –            ·     22.06.2026   27.07.2026
```

La lista se relee con `Ctrl+R` — y automáticamente cada vez que la ventana
vuelve al primer plano. Una carpeta creada mientras tanto en el Explorador
aparece así de inmediato. La selección se conserva.

Una diferencia entre ambos: calcular `MODIFICADO` y `AGENTE` cuesta unos
320 ms para 24 proyectos — demasiado para cada Alt-Tab. Por eso el escaneo
automático usa los valores recordados (unos 40 ms); **`Ctrl+R` los
recalcula**. Un proyecto que HQ nunca ha visto siempre se calcula, así que
una carpeta nueva aparece enseguida con la fecha correcta.

## Cómo se inicia

Al iniciar, un diálogo pregunta con qué:

```
┌─ ¿INICIAR CON? ─────────────────┐
│  > PROYECTO:  Tarkov            │
│                                 │
│   ■  CLAUDE   Claude Code       │
│   □  CODEX    OpenAI Codex CLI  │
│                                 │
│  > CONSOLA                      │
│   ■  CMD     □  POWERSHELL      │
│                                 │
│   □  COMO ADMINISTRADOR         │
│   □  SIN CONFIRMACIONES         │
│                                 │
│        [CANCELAR]  [INICIAR]    │
└─────────────────────────────────┘
```

La última elección está preseleccionada e `INICIAR` es el botón por
defecto — **basta con pulsar Intro**, el diálogo no cuesta ningún clic.
`Esc` cancela y no inicia nada.

Después se abre una consola con la carpeta del proyecto como directorio de
trabajo, y en ella se ejecuta el agente elegido. En esencia, la orden es
siempre

```
cmd /K claude      o      cmd /K codex
```

`/K` mantiene la ventana abierta cuando el agente termina — la salida y los
errores siguen legibles. Lo que haya en la carpeta no importa: ya no se
ejecuta un `start.bat` ni un `npm run dev`.

Todos los caminos preguntan igual — doble clic, `F5`, el botón `INICIAR` y
también el inicio justo después de `+ NUEVO`. Si el agente elegido no está
en el PATH, lo dice un mensaje con aspecto de terminal en lugar de abrir una
consola con un error de Windows.

Debajo se elige qué shell aporta la consola: `CMD` o `POWERSHELL`. Para el
agente en sí casi no cambia nada — elige sus propias herramientas. Pero
PowerShell carga tu perfil (`$PROFILE`), `cmd` no.

La elección se guarda como `last_agent` y `last_shell` en `config.json`.
La casilla `COMO ADMINISTRADOR`, en cambio, no — vuelve a estar vacía en
cada inicio. Recordarla significaría que cada inicio posterior abriría en
silencio un diálogo UAC; los derechos elevados son una excepción, no un
ajuste.

El aspecto de la consola lo decide el diseño de consola en
[Ajustes](#ajustes).

La nueva consola hereda el entorno del lanzador — salvo los marcadores de
una sesión de Claude en curso (`CLAUDE_CODE_CHILD_SESSION`,
`CLAUDE_CODE_SESSION_ID` y los demás de `runner.SESSION_MARKERS`). Si
ProjectHQ se inicia alguna vez desde una sesión de Claude, los hereda, y el
Claude de la nueva consola se creería una subsesión y dejaría de escribir
la transcripción. La lista es por nombre y no un barrido de `CLAUDE*`: tus
propios ajustes permanentes como `ANTHROPIC_API_KEY` siguen llegando a la
consola.

La columna `TIPO` sigue mostrando de qué se trata (`py`, `node`, `bat`,
`docker`, `web`, `dotnet`, `docs`, o `-` para todo lo demás). Es solo
información y no influye en el inicio.

## Sin confirmaciones

La casilla `SIN CONFIRMACIONES` añade al agente elegido los parámetros con
los que deja de preguntar (`runner.FREE_FLAGS`):

| Agente | Parámetros |
|--------|------------|
| Claude | `--dangerously-skip-permissions` |
| Codex | `--sandbox danger-full-access --ask-for-approval never` |

Claude ya no pregunta antes de ningún cambio de archivo ni de ninguna
orden; Codex además se ejecuta sin su sandbox. La casilla muestra los
parámetros del agente elegido, para que se vea qué se está permitiendo.

La casilla no depende de la shell: funciona en `cmd` igual que en
PowerShell. En PowerShell `-NoExit` mantiene la ventana abierta como `/K`
en `cmd`, y en el diseño CRT PowerShell se colorea con su propio prólogo
(`runner.ps_crt_prolog`), porque el prólogo de `cmd` falla en PowerShell:
allí no se permite `&`.

Igual que la casilla de administrador, no se recuerda — si no, cada inicio
posterior se ejecutaría en silencio sin confirmaciones. Como administrador
en PowerShell, la consola elevada entra en la carpeta del proyecto con
`Set-Location` (`_elevated_ps_params`). Aún no se ha probado si Claude
acepta el parámetro en una consola elevada.

## Como administrador

Con la casilla marcada, Windows pregunta antes — la misma consola, solo
que con derechos elevados. La orden de dentro no cambia. El camino hasta
allí sí: `subprocess.Popen` no puede elevar, porque el nuevo proceso hereda
el token del anterior. En Windows la única salida es `ShellExecuteW` con el
verbo `runas`, y este recibe una línea de órdenes en lugar de una lista. Se
construye en `_elevated_params`, a mano y no con `list2cmdline`: este
protege las comillas interiores con una barra invertida, y `cmd` no la lee
como protección sino como carácter. Las comillas exteriores, en cambio,
`cmd` puede quitarlas — con más de dos comillas elimina exactamente la
primera y la última y ejecuta el resto.

Si el diálogo UAC se responde con `No`, lo dice un mensaje con aspecto de
terminal. Si no, el botón no haría nada sin decir nada.

Un proceso elevado depende de la elevación de Windows y ya no de ProjectHQ
como proceso padre: no recibe su entorno de nosotros, así que el filtrado
de marcadores de sesión de arriba no actúa allí. Por eso se borran en la
propia consola — `set NOMBRE=` sin valor elimina una variable. Si no se
heredó ninguno, que es lo normal, la orden queda igual.

La carpeta del proyecto sigue el mismo camino. `ShellExecuteW` la recibe,
pero no la usa con el verbo `runas`: el proceso no lo iniciamos nosotros,
sino el servicio detrás de la elevación, y este fija su propio directorio.
Medido: cada consola elevada acababa en `C:\Windows\System32` — daba igual
qué proyecto fuera. Por eso el cambio de carpeta va en la propia orden,
como primer eslabón de la cadena: `cd /d "<carpeta del proyecto>"`. `/d`
cambia carpeta y unidad a la vez; los proyectos están en `D:`. Solo después
se limpian los marcadores, para que ocurra donde luego se trabaja.

También la terminal sin agente existe con derechos: `Shift+F4`, o
`Terminal aquí (administrador)` en el menú del clic derecho.

## Ajustes

El engranaje arriba a la derecha abre todo en un solo lugar: el diseño de
consola, el diseño de la interfaz, el idioma y la carpeta de proyectos.
Nada se toca hasta pulsar `ACEPTAR`.

El **diseño de consola** decide cómo se ve la ventana que se abre al
iniciar un proyecto — y también la terminal de `F4`. Ambas abren la misma
consola; en `F4` no se ejecuta ningún agente:

| Diseño | Qué pasa |
|--------|----------|
| `CRT` (por defecto) | La consola toma los colores del lanzador: fondo `#050b05`, texto `#33ff66` |
| `CLÁSICO` | Colores estándar de Windows, igual que una consola abierta a mano |

En el diseño CRT, un breve prólogo precede al agente:

```
cmd /K echo <OSC 11 fondo><OSC 10 texto>&cls&claude
```

La consola se colorea a sí misma, con dos secuencias ANSI. Esto no cambia
nada en Windows ni en los ajustes de Windows Terminal, y una consola que no
entiende las secuencias las imprime como texto — el `cls` siguiente lo
borra al instante. Los colores vienen de `projecthq/theme.py`: si allí
cambia el verde, cambia la consola.

Siempre se abre `cmd`, nunca Windows Terminal — aunque `wt` esté
instalado. `wt` analiza por sí mismo la línea de órdenes recibida y no se
entiende con las secuencias ESC del prólogo: una orden simple pasa, una
cadena con `&` también, el prólogo no. Por eso `F4` no abría ninguna
ventana en el diseño CRT hasta que se notó.

La **fuente** de la consola no se puede ajustar — para eso haría falta un
perfil propio en Windows Terminal. Y los colores que imprime el propio
agente no cambian; solo el fondo y el color de texto por defecto se
vuelven verdes.

**Idioma** cambia la interfaz: alemán (por defecto), inglés,
bosnio/croata/serbio, turco o español. El cambio surte efecto de inmediato,
sin reiniciar — botones, encabezados de columna, menús, diálogos, mensajes
y la pantalla de arranque. No se traducen la nota `AUFGABEN.md` ni lo que
imprimen los propios agentes.

Los textos están en `projecthq/i18n.py`. Allí el texto alemán es a la vez
la clave: `tr("Löschen")` devuelve la traducción, y si falta una, aparece
el alemán en lugar de un botón vacío. `tests/test_i18n.py` comprueba que
cada idioma conoce todos los textos, usa los mismos marcadores de posición
y que los encabezados caben en sus columnas. Un idioma nuevo se añade
poniendo su código en `LANGUAGES`, su nombre en `LANGUAGE_LABELS` y una
traducción para cada texto.

La **carpeta de proyectos** es la misma ruta que antes estaba detrás de
`RUTA ...`. Una carpeta nueva recarga la lista de inmediato.

Todo se guarda en `config.json` y sigue valiendo en el próximo inicio.

## Apagado automático

`⏻ APAGAR` abajo a la izquierda programa que el ordenador se apague tras
un tiempo elegible: `15`, `30`, `60` o `120` minutos, o un número propio de
minutos. Se programa con la herramienta de Windows `shutdown /t` — por eso
la cuenta atrás sigue aunque HQ se cierre entretanto, y un HQ reiniciado la
vuelve a mostrar.

Mientras hay un apagado pendiente, el botón está en rojo y la línea de
estado muestra el tiempo restante y la hora a la que se apagará. Un clic en
el botón rojo pregunta si se quiere cancelar.

## Proyecto nuevo

`+ NUEVO` o `Ctrl+N` pide un nombre, crea la carpeta en `projects_root` y
la inicia enseguida — con la misma pregunta de con qué. La carpeta queda
vacía; todo lo demás lo crea el agente. Los nombres no válidos o ya usados
se rechazan antes de crear nada.

## Tareas por proyecto

La columna `NOTA` dice si hay algo anotado para un proyecto: `≡` significa
sí, `·` significa nada todavía. Un **clic en el símbolo** abre la nota en
el Bloc de notas — igual que `F6` y `Abrir tareas` en el menú del clic
derecho. Un doble clic en esta columna **no** inicia el proyecto; en el
resto de la fila sí, como siempre.

La nota es un archivo normal llamado `AUFGABEN.md` **en la propia carpeta
del proyecto**, no junto a la configuración. Así se mueve con el proyecto,
se encuentra en el Explorador y puede ir a Git. Si aún no existe, se crea
al abrirla por primera vez — y **rellena**, no vacía:

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

La nota se escribe en alemán, sea cual sea el idioma de la interfaz. De
dónde sale su contenido se explica en
[De dónde saca HQ el estado](#de-dónde-saca-hq-el-estado).

Debajo, el archivo es tuyo: la próxima tarea, preguntas abiertas, lo que
quieras. El lanzador nunca lee el contenido; solo ve si el archivo existe.
Un archivo existente **nunca** se toca al abrirlo — si no, crecería con
cada vistazo. Borrar el archivo devuelve la columna a `·`.

### Añadir más tarde un estado actual

Clic derecho → **Insertar estado** escribe un bloque nuevo justo debajo del
título; todo lo anterior baja. En el Bloc de notas lo más reciente se ve
sin desplazarse, y no se pierde nada tuyo. El archivo se convierte así en
un pequeño historial del proyecto.

## Con qué se trabajó por última vez

La columna `AGENTE` muestra por proyecto con qué se trabajó en él por
última vez: `■ CLAUDE` o `● CODEX`. Un `–` significa que no se encontró
nada.

Lo que cuenta son los **archivos de sesión**, no solo los inicios desde
HQ. Una consola que abriste tú cuenta igual — si no, un proyecto en el que
estás escribiendo ahora mostraría un guion. De dónde vienen los archivos
se explica en [De dónde saca HQ el estado](#de-dónde-saca-hq-el-estado).

Lo que inició HQ rellena el hueco: se guarda en `config.json` bajo
`project_agents` y vale mientras el archivo de sesiones no sepa nada — por
ejemplo, cuando se ha eliminado una transcripción antigua. Solo se recuerda
cuando el inicio ha funcionado; si falla porque el agente no está en el
PATH, la columna queda como estaba.

## Dos fechas por proyecto

La lista muestra `CREADO` y `MODIFICADO`. `CREADO` es el momento de
creación de la carpeta y se conserva al renombrar.

`MODIFICADO` es el **cambio más reciente en todo el proyecto** — no la
hora de modificación de la carpeta. Esa no sirve: Windows solo la actualiza
cuando directamente dentro se añade, se quita o se renombra una entrada.
Escribir en un archivo, y más aún en una subcarpeta, no la toca.

Medido en `Webshop`: la carpeta decía 02.08., el archivo más
reciente era del 07.09. — 35 días de diferencia. Y como la lista ordena por
este campo por defecto, el proyecto estaba abajo del todo mientras se
trabajaba en él.

La propia `AUFGABEN.md` **no** cuenta. Si no, un simple vistazo a las
tareas subiría el proyecto, y la lista mostraría dónde escribió HQ en lugar
de dónde trabajaste tú.

## Ordenar

Un clic en un encabezado ordena por esa columna: `PROYECTO`, `TIPO`,
`AGENTE`, `NOTA`, `CREADO` o `MODIFICADO`. La columna activa brilla y
muestra con `▲` o `▼` en qué sentido se ordena; otro clic en la misma
columna invierte el sentido.

El primer clic en una columna de fecha empieza por la entrada más
reciente, el primero en `PROYECTO` o `TIPO` por la A. `AGENTE` y `NOTA`
empiezan por los proyectos que tienen entrada — en orden ascendente
saldrían primero los vacíos, justo los que nadie busca al pulsar la
columna. Los valores iguales se resuelven siempre alfabéticamente por
nombre.

La elección se guarda en `config.json` y sigue valiendo en el próximo
inicio. Sin entrada se ordena por `MODIFICADO` descendente, y el proyecto
editado más recientemente queda arriba.

## Una sola ventana

CODE/X HQ se ejecuta una sola vez. Si se inicia una segunda vez — un clic
en el acceso directo mientras ya está abierto —, ese inicio trae la ventana
existente al frente y se cierra. También desde la barra de tareas.

No es un fin en sí mismo: dos lanzadores a la vez tendrían cada uno su
propia copia de `config.json` y escribirían el archivo entero al guardar.
Gana quien guarda el último — el otro perdería orden, carpeta de proyectos
o diseño de consola.

Cómo está hecho: `projecthq/ui/instance.py`. Si ya hay uno en marcha lo
responde un mutex con nombre de Windows; traer la ventana al frente va por
una tubería con nombre de Qt. `QLocalServer` solo no basta — una tubería
permite varios servidores con el mismo nombre, así que un segundo `listen`
también tiene éxito.

Esto vale también al desarrollar: si el `.exe` está en marcha,
`py -3.12 main.py` trae su ventana al frente en lugar de abrir otra.

## Favoritos

`Ctrl+D` o la entrada del menú del clic derecho fija arriba el proyecto
seleccionado. Los proyectos fijados siempre van antes que los demás, sea
cual sea el orden, y llevan un asterisco en lugar de la flecha:

```
 *  Tarkov            py        01.09.2026    06.09.2026
 ►  Spielwiese        node      28.08.2026    05.09.2026
```

Es a propósito un `*` y no una `★`: Consolas no tiene estrella, y la fuente
de reserva la dibuja de 13 px en lugar de 7 — las columnas de una fila de
favorito quedaban desplazadas. Véase
[Caracteres en la cuadrícula](#caracteres-en-la-cuadrícula).

Entre ellos vale el mismo orden que abajo — un clic en `PROYECTO` ordena
alfabéticamente arriba y abajo. El mismo atajo los quita de nuevo.

Los nombres se guardan en `config.json` bajo `favorites` y sobreviven a
renombrados y reinicios. Si se elimina un proyecto, desaparece también su
entrada.

## config.json

Está en el perfil de usuario:

```
%APPDATA%\ProjectHQ\config.json
```

No junto al `.exe` — allí estaría en `dist\ProjectHQ`, y PyInstaller vacía
justo esa carpeta con `--noconfirm` en cada compilación; los ajustes se
perderían tras cada recompilación. Un archivo que siga en el lugar antiguo
se adopta una vez en el primer inicio (copiado, no movido).

Contenido:

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

`sort_key` es una de las columnas (`name`, `kind`, `agent`, `has_note`,
`created`, `mtime`), `sort_desc` el sentido. Si hay algo desconocido, se
ignoran ambos y se vuelve a ordenar por `MODIFICADO` descendente.

`console_style` es `crt` o `classic`; cualquier otra cosa usa `crt`.
`last_agent` es `claude` o `codex` y guarda lo último elegido en el diálogo
de inicio; lo desconocido vuelve a `claude`. `last_shell` es igualmente
`cmd` o `powershell`. `language` es `de`, `en`, `bhs`, `tr` o `es`; lo
desconocido vuelve a `de`.

`project_agents` asigna a cada proyecto el agente con el que se ejecutó
por última vez. Una entrada con un agente desconocido se descarta al
cargar — solo esa, no toda la tabla; el proyecto muestra entonces un `–`.

`projects_root`, `console_style`, `app_theme` y `language` se pueden
cambiar en el programa en `AJUSTES`. Si el archivo está dañado o falta, el
programa arranca con los valores por defecto. Un bloque `commands` de una
versión anterior se ignora al cargar.

## Eliminar

Eliminar mueve la carpeta del proyecto a la **papelera de reciclaje de
Windows**, nunca de forma definitiva. Antes aparece un diálogo de
confirmación con nombre, ruta y tamaño. Todo se puede restaurar desde la
papelera.

## Marco de ventana

Todas las ventanas van sin marco y traen su propia barra de título; si no,
sobre el aspecto de terminal habría una barra gris de Windows. Esto vale
también para los diálogos y la secuencia de arranque; en lugar de
`QMessageBox` hay un pequeño cuadro de mensaje propio.

Los gestos de Windows siguen funcionando, porque mover y redimensionar van
por `startSystemMove` y `startSystemResize`:

| Gesto | Efecto |
|-------|--------|
| Arrastrar la barra | Mover la ventana, acoplar al borde de la pantalla |
| Doble clic en la barra | Maximizar y volver |
| Arrastrar un borde o esquina | Cambiar tamaño (zona de agarre de 6 px) |
| `─` `□` `×` | Minimizar, maximizar, cerrar |

El marco brilla en verde mientras la ventana está activa y vuelve al verde
atenuado en caso contrario. Si la plataforma rechaza los gestos del sistema
— por ejemplo con la plataforma offscreen de las pruebas —, `frame.py`
calcula la geometría por sí mismo, así que la ventana sigue siendo usable.

## De dónde saca HQ el estado

Cuatro fuentes, cada una en `projecthq/activity.py`. Lo que no da nada no
aparece en la nota — una sección vacía sería peor que una ausente.

| Fuente | De dónde | Cubre |
|--------|----------|-------|
| En qué se trabajó | sesiones de Claude y Codex | 14 de 24 proyectos |
| Últimos commits | `git log -5 --oneline` | 7 de 24 |
| Sin commit | `git status --porcelain` | 7 de 24 |
| Cambiado recientemente | archivos más recientes de la carpeta | todos |

**Claude** guarda sus sesiones en `~/.claude/projects/<ruta>/` y da a cada
una un título por sí mismo — *"Opciones de inicio como administrador"*. Es
el mejor resumen disponible. Una sesión recién creada aún no tiene; entonces
aparece la primera pregunta.

**Codex** guarda por fecha, no por proyecto. A qué carpeta pertenece una
sesión figura en su primera línea — por eso solo se lee esa mientras no
esté claro si el archivo es el buscado. Codex no da título, así que aparece
la primera pregunta.

La asignación usa el directorio de trabajo registrado, no el nombre de la
carpeta: `Mi Proyecto` y `Mi-Proyecto` darían el mismo nombre, y cada uno
recibiría la nota del otro.

### Lo que tiene de incierto

**El formato no está documentado.** Codex cambió su registro entre mayo y
septiembre de 2026; ambas formas conviven en el archivo, y HQ lee las dos.
Si algo vuelve a cambiar, la sección afectada desaparece en silencio — la
nota se abre igualmente.

**Las sesiones desaparecen.** En `.claude/projects` algunos proyectos solo
tienen ya carpetas vacías. Es una ventana móvil, no un archivo. Por eso el
estado se **escribe en el archivo** y no se recalcula en cada apertura: lo
que está dentro una vez, se queda.

**La nota contiene lo que escribiste.** Fragmentos de lo que escribiste a
Claude y Codex. Por eso `AUFGABEN.md` está en el `.gitignore` de HQ. En
otros proyectos debes decidirlo tú — HQ no toca archivos `.gitignore`
ajenos.

### Tiempo de ejecución

Medido en los 24 proyectos: 2,6 s en total, de 0,03 a 0,57 s por proyecto.
Esto se ejecuta **solo** al crear una nota y en «Insertar estado» — nunca
al escanear la lista; si no, la ventana se congelaría en cada cambio de
ventana. Además, unos presupuestos de tiempo limitan la búsqueda, como con
`folder_size` en el diálogo de eliminar.

## Caracteres en la cuadrícula

Las columnas de la lista no están en una tabla, sino en una línea de texto
de caracteres de igual ancho. Funciona mientras cada carácter mida
exactamente un ancho — con Consolas 13 px son 7 px.

El problema: **ninguno** de los símbolos usados está en Consolas. Los
dibuja la fuente de reserva de Windows, y esta no respeta la cuadrícula.
Medido:

| Ancho | Caracteres |
|-------|------------|
| 7 px (correcto) | `►` `*` `≡` `·` `–` `●` `○` `■` `□` `▪` `▬` `▒` `─` |
| 8 px | `▶` `◆` `◇` `▤` `▣` |
| 13 px | `★` `☆` `✱` `✦` `☰` |

Un carácter demasiado ancho empuja todas las columnas de su fila a la
derecha. Eso es justo lo que hacía la estrella original `★` de la fila de
favoritos, seis píxeles — y pasó desapercibido porque la prueba solo
*contaba* caracteres en lugar de *medirlos*.

Esto solo puede medirse con una base de datos de fuentes real. Las pruebas
se ejecutan con `QT_QPA_PLATFORM=offscreen` y allí reciben el mismo ancho
para cada carácter — así que no pueden comprobarlo. Para eso existe

```
py -3.12 tools/messe_zeichen.py
```

La herramienta mide cada símbolo usado en una lista con estilo completo y
devuelve el código 1 si alguno no cabe. Las pruebas solo aseguran que
ningún símbolo entre sin pasar por esta medición: se permite lo que figura
en `GRID_MARKS` en `projecthq/ui/window.py`. Quien quiera un símbolo nuevo,
primero lo mide y después lo añade ahí.

## Icono

`assets/projecthq.ico` es el icono del `.exe` y a la vez el icono de la
ventana y de la barra de tareas en ejecución. Contiene todos los tamaños de
16 a 256 píxeles, para que la barra de tareas y el Explorador no tengan que
reducirlo.

No se dibuja a mano, sino con

```
py -3.12 tools/make_icon.py
```

El script renderiza a 1024 píxeles y reduce. Para cambiar el motivo, cambia
la cuadrícula de 16x16 `SKULL` en `tools/make_icon.py` y ejecuta el script
una vez; después `build.ps1` para un `.exe` nuevo.

Windows guarda los iconos en caché de forma agresiva. Si el Explorador
sigue mostrando la imagen antigua tras compilar, ayuda
`ie4uinit.exe -show` o reiniciar el Explorador.

## Recompilar

```
powershell -ExecutionPolicy Bypass -File build.ps1
```

El script ejecuta primero las pruebas y se detiene si alguna falla.
Después PyInstaller empaqueta en `dist\ProjectHQ\`. La compilación es a
propósito onedir y no onefile: arranca en un segundo en lugar de en cuatro,
porque no hay que desempaquetar nada.

**ProjectHQ debe estar cerrado al compilar.** Un `.exe` en marcha bloquea
sus DLL; PyInstaller no puede reemplazar `dist\ProjectHQ` y se detiene a
mitad de la limpieza — con una carpeta medio vacía. Si pasa, ayuda

```
Remove-Item -Recurse -Force build, dist
```

y volver a ejecutar. Si no, el análisis arrastra restos de la carpeta rota
a la siguiente compilación.

Ejecutar solo las pruebas:

```
py -3.12 -m pytest -q
```

## Estructura

```
assets/
  projecthq.ico icono de la aplicación (calavera con aspecto CRT)
tools/
  make_icon.py  vuelve a dibujar el icono
  messe_zeichen.py  mide si los símbolos de la lista caben en la cuadrícula
projecthq/
  config.py     ajustes, config.json
  scanner.py    encontrar proyectos, determinar tipo, leer marcas de
                tiempo, ordenar
  activity.py   estado de un proyecto: sesiones de Claude y Codex,
                commits, archivos cambiados recientemente
  runner.py     iniciar, crear, renombrar, eliminar,
                Explorador/Terminal/VS Code, nota (AUFGABEN.md)
  theme.py      paleta de colores y hoja de estilos Qt
  i18n.py       idiomas de la interfaz, tr()
  ui/
    window.py     ventana principal
    dialogs.py    proyecto nuevo, renombrar, eliminar, ajustes,
                  diálogo de inicio (¿con qué?)
    boot.py       secuencia de arranque
    crt.py        capa de líneas de barrido y viñeta
    frame.py      marco de ventana propio con barra de título
    appicon.py    icono para ventana y barra de tareas
main.py
```

`config.py`, `scanner.py`, `activity.py` y `runner.py` no contienen Qt. Es
intencionado: toda la lógica puede probarse sin interfaz en marcha. Las
pruebas de `tests/` cubren estos módulos directamente, y además hay pruebas
de extremo a extremo que construyen la ventana principal real en modo
offscreen.

## Licencia

[MIT](LICENSE)
