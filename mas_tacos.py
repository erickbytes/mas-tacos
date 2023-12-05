from flask import Flask, send_from_directory, request
from geopy import distance
import pandas as pd
import logging
import os
import sys

"""Requirements
- enable taco button click --> trigger "best tacos" page
- users can enter their zip code
- look up lat long coords from zip code
- use geopy to calculate closest restaurant from nearest in kaggle dataset
- users can thumbs up or thumbs down the suggestion(s)

TODO
- (location) Permissions API for the Web: https://developers.google.com/web/updates/2015/04/permissions-api-for-the-web
- Google review API? Or other review source?
- user collected sauce ratings & heat ratings
"""
logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
app = Flask(__name__)


@app.route("/static/tacofavicon.ico")
def favicon():
    """Render the site favicon in Flask."""
    try:
        return send_from_directory(
            os.path.join(app.root_path, "static"),
            "tacofavicon.ico",
            mimetype="image/vnd.microsoft.icon",
        )
    except:
        logging.exception("Failed to link Favicon.")


@app.route("/")
def find_tacos():
    """Renders the HTML form to ask for the user's zip code."""
    html_page = """<html><head><link rel='stylesheet' href="/static/styles/mastacos.css">
                    <link rel="shortcut icon" type="image/x-icon" href="/static/tacofavicon.ico">
                    <Title>mas tacos</Title></head>
                    <body>
                    <div class="form">
                    <form action="/taco_restaurants" method="post">
                    <label for="zipcode">Enter your zip code for tacos near you!</label>
                    <input type="text" id ="zipcode" name="zipcode">
                    <input type="image" id="taco" src="/static/iStock-1084361584.jpg" border="0" alt="Submit" />
                    </form></div></body></html>"""
    return html_page


@app.route("/taco_restaurants", methods=["GET", "POST"])
def taco_restaurants():
    """restaurant reviews & taco rating 4/5 tacos
    "how delicious are the sauces?"
    "thermometer for the heat of the sauces"
    comments on the flavor = how delicious the tacos ratings
    """
    try:
        zip_code = request.form["zipcode"]
        tacos = query_taco_restaurants(zip_code)
        user_loc = query_lat_long(zip_code)
        if isinstance(user_loc, tuple):
            tacos["miles_away"] = tacos[["latitude", "longitude"]].apply(
                calculate_distance, args=(user_loc,), axis=1
            )
            tacos["miles_away"] = tacos["miles_away"].apply(lambda m: int(m * 100))
            cols = ["name", "menus.description", "address", "city", "miles_away"]
            mapping = {"miles_away": "miles away", "menus.description": "type of food"}
            tacos = (
                tacos[cols]
                .rename(columns=mapping)
                .fillna("")
                .drop_duplicates(subset=["name", "address"])
            )
        else:
            return "No matches found."
        tacos = tacos.sort_values(by=["miles away"])
        html = f"""<html><head><link rel='stylesheet' href="/static/styles/table.css">
                        <link rel="shortcut icon" type="image/x-icon" href="/static/tacofavicon.ico">
                        <Title>mas tacos</Title></head>
                        <body><h2>mas tacos?</h2><br>
                        {tacos.to_html(index=False)}</body></html>"""
        return html
    except:
        logging.exception("Unable to find tacos!")
        return "Sorry! Taco-nical difficulties."


def calculate_distance(restaurant_loc, user_loc):
    """Returns distance in miles to taco restaurant based on zip code."""
    return distance.distance(user_loc, restaurant_loc).miles


def query_lat_long(zip_code):
    """Returns lat long pair by looking up zip code. Data is separated with ;"""
    cols = ["Zip", "Latitude", "Longitude", "geopoint"]
    zips = pd.read_csv("us-zip-code-latitude-and-longitude.csv", usecols=cols, sep=";")
    matches = zips[zips.Zip.astype(str) == str(zip_code)].reset_index(drop=True)
    if matches.empty:
        return zips
    else:
        latitude = matches.at[0, "Latitude"]
        longitude = matches.at[0, "Longitude"]
        user_loc = (latitude, longitude)
        return user_loc


def query_taco_restaurants(zip_code):
    """Read a csv of taco restaurants with their longitude and latitude coordinates.
    Returns restaurants with the same zip code."""
    cols = [
        "name",
        "address",
        "city",
        "country",
        "postalCode",
        "latitude",
        "longitude",
        "menus.description",
    ]
    tacos = pd.read_csv("just tacos and burritos.csv", usecols=cols)
    tacos = tacos.dropna(subset=["latitude", "longitude"])
    matches = tacos[tacos.postalCode.astype(str) == str(zip_code)].drop_duplicates()
    if matches.empty:
        return tacos
    else:
        return matches


def taco_rating(number):
    """Returns an HTML string of taco images, with the # of tacos being the given number."""
    taco = """<img src="/static/iStock-1084361584.jpg" alt="find tacos" width="40" height="40" >"""
    tacos = list()
    for i in range(0, number):
        tacos.append(taco)
    taco_html = "".join(tacos)
    return taco_html
