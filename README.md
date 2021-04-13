# SpotifyMe

## An app to learn something more about your music tastes and even discover new personalised playlists

We developed a simple HTML user interface to connect with Spotify API to recover an user's information on their music preferences and listen to new recomended tracks.

Used libraries:
* Spotipy to call Spotify API
* OAuth2.0 for authorization protocols
* Pandas to store data
* Plotly for data visualization

The File [Project.ipynb](https://github.com/kate14845/accademy_python_project/blob/main/Project.ipynb) is a Jupyter notebook that contains functions for connecting with an user's account throught Spotify Web API, saving user's data into pandas dataframes and visualising them with Plotly.

The file "flask_app.py" contains the functions related to spotify managed in several flask routes. This project considered three interactive web pages.
visit: spotifyme.pythonanywhere.com
