# GoalMind

Progetto Python per esplorare statistiche dei calciatori, risultati storici ed Elo delle squadre. La domanda è: **come cambia una stima della probabilità di segnare almeno un gol al variare dei minuti giocati e dei gol subiti dall'avversaria?**

Il progetto offre un notebook Jupyter per la presentazione e una CLI. Entrambe le interfacce importano gli stessi moduli: il notebook non duplica la logica dell'analisi.

## Installazione ed esecuzione

Verificato con Python 3.12; usare Python 3.11 o successivo.

```bash
git clone https://github.com/fabriziosabatino/goalmind.git
cd goalmind
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements-notebook.txt
python -m notebook goalmind.ipynb
```

Nel notebook scegliere **Restart Kernel and Run All Cells**. Per usare solo la CLI basta installare `requirements.txt`:

```bash
python -m pip install -r requirements.txt
python main.py
```

I percorsi predefiniti sono relativi a `main.py`, quindi l'avvio funziona anche da un'altra directory. Si possono specificare CSV alternativi e limiti temporali inclusivi:

```bash
python main.py --start-date 2020-08-01 --end-date 2025-06-01
python main.py --players /path/players.csv --matches /path/matches.csv
```

Comandi della CLI:

```text
searchplayer "Mohamed Salah"
searchplayer "Juan Cruz" "Leganes"
searchteam Bayern
scoreprob "Mohamed Salah" "Arsenal" 60
scoreprob "Juan Cruz" "Barcelona" 90 "Leganes"
analysis
analysis outputs
export outputs
exit
```

`analysis outputs` salva i grafici senza aprire finestre; `export outputs` salva le tabelle CSV. I nomi sono cercati ignorando maiuscole, accenti e spazi ridondanti. Gli alias delle squadre sono espliciti; un nome ambiguo richiede la squadra del giocatore.

## Dati e qualità

I CSV già presenti nel repository sono:

| File | Contenuto | Dimensioni originali |
| --- | --- | --- |
| `import/Football_Player_Data-Analysis.csv` | Statistiche aggregate dei calciatori, minuti, gol, xG, xG/90 e rating | 1.533 righe, 32 colonne |
| `import/Matches.csv` | Risultati di più campionati tra 28/07/2000 e 01/06/2025 | 230.557 righe, 48 colonne |

**Provenienza da completare prima della consegna:** gli URL originali, la licenza e la data di estrazione non sono documentati nel repository iniziale. Il file dei giocatori non contiene una data di osservazione o una stagione: il progetto non inventa queste informazioni. Recuperare e indicare la fonte di entrambi i CSV e l'intervallo esatto delle statistiche dei giocatori.

Il caricamento:

- conserva tutte le 1.533 osservazioni, comprese le due righe di Juan Cruz in squadre diverse;
- tratta `-` e valori mancanti come dati assenti, non come zero: 28 righe non hanno xG/90 disponibile;
- controlla colonne e valori numerici, esclude partite senza data/nome/punteggio valido e rende visibili i conteggi;
- elimina duplicati esatti dei risultati e rifiuta punteggi discordanti per la stessa partita;
- usa 22 alias espliciti per collegare le squadre dei due CSV, senza abbinamenti approssimativi;
- ordina le partite per data e orario prima di aggiornare l'Elo.

Con i dati forniti, dalla data predefinita 01/08/2020 si caricano **57.709 partite**, tutte le squadre dei giocatori trovano uno storico e vengono rilevate 3 righe con risultati mancanti nell'intero CSV (precedenti all'intervallo predefinito). I risultati restano storici: i file non si aggiornano automaticamente.

## Metodi e ipotesi

### Elo

Ogni squadra parte da 1.500. Per la squadra di casa:

\[
E_H = \frac{1}{1 + 10^{(R_A-R_H-H)/400}},\qquad
\Delta = K(S_H-E_H).
\]

`K=25`, vantaggio casa `H=40`, risultato `S_H=1`, `0.5`, `0` per vittoria, pareggio, sconfitta. La squadra di casa guadagna `delta` e quella ospite perde lo stesso valore. Le aspettative vengono calcolate prima di aggiornare i rating. Ripetere `update_all_elo()` ricostruisce il rating dalla base: non conta le partite due volte.

L'Elo misura **forza complessiva**, non difesa. `E_H` è un punteggio atteso, non la probabilità di vincere: da solo non separa vittorie e pareggi. Campionati privi di partite tra loro non hanno una scala comune calibrata: le classifiche visualizzate sono filtrate per divisione. Anche cambi di divisione e scelta della data iniziale influenzano i rating.

