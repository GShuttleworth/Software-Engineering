#!/usr/bin/python
#
from flask import Flask


#misc
import uuid #generating random session ids

def init_app():
	app = Flask(__name__)
	
	#flask configuration
	#for sessions, generate a key instead
	app.secret_key = str(uuid.uuid4())
	return app

app=init_app()
from app import views
