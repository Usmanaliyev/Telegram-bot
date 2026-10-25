








# ============================================================
#  TARTIB QOIDASI (4-darsdan):  tordan kengga.
#
#  5-darsda yangi qoida qo'shildi:
#    FSM router'i — ENG BIRINCHI.
#    Sabab: /bekor buyrug'i har qanday holatda ishlashi kerak.
#    Agar u pastda tursa, foydalanuvchi FSM ichida qamalib qoladi.
# ============================================================

# from aiogram import Dispatcher
#
# from handlers import cart, catalog, checkout, common
#
#
# def register(dp: Dispatcher) -> None:
#     dp.include_router(checkout.router)   # FSM + /bekor — ENG BIRINCHI
#     dp.include_router(cart.router)
#     dp.include_router(catalog.router)
#     dp.include_router(common.router)     # /start + FALLBACK — eng oxirida







# 4dars

# ============================================================
# #  Router'lar SHU YERDA ulanadi. TARTIB — eng muhim narsa.
# #  Bu — Django'dagi urls.py ning ekvivalenti.
# #
# #  QOIDA: tordan kengga.
# #    Aniq filtrli router'lar — yuqorida.
# #    "Hamma narsani ushlaydigan" router — ENG OXIRIDA.
# #
# #  common.py ichida @router.message(F.text) bor — u HAR QANDAY
# #  matnni ushlaydi. Agar common birinchi ulansa, u «🧺 Savat»
# #  tugmasini ham yutib yuboradi va savat hech qachon ochilmaydi.
# #
# #  SINAB KO'RING: common.router ni yuqoriga ko'chiring va
# #  «🧺 Savat» tugmasini bosing. Ishlamaydi. Keyin qaytaring.
# # ============================================================
#
# from aiogram import Dispatcher
#
# from handlers import cart, catalog, common
#
#
# def register(dp: Dispatcher) -> None:
#     dp.include_router(cart.router)      # aniq: «🧺 Savat» va savat callback'lari
#     dp.include_router(catalog.router)   # aniq: katalog callback'lari
#     dp.include_router(common.router)    # /start + FALLBACK — eng oxirida




# 6dars
# ============================================================
#  TARTIB QOIDASI (4-darsdan):  tordan kengga.
#
#  5-darsda yangi qoida qo'shildi:
#    FSM router'i — ENG BIRINCHI.
#    Sabab: /bekor buyrug'i har qanday holatda ishlashi kerak.
#    Agar u pastda tursa, foydalanuvchi FSM ichida qamalib qoladi.
# ============================================================

from aiogram import Dispatcher

from handlers import cart, catalog, checkout, common


def register(dp: Dispatcher) -> None:
    dp.include_router(checkout.router)   # FSM + /bekor — ENG BIRINCHI
    dp.include_router(cart.router)
    dp.include_router(catalog.router)
    dp.include_router(common.router)     # /start + FALLBACK — eng oxirida