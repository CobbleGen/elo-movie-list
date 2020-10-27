from my_server import app
from my_server.dbhandler import create_connection
from flask import request, url_for, flash, redirect, session, render_template, abort
import requests
import json
import bcrypt


def isLoggedIn():
  if 'logged_in' in session.keys() and session['logged_in']:
    return True
  else:
    return False


@app.route('/')
@app.route('/index')
def start():
  conn = create_connection()
  cur = conn.cursor()
  cur.execute('SELECT movie_id, score FROM scored_tags WHERE tag_id = 1 ORDER BY score DESC')
  data = cur.fetchall()
  index = 0
  for id in data:
    respons = requests.get('http://www.omdbapi.com/?i='+id[0]+'&apikey=cb9b8dd8', allow_redirects=True)
    movied = json.loads(respons.text)
    data[index] = {
      'imdbID': id[0],
      'Title': movied['Title'],
      'elo': int(id[1])
    }
    index += 1

  return render_template('index.html', loggedIn = isLoggedIn(), moviedets = data)


@app.route('/searched', methods=['GET', 'POST'])
def searched():
  if request.method == 'POST':
    respons = requests.get('http://www.omdbapi.com/?s='+request.form['search_text']+'&apikey=cb9b8dd8', allow_redirects=True)
    data = json.loads(respons.text)

  return render_template('searched.html', movies = data, search_term = request.form['search_text'], loggedIn = isLoggedIn())


@app.route('/movie/<dbid>')
def movie(dbid=None):
  if dbid == None:
    abort(401)
  else:
    respons = requests.get('http://www.omdbapi.com/?i='+dbid+'&apikey=cb9b8dd8', allow_redirects=True)
    data = json.loads(respons.text)
    
    #Make sure that dbid is a valid IMDB id
    if 'Incorrect IMDb ID.' in respons.text:
      abort(401)
    conn = create_connection()
    cur = conn.cursor()
    
    #Checks if movie is in database, if not add it
    cur.execute('SELECT COUNT(*) FROM movies WHERE imdbID = (?)', (dbid, ))
    if cur.fetchall()[0][0] == 0:
      cur.execute('INSERT INTO movies (imdbID) VALUES (?)', (dbid, ))
      genres = data['Genre'].split(', ')
      genres.append('Movie')
      for genre in genres:
        cur.execute('SELECT COUNT(*), tagID FROM tags WHERE tag_name = (?)', (genre, ))
        result = cur.fetchall()
        tag_id = result[0][1]
        if result[0][0] == 0:
          cur.execute('INSERT INTO tags (tag_name) VALUES (?)', (genre, ))
          cur.execute('SELECT tagID FROM tags WHERE tag_name = (?)', (genre, ))
          tag_id = cur.fetchall()[0][0]
        cur.execute('INSERT INTO scored_tags (movie_id, tag_id, score) VALUES (?,?,?)', (dbid, tag_id, 1000))
      conn.commit()
    cur.execute('SELECT score FROM scored_tags WHERE tag_id = 1 AND movie_id = (?)', (dbid, ))
    score = int(cur.fetchall()[0][0])
    print(score)
    conn.close()
    return render_template('movie.html', movie = data, loggedIn = isLoggedIn(), score = score)


@app.route('/login', methods=['GET', 'POST'])
def login():
  if request.method == 'POST':
    conn = create_connection()
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM users WHERE username = (?)', (request.form['username'], ))
    if cur.fetchall()[0][0] == 1:
      cur.execute('SELECT userID, password FROM users WHERE username = (?)', (request.form['username'], ))
      result = cur.fetchall()
      user_id = result[0][1]
      if bcrypt.checkpw(request.form['password'].encode('UTF-8'), result[0][1]):
        session['logged_in'] = True
        session['user_id'] = user_id
        conn.close()
        return redirect(url_for('start'))
    flash('Password or username incorrect.', 'danger')
    conn.close()
  return render_template('login.html', loggedIn = isLoggedIn())


@app.route('/register', methods=['GET', 'POST'])
def create_user():
  if request.method == 'POST':
    if request.form['pwd'] == request.form['pwd2']:
      conn = create_connection()
      cur = conn.cursor()
      hashed_pw = bcrypt.hashpw(request.form['pwd'].encode('UTF-8'), bcrypt.gensalt())
      cur.execute('INSERT INTO users (username, password) VALUES (?,?)', (request.form['username'], hashed_pw))
      conn.commit()
      conn.close()
    else:
      conn.close()
      flash('Paswords have to match!', 'warning')
  return render_template('createuser.html', loggedIn = isLoggedIn())


@app.route('/compare')
@app.route('/compare/<wid>/<lid>')
def compare(wid = None, lid = None):
  conn = create_connection()
  cur = conn.cursor()
  #Increase winners score and lower losers
  if wid != None and lid != None:
    cur.execute('SELECT score FROM scored_tags WHERE tag_id = 1 AND movie_id = (?)', (wid,))
    ratA = cur.fetchall()[0][0]
    cur.execute('SELECT score FROM scored_tags WHERE tag_id = 1 AND movie_id = (?)', (lid,))
    ratB = cur.fetchall()[0][0]
    probA = 1/(1 + (10**((ratB - ratA)/400)))
    probB = 1-probA
    print(f'Probability A: {probA}, Probability B: {probB}')
    newratA = ratA + (32*(1 - probA))
    newratB = ratB + (32*(0 - probB))
    cur.execute('UPDATE scored_tags SET score = (?) WHERE tag_id = 1 AND movie_id = (?)', (newratA, wid))
    cur.execute('UPDATE scored_tags SET score = (?) WHERE tag_id = 1 AND movie_id = (?)', (newratB, lid))
    conn.commit()
  cur.execute('SELECT imdbID FROM movies ORDER BY RANDOM() LIMIT 2')
  selected_movies = cur.fetchall()
  respons = requests.get('http://www.omdbapi.com/?i='+selected_movies[0][0]+'&apikey=cb9b8dd8', allow_redirects=True)
  movie1 = json.loads(respons.text)
  respons = requests.get('http://www.omdbapi.com/?i='+selected_movies[1][0]+'&apikey=cb9b8dd8', allow_redirects=True)
  movie2 = json.loads(respons.text)
  conn.close()
  return render_template('compare.html', loggedIn = isLoggedIn(), movie1 = movie1, movie2 = movie2)