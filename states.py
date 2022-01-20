from aiogram.dispatcher.filters.state import State, StatesGroup


class HomeForm(StatesGroup):
    """Форма для передачи показаний приборов учёта."""
    t = State()
    t1 = State()
    t2 = State()
    cold = State()
    hot = State()
    date = State()
    previous_t = State()
    previous_t1 = State()
    previous_t2 = State()
    previous_cold = State()
    previous_hot = State()
    previous_date = State()


class BloodPressureForm(StatesGroup):
    """Форма для передачи показаний приборов учёта."""
    date = State()
    am = State()
    systolic = State()
    diastolic = State()

