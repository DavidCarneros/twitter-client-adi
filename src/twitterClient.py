#!/usr/bin/python
# -*- coding: utf-8; mode: python -*-

from flask import Flask, request, redirect, url_for, flash, render_template
from flask_oauthlib.client import OAuth

app = Flask(__name__)
app.config['DEBUG'] = True
oauth = OAuth()
mySession=None
currentUser=None

app.secret_key = 'development'


twitter = oauth.remote_app('twitter',
    base_url='https://api.twitter.com/1.1/',
    request_token_url='https://api.twitter.com/oauth/request_token',
    access_token_url='https://api.twitter.com/oauth/access_token',
    authorize_url='https://api.twitter.com/oauth/authenticate',
    consumer_key='YdkRywlj5XBj2OfVmwgXizQ93',
    consumer_secret='Nn52ohLmK4LHzx0lfDsRymHASYgLirSjdfgaxeGPMO3Qe3Irh9'
)


# Obtener token para esta sesion
@twitter.tokengetter
def get_twitter_token(token=None):
    global mySession
    
    if mySession is not None:
        return mySession['oauth_token'], mySession['oauth_token_secret']

    
# Limpiar sesion anterior e incluir la nueva sesion
@app.before_request
def before_request():
    global mySession
    global currentUser
    
    currentUser = None
    if mySession is not None:
        currentUser = mySession
        

# Pagina principal
@app.route('/')
def index():
    global currentUser
    
    tweets = None
    if currentUser is not None:
        resp = twitter.request('statuses/home_timeline.json')
        if resp.status == 200:
            tweets = resp.data
        else:
            flash('Imposible acceder a Twitter.')
    return render_template('index.html', user=currentUser, tweets=tweets)


# Get auth token (request)
@app.route('/login')
def login():
    callback_url=url_for('oauthorized', next=request.args.get('next'))
    return twitter.authorize(callback=callback_url or request.referrer or None)


# Eliminar sesion
@app.route('/logout')
def logout():
    global mySession
    
    mySession = None
    return redirect(url_for('index'))


# Callback
@app.route('/oauthorized')
def oauthorized():
    global mySession
    
    resp = twitter.authorized_response()
    if resp is None:
        flash('You denied the request to sign in.')
    else:
        mySession = resp
    return redirect(url_for('index', next=request.args.get('next')))




# Operaciones
@app.route('/deleteTweet', methods=['POST'])
def deleteTweet():
    return redirect(url_for('index'))



@app.route('/retweet', methods=['POST'])
def retweet():
    return redirect(url_for('index'))


@app.route('/follow', methods=['POST'])
def follow():
    return redirect(url_for('index'))
    

    
@app.route('/tweet', methods=['POST'])
def tweet():
    # Paso 1: Si no estoy logueado redirigir a pagina de /login
               # Usar currentUser y redirect
    if currentUser is None:
        return redirect(url_for('login'))
    # Paso 2: Obtener los datos a enviar
               # Usar request (form)
    tweet = request.form['tweetTextPost']
    # Paso 3: Construir el request a enviar con los datos del paso 2
               # Utilizar alguno de los metodos de la instancia twitter (post, request, get, ...)
    if not tweet:
        return redirect(url_for('index'))

    response = twitter.post('statuses/update.json', data={
        'status': tweet
    })
    # Paso 4: Comprobar que todo fue bien (no hubo errores) e informar al usuario
               # La anterior llamada devuelve el response, mirar el estado (status)
    errorHandler(response)
    # Paso 5: Redirigir a pagina principal (hecho)
    return redirect(url_for('index'))


def errorHandler(response):
    if response.status == 403:
        flash("Error: #%d, %s " % (
            response.data.get('errors')[0].get('code'),
            response.data.get('errors')[0].get('message'))
        )
    elif response.status == 401:
        flash('Error de autorización.')
    else:
        flash('Tweet enviado correctamente, creado con (ID: #%s)' % response.data['id'])

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5005)


