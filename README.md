# API for a phonebook that stores users in an SQLite3 database.

## Behind
api.py is a FastAPI-based server that manages the user database. It exposes all functionality via an API.
And, of course, it has to be started.

## install
- pip install -r requirements.txt

## Using
- start api.py
- Open telefonbuch.html in the browser. This allows you to add, delete, and search for new entries...

index.html is a stripped-down HTML page.

konsole_telefonbuch.py ​​is a console program that allows you to create, search for, modify, delete, and restore entries—similar to telefonbuch.html.

db_sqlite.py is the database class; if the database or the "user" table does not exist, run the file directly so that the main method creates them.
user.py is the user class, a direct mapping of the user table in phonebook.db.
