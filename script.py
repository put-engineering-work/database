import os
import uuid
import random
from faker import Faker
import psycopg2
import math
from datetime import timedelta
import bcrypt
import random
from PIL import Image

fake = Faker()

dbname = "leisurelink"
user = "postgres"
passw = "postgres"
host = "localhost"
port = "5432"

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
    "Gdynia": {"latitude": 54.5189, "longitude": 18.5305},
}


def get_random_image_path(image_folder):
    """Selects a random image from the specified folder."""
    images = [
        img
        for img in os.listdir(image_folder)
        if img.endswith(".png") or img.endswith(".jpg") or img.endswith(".jpeg")
    ]
    if images:
        return os.path.join(image_folder, random.choice(images))
    else:
        return None


def insert_user_with_photo(
    cur,
    photo_path,
    user_details_id,
    address,
    birth_date,
    last_name,
    name,
    phone_number,
    user_id,
):
    """Inserts a user with a photo into the database."""
    with open(photo_path, "rb") as photo_file:
        photo = photo_file.read()
    cur.execute(
        "INSERT INTO user_details (id, address, birth_date, last_name, name, phone_number, photo, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        (
            user_details_id,
            address,
            birth_date,
            last_name,
            name,
            phone_number,
            psycopg2.Binary(photo),
            user_id,
        ),
    )


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
            cur.execute(
                "INSERT INTO events_categories (events_id, categories_id) VALUES (%s, %s)",
                (event_id, category_id),
            )
    print("Events linked with categories.")


def insert_event_image(cur, event_id, image_oid):
    """Associates an image with an event in the 'event_images' table."""
    cur.execute(
        "INSERT INTO event_images (id, image, event_id) VALUES (%s, %s, %s)",
        (str(uuid.uuid4()), image_oid, event_id),
    )


def save_image_to_large_object_storage(conn, image_path):
    """Saves the image as a large object and returns its OID (Object Identifier)."""
    with conn.cursor() as cur:
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
        oid = cur.execute("SELECT lo_create(0)")
        lobj_id = cur.fetchone()[0]
        large_object = conn.lobject(lobj_id, "wb")
        large_object.write(image_data)
        large_object.close()
        return lobj_id


def generate_events(cur, conn, num_records):
    print("Generating events...")

    cur.execute("SELECT id FROM event_categories")
    category_ids = [row[0] for row in cur.fetchall()]
    for _ in range(num_records):
        event_id = str(uuid.uuid4())
        name = fake.sentence()
        description = fake.text()
        address = fake.address()

        start_date = fake.date_time_between(start_date="now", end_date="+2y")
        end_days_after = random.randint(1, 14)
        end_date = start_date + timedelta(days=end_days_after)

        city_name, city_coords = random.choice(list(polish_cities.items()))
        latitude, longitude = random_point_in_circle(
            city_coords["latitude"], city_coords["longitude"], 20
        )
        location = f"POINT({longitude} {latitude})"

        cur.execute(
            "INSERT INTO events (id, name, description, address, start_date, end_date, location) VALUES (%s, %s, %s, %s, %s, %s, ST_GeomFromText(%s, 4326))",
            (event_id, name, description, address, start_date, end_date, location),
        )

        image_path = get_random_image_path("event_images/")
        if image_path:
            image_id = save_image_to_large_object_storage(conn, image_path)
            insert_event_image(cur, event_id, image_id)

        num_categories = random.randint(1, 3)
        chosen_categories = random.sample(category_ids, num_categories)
        for category_id in chosen_categories:
            cur.execute(
                "INSERT INTO events_categories (events_id, categories_id) VALUES (%s, %s)",
                (event_id, category_id),
            )

    conn.commit()
    print(f"{num_records} events added.")


def generate_comments(cur, event_ids, user_ids, num_records):
    print("Generating comments...")
    amount = 0
    for _ in range(num_records):
        try:
            comment_id = str(uuid.uuid4())
            content = fake.text()
            comment_date = fake.date_time()
            grade = random.randint(1, 5)
            event_id = random.choice(event_ids)
            user_id = random.choice(user_ids)
            cur.execute(
                "INSERT INTO comments (id, content, comment_date, grade, event_id, user_id) VALUES (%s, %s, %s, %s, %s, %s)",
                (comment_id, content, comment_date, grade, event_id, user_id),
            )
            amount += 1
        except Exception:
            cur.connection.rollback()
            continue
    print(f"comments added. Amount: {amount} of {num_records}")


