# # Tramite codice, riempire le tabelle _SSIS con il 20% dei dati mantenendo l'integrià dei dati

# Tramite codice, riempire le tabelle _SSIS con il 20% dei dati mantenendo l'integrià dei dati

import pyodbc
import csv
import random

# Connessione al database
server = 'tcp:lds.di.unipi.it'
database = 'Group_ID_13_DB'
username = 'Group_ID_13'
password = 'M1GUWCGQ'
connectionString = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

cnxn = pyodbc.connect(connectionString)
cursor = cnxn.cursor()
cursor.fast_executemany = True

# Percorsi dei file CSV
csv_files = {
    "tournament": "C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/tabAttm/tourney.csv",
    "matchStats": "C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/tabAttm/match_stats.csv",
    "player": "C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/tabAttm/player.csv",
    "geography": "C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/tabAttm/geography.csv",
    "date": "C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/tabAttm/date.csv",
    "matchFact": "C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/tabAttm/fact.csv"
}

def sample_data(file_path, sample_fraction=0.2):
    """Estrae un campione casuale dal file CSV mantenendo l'intestazione."""
    with open(file_path, "r", encoding="utf-8") as file:
        reader = list(csv.reader(file))
        header, rows = reader[0], reader[1:]
        total_rows = len(rows)  
        sample_size = max(1, int(total_rows * sample_fraction))  
        sampled_rows = random.sample(rows, sample_size)  
    return header, sampled_rows

# Step 1: Estrarre il 20% dei tornei
header_tourney, sampled_tourney = sample_data(csv_files["tournament"], 0.2)
valid_tourney = {row[0] for row in sampled_tourney}  # Set di chiavi valide

# Step 2: Estrarre i match appartenenti ai tornei selezionati
header_fact, all_facts = sample_data(csv_files["matchFact"], 1.0)
filtered_facts = [row for row in all_facts if row[header_fact.index("tourney_fk")] in valid_tourney]

sampled_facts = random.sample(filtered_facts, max(1, int(len(filtered_facts) * 0.2)))
valid_match_stats = {row[header_fact.index("match_stats_fk")] for row in sampled_facts}

valid_players = {row[header_fact.index("winner_fk")] for row in sampled_facts}.union(
                {row[header_fact.index("loser_fk")] for row in sampled_facts})

# Step 3: Estrarre i player coinvolti nei match selezionati
header_player, all_players = sample_data(csv_files["player"], 1.0)
filtered_players = [row for row in all_players if row[0] in valid_players]
sampled_players = random.sample(filtered_players, max(1, int(len(filtered_players) * 0.2)))

valid_geography = {row[header_player.index("geo_fk")] for row in sampled_players}

# Step 4: Estrarre la geografia collegata ai player selezionati
header_geography, all_geography = sample_data(csv_files["geography"], 1.0)
filtered_geography = [row for row in all_geography if row[0] in valid_geography]

# Step 5: Estrarre le statistiche dei match selezionati
header_stats, all_stats = sample_data(csv_files["matchStats"], 1.0)
filtered_stats = [row for row in all_stats if row[0] in valid_match_stats]
sampled_stats = random.sample(filtered_stats, max(1, int(len(filtered_stats) * 0.2)))

# Step 6: Estrarre le date collegate ai tornei selezionati
header_date, all_dates = sample_data(csv_files["date"], 1.0)
valid_dates = {row[header_tourney.index("date_fk")] for row in sampled_tourney}
filtered_dates = [row for row in all_dates if row[0] in valid_dates]

# Funzione per inserire dati nel database
def insert_data(table_name, header, data):
    if not data:
        print(f"No data to insert for {table_name}")
        return
    columns = ", ".join(header)
    placeholders = ", ".join(["?" for _ in header])
    insert_query = f"INSERT INTO {table_name}_SSIS_PY ({columns}) VALUES ({placeholders})"
    cursor.executemany(insert_query, data)
    cnxn.commit()
    print(f"Inserted {len(data)} records into {table_name}_SSIS_PY")

# Inserire i dati in ordine corretto
insert_data("tournament", header_tourney, sampled_tourney)
insert_data("player", header_player, sampled_players)
insert_data("geography", header_geography, filtered_geography)
insert_data("matchStats", header_stats, sampled_stats)
insert_data("date", header_date, filtered_dates)
insert_data("matchFact", header_fact, sampled_facts)

