skyra-api/
├── alembic/
│   ├── versions/
│   └── env.py
├── api/
│   ├── __pycache__/
│   ├── alembic/
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   ├── database.py
│   │   ├── redis.py
│   │   └── logging.py
│   ├── repositories/
│   │   ├── auth_repository.py
│   │   ├── user_repository.py
│   │   ├── airport_repository.py
│   │   ├── flight_repository.py
│   │   ├── seat_repository.py
│   │   ├── booking_repository.py
│   │   ├── payment_repository.py
│   │   ├── checkin_repository.py
│   │   ├── loyalty_repository.py
│   │   └── admin_repository.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── airports.py
│   │   ├── search.py
│   │   ├── flights.py
│   │   ├── seatmaps.py
│   │   ├── bookings.py
│   │   ├── payments.py
│   │   ├── checkin.py
│   │   ├── flight_status.py
│   │   ├── loyalty.py
│   │   ├── support.py
│   │   └── admin.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── airport.py
│   │   ├── flight.py
│   │   ├── search.py
│   │   ├── seatmap.py
│   │   ├── booking.py
│   │   ├── payment.py
│   │   ├── checkin.py
│   │   ├── loyalty.py
│   │   ├── support.py
│   │   └── admin.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── user_service.py
│   │   ├── search_service.py
│   │   ├── seat_lock_service.py
│   │   ├── booking_service.py
│   │   ├── fare_service.py
│   │   ├── payment_service.py
│   │   ├── webhook_service.py
│   │   ├── checkin_service.py
│   │   ├── pdf_ticket_service.py
│   │   ├── loyalty_service.py
│   │   ├── notification_service.py
│   │   └── flight_status_service.py
│   ├── tasks/
│   │   ├── celery_app.py
│   │   ├── seat_hold_tasks.py
│   │   ├── booking_expiry_tasks.py
│   │   ├── email_tasks.py
│   │   └── flight_status_tasks.py
│   ├── test/
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_search.py
│   │   ├── test_bookings.py
│   │   ├── test_seat_locking.py
│   │   ├── test_payments.py
│   │   └── test_checkin.py
│   ├── __init__.py
│   ├── main.py
│   └── models.py
├── myenv/
├── .env
├── .gitignore
├── alembic.ini
└── requirements.txt


Claude finished the response

INFO: 127.0.0.1:50316 - "POST /api/v1/auth/login HTTP/1.1" 500 Internal Server Error ERROR: Exception in ASGI application Traceback (most recent call last): File "C:\Users\user\Documents\Dev\Python\Airline reservation system\myenv\Lib\site-packages\uvicorn\protocols\http\httptools_impl.p

PASTED

Diagnosed package collision and prescribed reinstallation remedy
Diagnosed package collision and prescribed reinstallation remedy

This is a classic Python import collision — import jwt is resolving to a different package than the one your code expects. There are two likely causes; let's check both.

Most likely cause: the wrong package is installed. There are two unrelated PyPI packages that both install as jwt:

PyJWT (what your code needs — has .encode(), .decode())
jwt (a completely different, mostly-unmaintained package with a different API)

If both ever got installed, or jwt got installed instead of PyJWT, import jwt silently resolves to the wrong one and jwt.encode won't exist.

Check what's actually installed:

bash
pip show jwt
pip show PyJWT

If pip show jwt returns something (a package literally named jwt, not PyJWT), that's the bug. Fix it:

bash
pip uninstall jwt -y
pip uninstall PyJWT -y
pip install PyJWT==2.9.0

Then verify it's correct:

bash
python -c "import jwt; print(jwt.__file__); print(hasattr(jwt, 'encode'))"

That should print a path ending in something like ...\site-packages\jwt\__init__.py and then True. If it prints False, the wrong package is still active.

Second possible cause — less likely but worth a 10-second check: a local file in your project accidentally named jwt.py (anywhere on the Python path) would also shadow the real package.

bash
dir /s /b jwt.py

If that finds a file inside your own project folder, rename or delete it — it's shadowing the real library.

Run the two pip show commands first and paste back what they print — that'll tell us definitively whether it's a package conflict (most likely) or a shadowing file.

i want to write the remaining code myself guide me on what to do file for file, folder for folder

Architected step-by-step module construction guide with concrete patterns
Architected step-by-step module construction guide with concrete patterns

Good instinct — writing it yourself will teach you the patterns far better than me handing over more files. Here's a guide structured the same way your auth module was built, so you can follow the exact same pattern for every new module. I'll go folder by folder, in the order you should actually build them (each phase should be fully working and tested before moving to the next).

Before you start: the pattern you're repeating

Every feature in this codebase follows the same five-file chain:

models.py           → the database table(s)
schemas/X.py         → what the API accepts/returns (Pydantic)
repositories/X.py    → raw DB queries, no business logic
services/X.py         → business logic, calls the repository
routers/X.py           → HTTP endpoints, calls the service

Data flows one direction: router → service → repository → database. Never let a router talk directly to the database, and never put business logic (like "reject if already exists") in the repository — that belongs in the service. Your auth module already does this correctly; use it as the reference every time you're unsure.

