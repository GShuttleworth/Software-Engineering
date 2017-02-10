from flask import render_template
from app import app

from flask import request

@app.route('/')
@app.route('/index')
def index():
	pagename = "Home"
	return render_template('index.html',pagename=pagename)


@app.route('/', methods=['POST'])
def my_form_post():
	pagename = "Home"
	text = request.form['text']
	print(text)
	return render_template('index.html',pagename=pagename)
