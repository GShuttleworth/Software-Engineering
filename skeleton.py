#!/usr/bin/python

#front end imports
from app import app
import logging
#threading

############################## MAIN

#run web server on main thread
if __name__ == '__main__':
	#only show errors in console, needs logging import
	log = logging.getLogger('werkzeug')
	log.setLevel(logging.ERROR)
	
	#help
	print("\t\t\t****Use CTRL+C then Enter key to exit****")
	print("\t\t\t\tFlask logging mode off\n")
	

	app.run(debug=True, use_reloader=False)
