from aiogram import Dispatcher

from handlers import admin, cart, catalog, checkout, common, courier, orders


def register(dp: Dispatcher) -> None:
    dp.include_router(checkout.router)   # FSM + /bekor
    dp.include_router(admin.router)      # rol bilan qulflangan
    dp.include_router(courier.router)    # rol bilan qulflangan
    dp.include_router(orders.router)     # mijozning "Qabul qildim" tugmasi
    dp.include_router(cart.router)
    dp.include_router(catalog.router)
    dp.include_router(common.router)     # /start + fallback - eng oxirida