# Chiudere la connessione
cursor.close()
cnxn.close()
print("Data population completed!")




# import pyodbc
# import csv
# import random

# # Connessione al database
# server = 'tcp:lds.di.unipi.it'
# database = 'Group_ID_13_DB'
# username = 'Group_ID_13'
# password = 'M1GUWCGQ'
# connectionString = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

# cnxn = pyodbc.connect(connectionString)
# cursor = cnxn.cursor()
# cursor.fast_executemany = True

# # Percorsi dei file CSV
# csv_files = {
#     "tournament": "C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/tabAttm/tourney.csv",
#     "matchStats": "C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/tabAttm/match_stats.csv",
#     "player": "C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/tabAttm/player.csv",
#     "geography": "C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/tabAttm/geography.csv",
#     "date": "C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/tabAttm/date.csv",
#     "matchFact": "C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/tabAttm/fact.csv"
# }

# def sample_data(file_path, sample_fraction=0.2):
#     """Estrae un campione casuale dal file CSV mantenendo l'intestazione."""
#     with open(file_path, "r", encoding="utf-8") as file:
#         reader = list(csv.reader(file))
#         header, rows = reader[0], reader[1:]
#         total_rows = len(rows)  
#         sample_size = max(1, int(total_rows * sample_fraction))  
#         sampled_rows = random.sample(rows, sample_size)  
#     return header, sampled_rows

# # Step 1: Estrarre il 20% dei tornei
# header_tourney, sampled_tourney = sample_data(csv_files["tournament"], 0.2)
# valid_tourney = {row[0] for row in sampled_tourney}  # Set di chiavi valide

# # Step 2: Estrarre i match appartenenti ai tornei selezionati
# header_fact, all_facts = sample_data(csv_files["matchFact"], 1.0)  # Prendiamo tutti i match
# filtered_facts = [row for row in all_facts if row[header_fact.index("tourney_fk")] in valid_tourney]

# sampled_facts = random.sample(filtered_facts, max(1, int(len(filtered_facts) * 0.2)))
# valid_match_stats = {row[header_fact.index("match_stats_fk")] for row in sampled_facts}

# valid_players = {row[header_fact.index("winner_fk")] for row in sampled_facts}.union(
#                 {row[header_fact.index("loser_fk")] for row in sampled_facts})

# # Step 3: Estrarre i player coinvolti nei match selezionati
# header_player, all_players = sample_data(csv_files["player"], 1.0)
# filtered_players = [row for row in all_players if row[0] in valid_players]
# sampled_players = random.sample(filtered_players, max(1, int(len(filtered_players) * 0.2)))

# # Step 4: Estrarre le statistiche dei match selezionati
# header_stats, all_stats = sample_data(csv_files["matchStats"], 1.0)
# filtered_stats = [row for row in all_stats if row[0] in valid_match_stats]
# sampled_stats = random.sample(filtered_stats, max(1, int(len(filtered_stats) * 0.2)))

# # Step 5: Estrarre le date collegate ai tornei selezionati
# header_date, all_dates = sample_data(csv_files["date"], 1.0)
# valid_dates = {row[header_tourney.index("date_fk")] for row in sampled_tourney}
# filtered_dates = [row for row in all_dates if row[0] in valid_dates]

# # Funzione per inserire dati nel database
# def insert_data(table_name, header, data):
#     if not data:
#         print(f"No data to insert for {table_name}")
#         return
#     columns = ", ".join(header)
#     placeholders = ", ".join(["?" for _ in header])
#     insert_query = f"INSERT INTO {table_name}_SSIS_PY ({columns}) VALUES ({placeholders})"
#     cursor.executemany(insert_query, data)
#     cnxn.commit()
#     print(f"Inserted {len(data)} records into {table_name}_SSIS_PY")

# # Inserire i dati in ordine corretto
# insert_data("tournament", header_tourney, sampled_tourney)
# insert_data("player", header_player, sampled_players)
# insert_data("matchStats", header_stats, sampled_stats)
# insert_data("date", header_date, filtered_dates)
# insert_data("matchFact", header_fact, sampled_facts)

# # Chiudere la connessione
# cursor.close()
# cnxn.close()
# print("Data population completed!")








