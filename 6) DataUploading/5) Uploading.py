import pyodbc
import csv

server = 'tcp:lds.di.unipi.it'
database = 'Group_ID_13_DB'
username = 'Group_ID_13'
password = 'M1GUWCGQ'
connectionString = 'DRIVER={ODBC Driver 17 for SQL Server};SERVER='+server+';DATABASE='+database+';UID='+username+';PWD='+password

cnxn = pyodbc.connect(connectionString)
cursor = cnxn.cursor()
cursor.fast_executemany = True

# Function to populate a table from a csv file
def populate_table(file_path, table_name, cursor, cnxn):
    with open(file_path, encoding='utf-8-sig') as csvfile:
        file = csv.DictReader(csvfile)
        fields = file.fieldnames
        
        # Generate the SQL INSERT query dynamically based on table name and fields (csv header)
        insert_query = '''
            INSERT INTO Group_ID_13.{} ({})
            VALUES ({})'''.format(table_name, ', '.join(fields), ', '.join(['?'] * len(fields)))

        # Create a list of tuples, each representing a row of values from the csv
        values_list = [tuple(row.values()) for row in file]

        # Execute the query for multiple rows using executemany to speed up the process
        cursor.executemany(insert_query, values_list)

        # Commit the changes to the database
        cnxn.commit()

# =======================================
# POPULATION OF THE TABLES
# =======================================

input_geo = 'C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/geography.csv'
input_players = 'C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/player.csv'
input_dates = 'C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/date.csv'
input_tourney = 'C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/tourney.csv'
input_match_stats = 'C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/match_stats.csv'
input_fact = 'C:/Users/catta/OneDrive/Desktop/LAB2/tabelle/fact.csv'



# Populate the dimension tables
populate_table(input_geo, 'geography', cursor, cnxn)
populate_table(input_players, 'player', cursor, cnxn)
populate_table(input_dates, 'date', cursor, cnxn)
populate_table(input_tourney, 'tournament', cursor, cnxn)
populate_table(input_match_stats, 'match_stats', cursor, cnxn)
populate_table(input_fact, 'match_fact', cursor, cnxn)


# Close the cursor and connection
cursor.close()
cnxn.close()