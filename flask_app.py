import spotipy
import urllib
import requests
from flask import Flask, url_for, redirect, request, session, render_template, send_from_directory
import pandas as pd
import plotly.io as pio
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt

authorize_endpoint= "https://accounts.spotify.com/authorize?" #it would be used for a GET request
token_endpoint = "https://accounts.spotify.com/api/token"
api_endpoint="https://api.spotify.com/v1/" #we will not use it. instead we use sp object made of "spotipy.Spotify" class
clientid = '1902a------a6373'
clientsecret = '1b633-------d0465'
scopes = 'user-library-read user-follow-read user-top-read user-read-recently-played'


app=Flask(__name__)
app.secret_key ="app"

@app.route("/")
def login():
    return render_template("login.html")

@app.route("/authorize")
def authorize():
    params={"client_id" : clientid,
            "client_secret" : clientsecret,
            "scope" : scopes,
            "response_type" : "code",
            "show_dialog" : "True",
            "redirect_uri": "http://127.0.0.1:5000/gettoken"}
    auth_url= authorize_endpoint + urllib.parse.urlencode(params)
    return redirect(auth_url)

@app.route("/gettoken",)
def gettoken():
    code = request.args.get("code")
    session["code"]=code
    params={"client_id" : clientid,
            "client_secret" : clientsecret,
            "grant_type" : "authorization_code",
            "code" : code,
            "redirect_uri": "http://127.0.0.1:5000/gettoken"}
            #at this point there would be no redirection by spotify
            #this value is given only for verification
            #it should be equal to redirect_uri of authorize part
    token_info=requests.post(token_endpoint, data=params)
    token_info_body = token_info.json()
    session["acc_token"] = token_info_body.get("access_token")
    session["ref_token"] = token_info_body.get("refresh_token")
    return redirect(url_for("home"))

@app.route("/home")
def home():
    sp = spotipy.Spotify(auth=session["acc_token"])
    results= sp.new_releases(country="IT", limit=10, offset=0)
    new_photos=[]
    new_links=[]
    new_names=[]

    for i in range(8):
        album_img=results["albums"]["items"][i]["images"][0]["url"]
        new_photos.append(album_img)
        album_url=results["albums"]["items"][i]['external_urls']['spotify']
        new_links.append(album_url)
        album_name=results["albums"]["items"][0]['name']
        new_names.append(album_name)

    i=0
    for u in new_photos:
        response= requests.get(u)
        file=open(f"static/images/sample_image{i}.png","wb")
        file.write(response.content)
        i+=1
    file.close()
    return render_template("home.html", links=new_links, names=new_names)

