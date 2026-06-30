# Decision Support System per una Federazione Tennistica

Progetto per il corso di **Laboratory of Data Science** (Data Science and Business Informatics, Università di Pisa, A.A. 2024/2025).

## Panoramica

Il progetto simula la realizzazione di un **Decision Support System** per una federazione sportiva di tennis, coprendo l'intera pipeline: dalla comprensione e pulizia dei dati grezzi, alla progettazione di un data warehouse, fino al caricamento dati, alla costruzione di un cubo OLAP e alla creazione di dashboard analitiche.

I dati di partenza sono distribuiti su tre file eterogenei:

- **fact.csv** — dati principali delle partite (vincitori, perdenti, statistiche)
- **tourney.json** — informazioni sui tornei (nome, superficie, dimensione del tabellone, livello, timestamp)
- **countries.xml** — dati geografici aggiuntivi (codice paese, nome, continente)

## Pipeline del progetto

### 1. Data Understanding
Analisi della struttura dei tre dataset e delle relazioni tra di essi (`tourney`, `winner_ioc`/`loser_ioc`), con identificazione e quantificazione dei missing values per ciascun file.

### 2. Data Cleaning
Trattamento dei valori mancanti con strategie differenziate per colonna:
- mappatura di IOC e caratteristiche giocatori tramite ID
- imputazione del ranking basata su match adiacenti o media del torneo
- imputazione di età/altezza con mediana di torneo o globale
- recupero di codici paese obsoleti e arricchimento geografico tramite API esterne (restcountries.com)
- pulizia ed estrazione di componenti temporali dal timestamp dei tornei

### 3. Data Schema (Data Warehouse)
Progettazione di uno schema a 6 tabelle (`tournament`, `match_fact`, `player`, `date`, `match_stats`, `geography`), con la fact table `match_fact` collegata a due chiavi esterne sulla dimensione `player` (`winner_fk`, `loser_fk`) per ottimizzare le query sui giocatori.

### 4. Data Uploading
Confronto tra due strategie di caricamento (campione del 20% mantenendo l'integrità referenziale):
- **Python** (`pyodbc` + `fast_executemany`)
- **SSIS** (Lookup, Row Sampling, Merge Join, OLE DB Destination)

Python è risultato l'approccio più performante ed è stato quindi adottato per il caricamento completo dei dati.

### 5. SSIS — Workflow analitici
Implementazione di due workflow SSIS per rispondere a business question complesse:
- **Nemesis per anno**: per ogni giocatore e anno, l'avversario contro cui ha perso più partite
- **Age-outlier matches**: identificazione dei match con differenza di età anomala rispetto alla media del torneo (> 1.5×) e dei giocatori più coinvolti per anno

### 6. SSAS — Cubo OLAP
Costruzione di un cubo con gerarchie su Date (`DayMonthYear`) e Geography (`Geo`: Continent → Country → IOC code), misura calcolata `Profit` e misure `n Spectators`, `Match Expenses`, `n Matches`.

### 7. Query MDX
Implementazione di query per rispondere a business question, tra cui:
- giocatore con più sconfitte per continente (`TOPCOUNT`, `GENERATE`)
- numero di giocatori unici per torneo (`DistinctCount`, `Union`)
- variazione percentuale dei profitti per trimestre rispetto all'anno precedente (`PARALLELPERIOD`, `IIF`)

### 8. Dashboard
- Distribuzione geografica dei punti in classifica di vincitori e perdenti (equal frequency binning)
- Dashboard finanziaria su profitti per superficie/mese, spettatori per mese e spese per livello di torneo


## Tech Stack

- Python (`pandas`, `pyodbc`)
- SQL Server / SQL Server Management Studio
- SSIS (SQL Server Integration Services)
- SSAS (SQL Server Analysis Services) — cubo OLAP e query MDX
- Power BI (o strumento equivalente per le dashboard)

## Autori

- Cattari Simona
- Trivelli Matteo
