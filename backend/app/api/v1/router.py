from fastapi import APIRouter

from app.api.v1.routes import (
    admin,
    admin_bookings,
    admin_dashboard,
    admin_payments,
    auth,
    bookings,
    contact,
    contents,
    payments,
    tour_categories,
    tour_departures,
    tours,
    upload,
    users,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_bookings.router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_dashboard.router, prefix="/admin", tags=["admin"])
api_router.include_router(admin_payments.router, prefix="/admin", tags=["admin"])
api_router.include_router(contents.router, prefix="/contents", tags=["contents"])
api_router.include_router(contact.router, prefix="/contact", tags=["contact"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["Bookings"])
api_router.include_router(
    payments.router, prefix="/payments", tags=["payments"]
)
api_router.include_router(tours.router, prefix="/tours", tags=["Tours"])
api_router.include_router(
    tour_departures.router, prefix="/tour-departures", tags=["Tour Departures"]
)
api_router.include_router(
    tour_categories.router, prefix="/tour-categories", tags=["Tour Categories"]
)
api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
