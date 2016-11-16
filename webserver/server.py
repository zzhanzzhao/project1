#!/usr/bin/env python2.7

"""
Columbia W4111 Intro to databases
Example webserver

To run locally

    python server.py

Go to http://localhost:8111 in your browser


A debugger such as "pdb" may be helpful for debugging.
Read about it online.
"""

import os
from sqlalchemy import *
from sqlalchemy.pool import NullPool
from flask import Flask, request, render_template, g, redirect, Response
from datetime import datetime

tmpl_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, template_folder=tmpl_dir)


#
# The following uses the postgresql test.db -- you can use this for debugging purposes
# However for the project you will need to connect to your Part 2 database in order to use the
# data
#
# XXX: The URI should be in the format of: 
#
#     postgresql://USER:PASSWORD@<IP_OF_POSTGRE_SQL_SERVER>/postgres
#
# For example, if you had username ewu2493, password foobar, then the following line would be:
#
#     DATABASEURI = "postgresql://ewu2493:foobar@<IP_OF_POSTGRE_SQL_SERVER>/postgres"
#
# Swap out the URI below with the URI for the database created in part 2
DATABASEURI = "postgresql://zz2247:3ft64@104.196.175.120/postgres"


#
# This line creates a database engine that knows how to connect to the URI above
#
engine = create_engine(DATABASEURI)


#
# START SQLITE SETUP CODE
#
# after these statements run, you should see a file test.db in your webserver/ directory
# this is a sqlite database that you can query like psql typing in the shell command line:
# 
#     sqlite3 test.db
#
# The following sqlite3 commands may be useful:
# 
#     .tables               -- will list the tables in the database
#     .schema <tablename>   -- print CREATE TABLE statement for table
# 
# The setup code should be deleted once you switch to using the Part 2 postgresql database
#
# engine.execute("""DROP TABLE IF EXISTS test;""")
# engine.execute("""CREATE TABLE IF NOT EXISTS test (
#   id serial,
#   name text
# );""")
# engine.execute("""INSERT INTO test(name) VALUES ('grace hopper'), ('alan turing'), ('ada lovelace');""")
# END SQLITE SETUP CODE
#



@app.before_request
def before_request():
  """
  This function is run at the beginning of every web request 
  (every time you enter an address in the web browser).
  We use it to setup a database connection that can be used throughout the request

  The variable g is globally accessible
  """
  try:
    g.conn = engine.connect()
  except:
    print "uh oh, problem connecting to database"
    import traceback; traceback.print_exc()
    g.conn = None

@app.teardown_request
def teardown_request(exception):
  """
  At the end of the web request, this makes sure to close the database connection.
  If you don't the database could run out of memory!
  """
  try:
    g.conn.close()
  except Exception as e:
    pass


#
# @app.route is a decorator around index() that means:
#   run index() whenever the user tries to access the "/" path using a GET request
#
# If you wanted the user to go to e.g., localhost:8111/foobar/ with POST or GET then you could use
#
#       @app.route("/foobar/", methods=["POST", "GET"])
#
# PROTIP: (the trailing / in the path is important)
# 
# see for routing: http://flask.pocoo.org/docs/0.10/quickstart/#routing
# see for decorators: http://simeonfranklin.com/blog/2012/jul/1/python-decorators-in-12-steps/
#
@app.route('/')
def index():
  """
  request is a special object that Flask provides to access web request information:

  request.method:   "GET" or "POST"
  request.form:     if the browser submitted a form, this contains the data in the form
  request.args:     dictionary of URL arguments e.g., {a:1, b:2} for http://localhost?a=1&b=2

  See its API: http://flask.pocoo.org/docs/0.10/api/#incoming-request-data
  """

  # DEBUG: this is debugging code to see what request looks like
  print request.args

  cursor = g.conn.execute("SELECT * FROM country")
  names = []
  for result in cursor:
    names.append(result['cname'])
  cursor.close()

  #
  # Flask uses Jinja templates, which is an extension to HTML where you can
  # pass data to a template and dynamically generate HTML based on the data
  # (you can think of it as simple PHP)
  # documentation: https://realpython.com/blog/python/primer-on-jinja-templating/
  #
  # You can see an example template in templates/index.html
  #
  # context are the variables that are passed to the template.
  # for example, "data" key in the context variable defined below will be 
  # accessible as a variable in index.html:
  #
  #     # will print: [u'grace hopper', u'alan turing', u'ada lovelace']
  #     <div>{{data}}</div>
  #     
  #     # creates a <div> tag for each element in data
  #     # will print: 
  #     #
  #     #   <div>grace hopper</div>
  #     #   <div>alan turing</div>
  #     #   <div>ada lovelace</div>
  #     #
  #     {% for n in data %}
  #     <div>{{n}}</div>
  #     {% endfor %}
  #
  print(names)

  context = dict(data = names)
  #
  # render_template looks in the templates/ folder for files.
  # for example, the below file reads template/index.html
  #
  return render_template("index.html", **context)

