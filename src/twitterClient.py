#!/usr/bin/python
# -*- coding: utf-8; mode: python -*-

from flask import Flask, request, redirect, url_for, flash, render_template,jsonify, make_response
from flask_oauthlib.client import OAuth

import requests 
import json
from requests_oauthlib import OAuth1

app = Flask(__name__)
app.config['DEBUG'] = True
oauth = OAuth()
mySession = None
currentUser = None

app.secret_key = 'development'

consumer_key = 'YdkRywlj5XBj2OfVmwgXizQ93'
consumer_secret = 'Nn52ohLmK4LHzx0lfDsRymHASYgLirSjdfgaxeGPMO3Qe3Irh9'

twitter = oauth.remote_app('twitter',
                           base_url='https://api.twitter.com/1.1/',
                           request_token_url='https://api.twitter.com/oauth/request_token',
                           access_token_url='https://api.twitter.com/oauth/access_token',
                           authorize_url='https://api.twitter.com/oauth/authenticate',
                           consumer_key=consumer_key,
                           consumer_secret=consumer_secret
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
            #print(tweets)
        else:
            flash('Imposible acceder a Twitter.', 'error')
    return render_template('index.html', user=currentUser, tweets=tweets)


# Get auth token (request)
@app.route('/login')
def login():
    callback_url = url_for('oauthorized', next=request.args.get('next'))
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
    if currentUser is None:
        flash("Not done because you weren't logged in .Please, try it again", 'error')
        return redirect(url_for('login'))

    tweetId = request.form['deleteTweetId']
    if not tweetId:
        flash("ID for 'Delete tweet' operation cannot be empty", 'warning')
        return redirect(url_for('index'))

    url = 'https://api.twitter.com/1.1/statuses/destroy/'+tweetId+'.json'
    auth = OAuth1(consumer_key,consumer_secret,mySession['oauth_token'],mySession['oauth_token_secret'])
    headers = {"Accept":"*/*",
        "Host":"api.twitter.com",
        "Accept-Encoding":"gzip, deflate"
    }
    response = requests.post(url=url,headers=headers,auth=auth)

    #response = twitter.post('statuses/destroy/'+tweetId+'.json')
    errorHandler(response, 'deleteTweet')

    return redirect(url_for('index'))


@app.route('/retweet', methods=['POST'])
def retweet():
    if currentUser is None:
        flash("Not done because you weren't logged in .Please, try it again", 'error')
        return redirect(url_for('login'))

    tweetId = request.form['retweetId']
    if not tweetId:
        flash("ID for 'Retweet' operation cannot be empty", 'warning')
        return redirect(url_for('index'))

    url = 'https://api.twitter.com/1.1/statuses/retweet/'+tweetId+'.json'
    auth = OAuth1(consumer_key,consumer_secret,mySession['oauth_token'],mySession['oauth_token_secret'])
    headers = {"Accept":"*/*",
        "Host":"api.twitter.com",
        "Accept-Encoding":"gzip, deflate"
    }
    #response = twitter.post('statuses/retweet/'+tweetId+'.json')
    response = requests.post(url=url,headers=headers,auth=auth)
    errorHandler(response, 'retweet')

    return redirect(url_for('index'))


@app.route('/follow', methods=['POST'])
def follow():
    if currentUser is None:
        flash("Not done because you weren't logged in .Please, try it again", 'error')
        return redirect(url_for('login'))

    userId = request.form['followUserId']
    userName = request.form['followUserName']
    if not userId and not userName:
        flash("User id or user name must be provided", 'warning')
        return redirect(url_for('index'))
    elif userId and userName:
        flash("Please, enter either id or name, but not both", 'warning')
        return redirect(url_for('index'))

    elif userId:
        #response = twitter.post('friendships/create.json', data={
        #    'user_id': userId
        #})
        #errorHandler(response, 'follow')
        params = {'user_id':userId}
    else:
        #response = twitter.post('friendships/create.json', data={
        #    'screen_name': userName
        #})
        #errorHandler(response, 'follow')
        params = {'screen_name':userName}

    url = 'https://api.twitter.com/1.1/friendships/create.json'
    auth = OAuth1(consumer_key,consumer_secret,mySession['oauth_token'],mySession['oauth_token_secret'])
    headers = {"Accept":"*/*",
        "Host":"api.twitter.com",
        "Accept-Encoding":"gzip, deflate"
    }
    response = requests.post(url=url,headers=headers,auth=auth, params = params)
    errorHandler(response,'follow')

    return redirect(url_for('index'))


@app.route('/tweet', methods=['POST'])
def tweet():
    # Paso 1: Si no estoy logueado redirigir a pagina de /login
               # Usar currentUser y redirect
    if currentUser is None:
        flash("Not done because you weren't logged in. Please, try it again", 'error')
        return redirect(url_for('login'))
    # Paso 2: Obtener los datos a enviar
        # Usar request (form)
    tweet = request.form['tweetTextPost']
    # Paso 3: Construir el request a enviar con los datos del paso 2
    # Utilizar alguno de los metodos de la instancia twitter (post, request, get, ...)
    if not tweet:
        flash("Tweet for 'Post tweet operation' cannot be empty", 'warning')
        return redirect(url_for('index'))

    #response = twitter.post('statuses/update.json', data={
    #    'status': tweet
    #})
    URL = "https://api.twitter.com/1.1/statuses/update.json"
    params = {"status":tweet}
    auth = OAuth1(consumer_key, consumer_secret, mySession['oauth_token'], mySession['oauth_token_secret'])
    headers = {"Accept":"*/*",
    "Host":"api.twitter.com",
    "Accept-Encoding":"gzip, deflate",
    }
    response = requests.post(url=URL,headers=headers,auth=auth,params=params)
    # Paso 4: Comprobar que todo fue bien (no hubo errores) e informar al usuario
    # La anterior llamada devuelve el response, mirar el estado (status)
    errorHandler(response, 'tweet')
    # Paso 5: Redirigir a pagina principal (hecho)
    return redirect(url_for('index'))


def errorHandler(response, operation):
    if response.status_code == 403:
        flash('Error', 'error')
    elif response.status_code == 401:
        flash('Error de autorización', 'error')
    elif response.status_code == 404:
        flash('Error, recurso no encontrado','error')
    elif response.status_code == 500:
        flash('Error interno del servidor','error')
    else:
        print(response)
        if operation == 'tweet':
            flash('Posted Tweet! (ID: #%s)' % response.json()['id'], 'success')
        elif operation == 'deleteTweet':
            flash('Deleted Tweet! (ID: #%s)' % response.json()['id'], 'success')
        elif operation == 'retweet':
            flash('Retweet Tweet Done! (ID: #%s)' %
                  response.json()['id'], 'success')
        elif operation == 'follow':
            flash('User (ID: #%s) followed!' % response.json()['id'], 'success')


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5005)
