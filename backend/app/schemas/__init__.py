"""Pydantic DTOs used at the API boundary."""

from app.schemas.auth import Token, TokenPayload
from app.schemas.booking import (
    BookingBase,
    BookingCreate,
    BookingRead,
    BookingResponse,
    booking_to_response,
)
from app.schemas.contact import ContactCreate, ContactResponse
from app.schemas.content import ContentCreate, ContentRead, ContentUpdate
from app.schemas.hotel import (
    HotelCreate,
    HotelRead,
    HotelUpdate,
    TourHotelIn,
    TourHotelRead,
)
from app.schemas.pagination import Page
from app.schemas.payment import PaymentCreate, PaymentRead, PaymentResponse
from app.schemas.route import (
    BoardingPointRead,
    RouteStopIn,
    RouteStopRead,
    RouteStopUpdate,
)
from app.schemas.setting import SettingCreate, SettingRead, SettingUpdate
from app.schemas.tour import BoardingPointResponse, TourDepartureResponse, TourResponse
from app.schemas.user import AdminUserUpdate, UserCreate, UserRead, UserUpdate

__all__ = [
    "AdminUserUpdate",
    "BoardingPointRead",
    "BoardingPointResponse",
    "BookingBase",
    "BookingCreate",
    "BookingRead",
    "BookingResponse",
    "ContactCreate",
    "ContactResponse",
    "ContentCreate",
    "ContentRead",
    "ContentUpdate",
    "HotelCreate",
    "HotelRead",
    "HotelUpdate",
    "Page",
    "PaymentCreate",
    "PaymentRead",
    "PaymentResponse",
    "RouteStopIn",
    "RouteStopRead",
    "RouteStopUpdate",
    "SettingCreate",
    "SettingRead",
    "SettingUpdate",
    "Token",
    "TokenPayload",
    "TourDepartureResponse",
    "TourHotelIn",
    "TourHotelRead",
    "TourResponse",
    "UserCreate",
    "UserRead",
    "UserUpdate",
    "booking_to_response",
]
