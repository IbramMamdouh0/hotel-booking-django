# Hotel Booking System

A server-rendered hotel booking web app built with Django 6. Visitors browse and filter hotels and rooms; registered users book a room for a date range, cancel their bookings, and leave one review per hotel. Hotels, rooms, bookings and reviews are managed from the Django admin.

## Tech Stack

- Python 3.13 / Django 6.0
- SQLite by default, PostgreSQL through `DATABASE_URL` (`dj-database-url` + `psycopg2-binary`)
- Django templates (no JavaScript framework, no REST API)
- WhiteNoise for static files
- Gunicorn for serving
- Render deployment config (`render.yaml` + `build.sh`)

## Features

- Registration with username, email and password, which logs the new user straight in; login and logout use Django's built-in auth views
- Hotel list with free-text search over name and address, a minimum-rating filter, a maximum-price filter, and each hotel annotated with its cheapest room price
- Hotel detail page listing the hotel's rooms and reviews
- Room detail page with the booking form
- Booking validation in `create_booking`:
  - check-in must be later than today
  - the stay must be at least one night
  - dates that overlap an existing `pending` or `confirmed` booking for the same room are rejected
  - `total_price` is computed as `price_per_night × nights`
  - new bookings are saved with the model default status, `confirmed`
- "My bookings" page, with cancellation allowed while a booking is `pending` or `confirmed`
- Reviews rated 1–5 with a comment, one per user per hotel (enforced by `unique_together`); submitting again updates the existing review, and the hotel shows an average rating and review count
- Django admin with rooms and reviews inline on the hotel, plus list filters and search on all four models

## Setup

### Prerequisites

- Python 3.13
- PostgreSQL only if you want it; SQLite works out of the box

### Install

```bash
git clone https://github.com/IbramMamdouh0/hotel-booking-django.git
cd hotel-booking-django
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment

`settings.py` reads its configuration from the process environment. The project
does not bundle a `.env` loader — there is no `python-dotenv` or `django-environ`
in `requirements.txt`, and nothing in `manage.py` or `core/wsgi.py` reads a file.
`.env.example` is there to document the variables; export them in your shell (or
add a loader yourself) before running anything.

```bash
export SECRET_KEY='...'
export DEBUG=True
export ALLOWED_HOSTS=localhost,127.0.0.1
```

| Variable         | Default                   | Purpose                                                  |
|------------------|---------------------------|----------------------------------------------------------|
| `SECRET_KEY`     | none — required           | Django signing key. Startup fails with `ImproperlyConfigured: SECRET_KEY environment variable is not set.` if it is missing |
| `DEBUG`          | `False`                   | Set to `True` for local development only                 |
| `ALLOWED_HOSTS`  | `localhost,127.0.0.1`     | Comma-separated host list                                |
| `DATABASE_URL`   | `sqlite:///db.sqlite3`    | Any URL `dj-database-url` understands                    |

On Render, `RENDER_EXTERNAL_HOSTNAME` is set automatically for every service and `settings.py` appends it to `ALLOWED_HOSTS`, so the deployed hostname does not have to be listed by hand.

### Database and run

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

The site runs at `http://127.0.0.1:8000/`, the admin at `http://127.0.0.1:8000/admin/`. `db.sqlite3` is git-ignored.

## Pages

| Method    | URL                                   | View             | Auth     | Description                                            |
|-----------|---------------------------------------|------------------|----------|--------------------------------------------------------|
| GET       | `/`                                   | `home`           | —        | Home page                                              |
| GET, POST | `/accounts/login/`                    | `LoginView`      | —        | Log in                                                 |
| POST      | `/accounts/logout/`                   | `LogoutView`     | —        | Log out, redirects to the login page                   |
| GET, POST | `/accounts/register/`                 | `register`       | —        | Create an account and log in                           |
| GET       | `/hotels/`                            | `hotel_list`     | —        | Hotel list. Query: `q`, `rating_min`, `price_max`      |
| GET, POST | `/hotels/<hotel_id>/`                 | `hotel_detail`   | POST: yes | Rooms and reviews; POST submits or updates a review    |
| GET       | `/hotels/<hotel_id>/<room_id>/`       | `room_detail`    | —        | Room details and booking form                          |
| POST      | `/hotels/<hotel_id>/<room_id>/book/`  | `create_booking` | yes      | Create a booking                                       |
| GET       | `/bookings/`                          | `my_bookings`    | yes      | The signed-in user's bookings                          |
| GET       | `/bookings/<booking_id>/cancel/`      | `cancel_booking` | yes      | Cancel one of your bookings                            |
| —         | `/admin/`                             | Django admin     | staff    | Manage hotels, rooms, bookings, reviews                |

