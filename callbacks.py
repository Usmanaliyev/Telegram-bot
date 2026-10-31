from aiogram.filters.callback_data import CallbackData


class MenuCB(CallbackData, prefix="menu"):
    action: str


class CategoryCB(CallbackData, prefix="cat"):
    category_id: int          # 7-dars: satr kalit o'rniga baza ID si


class ProductCB(CallbackData, prefix="prod"):
    action: str
    product_id: int = 0
    qty: int = 1


class CartCB(CallbackData, prefix="cart"):
    action: str
    product_id: int = 0


class CheckoutCB(CallbackData, prefix="chk"):
    action: str
    value: str = ""


class AdminCB(CallbackData, prefix="adm"):
    action: str
    order_id: int = 0
    value: str = ""


class CourierCB(CallbackData, prefix="crr"):
    action: str
    order_id: int = 0


class OrderCB(CallbackData, prefix="ord"):
    action: str
    order_id: int = 0