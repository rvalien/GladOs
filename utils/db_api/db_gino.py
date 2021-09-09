from gino import Gino
from aiogram import Dispatcher
import os

db = Gino()


class User(db.Model):
    __tablename__ = 'users'

    chat_id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.Unicode())
    phone = db.Column(db.Integer())
    password = db.Column(db.Unicode())


class Flat(db.Model):
    __tablename__ = 'flat'

    date = db.Column(db.Date, primary_key=True)
    t = db.Column(db.Integer())
    t1 = db.Column(db.Integer())
    t2 = db.Column(db.Integer())
    hot = db.Column(db.Integer())
    cold = db.Column(db.Integer())


async def on_startup(dispatcher: Dispatcher):
    print("Установка связи с PostgreSQL")
    await db.set_bind(os.environ["DATABASE_URL"])
