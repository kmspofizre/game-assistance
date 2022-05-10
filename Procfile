web: gunicorn runp-heroku:app
init: python main.py && pybabel compile -d app/translations
upgrade: python main.py && pybabel compile -d app/translations
