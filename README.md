# glados

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![Python-Versions](https://img.shields.io/badge/python-3.9-blue)
[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/rvalien/orbbot/master/LICENSE)
[![Discord.py-Version](https://img.shields.io/badge/aiogram-2.13-blue)](https://pypi.org/project/discord.py/)

### description

Create for experiments. Now it helps me with routine.
---

### bot's commands: 

### /time  
can help you to choose what to do in your free time.  
#### Usage:
`/time` - fetch random element from your todo list if list is not empty.  
`/time game1` - add 1 element `game1` to your todo list.  
`/time reading, sleep, bath` - add multiple elements to your todo list.  
`/time all` - show all your opportunities in list.  
`/time clean` - clean up your list.


### /bill  
I don't think that you need it. It's specified for small virtual operator.


### /internet  
I don't think that you need it. It's specified for small virtual operator.


### /weather  
Weather in my hometown.
#### Usage:

`/weather` - example:  21.4C, ясно


### /myid  
debug help command


### /flat 🏡
send flat meters data to database.

---

### setup

[heroku needs requirements.txt to build the app](https://devcenter.heroku.com/articles/getting-started-with-python#declare-app-dependencies)
so make it with the command below if you use poetry
```shell
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

set environment variables  
`TELEGRAM_TOKEN`- bot token  
`WEATHER_TOKEN` - token for `openweathermap.org` api  
`DATABASE_URL` - postgres db connection string  
`REDISTOGO_URL` - redis db connection string  
`DELAY`- seconds for repeating background tasks  
`ADMIN`- telegram id to notifications  

create table
```sql
/* postgres */
CREATE TABLE public.chat_ids (
	chat_id int4 NULL,
	"name" varchar NULL
);
```
---

### deploy

[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy?template=https://github.com/rvalien/GladOs)


---
### todo
move from redis to aioredis  
redis do postgres backup (new users, TODOes...)  

Wanna new features? [Create an issue](https://github.com/rvalien/GladOs/issues) on this repo.