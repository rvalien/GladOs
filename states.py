from aiogram.dispatcher.filters.state import State, StatesGroup


class HomeForm(StatesGroup):
    """Форма для передачи показаний приборов учёта."""
    t = State()
    t1 = State()
    t2 = State()
    cw = State()
    hw = State()
    fin = State()
