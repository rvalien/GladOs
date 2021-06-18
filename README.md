# glados

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
![Python-Versions](https://img.shields.io/badge/python-3.9-blue)
[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/rvalien/orbbot/master/LICENSE)
[![Discord.py-Version](https://img.shields.io/badge/aiogram-2.13-blue)](https://pypi.org/project/discord.py/) 


[heroku needs requirements.txt to build the app](https://devcenter.heroku.com/articles/getting-started-with-python#declare-app-dependencies)
so make ti with the command below if you use poetry
```shell
poetry export -f requirements.txt --output requirements.txt --without-hashes
```

set environment variables  
`TELEGRAM_TOKEN`  
`WEATHER_TOKEN`  
`DATABASE_URL`  
`REDISTOGO_URL`  
`DELAY`  

use [.app.json](app.json) for deploy on [heroku](https://devcenter.heroku.com/articles/app-json-schema)

create table
```sql
/* postgres */
CREATE TABLE public.chat_ids (
	chat_id int4 NULL,
	"name" varchar NULL
);
```

## bot's commands: 
---
### /time  
can help you to choose what to do in your free time.  
#### Usage:
`/time` - fetch random element from your todo list if list not empty.  
`/time game1` - add 1 element to your todo list.  
`/time reading, sleep, bath` - add multiple elements to your todo list.  
`/time all` - show all your opportunities in list.  
`/time clean` - cleanup your list.
---
### /bill  
I don't think that you are need it. It's specified for small virtual operator.

---
### /internet  
I don't think that you are need it. It's specified for small virtual operator.

---
### /weather  
Weather for my hometown.
#### Usage:

`/weather` - example:  21.4C, ясно

---

### /myid  
debug help command
