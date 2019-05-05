from flask import Flask, request, jsonify, make_response, render_template, flash, redirect
import tweepy
from tweepy import API 
from tweepy import Cursor
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
import twitter_credentials
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from flask_mysqldb import MySQL
import hashlib

app = Flask(__name__, template_folder='template')

app.config['MYSQL_HOST'] = 'remotemysql.com'             
app.config['MYSQL_USER'] = 'KfZiCHimwl'
app.config['MYSQL_PASSWORD'] = '3UfECxWJRp'
app.config['MYSQL_DB'] = 'KfZiCHimwl'
app.config['Templates_AUTO_RELOAD']=True
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = MySQL(app)

class TwitterAuthenticator():    
    def authenticate_twitter_app(self):
        auth = OAuthHandler(twitter_credentials.CONSUMER_KEY, twitter_credentials.CONSUMER_SECRET)
        auth.set_access_token(twitter_credentials.ACCESS_TOKEN, twitter_credentials.ACCESS_TOKEN_SECRET)
        return auth

class TweetAnalyzer():
    """
    Functionality for analyzing and categorizing content from tweets.
    """
    def tweets_to_data_frame(self, tweets):
        df = pd.DataFrame(data=[tweet.text for tweet in tweets], columns=['tweets'])

        #df['id'] = np.array([tweet.id for tweet in tweets])
        #df['len'] = np.array([len(tweet.text) for tweet in tweets])
        df['date'] = np.array([tweet.created_at for tweet in tweets])
        #df['source'] = np.array([tweet.source for tweet in tweets])
        df['likes'] = np.array([tweet.favorite_count for tweet in tweets])
        #df['retweets'] = np.array([tweet.retweet_count for tweet in tweets])

        return df

   
class TwitterClient():
    def __init__(self, twitter_user=None):
        self.auth = TwitterAuthenticator().authenticate_twitter_app()
        self.twitter_client = API(self.auth)

        self.twitter_user = twitter_user

    def get_twitter_client_api(self):
        return self.twitter_client

    def get_user_timeline_tweets(self, num_tweets):
        tweets = []
        for tweet in Cursor(self.twitter_client.user_timeline, id=self.twitter_user).items(num_tweets):
            tweets.append(tweet)
        return tweets

    def get_friend_list(self, num_friends):
        friend_list = []
        for friend in Cursor(self.twitter_client.friends, id=self.twitter_user).items(num_friends):
            friend_list.append(friend)
        return friend_list

    def get_home_timeline_tweets(self, num_tweets):
        home_timeline_tweets = []
        for tweet in Cursor(self.twitter_client.home_timeline, id=self.twitter_user).items(num_tweets):
            home_timeline_tweets.append(tweet)
        return home_timeline_tweets

class MyStreamListener(tweepy.StreamListener):
    """
    This is a basic listener that just prints received tweets to stdout.
    """
    def __init__(self, fetched_tweets_filename):
        self.fetched_tweets_filename = fetched_tweets_filename

    def on_data(self, data):
        try:
            print(data)
            with open(self.fetched_tweets_filename, 'a') as tf:
                tf.write(data)
            return True
        except BaseException as e:
            print("Error on_data %s" % str(e))
        return True
          
    def on_error(self, status):
        if status == 420:
            # Returning False on_data method in case rate limit occurs.
            return False
        print(status)






@app.route('/', methods = ['GET','POST'])
def twitter_stream():
    request_data = request.form
    insert = request_data.get('list')
    authenticator = TwitterAuthenticator()
    auth = authenticator.authenticate_twitter_app()
    user = TwitterClient()
    user.__init__(insert)
    analyzer = TweetAnalyzer()
    tweets = user.get_user_timeline_tweets(30)
    df = analyzer.tweets_to_data_frame(tweets)
    tweets=[]
    tweets = df.values
    
    time_favs = pd.Series(data=df['likes'].values, index=df['date'])
    time_favs.plot(figsize=(16, 4), color='r')
    plt.savefig("static/img/my_plot.png")
 
    return render_template('home.html', x=tweets)


@app.route("/listings")
def show():
    cur=mysql.connection.cursor()
    cur.execute('''SELECT * from Channels''')
    check=cur.fetchall()
    return str(check)

@app.route('/form2')
def form2():
    return render_template('listing.html')


@app.route('/listingsadd', methods=['POST'])
def add():
        request_data = request.form
        cur = mysql.connection.cursor()
        insert = request_data.get('list')
        myString = "INSERT INTO Channels (Channel) VALUES ('" + insert + "')"
        cur.execute(myString)
        mysql.connection.commit()
        return "Done"


@app.route('/form')
def form():
    return render_template('register.html')


@app.route('/api/users', methods=['POST'])
def registerUser():
        if request.form:  # Check if the user info is submitted by an HTML form
            request_data = request.form
        else:  # Information is submitted via an API request using JSON
            request_data = request.get_json()
        # retrieve the data from the request from the client
        username = request_data.get('username')
        password = request_data.get('password')
        email= request_data.get('email')
        cur = mysql.connection.cursor()
        hashed_password = hashlib.sha1(username.encode('utf-8')).hexdigest()
        cur.execute("INSERT INTO User (Username, Password, Email) VALUES ('" + username + "','" + hashed_password + "','" + email + "')")
        mysql.connection.commit()
        return "DONE"





