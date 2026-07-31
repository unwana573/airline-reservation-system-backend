import uuid
from datetime import date, datetime
from datetime import time
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Numeric, Time
from api.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str | None] = mapped_column(String, nullable=True)          # Mr/Mrs/Ms/Dr...
    first_name: Mapped[str] = mapped_column(String, nullable=False)            # as on passport
    last_name: Mapped[str] = mapped_column(String, nullable=False)             # as on passport
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    is_email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    totp_secret: Mapped[str | None] = mapped_column(String, nullable=True)
    totp_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String, default="customer")  # customer|staff|admin|super_admin
    loyalty_tier: Mapped[str] = mapped_column(String, default="silver")
    loyalty_miles: Mapped[int] = mapped_column(Integer, default=0)
    accepted_terms_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    marketing_opt_in: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    oauth_accounts: Mapped[list["OAuthAccount"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    saved_passengers: Mapped[list["SavedPassenger"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)  # google | apple
    provider_user_id: Mapped[str] = mapped_column(String, nullable=False)

    user: Mapped["User"] = relationship(back_populates="oauth_accounts")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    token_hash: Mapped[str] = mapped_column(String, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="refresh_tokens")


class SavedPassenger(Base):
    __tablename__ = "saved_passengers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    dob: Mapped[date | None] = mapped_column(Date, nullable=True)
    nationality: Mapped[str | None] = mapped_column(String, nullable=True)
    passport_number: Mapped[str | None] = mapped_column(String, nullable=True)
    passport_expiry: Mapped[date | None] = mapped_column(Date, nullable=True)

    user: Mapped["User"] = relationship(back_populates="saved_passengers") 

# class FlightSearch(Base):
#     __tablename__ = "flight_searches"

#     id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
#     user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
#     airport: Mapped[str] = mapped_column(String, nullable=False)
#     airline: Mapped[str] = mapped_column(String, nullable=False)
#     aircraft_type: Mapped[str] = mapped_column(String, nullable=False)
#     route: Mapped[str] = mapped_column(String, nullable=False)
#     flightschedule: Mapped[str] = mapped_column(String, nullable=False)
#     flightinstance: Mapped[str] = mapped_column(String, nullable=False)
#     fareclass: Mapped[str] = mapped_column(String, nullable=False)
#     flightfare: Mapped[str] = mapped_column(String, nullable=False)

#     user: Mapped["User"] = relationship(back_populates="flight_searches")

class Route(Base):
    __tablename__ = "routes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    origin_airport_id: Mapped[int] = mapped_column(ForeignKey("airports.id"))
    destination_airport_id: Mapped[int] = mapped_column(ForeignKey("airports.id"))

class Airport(Base):
    __tablename__ = "airports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    iata_code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    country: Mapped[str] = mapped_column(String, nullable=False)

class AircraftType(Base):
    __tablename__ = "aircraft_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model: Mapped[str] = mapped_column(String, nullable=False)
    total_seats: Mapped[int] = mapped_column(Integer, nullable=False)

class Airline(Base):
    __tablename__ = "airlines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    iata_code: Mapped[str] = mapped_column(String(2), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)

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