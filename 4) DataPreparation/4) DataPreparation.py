import csv
import calendar

def read_csv(file_path):
    """Legge un file CSV e restituisce i dati come lista di dizionari."""
    with open(file_path, mode='r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)
        data = list(reader)  # Converte il reader in una lista di dizionari
    
    return data

def save_to_csv(matches, output_file):
    """Salva i match in un file CSV."""
    if not matches:
        return
    
    headers = matches[0].keys()
    with open(output_file, mode='w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(matches)

# # TOURNAMENT

def create_tourney(fact, data, date_map):
    tourneys = []
    pk_counter = 1  # Contatore per la PK sequenziale
    
    # Creiamo un dizionario che mappa 'tourney' al corrispondente 'best_of' da fact
    fact_best_of = {row['tourney']: row['best_of'] for row in fact}
    fact_tourneys = set(fact_best_of.keys())  # Set con tutti i tornei presenti in fact

    for row in data:
        if row['tourney'] in fact_tourneys:
            b_of = fact_best_of[row['tourney']]  # Ora prendiamo il valore corretto da fact
            date_fk = date_map[row['date_id']]['date_pk'] if row['date_id'] in date_map else None  # Mappa correttamente il valore
            
            tourneys.append({
                'tourney_pk': pk_counter,  # Incrementa la PK
                'tourney_id': row['tourney_id'],
                'tourney_name': row['tourney_name'],
                'draw_size': row['draw_size'],
                'surface': row['surface'],
                'tourney_level': row['tourney_level'],
                'date_fk': date_fk,
                'best_of': b_of  
            })
            
            pk_counter += 1  # Incrementa la PK per il prossimo torneo
    return tourneys


## GEOGRAPHY

def create_geography(data):
    """Genera la tabella 'geography' con surrogate keys"""
    geo = []
    geo_map = {}  # Dizionario per associare geo_id e surrogate key
    for i, row in enumerate(data, start=1):
        geo.append({
            'geo_pk': i,
            'geo_id': row['country_code'],
            'country_name': row['country_name'],
            'continent': row['continent'],
        })
        geo_map[row['country_code']] = i  # Mappa per sostituire player_ioc con geo_pk
    return geo, geo_map

## PLAYERS
def unique_players(data, geo_map):
    """Genera la tabella 'player' con surrogate keys, collegandola a geography"""
    players = []
    player_mapping = {}  # Mappa player_id -> player_pk
    sk_counter = 1  # Contatore per le surrogate keys

    for row in data:
        for prefix in ['winner', 'loser']:
            player_id = row[f'{prefix}_id']

            if player_id not in player_mapping:  # Se il giocatore non è ancora mappato
                player_mapping[player_id] = sk_counter
                players.append({
                    'player_pk': sk_counter,
                    'player_id': player_id,
                    'player_name': row[f'{prefix}_name'],
                    'player_hand': row[f'{prefix}_hand'],
                    'player_ht': row[f'{prefix}_ht'],
                    'geo_fk': geo_map.get(row[f'{prefix}_ioc'], None)  # FK da geography
                })
                sk_counter += 1  # Incrementa solo quando un nuovo giocatore viene aggiunto

    return players

## DATE

def create_date(data):
    date = []
    date_map = {}  # Dizionario per mappare date_id ai record
    seen_dates = set()  # Per evitare duplicati
    pk_counter = 1  # Contatore per generare surrogate key coerenti

    for row in data:
        date_id = row['date_id']

        if date_id not in seen_dates:  # Controlla se l'ID esiste già
            seen_dates.add(date_id)  # Aggiungi l'ID al set
            
            date_entry = {
                'date_pk': pk_counter,  # Usa il contatore separato
                'date_id': date_id,
                'date': row['date'],
                'day': row['day'],
                'month': row['month'],
                'quarter': row['quarter'],
                'year': row['year'],
                'day_of_week': row['day_of_week'],
                'the_day': calendar.day_name[int(row['day_of_week']) - 1],  # Converte in nome del giorno
                'the_month': calendar.month_name[int(row['month'])]  # Converte in nome del mese
            }

            date.append(date_entry)
            date_map[date_id] = date_entry  # Aggiunge la mappatura
            pk_counter += 1  # Incrementa solo quando una nuova data viene aggiunta
    
    return date, date_map

## MATCH_STATS

def create_match_stats(data):
    """Genera la tabella 'match_stats' con surrogate keys"""
    stats = []
    for i, row in enumerate(data, start=1):
        stats.append({
            'match_stats_pk': i,
            'match_stats_id': f"{row['match_num']}_{row['tourney']}",
            'winner_rank': row['winner_rank'],
            'winner_rank_points': row['winner_rank_points'],
            'loser_rank': row['loser_rank'],
            'loser_rank_points': row['loser_rank_points'],
            'winner_age': row['winner_age'],
            'loser_age': row['loser_age'],
            'round': row['round'],
            'score': row['score']
        })
    return stats


## FACT TABLE
def create_fact(matches, players, tourneys, match_stats):
    """Genera la tabella 'fact' usando surrogate keys"""
    player_map = {p['player_id']: p['player_pk'] for p in players}
    tourney_map = {t['tourney_id']: t['tourney_pk'] for t in tourneys}
    match_stats_map = {m['match_stats_id']: m['match_stats_pk'] for m in match_stats}

    fact_table = []
    for i, match in enumerate(matches, start=1):
        fact_table.append({
            'fact_pk': i,
            'n_spectators': match['spectator'],
            'avg_ticket_price': match['avg_ticket_price'],
            'match_expenses': match['match_expenses'],
            'tourney_fk': tourney_map.get(match['tourney']),
            'match_id': f"{match['match_num']}_{match['tourney']}",
            'winner_fk': player_map.get(match['winner_id']),
            'loser_fk': player_map.get(match['loser_id']),
            'match_stats_fk': match_stats_map.get(f"{match['match_num']}_{match['tourney']}")
        })
    return fact_table


def main():
    # File di input
    input_fact = 'group_13_lab/output/final_fact1.csv'
    input_tourney = 'group_13_lab/output/file_tourney.csv'
    input_country = 'group_13_lab/output/countries_done.csv'

    fact_data = read_csv(input_fact)
    tourney_data = read_csv(input_tourney)
    country_data = read_csv(input_country)

    # # Creazione delle tabelle con surrogate keys
    geo, geo_map = create_geography(country_data)
    players = unique_players(fact_data, geo_map)
    dates, date_map = create_date(tourney_data)
    tourneys = create_tourney(fact_data, tourney_data, date_map)
    match_stats = create_match_stats(fact_data)

    def handle_missing_and_errors(data, col, errors):
        
        for row in data:
            if not row[col] or row[col] == "Unknown" or row[col] in errors:  
                row[col] = 'UNK'
        
        return data

    stats = handle_missing_and_errors(match_stats, 'score', ['>', '&nbsp;'])
    fact = create_fact(fact_data, players, tourneys, match_stats)

    # # Salvataggio dei file
    save_to_csv(geo, 'group_13_lab/output/geography.csv')
    save_to_csv(players, 'group_13_lab/output/player.csv')
    save_to_csv(dates, 'group_13_lab/output/date.csv')
    save_to_csv(tourneys, 'group_13_lab/tabelle/tourney.csv')
    save_to_csv(stats, 'group_13_lab/tabelle/match_stats.csv')
    save_to_csv(fact, 'group_13_lab/tabelle/fact.csv')

if __name__ == '__main__':
    main()



