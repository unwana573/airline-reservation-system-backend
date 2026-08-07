import uuid
from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Time, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)  # null for OAuth-only accounts
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String, default="customer")  # customer|staff|admin|super_admin
    loyalty_tier: Mapped[str] = mapped_column(String, default="silver")
    loyalty_miles: Mapped[int] = mapped_column(Integer, default=0)
    marketing_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    oauth_accounts: Mapped[list["OAuthAccount"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)  # "google"
    provider_user_id: Mapped[str] = mapped_column(String, nullable=False)

    user: Mapped["User"] = relationship(back_populates="oauth_accounts")


class Airport(Base):
    __tablename__ = "airports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    iata_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)


class Airline(Base):
    __tablename__ = "airlines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    iata_code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)


class AircraftType(Base):
    __tablename__ = "aircraft_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model: Mapped[str] = mapped_column(String, nullable=False)
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)


class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    origin_airport_id: Mapped[int] = mapped_column(ForeignKey("airports.id"), nullable=False)
    destination_airport_id: Mapped[int] = mapped_column(ForeignKey("airports.id"), nullable=False)


class FlightSchedule(Base):
    __tablename__ = "flight_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    airline_id: Mapped[int] = mapped_column(ForeignKey("airlines.id"), nullable=False)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id"), nullable=False)
    aircraft_type_id: Mapped[int | None] = mapped_column(ForeignKey("aircraft_types.id"), nullable=True)
    flight_number: Mapped[str] = mapped_column(String, nullable=False)
    departure_time_local: Mapped[time] = mapped_column(Time, nullable=False)
    arrival_time_local: Mapped[time] = mapped_column(Time, nullable=False)


class FlightInstance(Base):
    __tablename__ = "flight_instances"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    schedule_id: Mapped[int] = mapped_column(ForeignKey("flight_schedules.id"), nullable=False)
    flight_date: Mapped[date] = mapped_column(Date, nullable=False)
    departure_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    arrival_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String, default="scheduled")


class FareClass(Base):
    __tablename__ = "fare_classes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    refundable: Mapped[bool] = mapped_column(Boolean, default=False)
    baggage_allowance_kg: Mapped[int] = mapped_column(Integer, nullable=False)


class FlightFare(Base):
    __tablename__ = "flight_fares"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flight_instance_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("flight_instances.id"), nullable=False)
    fare_class_id: Mapped[int] = mapped_column(ForeignKey("fare_classes.id"), nullable=False)
    base_price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="NGN")
    seats_available: Mapped[int] = mapped_column(Integer, nullable=False)


class Seat(Base):
    __tablename__ = "seats"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    flight_instance_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("flight_instances.id"), nullable=False)
    seat_number: Mapped[str] = mapped_column(String, nullable=False)          # e.g. "14A"
    cabin_class: Mapped[str] = mapped_column(String, nullable=False)          # economy|premium|business|first
    is_window: Mapped[bool] = mapped_column(Boolean, default=False)
    is_aisle: Mapped[bool] = mapped_column(Boolean, default=False)
    is_extra_legroom: Mapped[bool] = mapped_column(Boolean, default=False)
    is_emergency_exit: Mapped[bool] = mapped_column(Boolean, default=False)
    extra_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    status: Mapped[str] = mapped_column(String, default="available")         # available|held|occupied
    held_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Booking(Base):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    pnr: Mapped[str] = mapped_column(String(6), unique=True, nullable=False, index=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)  # null for guest checkout
    guest_email: Mapped[str | None] = mapped_column(String, nullable=True)
    guest_phone: Mapped[str | None] = mapped_column(String, nullable=True)
    trip_type: Mapped[str] = mapped_column(String, nullable=False)  # one_way|round_trip|multi_city
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|confirmed|cancelled|refunded|completed
    total_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="NGN")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)  # fare hold expiry

    segments: Mapped[list["BookingSegment"]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    passengers: Mapped[list["BookingPassenger"]] = relationship(back_populates="booking", cascade="all, delete-orphan")


class BookingSegment(Base):
    __tablename__ = "booking_segments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    flight_instance_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("flight_instances.id"), nullable=False)
    fare_class_id: Mapped[int] = mapped_column(ForeignKey("fare_classes.id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)  # ordering for multi-city

    booking: Mapped["Booking"] = relationship(back_populates="segments")


class BookingPassenger(Base):
    __tablename__ = "booking_passengers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    title: Mapped[str | None] = mapped_column(String, nullable=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    passenger_type: Mapped[str] = mapped_column(String, nullable=False)  # adult|child|infant
    nationality: Mapped[str | None] = mapped_column(String, nullable=True)
    passport_number: Mapped[str | None] = mapped_column(String, nullable=True)
    passport_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)
    frequent_flyer_number: Mapped[str | None] = mapped_column(String, nullable=True)
    special_assistance: Mapped[str | None] = mapped_column(String, nullable=True)

    booking: Mapped["Booking"] = relationship(back_populates="passengers")


class BookingSeatAssignment(Base):
    __tablename__ = "booking_seat_assignments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_passenger_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("booking_passengers.id"), nullable=False)
    booking_segment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("booking_segments.id"), nullable=False)
    seat_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("seats.id"), nullable=False)


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bookings.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)  # paystack|flutterwave
    provider_reference: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="NGN")
    status: Mapped[str] = mapped_column(String, default="pending")  # pending|success|failed|refunded
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FeaturedDestination(Base):
    __tablename__ = "featured_destinations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    airport_id: Mapped[int] = mapped_column(ForeignKey("airports.id"), nullable=False)
    badge: Mapped[str | None] = mapped_column(String, nullable=True)  # "Trending" | "Popular" | "Romantic" | "Skyline"
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Destination detail page fields
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    best_time_to_visit: Mapped[str | None] = mapped_column(String, nullable=True)
    popular_attractions: Mapped[str | None] = mapped_column(String, nullable=True)  # comma-separated for now
    travel_requirements: Mapped[str | None] = mapped_column(String, nullable=True)


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String, nullable=False)          # "Early Bird"
    subtitle: Mapped[str] = mapped_column(String, nullable=False)       # "Save up to 35% booking 60+ days ahead"
    badge: Mapped[str | None] = mapped_column(String, nullable=True)    # "Limited" | "Fri–Sun" | "Premium" | "Bundle"
    promo_code: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class NewsletterSubscriber(Base):
    __tablename__ = "newsletter_subscribers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    subscribed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())