@app.route("/results")
def results():
    sp = spotipy.Spotify(auth=session["acc_token"])
    result=sp.current_user_followed_artists(limit=20, after=None)

    # (1) Followed Artists of the user
    artist_db=pd.DataFrame(columns=['id','name','genres','followers','popularity'])

    for j in range(100):
        for artist in result['artists']['items']:
            artist_db=artist_db.append({'id':artist['id'],
                                        'name':artist['name'],
                                        'genres':artist['genres'],
                                        'followers':artist['followers']['total'],
                                        'popularity':artist['popularity']},
                                       ignore_index=True)

            result =sp.current_user_followed_artists(after=artist['id'])
        if len(result['artists']['items'])==0:
            break

    # (2) Genres of artists (and subsequently of user)
    # create a list with user favourite genres
    genres_list=[]
    for item in artist_db['genres']:
        for genre in item:
            genres_list.append(genre)
    # create a wordbubble with user's favourite genres
    words = genres_list
    plt.subplots(figsize = (10,10))
    wordcloud = WordCloud (background_color = 'white',
                           width = 900,
                           height = 700).generate(' '.join(words))

    plt.imshow(wordcloud) # image show
    plt.axis('off') # to off the axis of x and y
    plt.savefig('static/images/taste1.png')

    # (3) most popular artists of user
    # create a scatterplot with user's most popular artist
    df_top=artist_db.sort_values(by='popularity').tail(10)
    df_top['size']=2

    fig = px.scatter(df_top[['popularity','followers','name','size']], x="popularity", y="followers",color='name',size='size')
    fig.update_layout(width=900, height=700)
    fig.write_image("static/images/taste2.png")

    # (4) user's top Tracks and Artists in time
    #request of user's top tracks and artists
    mr_tracks = sp.current_user_top_tracks(time_range='short_term') #Client Module
    mr_tracks_now= sp.current_user_top_tracks(limit=10,time_range='short_term')
    mr_tracks_ever= sp.current_user_top_tracks(limit=10,time_range='long_term')
    mr_artists_now= sp.current_user_top_artists(limit=10,time_range='short_term')
    mr_artists_ever= sp.current_user_top_artists(limit=10,time_range='long_term')

    # "def" to make dataframes
    #function to export spotify top-objects into a database
    def create_db(spot_obj):
        df=pd.DataFrame(columns=['number','name','id'])
        pos=1
        for track in spot_obj['items']:
            df=df.append({'name':track['name'],'number':pos,'id':track['id']},ignore_index=True)
            pos+=1
        return df

    # "def" to plot
    #function to plot the top-ten tracks in panda.DataBase format
    def topten(df):
        colors = ['rgb(239, 243, 255)',
                  'rgb(239, 243, 255)',
                  'rgb(239, 243, 255)',
                  'rgb(189, 215, 231)',
                  'rgb(189, 215, 231)',
                  'rgb(189, 215, 231)',
                  'rgb(189, 215, 231)',
                  'rgb(107, 174, 214)',
                  'rgb(107, 174, 214)',
                  'rgb(107, 174, 214)']

        df['Color']=colors
        fig = go.Figure(data=[go.Table(columnwidth = [50,200],
                                       header=dict(values=['<b>Number</b>', '<b>Track</b>'],
                                                   fill_color='white',
                                                   align='center',
                                                   font=dict(color='black', size=17)),
                                       cells=dict(values=[df.number[0:10], df.name[0:10]],
                                                  align='center',line_color=[df.Color],
                                                  fill_color=[df.Color],
                                                  font=dict(color='black', size=14),
                                                  height=40))
                             ])

        fig.update_layout(width=900, height=700)
        return fig

    #function to plot the top-ten artists
    def topten_artists(df):
        colors = ['rgb(239, 243, 255)',
                  'rgb(239, 243, 255)',
                  'rgb(239, 243, 255)',
                  'rgb(189, 215, 231)',
                  'rgb(189, 215, 231)',
                  'rgb(189, 215, 231)',
                  'rgb(189, 215, 231)',
                  'rgb(107, 174, 214)',
                  'rgb(107, 174, 214)',
                  'rgb(107, 174, 214)']

        df['Color']=colors
        fig = go.Figure(data=[go.Table(columnwidth = [50,200],
                                       header=dict(values=['<b>Number</b>', '<b>Artist</b>'],
                                                   fill_color='white',
                                                   align='center',
                                                   font=dict(color='black', size=17)),
                                       cells=dict(values=[df.number[0:10], df.name[0:10]],
                                                  align='center',line_color=[df.Color],
                                                  fill_color=[df.Color],
                                                  font=dict(color='black', size=14),
                                                  height=40))
                             ])

        fig.update_layout(width=900, height=700)
        return fig

    # make the dataframes
    top_tracks_now_df=create_db(mr_tracks_now)
    top_tracks_ever_df=create_db(mr_tracks_ever)
    top_artists_now_df=create_db(mr_artists_now)
    top_artists_ever_df=create_db(mr_artists_ever)

    fig=topten(top_tracks_now_df)
    fig.write_image("static/images/top1.png")
    fig=topten(top_tracks_ever_df)
    fig.write_image("static/images/top2.png")
    fig=topten_artists(top_artists_now_df)
    fig.write_image("static/images/top3.png")
    fig=topten_artists(top_artists_ever_df)
    fig.write_image("static/images/top4.png")

    #convert 20 most listened song in a dataframe
    top_tracks_df=pd.DataFrame(columns=['number','name'])
    for pos,track in enumerate(mr_tracks['items']):
        top_tracks_df=top_tracks_df.append({'name':track['name'],
                                            'number':pos+1,
                                            'liveness':sp.audio_features(track['id'])[0]['liveness'],
                                            'energy':sp.audio_features(track['id'])[0]['energy'],
                                            'loudness':sp.audio_features(track['id'])[0]['loudness'],
                                            'danceability':int((sp.audio_features(track['id'])[0]['danceability'])*100)},
                                           ignore_index=True)
    #plot top listened track features
    df = px.data.gapminder()

    fig = px.scatter(top_tracks_df[0:20], x="liveness", y="loudness",hover_name='name',size='energy',color="name")
    fig.write_image("static/images/mood1.png")

    # plot the average of most listened song deanceability
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = top_tracks_df['danceability'].mean(),
        title = {'text': "your party mood"},
        domain = {'x':[0,1], 'y': [0, 1]}
    ))
    fig.update_traces(gauge_axis_range=[0,100], selector=dict(type='indicator'))
    fig.write_image("static/images/mood2.png")

    #request for recomended tracks based on user's top artists
    artist_id=top_artists_now_df['id'][0:5].tolist()
    recom_tracks=sp.recommendations(seed_artists=artist_id)
    photos=[]
    links=[]
    names=[]
    for i in range(4):
        album_img=recom_tracks["tracks"][i]["album"]["images"][0]["url"]
        photos.append(album_img)
        album_url=recom_tracks["tracks"][i]["album"]["external_urls"]["spotify"]
        links.append(album_url)
        album_name=recom_tracks["tracks"][i]["album"]["name"]
        names.append(album_name)

    links = links
    names = names
    i=0
    for url in photos:
        response= requests.get(url)
        file=open(f"static/images/recom{i}.png","wb")
        file.write(response.content)
        i+=1
    file.close()
    return render_template("results.html",links=links, names=names)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug= True)
