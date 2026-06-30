import csv
from collections import defaultdict
import statistics
from datetime import datetime, timezone
import json
import re
import xml.etree.ElementTree as ET
import requests


def read_csv(file_path):
    with open(file_path, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        data = list(reader)  # Converte il reader in una lista di dizionari
    
    return data


def to_csv(data, output_file):
    if not data:
        return
    
    headers = data[0].keys()
    with open(output_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)


def missing_values(data):
    count = {}
    for row in data:
        for key, value in row.items():
            if value == '' or value is None:
                if key in count:
                    count[key] += 1
                else:
                    count[key] = 1
    return count

def remove_keys(data, to_remove):
    for row in data:
        for key in to_remove:
            row.pop(key, None)

def fill_categorical(fact, columns_to_fill, id_columns, default_value):
    for col, id_col in zip(columns_to_fill, id_columns):
        # Creiamo una mappa con gli ID e i loro valori noti
        col_map = {row[id_col]: row[col] for row in fact if row[col] not in ('', None)}

        initial_missing = sum(1 for row in fact if row[col] in ('', None))

        for row in fact:
            if row[col] in ('', None):
                row[col] = col_map.get(row[id_col], default_value)

        after_map_missing = sum(1 for row in fact if row[col] in ('', None))

        filled = initial_missing - after_map_missing
        print(f"Valori riempiti con la mappa in {col}: {filled}")

        final_missing = sum(1 for row in fact if row[col] in ('', None))
        print(f"Valori impostati a '{default_value}' in {col}: {after_map_missing}")

    return fact

def fill_int(fact, columns, id_cols):
    for col, id_col in zip(columns, id_cols):
        # Crea una mappa con l'ID giocatore e la prima altezza trovata
        col_map = {}
        for row in fact:
            if row[id_col] and row[col] not in ('', None):
                col_map[row[id_col]] = row[col]  # Salva il primo valore valido trovato per quell'ID

        # Calcola la mediana globale della colonna
        valid_values = [float(row[col]) for row in fact if row[col] not in ('', None)]
        global_median = statistics.median(valid_values) if valid_values else None

        initial_missing = sum(1 for row in fact if row[col] in ('', None))

        for row in fact:
            if row[col] in ('', None):
                if row[id_col] in col_map:
                    row[col] = col_map[row[id_col]]  # Usa l'altezza già registrata per quell'ID
                else:
                    row[col] = global_median  # Se non c'è, usa la mediana globale

        after = sum(1 for row in fact if row[col] in ('', None))
        filled = initial_missing - after
        print(f"Filled {filled} missing values in column {col}")

    return fact

def fill_with_mean(fact, columns, id):
    age_sums = defaultdict(float)
    age_counts = defaultdict(int)
    
    # Calcola la media per ogni giocatore
    for row in fact:
        for col, id_col in zip(columns, id):
            if row[col] not in ('', None):
                age_sums[row[id_col]] += float(row[col])
                age_counts[row[id_col]] += 1

    age_means = {player_id: age_sums[player_id] / age_counts[player_id] for player_id in age_sums}

    # Riempie i valori mancanti con la media del giocatore
    for row in fact:
        for col, id_col in zip(columns, id):
            if row[col] in ('', None):
                row[col] = age_means.get(row[id_col])

    return fact

def fill_with_global_mean(fact, columns):
    for col in columns:
        existing_ages = [float(row[col]) for row in fact if row[col] not in ('', None)]
        global_mean = sum(existing_ages) / len(existing_ages) if existing_ages else None

        for row in fact:
            if row[col] in ('', None) and global_mean is not None:
                row[col] = global_mean
    
    return fact

def compute_next_indices_by_tourney(matches):
    tourney_dict = defaultdict(list)
    
    for idx, match in enumerate(matches):
        tourney_dict[match["tourney"]].append(idx)
    
    next_indices = {}
    for indices in tourney_dict.values():
        for i, idx in enumerate(indices):
            next_indices[idx] = indices[i+1] if i < len(indices) - 1 else None
    
    return next_indices


def fill_missing_rankings(matches):
    """Riempie i ranking mancanti con backward fill, forward fill e media torneo."""
    def is_missing(val):
        return val in (None, '')

    player_ranking_history = defaultdict(lambda: {"rank": None, "rank_points": None})
    tournament_stats = defaultdict(lambda: defaultdict(list))

    for match in matches:
        tourney_id = match["tourney"]
        winner_id, loser_id = match["winner_id"], match["loser_id"]

        for col, key, pid in [("winner_rank", "rank", winner_id),
                              ("loser_rank", "rank", loser_id),
                              ("winner_rank_points", "rank_points", winner_id),
                              ("loser_rank_points", "rank_points", loser_id)]:
            value = match.get(col)
            if not is_missing(value):
                player_ranking_history[(tourney_id, pid)][key] = value
                try:
                    numeric_val = float(value)
                except (ValueError, TypeError):
                    numeric_val = 0
                tournament_stats[tourney_id][col].append(numeric_val)

    tournament_averages = {
        tourney_id: {col: sum(values) / len(values) if values else 0 
                     for col, values in stats.items()}
        for tourney_id, stats in tournament_stats.items()
    }

    next_match_indices = compute_next_indices_by_tourney(matches)

    for i, match in enumerate(matches):
        tourney_id = match["tourney"]
        winner_id, loser_id = match["winner_id"], match["loser_id"]

        for col, key, pid in [("winner_rank", "rank", winner_id),
                              ("loser_rank", "rank", loser_id),
                              ("winner_rank_points", "rank_points", winner_id),
                              ("loser_rank_points", "rank_points", loser_id)]:
            if is_missing(match.get(col)):
                player_key = (tourney_id, pid)
                value = player_ranking_history.get(player_key, {}).get(key)
                
                if not is_missing(value):
                    match[col] = value
                else:
                    next_index = next_match_indices.get(i)
                    if next_index is not None:
                        candidate = matches[next_index].get(col)
                        if not is_missing(candidate):
                            match[col] = candidate

                    if is_missing(match.get(col)):
                        match[col] = tournament_averages.get(tourney_id, {}).get(col, 0)
    
    return matches


def save_matches_to_csv(matches, output_file):
    """Salva i match in un file CSV."""
    if not matches:
        return
    
    headers = matches[0].keys()
    with open(output_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(matches)


def process_rankings(matches, output_file):
    """Funzione principale che esegue tutte le fasi del processo."""
    matches = convert_to_int(matches, ['winner_rank', 'loser_rank', 'winner_rank_points', 'loser_rank_points'])
    matches = fill_missing_rankings(matches)

    for match in matches:
        for col in ['winner_rank', 'loser_rank', 'winner_rank_points', 'loser_rank_points']:
            if match[col] is not None:
                match[col] = int(float(match[col])) 

    save_matches_to_csv(matches, output_file)
    print(f"File salvato: {output_file}")

def check_specific_missing(data, keys_to_check):
    missing = {key: 0 for key in keys_to_check}
    for row in data:
        for key in keys_to_check:
            if row.get(key) in ('', None):
                missing[key] += 1
    return missing

def convert_to_int(matches, columns):

    for match in matches:
        for col in columns:
            val = match.get(col)
            if val not in (None, ''):
                # Rimuovi spazi extra e caratteri non numerici 
                val = str(val).strip()
                val = re.sub(r'[^\d.]', '', val)  # Rimuove tutto tranne i numeri e il punto
                
                # Se il valore è un numero valido, prova a convertirlo
                try:
                    match[col] = int(float(val))  # Converte prima in float, poi in int
                except ValueError:
                    print(f"Valore non convertibile: {val} in colonna {col}")
    return matches

def age_median(data, age_col, tourn_col):
    median = defaultdict(dict)
    global_median = {}

    # Mediana per ogni torneo e ogni età
    for col in age_col:
        tourney_gr = defaultdict(list)
        all_ages = []

        # Età valide per ogni torneo
        for match in data:
            tourney = match[tourn_col]
            age = match.get(col)
            if age not in ('', None):
                try:
                    age = int(float(age))  # Prova a convertirlo in int
                except ValueError:
                    continue  # Se non può essere convertito, ignora quel valore
                tourney_gr[tourney].append(age)
                all_ages.append(age)

        # Mediana per ogni torneo
        for tourney, ages in tourney_gr.items():
            median[tourney][col] = statistics.median(ages)
        
        if all_ages:
            global_median[col] = statistics.median(all_ages)
        else:
            global_median[col] = None

    # Riempimento età mancanti con la mediana del torneo o la mediana globale
    for match in data:
        tourney = match[tourn_col]
        for col in age_col:
            if match[col] in ('', None):  # Se l'età è mancante
                # Usa la mediana del torneo, se esiste, altrimenti la mediana globale
                match[col] = median.get(tourney, {}).get(col, global_median.get(col))

    return data


def handle_missing_and_errors(data, col, errors):
    
    for row in data:
        if not row[col] or row[col] == "Unknown" or row[col] in errors:  
            row[col] = 'UNK'
    
    return data

# TOURNEY 

def clean_draw_size(tournament_data, fact_data):
    
    # Converte i valori a interi, escludendo "R" e valori mancanti
    for match in tournament_data:
        try:
            match['draw_size'] = int(float(match['draw_size']))
        except ValueError:
            match['draw_size'] = None 
    
    # Crea un dizionario per mappare torneo e draw_size esistenti
    tourney_sizes = {}
    for match in tournament_data:
        tourney = match['tourney']
        if match['draw_size'] is not None:
            tourney_sizes[tourney] = match['draw_size']

    # Conta gli id unici (winner_id, loser_id) per torneo in fact_data
    player_counts = defaultdict(set)
    for match in fact_data:
        player_counts[match['tourney']].add(match['winner_id'])
        player_counts[match['tourney']].add(match['loser_id'])

    # Riempie i missing values
    for match in tournament_data:
        tourney = match['tourney']
        if match['draw_size'] is None or match['draw_size'] == 'R':
            if tourney in tourney_sizes:  
                match['draw_size'] = tourney_sizes[tourney]  
            else:
                match['draw_size'] = len(player_counts[tourney]) 

    return tournament_data

def fill_missing_surface(tournament_data):
    # Dizionario per memorizzare la superficie nota per ogni torneo
    tourney_surface = {}

    # raccoglie i valori noti di surface per ogni torneo
    for match in tournament_data:
        tourney = match['tourney']
        surface = match['surface']

        if surface and surface != '':  
            tourney_surface[tourney] = surface 

    # riempire i valori mancanti
    for match in tournament_data:
        if not match['surface'] or match['surface'] == '':  
            match['surface'] = tourney_surface.get(match['tourney'], 'Unknown')

    return tournament_data


def timestamp_to_date(timestamp):
    try:
        # Se è una stringa lo converte in float 
        if isinstance(timestamp, str):
            timestamp = float(timestamp)
        
        if not isinstance(timestamp, (int, float)):
            raise ValueError("Invalid timestamp type")
        
        # timestamp in datetime
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        
        date = dt.strftime("%Y-%m-%d")
        day = dt.day
        month = dt.month
        quarter = (dt.month - 1) // 3 + 1 
        year = dt.year

        return date, day, month, quarter, year
    
    except (ValueError, OSError) as e:
        print(f"Errore nella conversione del timestamp: {e}")
        return None, None, None, None, None



def calculate_median_timestamp(tourney_data):
    positive_timestamps = [float(t['tourney_timestamp']) for t in tourney_data if float(t['tourney_timestamp']) > 0]
    return statistics.median(positive_timestamps) if positive_timestamps else None

def update_tournament_timestamps(tourney_data):
    median_timestamp = calculate_median_timestamp(tourney_data)
    
    if median_timestamp is None:
        raise ValueError("Non ci sono timestamp positivi per calcolare la mediana.")

    for t in tourney_data:
        try:
            timestamp = float(t['tourney_timestamp'])

            # Se il timestamp è negativo, sostituiscilo con la mediana
            if timestamp < 0:
                timestamp = median_timestamp
                t['tourney_timestamp'] = timestamp

            # Converti il timestamp in data
            dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
            t['date'] = dt.strftime("%Y-%m-%d")
            t['day'] = dt.day
            t['month'] = dt.month
            t['quarter'] = (dt.month - 1) // 3 + 1
            t['year'] = dt.year

        except (ValueError, OSError):
            t['date'], t['day'], t['month'], t['quarter'], t['year'] = None, None, None, None, None

    return tourney_data



def replace_invalid_heights(data, key):
    # Converte tutti i valori in int, se possibile
    for d in data:
        if isinstance(d, dict) and d.get(key) is not None:
            try:
                d[key] = int(d[key]) 
            except ValueError:
                d[key] = None  

    # Filtra altezze valide escludendo i valori da sostituire
    valid_heights = [d[key] for d in data if isinstance(d, dict) and d.get(key) not in {13, 3, 71, 15} and d[key] is not None]
    
    # Calcola la mediana se ci sono valori validi, altrimenti 0
    median = int(statistics.median(valid_heights)) if valid_heights else 0  

    # Sostituisci i valori errati con la mediana
    for d in data:
        if isinstance(d, dict) and d.get(key) in {13, 3, 71, 15}:
            d[key] = median
    
    return data


def float_to_int(data, columns):
    
    for row in data:
        if isinstance(row, dict):  
            for col in columns:
                if col in row and row[col]:
                    try:
                        row[col] = int(float(row[col]))  
                    except ValueError:
                        row[col] = None  

    return data

##################
# Athletes and their countries of origin preprocessing
################

def update_ioc(data, ioc_map):
    for row in data:

        winner_ioc = row["winner_ioc"]
        
        if winner_ioc == '' or winner_ioc is None:
            row["winner_ioc"] = "UNK"
        elif winner_ioc in ioc_map:
            row["winner_ioc"] = ioc_map[winner_ioc]
        
        loser_ioc = row["loser_ioc"]
        
        if loser_ioc == '' or loser_ioc is None:
            row["loser_ioc"] = "UNK"
        elif loser_ioc in ioc_map:
            row["loser_ioc"] = ioc_map[loser_ioc]

    return data


def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    country_data = []
    # iterate through each country
    for row in root.findall('row'):
        country_code = row.find('country_code').text
        country_name = row.find('country_name').text
        continent_name = row.find('continent').text

        country_data.append({
            "country_code": country_code,
            "country_name": country_name,
            "continent": continent_name
        })

    return country_data


##########
# API call to get country info
def api_call(ioc_code):
    try:

        url = f'https://restcountries.com/v3.1/alpha/{ioc_code}'
        response = requests.get(url, timeout=10)  
        response.raise_for_status()
         
        if response.status_code == 200:
            data = response.json()
            if data:
                country_info = data[0]
                country_name = country_info.get('name', {}).get('common', 'N/A')
                continent = country_info.get('region', 'N/A')
            return ioc_code, country_name, continent   
       
    except requests.exceptions.Timeout:
        print(f"Timeout durante la richiesta per {ioc_code}")
        return 'UNK', 'Unknown', 'Unknown'
    except requests.exceptions.RequestException as e:
        print(f"Errore nella richiesta: {e}")
        return 'UNK', 'Unknown', 'Unknown'



def get_country_info(fact_data, countries):
    for row in fact_data:
        
        if row['loser_ioc'] == 'UNK' or row['winner_ioc'] == 'UNK':
            continue

        # Check if loser IOC is already in countries, if not, get info
        if row['loser_ioc'] not in {country['country_code'] for country in countries}:
            ioc_code_l = row['loser_ioc']
            result = api_call(ioc_code_l)
            if result is None:
                continue
            loser_ioc_code, loser_country_name, loser_continent = result
            countries.append({
                "country_code": loser_ioc_code,
                "country_name": loser_country_name,
                "continent": loser_continent
            })

        # Check if winner IOC is already in countries, if not, get info
        if row['winner_ioc'] not in {country['country_code'] for country in countries}:
            ioc_code_w = row['winner_ioc']
            result = api_call(ioc_code_w)
            if result is None:
                continue
            winner_ioc_code, winner_country_name, winner_continent = result
            countries.append({
                "country_code": winner_ioc_code,
                "country_name": winner_country_name,
                "continent": winner_continent
            })

    # add UNK country if not present
    if 'UNK' not in {country['country_code'] for country in countries}:
        countries.append({
            "country_code": 'UNK',
            "country_name": 'Unknown',
            "continent": 'Unknown'
        })

    return countries


def geo_table(data, ioc_mapping):
    filtered_data = [row for row in data if row['country_code'] not in ioc_mapping]
    return filtered_data


def main():
    # dictionary to map obsolete IOC codes to current ones
    ioc_mapping = {
        'TCH': 'CZE', 'FRG': 'DEU', 'GDR': 'DEU', 'RHO': 'ZIM',  
        'ECA': 'ECU', 'HAW': 'USA', 'CEY': 'SRI', 'CAR': 'CAF',
        'POC': 'UNK', 'NGA': 'NGR', 'AHO': 'NED', '': 'UNK',
        'URS': 'UNK', 'YUG': 'UNK', 'ANZ': 'UNK', 'BRI': 'UNK',
        'SCG': 'UNK', 'NMI': 'UNK', 'ITF': 'UNK', 'UKN': 'UNK',
        'CHI': 'CHL', 'GER': 'DEU', 'GRE': 'GRC', 'NLD': 'NED',
        'TPE': 'TWN', 'GUA': 'GTM', 'PHI': 'PHL', 'ZWE' : 'ZIM',
        'LIB': 'LBA', 'PAR': 'PRY', 'SGP':'SIN', 'TOG':'TGO',
        'BRN':'BRU','MAD':'MDG', 'ISV':'VIR', 'KUW':'KWT', 
        'TRI':'TTO', 'BOT':'BWA', 'NEP':'NPL','ANG':'AGO',
        'CGO':'COG', 'NCA':'NIC'
    }

    # countries to drop
    countries_to_drop = [{'country_code': 'UNK', 'country_name': 'Kosovo', 'continent': 'Europe'}]
                        
    fact = read_csv('group_13_lab/output/final_fact.csv')
    countries_path = 'group_13_lab/dataset/countries.xml'
    new_countries_path = 'group_13_lab/output/countries_done.csv'
    new_fact_path = 'group_13_lab/output/final_fact.csv'

    #countries = parse_xml(countries_path)
    fact_ioc_update = update_ioc(fact, ioc_mapping)
    updated_countries = [country for country in countries if country not in countries_to_drop]
    updated_countries = get_country_info(fact_ioc_update, updated_countries)
    geo_tab = geo_table(updated_countries, ioc_mapping)
    
    to_csv(geo_tab, new_countries_path)
    to_csv(fact_ioc_update, new_fact_path)


fact_path = 'group_13_lab/dataset/fact.csv'
countries_path = 'group_13_lab/conversione/countries_out.csv'
tourney_path = 'group_13_lab/conversione/file_tourney.csv'

fact = read_csv(fact_path)
countries = read_csv(countries_path)
tourney = read_csv(tourney_path)

missing_f = missing_values(fact)
missing_c = missing_values(countries)
missing_t = missing_values(tourney)

print(f"Missing fact: \n{missing_f}")
print(f"Missing countrie: \n{missing_c}")
print(f"Missing tourney: \n{missing_t}")


to_remove = ['winner_entry', 'winner_seed','loser_seed', 'loser_entry', 'minutes', 'w_ace', 'w_df',
    'w_svpt', 'w_1stIn', 'w_1stWon', 'w_2ndWon', 'w_SvGms', 'w_bpSaved',
    'w_bpFaced', 'l_ace', 'l_df', 'l_svpt', 'l_1stIn', 'l_1stWon',
    'l_2ndWon', 'l_SvGms', 'l_bpSaved', 'l_bpFaced']

remove = remove_keys(fact, to_remove)

categorical = fill_categorical(fact, columns_to_fill=['winner_ioc', 'loser_ioc', 'winner_hand', 'loser_hand'], 
                            id_columns=['winner_id', 'loser_id'], default_value='UNK')
categoricall = fill_categorical(fact, columns_to_fill=['winner_hand', 'loser_hand'], 
                            id_columns=['winner_id', 'loser_id'], default_value='U')

interi = fill_int(fact, columns=['winner_ht', 'loser_ht'], id_cols=['winner_id', 'loser_id'])

conversione = convert_to_int(fact, ['winner_age', 'loser_age'])
age = age_median(fact, ['winner_age', 'loser_age'], 'tourney')

score = handle_missing_and_errors(fact, 'score', ['<','&nbsp;'])

output_file = 'group_13_lab/output/final_fact.csv'
ranks = process_rankings(fact, output_file)

draw = clean_draw_size(tourney, fact)
surface = fill_missing_surface(tourney)
median_value = calculate_median_timestamp(tourney)
updated_tourney_data = update_tournament_timestamps(tourney)
float_to_int_fact = float_to_int(fact, ['winner_ht', 'loser_ht', 'winner_age', 'loser_age', 'spectator'])
updated_wht = replace_invalid_heights(float_to_int_fact, 'winner_ht')
final_fact = replace_invalid_heights(updated_wht, 'loser_ht')
to_csv(final_fact, 'group_13_lab/output/final_fact1.csv')

o = 'group_13_lab/output/file_tourney.csv'
to_csv(updated_tourney_data, o)

missing_t = missing_values(tourney)
print(f"Missing tourney: \n{missing_t}")

if __name__ == "__main__":
    main()


