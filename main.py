from flask import Flask, render_template, request

import requests
import urllib


def compare(item):
    # Тут можно придумать более сложную формулу
    # для более правильной оценки и составления рейтинга найденых мест
    return item['rating'] * item['user_ratings_total'] ** 0.5


# функция принимает адрес и возвращает в его координаты
def coordinates_from_address(address, api_key):
    base_url = 'https://maps.googleapis.com/maps/api/geocode/json?'
    parameters = {'address': address, 'key': api_key}
    url = f"{base_url}{urllib.parse.urlencode(parameters)}"
    response = requests.get(url)
    location = response.json()['results'][0]['geometry']['location']
    return f"{location['lat']},{location['lng']}"


# функция вернет список мест
def find_places(landmark, preferences, radius, api_key):
    base_url = 'https://maps.googleapis.com/maps/api/place/nearbysearch/json?'
    parameters1 = 'location='+landmark+'&radius='+radius
    parameters2 = '&keyword='+preferences+'&language=ru-Ru'+'&key='+api_key
    final_url = base_url + parameters1 + parameters2
    response = requests.get(final_url)
    places = response.json()['results']
    return places


def place_finder(dest_location, radius, tag):
    with open('../googleApiKey.txt') as ggl:
        api_key = ggl.read()
    coordinates = coordinates_from_address(dest_location, api_key)
    places_list = find_places(coordinates, tag, radius, api_key)
    if len(places_list) == 0:
        return {
            "status": "NO_RESULTS"
        }
    places = sorted(places_list, key=compare, reverse=True)
    favourite_place = places[0]
    return {
        "name": favourite_place['name'],
        "address": favourite_place['vicinity'],
        "rating": favourite_place['rating'],
        "rating_amount": favourite_place['user_ratings_total'],
        "lat": favourite_place['geometry']['location']['lat'],
        "lng": favourite_place['geometry']['location']['lng'],
        "status": 'OK'
    }


def get_weather(lat, lng, arriving_time, api_key):
    base_url = 'https://api.openweathermap.org/data/2.5/onecall?'
    parameters1 = 'lat='+f"{lat}"+'&lon='+f"{lng}"
    parameters2 = '&exclude=minutely&appid='+api_key+'&lang=ru'
    request_url = base_url + parameters1 + parameters2
    response = requests.get(request_url)
    response.json()
    if int(arriving_time) > 47:
        # без погоды
        return ''
    # возвращаем погоду в указанный час
    return response.json()['hourly'][int(arriving_time)]


def weather_finder(lat, lng, time):
    with open('../oneCallApiKey.txt') as open_weather_api_key:
        api_key = open_weather_api_key.read()
    weather = get_weather(lat, lng, time, api_key)
    if weather != '':
        return {
            "temp": round(weather['temp'] - 273),
            "feels": round(weather['feels_like'] - 273),
            "humidity": f"{weather['humidity']}" + '%',
            "description": weather['weather'][0]['description'],
        }
    else:
        return {
            "temp": '',
            "feels": '',
            "humidity": '',
            "description": 'Более чем на 2 дня прогноз погоды недоступен :(',
        }


app = Flask(__name__)


@app.route('/form')
def form():
    return render_template('form.html')


@app.route('/data', methods=['POST', 'GET'])
def data():
    if request.method == 'GET':
        return (
            "The URL /data is accessed directly.Try going to '/form' to submit"
        )
    if request.method == 'POST':
        place = place_finder(
            request.form['dest_location'],
            request.form['radius'],
            request.form['tag'],
        )
        if place['status'] != "OK":
            return render_template('noplaces.html')
        else:
            weather = weather_finder(
               place['lat'],
               place['lng'],
               request.form['time']
            )
            form_data = {
                "name": place['name'],
                "address": place['address'],
                "rating": place['rating'],
                "ratings_amount": place['rating_amount'],
                "temp": weather['temp'],
                "feels": weather['feels'],
                "humidity": weather['humidity'],
                "description": weather['description'],
                "time": request.form['time']
            }
            return render_template('data.html', form_data=form_data)


if __name__ == "__main__":
    app.run(host='localhost', port=5000, debug=False)
