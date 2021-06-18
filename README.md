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

use app.json for deploy

{% codeblock lang:markdown %} [Deploy my app to Heroku] (https://heroku.com/deploy?template=https://github.com/heroku/python-sample) {% endcodeblock %}