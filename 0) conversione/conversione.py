import csv
import json
import xml.etree.ElementTree as ET

def json_to_csv(json_file, csv_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    columns = data["columns"]
    rows = data["data"]
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)

def xml_to_csv(xml_file, csv_file):
    # Parsing dell'XML
    tree = ET.parse(xml_file)
    root = tree.getroot()
    columns = [elem.tag for elem in root.find('row')]
    
    rows = []
    for row in root.findall('row'):
        rows.append([value.text for value in row])
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)


countries_in = 'C:/Users/catta/OneDrive/Desktop/LAB2/dataset/countries.xml'
countries_out = 'C:/Users/catta/OneDrive/Desktop/LAB2/conversione/countries_out.csv'

input_j = 'C:/Users/catta/OneDrive/Desktop/LAB2/dataset/tourney.json'
output_csv = 'C:/Users/catta/OneDrive/Desktop/LAB2/conversione/file_tourney.csv'

xml_to_csv(countries_in, countries_out)
json_to_csv(input_j, output_csv)


# def read_csv(file_path):
#     """Legge un file CSV e restituisce i dati come lista di dizionari."""
#     with open(file_path, mode='r', encoding='utf-8-sig') as file:
#         reader = csv.DictReader(file)
#         data = list(reader)  # Converte il reader in una lista di dizionari
    
#     return data

# def missing_values(data):
#     count = {}
#     for row in data:
#         for key, value in row.items():
#             if value == '' or value is None:
#                 if key in count:
#                     count[key] += 1
#                 else:
#                     count[key] = 1
#     return count

# def load_json(path):
#     with open(path, "r", encoding="utf-8") as file:
#         data = json.load(file)
#     return data

# tourney_path = 'C:/Users/catta/OneDrive/Desktop/LAB2/dataset/tourney.json'
# tourney = load_json(tourney_path)
# print(type(tourney)) 


# fact_path = 'C:/Users/catta/OneDrive/Desktop/LAB2/dataset/final_fact.csv'
# fact = read_csv(fact_path   )

# missing_t = missing_values(tourney)
# print(f"Missing : \n{missing_t}")


# def clean_draw_size(tournament_data, fact_data):
#     """
#     1. Converte draw_size in interi.
#     2. Riempie i missing values con il draw_size noto per lo stesso torneo.
#     3. Se non disponibile, usa il conteggio degli id unici da fact_data.
#     """
    
#     # Step 1: Convertire i valori a interi, escludendo "R" e valori mancanti
#     for match in tournament_data:
#         try:
#             match['draw_size'] = int(float(match['draw_size']))
#         except ValueError:
#             match['draw_size'] = None  # Segniamo i valori non validi come None
    
#     # Step 2: Creare un dizionario per mappare torneo → draw_size esistenti
#     tourney_sizes = {}
#     for match in tournament_data:
#         tourney = match['tourney']
#         if match['draw_size'] is not None:
#             tourney_sizes[tourney] = match['draw_size']

#     # Step 3: Contare gli id unici (winner_id, loser_id) per torneo in fact_data
#     player_counts = defaultdict(set)
#     for match in fact_data:
#         player_counts[match['tourney']].add(match['winner_id'])
#         player_counts[match['tourney']].add(match['loser_id'])

#     # Step 4: Riempire i missing values
#     for match in tournament_data:
#         tourney = match['tourney']
#         if match['draw_size'] is None or match['draw_size'] == 'R':
#             if tourney in tourney_sizes:  
#                 match['draw_size'] = tourney_sizes[tourney]  # Usa valore noto
#             else:
#                 match['draw_size'] = len(player_counts[tourney])  # Usa numero di giocatori unici

#     return tournament_data

# def fill_missing_surface(tournament_data):
#     # Dizionario per memorizzare la superficie nota per ogni torneo
#     tourney_surface = {}

#     # Prima passata: raccogliere i valori noti di surface per ogni torneo
#     for match in tournament_data:
#         tourney = match['tourney']
#         surface = match['surface']

#         if surface and surface != '':  # Controlla che il valore non sia mancante
#             tourney_surface[tourney] = surface  # Salva la superficie per il torneo

#     # Seconda passata: riempire i valori mancanti
#     for match in tournament_data:
#         if not match['surface'] or match['surface'] == '':  # Se mancante
#             match['surface'] = tourney_surface.get(match['tourney'], 'Unknown')

#     return tournament_data



# def save_matches_to_csv(matches, output_file):
#     """Salva i match in un file CSV."""
#     if not matches:
#         return
    
#     headers = matches[0].keys()
#     with open(output_file, mode='w', newline='', encoding='utf-8') as f:
#         writer = csv.DictWriter(f, fieldnames=headers)
#         writer.writeheader()
#         writer.writerows(matches)

# tour = clean_draw_size(tourney, fact)
# tour = fill_missing_surface(tour)

# save_matches_to_csv(tour, 'C:/Users/catta/OneDrive/Desktop/LAB2/dataset/to.csv')

# missing_t = missing_values(tour)
# print(f"Missing : \n{missing_t}")



