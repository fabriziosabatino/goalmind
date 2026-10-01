# Correzioni e preparazione alla discussione

## Problemi riprodotti

| Problema iniziale | Effetto | Correzione |
| --- | --- | --- |
| `deserialize_players()` restituiva un dizionario mai riempito | Dati presenti internamente, risultato della funzione vuoto | Restituzione di una copia del dizionario caricato |
| Dizionario giocatori indicizzato solo per nome | Uno dei due Juan Cruz veniva sovrascritto: 1.532 righe su 1.533 | Chiave nome/squadra; errore esplicito sulle ricerche ambigue |
| Nomi di squadra diversi nei CSV | Bayern, PSG, AC Milan e altri non trovati | Alias espliciti e normalizzazione |
| `to_float()` convertiva errori/mancanti in zero | Mancanza di xG interpretata come nessuna possibilità di segnare | NaN per mancanti, errore per valori malformati |
| Somma pesata di indicatori e clipping a [0,1] | Salah arrivava automaticamente al 100% | Modello Poisson con formula, esposizione e ipotesi esplicite |
| Elo interpretato come solidità difensiva | Forza complessiva confusa con gol subiti | Elo descrittivo separato dal fattore difensivo osservato |
| Confronto xG/90 con gol totali nella CLI | Quantità su scale/esposizioni diverse | Unica analisi condivisa con xG totali e gol totali |
| xG totali ricostruiti da xG/90 arrotondati | Ignorata una colonna disponibile più precisa | Uso della colonna `xG` del CSV |
| Partite non ordinate esplicitamente, nessuna validazione punteggi | Elo dipendente dall'ordine del file; un NaN sarebbe trattato come pareggio | Ordinamento cronologico, controlli, conteggi degli scarti |
| Aggiornamenti Elo ripetuti senza reset | Stesse partite contate nuovamente | Ricalcolo dalla base 1.500 |
| README con file/funzioni inesistenti, dipendenze mancanti | Installazione e uso non riproducibili | Istruzioni reali, dipendenze versionate, notebook |
| Solo CLI per presentare il progetto | Mancava notebook/app richiesto dalla consegna | Notebook che importa i moduli |

Non era tutto sbagliato: il risultato vittoria/pareggio/sconfitta e l'aggiornamento simmetrico dell'Elo erano corretti per punteggi validi. Sono stati mantenuti e verificati.

## Percorso di studio

1. Segui una riga del CSV attraverso `deserialize_players()`, la chiave del dizionario e `Player`.
2. Spiega perché `NaN` e zero hanno significati diversi e perché servono due colonne nella chiave dei giocatori.
3. Calcola a mano un aggiornamento Elo: 1.500 contro 1.500, `H=0`, vittoria in casa, `K=25` → 1.512,5 e 1.487,5.
4. Spiega che il risultato atteso Elo include il valore 0,5 del pareggio.
5. Deriva `P(G >= 1) = 1 - P(G = 0)` nel modello Poisson. `xG/90` è un'intensità, non una probabilità.
6. Confronta 90 e 45 minuti mantenendo lo stesso tasso. Non dimezzi direttamente la probabilità: dimezzi lambda.
7. Calcola il fattore difensivo e spiega perché non è una misura perfetta della difesa.
8. Leggi `statistics()`: coppie complete, controllo della variabilità, Pearson e significato descrittivo.
9. Spiega cosa importa il notebook e perché la logica non è duplicata nelle celle.
10. Esegui i test e identifica quale errore iniziale intercetta ciascun gruppo.

## Prima della consegna

- Recuperare gli URL e le licenze originali dei CSV e la data/intervallo delle statistiche dei giocatori.
- Confermare con i docenti l'approvazione del tema personalizzato, secondo la consegna allegata.
- Eseguire il notebook nel proprio ambiente e studiare i moduli: non presentare il modello come una previsione validata.
- Aggiungere eventuali modifiche personali con commit piccoli e descrittivi, senza ricostruire una cronologia artificiale.
