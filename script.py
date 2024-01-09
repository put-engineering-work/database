import uuid
import random
from faker import Faker
import psycopg2
import math
from datetime import timedelta


fake = Faker()

dbname = 'leisurelink'
user = 'postgres'
passw = 'postgres'
host = 'localhost'
port = '5432'

polish_cities = {
    "Warsaw": {"latitude": 52.2297, "longitude": 21.0122},
    "Krakow": {"latitude": 50.0647, "longitude": 19.9450},
    "Lodz": {"latitude": 51.7592, "longitude": 19.4560},
    "Wroclaw": {"latitude": 51.1079, "longitude": 17.0385},
    "Poznan": {"latitude": 52.4064, "longitude": 16.9252},
    "Gdansk": {"latitude": 54.3520, "longitude": 18.6466},
    "Szczecin": {"latitude": 53.4285, "longitude": 14.5528},
    "Bydgoszcz": {"latitude": 53.1235, "longitude": 18.0084},
    "Lublin": {"latitude": 51.2465, "longitude": 22.5684},
    "Katowice": {"latitude": 50.2709, "longitude": 19.0390},
    "Bialystok": {"latitude": 53.1325, "longitude": 23.1688},
    "Gdynia": {"latitude": 54.5189, "longitude": 18.5305}
}

def random_point_in_circle(latitude, longitude, radius_km):
    radius_in_degrees = radius_km / 111.32

    angle = random.uniform(0, 2 * math.pi)
    distance = random.uniform(0, radius_in_degrees)
    delta_lat = distance * math.cos(angle)
    delta_lon = distance * math.sin(angle) / math.cos(math.radians(latitude))

    return latitude + delta_lat, longitude + delta_lon

def link_events_with_categories(cur, event_ids, category_ids):
    print("Linking events with categories...")
    for event_id in event_ids:
        num_categories = random.randint(1, min(3, len(category_ids)))
        chosen_categories = random.sample(category_ids, num_categories)
        for category_id in chosen_categories:
            cur.execute("INSERT INTO event_categories (events_id, categories_id) VALUES (%s, %s)", (event_id, category_id))
    print("Events linked with categories.")

def generate_event_categories(cur, num_records):
    print("Generating event categories...")
    for _ in range(num_records):
        category_id = str(uuid.uuid4())
        name = fake.word()
        cur.execute("INSERT INTO event_categories (id, name) VALUES (%s, %s)", (category_id, name))
    print(f"{num_records} event categories added.")

def generate_events(cur, num_records):
    print("Generating events...")
    for _ in range(num_records):
        event_id = str(uuid.uuid4())
        name = fake.sentence()
        description = fake.text()
        address = fake.address()

        start_date = fake.date_time_between(start_date='now', end_date='+2y')
        end_days_after = random.randint(1, 14)
        end_date = start_date + timedelta(days=end_days_after)

        city_name, city_coords = random.choice(list(polish_cities.items()))
        latitude, longitude = random_point_in_circle(city_coords['latitude'], city_coords['longitude'], 20)
        location = f"POINT({longitude} {latitude})"

        cur.execute("INSERT INTO events (id, name, description, address, start_date, end_date, location) VALUES (%s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326))", (event_id, name, description, address, start_date, end_date, location))
    print(f"{num_records} events added.")

def generate_comments(cur, event_ids, user_ids, num_records):
    print("Generating comments...")
    for _ in range(num_records):
        comment_id = str(uuid.uuid4())
        content = fake.text()
        comment_date = fake.date_time()
        grade = random.randint(1, 5)
        event_id = random.choice(event_ids)
        user_id = random.choice(user_ids)
        cur.execute("INSERT INTO comments (id, content, comment_date, grade, event_id, user_id) VALUES (%s, %s, %s, %s, %s, %s)", (comment_id, content, comment_date, grade, event_id, user_id))
    print(f"{num_records} comments added.")


def link_events_with_comments(cur, event_ids, comment_ids):
    print("Linking events with comments...")
    for comment_id in comment_ids:
        event_id = random.choice(event_ids)
        cur.execute("INSERT INTO events_comments (event_id, comments_id) VALUES (%s, %s)", (event_id, comment_id))
    print("Events linked with comments.")

def generate_users(cur, num_records):
    print("Generating users...")
    for _ in range(num_records):
        user_id = str(uuid.uuid4())
        email = fake.email()
        password = fake.password()
        cur.execute("INSERT INTO users (id, email, password) VALUES (%s, %s, %s)", (user_id, email, password))
    print(f"{num_records} users added.")

def generate_data():
    conn = psycopg2.connect(dbname=dbname, user=user, password=passw, host=host, port=port)
    cur = conn.cursor()

    try:
        num_event_categories = 5
        num_events = 1000
        num_users = 500
        num_comments = 5000

        # generate_users(cur, num_users)
        cur.execute("SELECT id FROM users")
        user_ids = [row[0] for row in cur.fetchall()]

        generate_event_categories(cur, num_event_categories)
        cur.execute("SELECT id FROM event_categories")
        category_ids = [row[0] for row in cur.fetchall()]

        generate_events(cur, num_events)
        cur.execute("SELECT id FROM events")
        event_ids = [row[0] for row in cur.fetchall()]

        # link_events_with_categories(cur, event_ids, category_ids)

        # generate_comments(cur, event_ids,user_ids, num_comments)
        
        # coments_ids = [row[0] for row in cur.fetchall()]
        
        # link_events_with_comments(cur, event_ids, coments_ids)

        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

generate_data()