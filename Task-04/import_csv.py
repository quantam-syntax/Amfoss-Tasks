import csv
import mysql.connector

db_config = {
    "host": "localhost",
    "user": "movie_user",       
    "password": "Gsk@6363",     
    "database": "movies_db"     
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS movies")

create_table_query = """
CREATE TABLE movies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    year INT,
    genre VARCHAR(255),
    rating FLOAT,
    director VARCHAR(255),
    stars TEXT,
    duration VARCHAR(50),
    votes INT
);
"""
cursor.execute(create_table_query)

with open("movies.csv", "r", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    insert_query = """
    INSERT INTO movies
        (title, year, genre, rating, director, stars, duration, votes)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    for row in reader:
        def safe_int(val):
            try:
                return int(val)
            except (ValueError, TypeError):
                return None

        def safe_float(val):
            try:
                return float(val)
            except (ValueError, TypeError):
                return None

        stars = ", ".join(filter(None, [row.get("Star1"), row.get("Star2"), row.get("Star3")]))

        data = (
            row.get("Series_Title", ""),
            safe_int(row.get("Released_Year")),
            row.get("Genre", ""),
            safe_float(row.get("IMDB_Rating")),
            row.get("Director", ""),
            stars,
            None,   
            None    
        )
        cursor.execute(insert_query, data)

# Commit & close
conn.commit()
cursor.close()
conn.close()
print("CSV data imported successfully into movies_db.movies!")
