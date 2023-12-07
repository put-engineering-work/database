import uuid
import random
from faker import Faker
import psycopg2

fake = Faker()

dbname = 'leisurelink'
user = 'postgres'
passw = 'postgres'
host = 'localhost'
port = '5432'

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
        start_date = fake.date_time()
        end_date = fake.date_time()
        location = f"POINT({fake.longitude()} {fake.latitude()})"
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
        num_events = 10
        num_users = 10
        num_comments = 20

        generate_users(cur, num_users)
        cur.execute("SELECT id FROM users")
        user_ids = [row[0] for row in cur.fetchall()]

        generate_event_categories(cur, num_event_categories)
        generate_events(cur, num_events)

        cur.execute("SELECT id FROM events")
        event_ids = [row[0] for row in cur.fetchall()]

        generate_comments(cur, event_ids, user_ids, num_comments)

        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

generate_data()