Only hotels with `is_active=True` are reachable from the public pages.

## Database Schema

**Hotel**

| Field          | Type                    | Notes                             |
|----------------|-------------------------|-----------------------------------|
| `name`         | `CharField(200)`        |                                   |
| `description`  | `TextField`             |                                   |
| `address`      | `CharField(300)`        |                                   |
| `phone`        | `CharField(20)`         |                                   |
| `email`        | `EmailField`            |                                   |
| `website`      | `URLField`              | optional                          |
| `image`        | `URLField`              | optional                          |
| `rating`       | `IntegerField`          | 1–5, default 3                    |
| `is_active`    | `BooleanField`          | default `True`                    |
| `created_at` / `updated_at` | `DateTimeField` | auto                       |

Ordered by newest first. `avg_rating()` averages the hotel's reviews and falls back to `rating`; `reviews_count()` counts them.

**Room**

| Field             | Type                          | Notes                                        |
|-------------------|-------------------------------|----------------------------------------------|
| `hotel`           | FK → `Hotel`                  | cascade, `related_name='rooms'`              |
| `room_number`     | `CharField(10)`               |                                              |
| `room_type`       | `CharField(20)` with choices  | `single`, `double`, `suite`, `deluxe`        |
| `price_per_night` | `DecimalField(10,2)`          |                                              |
| `capacity`        | `IntegerField`                | minimum 1                                    |
| `description`     | `TextField`                   | optional                                     |
| `is_available`    | `BooleanField`                | default `True`                               |
| `created_at` / `updated_at` | `DateTimeField`     | auto                                         |

Ordered by `room_number`.

**Booking**

| Field         | Type                         | Notes                                                    |
|---------------|------------------------------|----------------------------------------------------------|
| `user`        | FK → `auth.User`             | cascade, `related_name='bookings'`                       |
| `room`        | FK → `Room`                  | cascade, `related_name='bookings'`                       |
| `check_in`    | `DateField`                  |                                                          |
| `check_out`   | `DateField`                  |                                                          |
| `total_price` | `DecimalField(10,2)`         | computed at creation                                     |
| `status`      | `CharField(20)` with choices | `pending`, `confirmed`, `cancelled`, `completed`; default `confirmed` |
| `created_at` / `updated_at` | `DateTimeField` | auto                                                     |

Ordered by newest first.

**Review**

| Field        | Type              | Notes                                   |
|--------------|-------------------|-----------------------------------------|
| `user`       | FK → `auth.User`  | cascade, `related_name='reviews'`       |
| `hotel`      | FK → `Hotel`      | cascade, `related_name='reviews'`       |
| `rating`     | `IntegerField`    | 1–5                                     |
| `comment`    | `TextField`       |                                         |
| `created_at` | `DateTimeField`   | auto                                    |

`unique_together = ['user', 'hotel']` — one review per user per hotel. Ordered by newest first.

## Deployment

`render.yaml` describes a free Render web service plus a free PostgreSQL database:

- `buildCommand`: `./build.sh` — upgrades pip, installs requirements, runs `collectstatic --no-input`, then `migrate`
- `startCommand`: `gunicorn core.wsgi:application --bind 0.0.0.0:$PORT`
- `healthCheckPath`: `/`
- `SECRET_KEY` is generated by Render, `DEBUG` is `False`, `ALLOWED_HOSTS` lists any extra domains, and `DATABASE_URL` comes from the attached database

`runtime.txt` pins Python 3.13.2, and WhiteNoise serves the collected static files with `CompressedManifestStaticFilesStorage`.

## Tests

`hotels/tests.py` is empty — there are no tests in the repository yet.

The CI workflow at `.github/workflows/ci.yml` runs on pushes and pull requests to `main` with Python 3.13. It installs the requirements, runs `python manage.py check`, then:

```bash
python manage.py test
```

which currently collects zero tests and passes.