def link_events_with_comments(cur, event_ids, comment_ids):
    print("Linking events with comments...")
    amount = 0
    for comment_id in comment_ids:
        event_id = random.choice(event_ids)
        try:
            cur.execute(
                "INSERT INTO events_comments (event_id, comments_id) VALUES (%s, %s)",
                (event_id, comment_id),
            )
            amount += 1
        except Exception as err:
            print(err)
            cur.connection.rollback()
            continue
    print(f"Events linked with comments. Linked amount: {amount}")


def link_users_with_events(conn, cur, event_ids, user_ids):
    print("Linking users with events...")
    statuses = ["STATUS_ACTIVE", "STATUS_INACTIVE"]
    types = ["ROLE_GUEST", "ROLE_HOST"]  # add 'ROLE_HOST'

    for event_id in event_ids:
        # Check if host exists for event
        cur.execute(
            "SELECT COUNT(*) FROM members WHERE event_id = %s AND type = 'ROLE_HOST'",
            (event_id,),
        )
        host_exists = cur.fetchone()[0] > 0

        if not host_exists:
            # If there is no host, choose one user as a host
            host_user_id = random.choice(user_ids)
            host_member_id = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO members (id, status, type, event_id, user_id) VALUES (%s, %s, %s, %s, %s)",
                (host_member_id, "STATUS_ACTIVE", "ROLE_HOST", event_id, host_user_id),
            )

        # Add guests to the event
        num_guests = random.randint(0, min(10, len(user_ids) - 1))
        guest_user_ids = (
            random.sample([uid for uid in user_ids if uid != host_user_id], num_guests)
            if not host_exists
            else random.sample(user_ids, num_guests)
        )

        for user_id in guest_user_ids:
            guest_member_id = str(uuid.uuid4())
            status = random.choice(statuses)
            cur.execute(
                "INSERT INTO members (id, status, type, event_id, user_id) VALUES (%s, %s, %s, %s, %s)",
                (guest_member_id, status, "ROLE_GUEST", event_id, user_id),
            )

    conn.commit()
    print("Users linked with events.")


def generate_random_password():
    password = "123456789"
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(12))
    return hashed_password.decode("utf-8")


def generate_users(conn, cur, num_records):
    print("Generating users...")
    for _ in range(num_records):
        try:
            user_id = str(uuid.uuid4())
            user_details_id = str(uuid.uuid4())
            app_user_roles = 1
            is_activated = False
            email = fake.email()
            password = generate_random_password()

            cur.execute(
                "INSERT INTO users (id, app_user_roles, is_activated, email, password) VALUES (%s, %s, %s, %s, %s)",
                (user_id, app_user_roles, is_activated, email, password),
            )

            name = fake.first_name()
            last_name = fake.last_name()
            address = fake.address()
            birth_date = fake.date_of_birth()
            phone_number = fake.phone_number()
            # photo_path = get_random_image_path("user_images/")
            photo_path = None  # TODO: Add user images (works slowly)

            if photo_path:
                insert_user_with_photo(
                    cur,
                    photo_path,
                    user_details_id,
                    address,
                    birth_date,
                    last_name,
                    name,
                    phone_number,
                    user_id=user_id,
                )
            else:
                cur.execute(
                    "INSERT INTO user_details (id, address, birth_date, last_name, name, phone_number, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                    (
                        user_details_id,
                        address,
                        birth_date,
                        last_name,
                        name,
                        phone_number,
                        user_id,
                    ),
                )

            cur.execute(
                "UPDATE users SET user_details_id = %s WHERE id = %s",
                (user_details_id, user_id),
            )
        except Exception as e:
            continue

    conn.commit()
    print(f"{num_records} users added.")


def generate_data():
    conn = psycopg2.connect(
        dbname=dbname, user=user, password=passw, host=host, port=port
    )
    cur = conn.cursor()

    try:
        num_events = 1000
        num_users = 100
        # num_comments = 20

        # this function generates users
        generate_users(conn, cur, num_users)

        # it takes user ids
        cur.execute("SELECT id FROM users")
        user_ids = [row[0] for row in cur.fetchall()]

        # this function generates events
        generate_events(cur, conn, num_events)

        # it takes event ids
        cur.execute("SELECT id FROM events")
        event_ids = [row[0] for row in cur.fetchall()]

        # this function links users with events
        if user_ids and event_ids:
            link_users_with_events(conn, cur, event_ids, user_ids)

        # TODO : uncomment if you want to generate comments
        # This function generates comments and links them with events
        # generate_comments(cur, event_ids,user_ids, num_comments)
        # conn.commit()
        # cur.execute("SELECT id FROM comments")
        # coments_ids = [row[0] for row in cur.fetchall()]

        # if coments_ids and event_ids:
        #     link_events_with_comments(cur, event_ids, coments_ids)
        # conn.commit()

    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


generate_data()