### Stima dei gol

Assumendo un conteggio dei gol di Poisson con intensità costante:

\[
\lambda = \mathrm{xG/90}\,\frac{m}{90}\,d,\qquad
P(G\geq 1)=1-e^{-\lambda}.
\]

`m` è il numero di minuti ipotizzati (0–120). `d=1` dà la stima di base. Per un'avversaria della stessa ultima divisione osservata:

\[
d = \frac{\text{gol subiti dall'avversaria / partite dell'avversaria}}
{\text{media gol per squadra-partita nel campionato}}.
\]

Il fattore usa gli ultimi 365 giorni rispetto all'ultima partita caricata, nell'ultima divisione dell'avversaria, e richiede almeno 5 partite. La media di campionato usa lo stesso intervallo disponibile. Con una data iniziale più recente, la finestra disponibile può essere più breve di 365 giorni. Un fattore inferiore a uno riduce l'intensità; uno superiore la aumenta. La correzione viene applicata all'intensità prima della trasformazione in probabilità.

Esempio: Salah ha `xG/90=0.75`, quindi per 90 minuti contro un'avversaria media `1-exp(-0.75)=52.76%`. Per 60 minuti la stima di base è `39.35%`. Non viene trasformato automaticamente in un 100% come nel punteggio originale.

**Limiti:** il giocatore deve effettivamente partecipare per i minuti specificati; non stimiamo convocazione, titolarità o infortuni. Il fattore difensivo è descrittivo e non è corretto per casa/trasferta o forza del calendario. Il modello non è calibrato né validato su partite future. Il disallineamento temporale tra statistiche aggregate dei giocatori e storico delle partite impedisce di dichiarare queste stime come previsioni senza leakage. Per valutare accuratezza servirebbero dati giocatore-partita datati, separazione cronologica tra stima e valutazione, e misure di calibrazione. Non usiamo coefficienti arbitrari di ruolo, tackle o rating come se fossero probabilità.

### Analisi descrittiva

La correlazione di Pearson confronta **xG totali osservati** con **gol totali** dello stesso snapshot. Include gli zeri osservati, esclude coppie mancanti e gestisce campioni piccoli/costanti. Il CSV contiene gli xG totali: non occorre ricostruirli da un tasso arrotondato. La correlazione positiva è descrittiva: volume di gioco, eterogeneità e dipendenze tra giocatori limitano l'interpretazione del p-value. Non dimostra capacità predittiva su nuove partite.

I grafici mostrano gol/xG (almeno 500 minuti), distribuzione del rating e classifica Elo delle squadre attive di una divisione. Le tabelle possono essere esportate in CSV e i grafici in PNG.

## Organizzazione

```text
goalmind/
├── main.py                       # Caricamento comune e avvio CLI
├── goalmind.ipynb                 # Presentazione e analisi con moduli importati
├── app/
│   ├── cli.py                    # Interfaccia a comandi
│   └── elo_application.py        # Input, pulizia, Elo, statistiche e grafici
├── data_structure/
│   ├── player.py                 # Statistiche e stima Poisson
│   ├── team.py                   # Elo e statistiche difensive
│   ├── match.py                  # Risultato valido di una partita
│   └── names.py                  # Normalizzazione e alias
├── import/                       # CSV originali conservati
├── tests/test_goalmind.py         # Test di regressione e sui dati reali
├── docs/CORREZIONI.md             # Problemi risolti e domande per la discussione
├── requirements.txt              # Dipendenze dell'analisi con versioni
└── requirements-notebook.txt     # Dipendenze aggiuntive per Jupyter
```

## Verifica

```bash
python -m unittest discover -s tests -v
```

I test coprono formula Poisson, minuti, dati mancanti, risultati non validi, ordinamento, filtri temporali, duplicati, omonimi, alias, somma dei rating e ricalcolo Elo. Tutte le sette celle di codice del notebook sono state eseguite in ordine tramite IPython sui CSV originali e i grafici sono stati controllati. L'avvio del kernel Jupyter non è stato verificabile nell'ambiente di correzione, che blocca i socket: eseguire anche **Restart Kernel and Run All Cells** sul proprio computer.

Per la discussione, studiare `docs/CORREZIONI.md` ed essere in grado di spiegare ogni passaggio. Le correzioni sono state preparate con assistenza AI e verificate; la comprensione del codice e il completamento della provenienza dei dati restano necessari prima della consegna.

Autore: Fabrizio Sabatino.
