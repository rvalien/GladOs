import logging
import os

from aiogram import Dispatcher
from gino import Gino

db = Gino()


class User(db.Model):
    __tablename__ = 'users'

    chat_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode)
    phone = db.Column(db.Integer)
    password = db.Column(db.Unicode)

    def __str__(self):
        return f"user object {self.name}"


class Flat(db.Model):
    __tablename__ = 'flat'

    date = db.Column(db.Date, primary_key=True)
    t = db.Column(db.Integer)
    t1 = db.Column(db.Integer)
    t2 = db.Column(db.Integer)
    hot = db.Column(db.Integer)
    cold = db.Column(db.Integer)

    def __str__(self):
        return f"flat data object {self.date}"


class BloodPressure(db.Model):
    __tablename__ = 'blood_pressure'

    date = db.Column(db.Date)
    am = db.Column(db.Boolean)  # "утреннее измерение"
    systolic = db.Column(db.Integer)  # "систолическое"
    diastolic = db.Column(db.Integer)  # "диастолическое"

    _pk = db.PrimaryKeyConstraint('date', 'am', name='date_daypart_pkey')

    def __str__(self):
        return f"BloodPressure object {self.date}_{int(self.am)}"


async def on_startup(dispatcher: Dispatcher):
    logging.info("set bind to PostgreSQL")
    await db.set_bind(os.environ["DATABASE_URL"])
    logging.info("prepare tables PostgreSQL")
    await db.gino.create_all()