Phase 2: Flights & Search (build this next)

1. api/models.py — add these classes to your existing file (don't create a new file):

Airport (iata_code, name, city, country)
Airline (iata_code, name)
AircraftType (model, total_seats)
Route (origin_airport_id, destination_airport_id → both FKs to Airport)
FlightSchedule (airline_id, route_id, flight_number, days_of_week, departure_time)
FlightInstance (schedule_id, flight_date, departure_at, arrival_at, status)
FareClass (code, name, refundable, baggage_allowance_kg)
FlightFare (flight_instance_id, fare_class_id, base_price, seats_available)

Reference the schema I gave you in the roadmap doc for exact columns. Use Mapped[]/mapped_column() exactly like User does.

2. api/schemas/flights.py

FlightSearchRequest (origin, destination, departure_date, return_date optional, passengers, cabin_class)
FlightSearchResult (flight_number, airline_name, departure_at, arrival_at, duration, price, seats_available)
FlightDetailOut (full detail — aircraft, fare rules, baggage)

3. api/repositories/flight_repository.py

search_flights(db, origin, destination, date) — a select() joining FlightInstance → FlightSchedule → Route → Airport (twice, aliased for origin/destination) → FlightFare
get_flight_by_id(db, flight_instance_id)

4. api/services/search_service.py

search_flights(db, request: FlightSearchRequest) — calls the repository, maps DB rows into FlightSearchResult schemas, applies any business rules (e.g. exclude flights with 0 seats)

5. api/routers/flights.py

POST /search/flights
GET /flights/{flight_instance_id}

Test it like your auth tests: write api/test/test_flights.py mirroring test_auth.py's structure — a conftest.py fixture already exists, reuse it. Seed a couple of airports/flights in the test itself before asserting search results.

Phase 3: Seat Maps

1. api/models.py — add Seat (flight_instance_id, seat_number, cabin_class, status, held_until)

2. api/schemas/seatmap.py — SeatOut, SeatMapResponse (grouped by cabin class)

3. api/repositories/seat_repository.py — get_seats_for_flight(), hold_seat(), release_seat()

4. api/services/seat_lock_service.py — this is the one place you should be extra careful: use a transaction with SELECT ... FOR UPDATE (or check seat.status == 'available' inside the same transaction as the update) so two people can't hold the same seat simultaneously. This is the concurrency bug I flagged in the original roadmap — worth taking your time here and writing a test that simulates two near-simultaneous hold requests.

5. api/routers/seatmaps.py — GET /flights/{id}/seatmap, POST /flights/{id}/seats/{seat_id}/hold

Phase 4: Bookings

This is the biggest module — build it in this internal order:

1. Models (add to models.py): Booking, BookingSegment, BookingPassenger, BookingSeatAssignment, AncillaryService, BookingAncillary

2. api/schemas/booking.py: BookingCreateRequest, PassengerDetail, BookingOut

3. api/repositories/booking_repository.py: create_booking(), get_booking_by_pnr(), add_passenger()

4. api/services/booking_service.py: this is where PNR generation lives. Write a small helper:

python
import secrets, string

def generate_pnr() -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O, 1/I
    return "".join(secrets.choice(alphabet) for _ in range(6))

Check uniqueness against the DB before accepting it (retry on collision — extremely rare but possible).

5. api/routers/bookings.py: POST /bookings, GET /bookings/{pnr}, GET /bookings/retrieve?pnr=&last_name=

Test this one thoroughly — booking creation touching seats, passengers, and fares all at once is exactly the kind of code where a passing "happy path" test hides a broken edge case. Write tests for: booking with 0 passengers (should reject), booking a seat that's already held by someone else (should reject), booking after the fare hold expires (should reject).

Phase 5: Payments

1. api/schemas/payment.py: PaymentIntentRequest, PaymentWebhookPayload

2. api/services/payment_service.py: wraps whichever provider SDK you pick (Paystack/Flutterwave). Keep provider-specific code isolated here — never let routers/payments.py know which provider is in use.

3. api/services/webhook_service.py: this is the one place to be paranoid. Before trusting any webhook payload:

Verify the HMAC signature against the raw request body
Check provider_reference hasn't already been processed (idempotency — providers retry webhooks)
Only then flip booking.status to confirmed

4. api/routers/payments.py: POST /payments/intent, POST /payments/webhook/{provider}

Write this module last among the core ones, and test the webhook idempotency specifically — send the same webhook payload twice in a test and assert the booking only gets processed once.

How to actually execute this, session by session
One phase at a time. Don't start Phase 3 until Phase 2 has passing tests.
Write the model first, then run python -m api.core.init_db to confirm it creates the table without errors before writing anything else.
Write the schema next, and sanity-check it in isolation: open a Python shell, from api.schemas.flights import FlightSearchRequest, and try constructing one with valid/invalid data to confirm your validators work before wiring up the rest.
Repository → service → router, in that order, testing with curl or /docs after each router endpoint goes in — don't write five endpoints and then test all five at once; you'll lose track of which one broke.
When something breaks, paste me the traceback — that's genuinely the fastest way to unblock, and you'll still be the one who wrote and understands the code around the bug.