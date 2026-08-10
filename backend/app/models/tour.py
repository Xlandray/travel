import uuid
from datetime import date

from sqlalchemy import Boolean, Column, Date, ForeignKey, Integer, Numeric, String, Table, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin

# Tur ve Binis Noktasi arasindaki "Coka Cok" (Many-to-Many) iliski tablosu
tour_boarding_points = Table(
    "tour_boarding_points",
    Base.metadata,
    Column(
        "tour_id",
        UUID(as_uuid=True),
        ForeignKey("tours.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "boarding_point_id",
        UUID(as_uuid=True),
        ForeignKey("boarding_points.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class BoardingPoint(Base, TimestampMixin):
    """Boarding points for tour pick-ups."""

    __tablename__ = "boarding_points"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), index=True)  # Örn: "Orion AVM Önu"
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Cift yonlu iliski
    tours: Mapped[list["Tour"]] = relationship(
        secondary=tour_boarding_points, back_populates="boarding_points"
    )


class TourCategory(Base, TimestampMixin):
    """Category grouping for tours, e.g. 'Gunubirlik', 'Yurt Ici', 'Balayi'."""

    __tablename__ = "tour_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    tours: Mapped[list["Tour"]] = relationship(back_populates="category")


class Tour(Base, TimestampMixin):
    """Main tour product entity."""

    __tablename__ = "tours"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))
    slug: Mapped[str] = mapped_column(
        String(255), unique=True, index=True
    )  # SEO dostu URL (kapadokya-turu)
    description: Mapped[str] = mapped_column(Text)
    days: Mapped[int] = mapped_column(Integer)  # Örn: 3 (Gun)
    nights: Mapped[int] = mapped_column(Integer)  # Örn: 2 (Gece)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tour_categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Iliskiler: Bir turun birden fazla kalkis tarihi ve binis noktasi olabilir
    departures: Mapped[list["TourDeparture"]] = relationship(
        back_populates="tour", cascade="all, delete-orphan"
    )
    boarding_points: Mapped[list["BoardingPoint"]] = relationship(
        secondary=tour_boarding_points, back_populates="tours"
    )
    category: Mapped["TourCategory | None"] = relationship(back_populates="tours")
    images: Mapped[list["TourImage"]] = relationship(
        back_populates="tour",
        cascade="all, delete-orphan",
        order_by="TourImage.sort_order",
    )


class TourImage(Base, TimestampMixin):
    """Gallery images for a tour."""

    __tablename__ = "tour_images"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tour_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tours.id", ondelete="CASCADE"), index=True
    )
    url: Mapped[str] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    tour: Mapped["Tour"] = relationship(back_populates="images")


class TourDeparture(Base, TimestampMixin):
    """Tour departure dates, pricing, and quota management."""

    __tablename__ = "tour_departures"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tour_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tours.id", ondelete="CASCADE"))

    start_date: Mapped[date] = mapped_column(Date, index=True)
    end_date: Mapped[date] = mapped_column(Date)

    # Parasal islemler icin hassas veri tipi (10 basamak, 2'si kurus)
    price: Mapped[float] = mapped_column(Numeric(10, 2))

    total_quota: Mapped[int] = mapped_column(Integer)  # Örn: 45 (Toplam Otobus Kapasitesi)
    available_seats: Mapped[int] = mapped_column(
        Integer
    )  # Örn: 45 (Satis yapildikca azalacak stok)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Iliski
    tour: Mapped["Tour"] = relationship(back_populates="departures")