#
# This is an example of a different path.  You can see it at
# 
#     localhost:8111/another
#
# notice that the functio name is another() rather than index()
# the functions for each app.route needs to have different names
#
@app.route('/another')
def another():
  # lifter_belongs table
  cursor = g.conn.execute("SELECT name, cname, gender, dob, weight_class FROM lifter_belongs l LEFT JOIN (SELECT o.lid, weight_class FROM weigh_in o INNER JOIN (SELECT lid, max(weigh_time) as weigh_time FROM Weigh_In GROUP BY lid) m ON o.lid = m.lid AND o.weigh_time = m.weigh_time) w on l.lid = w.lid")
  lifters = []
  lifters.append(dict(Name='Name', Country='Country', Gender='Country', DOB='DOB', weight_class = "Latest Weight Class"))
  for result in cursor:
      lifters.append(dict(Name=result['name'], Country=result['cname'], Gender=result['gender'], DOB=result['dob'].strftime('%m/%d/%Y'), weight_class = result['weight_class']))
  cursor.close()
  return render_template("anotherfile.html", lifters=lifters)

@app.route('/competition')
def competition():
  # competition_division table joined with competition and division tables
  cursor = g.conn.execute("SELECT loc, date, age, gender, weight_class, cdid FROM competition_division cd INNER JOIN competition c ON cd.cid = c.cid INNER JOIN division d ON cd.did = d.did")
  competitions = []
  competitions.append(dict(Location='Location', Date='Date', Age='Age Division', Gender='Gender Division', Weight_Class='Weight Class', cdid = 'Competition ID'))
  for result in cursor:
      competitions.append(dict(Location=result['loc'],Date=result['date'].strftime('%m/%d/%Y'), Age=result['age'], Gender=result['gender'], Weight_Class=result['weight_class'], cdid=result['cdid']))
  cursor.close()
  return render_template("competition.html", competitions=competitions)

@app.route('/add', methods=['POST'])
def add():
  name = request.form['name']
  print name
  cmd = 'INSERT INTO country(cname) VALUES (:name1)';
  g.conn.execute(text(cmd), name1 = name);
  return redirect('/')

@app.route('/addlifter', methods=['POST'])
def addlifter():
  name = request.form['name']
  country = request.form['cname']
  gender = request.form['gender']
  dob = request.form['dob']

  cursor = g.conn.execute("SELECT cname FROM country")
  names = []
  for result in cursor:
    names.append(result['cname'])
  cursor.close()

  if (gender not in ['M','F'] or country not in names):
      return redirect('/another')

  try:
      datetime.strptime(dob, '%m/%d/%Y')
  except ValueError:
      return redirect('/another')

  cmd = 'INSERT INTO lifter_belongs(name, cname, gender, dob) VALUES ((:name),(:country),(:gender),(:dob))';
  g.conn.execute(text(cmd), name = name, country = country, gender = gender, dob = dob);

  return redirect('/another')

@app.route('/competitors', methods=['POST'])
def competitors():
  id = request.form['id']

  cmd = 'SELECT name, type, attempt, weight, successful, national_ranking FROM competes c INNER JOIN (SELECT cid, did FROM competition_division WHERE cdid = (:id)) cd ON c.cid = cd.cid AND c.did = cd.did LEFT JOIN lifter_belongs l ON c.lid = l.lid LEFT JOIN country_rank r ON c.liid = r.liid'
  try:
    cursor = g.conn.execute(text(cmd), id = id)
  except:
    return redirect('/competition')

  competitors = []
  competitors.append(dict(name='Name', type='Type', attempt='Attempt#', weight='Weight', successful='Successful',national_ranking='National Ranking'))
  for result in cursor:
      competitors.append(dict(name=result['name'], type=result['type'], attempt=result['attempt'], weight=result['weight'], successful=result['successful'],national_ranking=result['national_ranking']))
  cursor.close()
  print(competitors)
  return render_template("compete.html", competitors=competitors, x=id)

@app.route('/login')
def login():
    abort(401)
    this_is_never_executed()


if __name__ == "__main__":
  import click

  @click.command()
  @click.option('--debug', is_flag=True)
  @click.option('--threaded', is_flag=True)
  @click.argument('HOST', default='0.0.0.0')
  @click.argument('PORT', default=8111, type=int)
  def run(debug, threaded, host, port):
    """
    This function handles command line parameters.
    Run the server using

        python server.py

    Show the help text using

        python server.py --help

    """

    HOST, PORT = host, port
    print "running on %s:%d" % (HOST, PORT)
    app.run(host=HOST, port=PORT, debug=debug, threaded=threaded)


  run()
