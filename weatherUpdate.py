#!/usr/bin/python
# coding=utf-8

import codecs
import sqlite3
from urllib import request
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta
import sys
from string import Template
import json

DB_PATH = '/home/kyle/weather/weather.db'
SENSOR_URL = 'http://192.168.1.55/livedata.htm'
UNITS_URL = 'http://192.168.1.55/station.htm'
CUMULUS_TXT_PATH = '/var/www/weather/Realtime.txt'
PLAIN_HTML_PATH = '/var/www/weather/index.html'

def update_database(data):
	db = sqlite3.connect(DB_PATH)
	cursor = db.cursor()

	cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='weather';")
	if cursor.fetchone() is None:
		cursor.execute("""CREATE TABLE weather (
			id INTEGER PRIMARY KEY NOT NULL,
			datetime DATETIME NOT NULL,
			temp_indoor REAL,
			temp_outdoor REAL,
			temp_units TEXT,
			humidity_indoor INTEGER,
			humidity_outdoor INTEGER,
			pm25_outdoor INTEGER,
			pressure_absolute REAL,
			pressure_relative REAL,
			pressure_units TEXT,
			wind_direction INTEGER,
			wind_speed REAL,
			wind_gust REAL,
			wind_units TEXT,
			solar_radiation REAL,
			solar_radiation_units TEXT,
			uv INTEGER,
			uv_index INTEGER,
			rain_hourly REAL,
			rain_daily REAL,
			rain_weekly REAL,
			rain_monthly REAL,
			rain_yearly REAL,
			rain_units TEXT
		)""")

		db.commit()

	ordered_data = []
	ordered_data.append(data['datetime'])
	ordered_data.append(data['temp_indoor'])
	ordered_data.append(data['temp_outdoor'])
	ordered_data.append(data['temp_units'])
	ordered_data.append(data['humidity_indoor'])
	ordered_data.append(data['humidity_outdoor'])
	ordered_data.append(data['pm25_outdoor'])
	ordered_data.append(data['pressure_absolute'])
	ordered_data.append(data['pressure_relative'])
	ordered_data.append(data['pressure_units'])
	ordered_data.append(data['wind_direction'])
	ordered_data.append(data['wind_speed'])
	ordered_data.append(data['wind_gust'])
	ordered_data.append(data['wind_units'])
	ordered_data.append(data['solar_radiation'])
	ordered_data.append(data['solar_radiation_units'])
	ordered_data.append(data['uv'])
	ordered_data.append(data['uv_index'])
	ordered_data.append(data['rain_hourly'])
	ordered_data.append(data['rain_daily'])
	ordered_data.append(data['rain_weekly'])
	ordered_data.append(data['rain_monthly'])
	ordered_data.append(data['rain_yearly'])
	ordered_data.append(data['rain_units'])

	cursor.execute("""INSERT INTO weather
		(
			datetime,
			temp_indoor,
			temp_outdoor,
			temp_units,
			humidity_indoor,
			humidity_outdoor,
			pm25_outdoor,
			pressure_absolute,
			pressure_relative,
			pressure_units,
			wind_direction,
			wind_speed,
			wind_gust,
			wind_units,
			solar_radiation,
			solar_radiation_units,
			uv,
			uv_index,
			rain_hourly,
			rain_daily,
			rain_weekly,
			rain_monthly,
			rain_yearly,
			rain_units
		)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	""", ordered_data)

	db.commit()
	fetch_aggregate_data(data, cursor)
	fetch_historic_data(data, cursor)
	db.close()

def fetch_historic_data(data, cursor):
	now = datetime.today().strftime('%Y-%m-%d %H:%M:%S')
	_24hrs_ago = (datetime.today() - timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S')
	data['historic'] = []

	cursor.execute('SELECT datetime, temp_outdoor, pm25_outdoor, humidity_outdoor, pressure_relative, wind_speed, wind_gust, solar_radiation, uv, temp_indoor, humidity_indoor, rain_hourly FROM weather WHERE datetime > ? AND datetime <= ? ORDER BY datetime asc;', [_24hrs_ago, now])
	for row in cursor.fetchall():
		data['historic'].append({
			'date': row[0],
			'tempOutdoor': row[1],
			'pm25Outdoor': row[2],
			'humidityOutdoor': row[3],
			'pressureRelative': row[4],
			'windSpeed': row[5],
			'windGust': row[6],
			'solarRadiation': row[7],
			'uv': row[8],
			'tempIndoor': row[9],
			'humidityIndoor': row[10],
			'rainHourly': row[11],
		})
	data['historic'] = data['historic'][0::5] # Every 5th element

def fetch_aggregate_data(data, cursor):
	today = datetime.today().strftime('%Y-%m-%d 00:00:00')
	tomorrow = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d 00:00:00')

	cursor.execute('SELECT datetime, MAX(temp_indoor) FROM weather WHERE datetime >= ? AND datetime < ?;', [today, tomorrow])
	data['temp_indoor_daily_high_time'], data['temp_indoor_daily_high'] = cursor.fetchone()
	data['temp_indoor_daily_high_time'] = datetime.strptime(data['temp_indoor_daily_high_time'], '%Y-%m-%d %H:%M:%S')

	cursor.execute('SELECT datetime, MIN(temp_indoor) FROM weather WHERE datetime >= ? AND datetime < ?;', [today, tomorrow])
	data['temp_indoor_daily_low_time'], data['temp_indoor_daily_low'] = cursor.fetchone()
	data['temp_indoor_daily_low_time'] = datetime.strptime(data['temp_indoor_daily_low_time'], '%Y-%m-%d %H:%M:%S')


	cursor.execute('SELECT datetime, MAX(temp_outdoor) FROM weather WHERE datetime >= ? AND datetime < ?;', [today, tomorrow])
	data['temp_outdoor_daily_high_time'], data['temp_outdoor_daily_high'] = cursor.fetchone()
	data['temp_outdoor_daily_high_time'] = datetime.strptime(data['temp_outdoor_daily_high_time'], '%Y-%m-%d %H:%M:%S')

	cursor.execute('SELECT datetime, MIN(temp_outdoor) FROM weather WHERE datetime >= ? AND datetime < ?;', [today, tomorrow])
	data['temp_outdoor_daily_low_time'], data['temp_outdoor_daily_low'] = cursor.fetchone()
	data['temp_outdoor_daily_low_time'] = datetime.strptime(data['temp_outdoor_daily_low_time'], '%Y-%m-%d %H:%M:%S')


	cursor.execute('SELECT datetime, MAX(pm25_outdoor) FROM weather WHERE datetime >= ? AND datetime < ?;', [today, tomorrow])
	data['pm25_outdoor_daily_high_time'], data['pm25_outdoor_daily_high'] = cursor.fetchone()
	data['pm25_outdoor_daily_high_time'] = datetime.strptime(data['pm25_outdoor_daily_high_time'], '%Y-%m-%d %H:%M:%S')

	cursor.execute('SELECT datetime, MIN(pm25_outdoor) FROM weather WHERE datetime >= ? AND datetime < ?;', [today, tomorrow])
	data['pm25_outdoor_daily_low_time'], data['pm25_outdoor_daily_low'] = cursor.fetchone()
	data['pm25_outdoor_daily_low_time'] = datetime.strptime(data['pm25_outdoor_daily_low_time'], '%Y-%m-%d %H:%M:%S')


	cursor.execute('SELECT datetime, MAX(pressure_relative) FROM weather WHERE datetime >= ? AND datetime < ?;', [today, tomorrow])
	data['pressure_relative_daily_high_time'], data['pressure_relative_daily_high'] = cursor.fetchone()
	data['pressure_relative_daily_high_time'] = datetime.strptime(data['pressure_relative_daily_high_time'], '%Y-%m-%d %H:%M:%S')

	cursor.execute('SELECT datetime, MIN(pressure_relative) FROM weather WHERE datetime >= ? AND datetime < ?;', [today, tomorrow])
	data['pressure_relative_daily_low_time'], data['pressure_relative_daily_low'] = cursor.fetchone()
	data['pressure_relative_daily_low_time'] = datetime.strptime(data['pressure_relative_daily_low_time'], '%Y-%m-%d %H:%M:%S')

	cursor.execute('SELECT datetime, MAX(wind_speed) FROM weather WHERE datetime >= ? AND datetime < ?;', [today, tomorrow])
	data['wind_speed_daily_max_time'], data['wind_speed_daily_max'] = cursor.fetchone()
	data['wind_speed_daily_max_time'] = datetime.strptime(data['wind_speed_daily_max_time'], '%Y-%m-%d %H:%M:%S')

	cursor.execute('SELECT datetime, MAX(wind_gust) FROM weather WHERE datetime >= ? AND datetime < ?;', [today, tomorrow])
	data['wind_gust_daily_max_time'], data['wind_gust_daily_max'] = cursor.fetchone()
	data['wind_gust_daily_max_time'] = datetime.strptime(data['wind_gust_daily_max_time'], '%Y-%m-%d %H:%M:%S')

def fetch_data():
	data = {}

	response = request.urlopen(UNITS_URL, timeout=30).read()
	soup = BeautifulSoup(response, 'html.parser')

	data['wind_units'] = soup.find('select', attrs={'name':'unit_Wind'}).find('option', selected=True).string
	data['rain_units'] = soup.find('select', attrs={'name':'u_Rainfall'}).find('option', selected=True).string
	data['pressure_units'] = soup.find('select', attrs={'name':'unit_Pressure'}).find('option', selected=True).string
	data['temp_units'] = soup.find('select', attrs={'name':'u_Temperature'}).find('option', selected=True).string
	data['solar_radiation_units'] = soup.find('select', attrs={'name':'unit_Solar'}).find('option', selected=True).string

	response = request.urlopen(SENSOR_URL, timeout=30).read()
	soup = BeautifulSoup(response, 'html.parser')

	data['datetime'] = datetime.strptime(soup.find('input', attrs={'name':'CurrTime'})['value'], '%H:%M %m/%d/%Y')

	data['battery_indoor'] = soup.find('input', attrs={'name':'inBattSta'})['value']
	data['battery_outdoor'] = soup.find('input', attrs={'name':'outBattSta1'})['value']

	data['temp_indoor'] = float(soup.find('input', attrs={'name':'inTemp'})['value'])
	data['temp_outdoor'] = float(soup.find('input', attrs={'name':'outTemp'})['value'])

	data['humidity_indoor'] = int(soup.find('input', attrs={'name':'inHumi'})['value'])
	data['humidity_outdoor'] = int(soup.find('input', attrs={'name':'outHumi'})['value'])

	data['pressure_absolute'] = float(soup.find('input', attrs={'name':'AbsPress'})['value'])
	data['pressure_relative'] = float(soup.find('input', attrs={'name':'RelPress'})['value'])

	data['wind_direction'] = int(soup.find('input', attrs={'name':'windir'})['value'])
	data['wind_speed'] = float(soup.find('input', attrs={'name':'avgwind'})['value'])
	data['wind_gust'] = float(soup.find('input', attrs={'name':'gustspeed'})['value'])

	data['solar_radiation'] = float(soup.find('input', attrs={'name':'solarrad'})['value'])
	data['uv'] = int(soup.find('input', attrs={'name':'uv'})['value'])
	data['uv_index'] = int(soup.find('input', attrs={'name':'uvi'})['value'])

	data['rain_hourly'] = float(soup.find('input', attrs={'name':'rainofhourly'})['value'])
	data['rain_daily'] = float(soup.find('input', attrs={'name':'rainofdaily'})['value'])
	data['rain_weekly'] = float(soup.find('input', attrs={'name':'rainofweekly'})['value'])
	data['rain_monthly'] = float(soup.find('input', attrs={'name':'rainofmonthly'})['value'])
	data['rain_yearly'] = float(soup.find('input', attrs={'name':'rainofyearly'})['value'])

	try:
		data['pm25_outdoor'] = int(round(float(soup.find('input', attrs={'name':'pm25'})['value'])))
	except:
		print('Failed to retrieve PM2.5 value')
		data['pm25_outdoor'] = None

	return data

def degToCompass(num):
	val=int((num/22.5)+.5)
	arr=["N","NNE","NE","ENE","E","ESE", "SE", "SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
	return arr[(val % 16)]

MM_PER_IN = 25.4

def rebuild_plain_html(data):
	data2 = data.copy()
	# Historic average: 30.268 -- Standard Deviation: 0.416
	data2['pressure_range_min'] = 29.2
	data2['pressure_range_max'] = 31.3
	if data2['pressure_units'] == 'inhg':
		data2['pressure_units'] = 'mmhg'
		data2['pressure_relative'] = round(data2['pressure_relative'] * MM_PER_IN, 1)
		data2['pressure_range_min'] = round(data2['pressure_range_min'] * MM_PER_IN)
		data2['pressure_range_max'] = round(data2['pressure_range_max'] * MM_PER_IN)
		for entry in data2['historic']:
			entry['pressureRelative'] = round(entry['pressureRelative'] * MM_PER_IN, 1)

	data2['aqi_outdoor'] = calculate_aqi(data2['pm25_outdoor'])
	data2['aqi_outdoor_daily_high'] = calculate_aqi(data2['pm25_outdoor_daily_high'])
	data2['aqi_outdoor_daily_low'] = calculate_aqi(data2['pm25_outdoor_daily_low'])
	data2['aqi_text'] = aqi_text(data2['aqi_outdoor'])
	for entry in data2['historic']:
		entry['aqiOutdoor'] = calculate_aqi(entry['pm25Outdoor'])
	data2['temp_units'] = 'F' if data['temp_units'] == 'degF' else 'C'
	data2['wind_direction'] = degToCompass(data['wind_direction'])
	data2['historic'] = json.dumps(data['historic'])
	template = Template(u'''<!DOCTYPE html>
	<head>
		<title>Dickerson Weather</title>
		<meta charset="UTF-8">
	</head>
	<body>
		<h1>Dickerson Weather</h1>
		<h2>${datetime}</h2>

		<h3>Outside</h3>
		<table><tbody>
			<tr><td>Battery Status</td><td>${battery_outdoor}</td><td>&nbsp;</td></tr>
			<tr><td>Temperature</td>
				<td style="text-align:right;">
					Daily High: ${temp_outdoor_daily_high} ${temp_units}
					<br>${temp_outdoor} ${temp_units}
					<br>Daily Low: ${temp_outdoor_daily_low} ${temp_units}
				</td>
				<td><canvas id="tempOutdoor"></canvas></td></tr>
			<tr><td>PM2.5</td>
				<td style="text-align:right;">
					Daily High: ${pm25_outdoor_daily_high} µg/m<sup>3</sup>
					<br>${pm25_outdoor} µg/m<sup>3</sup>
					<br>Daily Low: ${pm25_outdoor_daily_low} µg/m<sup>3</sup>
				</td>
				<td><canvas id="pm25Outdoor" data-min="0"></canvas></td></tr>
			<tr><td>AQI (PM2.5 only)</td>
				<td style="text-align:right;">
					Daily High: ${aqi_outdoor_daily_high}
					<br>${aqi_outdoor}: ${aqi_text}
					<br>Daily Low: ${aqi_outdoor_daily_low}
				</td>
				<td><canvas id="aqiOutdoor" data-min="0"></canvas></td></tr>
			<tr><td>Relative Humidity</td><td>${humidity_outdoor} %</td><td><canvas id="humidityOutdoor" data-min="0" data-max="100"></canvas></td></tr>
			<tr><td>Pressure</td><td>${pressure_relative} ${pressure_units}</td><td><canvas id="pressureRelative" data-min="${pressure_range_min}" data-max="${pressure_range_max}"></canvas></td></tr>
			<tr><td>Wind/Gust</td>
				<td>${wind_speed}/${wind_gust} ${wind_units} ${wind_direction}
					<br>Daily Max: ${wind_gust_daily_max}
				</td>
				<td><canvas id="windSpeed" data-min="0"></canvas></td></tr>
			<tr><td>Solar Radiation</td><td>${solar_radiation} ${solar_radiation_units}</td><td><canvas id="solarRadiation" data-min="0"></canvas></td></tr>
			<tr><td>UV</td><td>${uv} (Index: ${uv_index})</td><td><canvas id="uv" data-min="0"></canvas></td></tr>
			<tr><td>Hourly Rain</td><td>${rain_hourly} ${rain_units}</td><td><canvas id="rainHourly" data-min="0"></canvas></td></tr>
			<tr><td>Daily Rain</td><td>${rain_daily} ${rain_units}</td></tr>
		</tbody></table>

		<h3>Inside</h3>
		<table><tbody>
			<tr><td>Battery Status</td><td>${battery_indoor}</td><td>&nbsp;</td></tr>
			<tr><td>Temperature</td>
				<td style="text-align:right;">
					Daily High: ${temp_indoor_daily_high} ${temp_units}
					<br>${temp_indoor} ${temp_units}
					<br>Daily Low: ${temp_indoor_daily_low} ${temp_units}
				</td>
				<td><canvas id="tempIndoor"></canvas></td></tr>
			<tr><td>Relative Humidity</td><td>${humidity_indoor} %</td><td><canvas id="humidityIndoor"></canvas></td></tr>
		</tbody></table>

		<script src="Chart.bundle.min.js"></script>
		<script>
			(function() {
				"use strict";

				const weatherData = ${historic};

				function buildChart(canvasId, data, xKey, yKey, yKey2) {
					const canvas = document.getElementById(canvasId);
					if (!canvas) {console.log('No element found with ID' + canvasId); return;}
					canvas.style.width = '800px';
					canvas.style.height = '120px';
					const ctx = canvas.getContext('2d');

					const datasets = [];

					let extractedData = [];
					data.forEach(function(entry) {
						extractedData.push({x: entry[xKey], y: entry[yKey]});
					});
					datasets.push({data: extractedData, label: yKey, pointRadius: 0});

					if (yKey2) {
						extractedData = [];
						data.forEach(function(entry) {
							extractedData.push({x: entry[xKey], y: entry[yKey2]});
						});
						datasets.push({data: extractedData, fill: false, label: yKey2, pointRadius: 0});
					}

					const scales = {xAxes: [{type: "time"}]};
					const ticks = {};
					if (canvas.dataset.min) {ticks.min = parseFloat(canvas.dataset.min);}
					if (canvas.dataset.max) {ticks.max = parseFloat(canvas.dataset.max);}
					if (Object.keys(ticks).length > 0) {scales.yAxes = [{ticks}];}

					const myChart = new Chart(ctx, {
						type: 'line',
						data: {datasets: datasets},
						options: {
							legend: {display: false},
							scales,
						}
					});
				}

				buildChart('tempOutdoor', weatherData, 'date', 'tempOutdoor');
				buildChart('pm25Outdoor', weatherData, 'date', 'pm25Outdoor');
				buildChart('aqiOutdoor', weatherData, 'date', 'aqiOutdoor');
				buildChart('humidityOutdoor', weatherData, 'date', 'humidityOutdoor');
				buildChart('pressureRelative', weatherData, 'date', 'pressureRelative');
				buildChart('windSpeed', weatherData, 'date', 'windSpeed', 'windGust');
				buildChart('solarRadiation', weatherData, 'date', 'solarRadiation');
				buildChart('uv', weatherData, 'date', 'uv');
				buildChart('tempIndoor', weatherData, 'date', 'tempIndoor');
				buildChart('humidityIndoor', weatherData, 'date', 'humidityIndoor');
				buildChart('rainHourly', weatherData, 'date', 'rainHourly');
			})();
		</script>
	</body>
	</html>''')
	html = template.substitute(data2)
	with codecs.open(PLAIN_HTML_PATH, 'w', encoding='utf-8') as file:
		file.write(html)

def rebuild_cumulus_txt(data):
	# See http://wiki.sandaysoft.com/a/Realtime.txt
	vals = ['0' for x in range(58)]
	vals[0] = data['datetime'].strftime("%d/%m/%y")
	vals[1] = data['datetime'].strftime("%H:%M:%S")
	vals[2] = data['temp_outdoor']
	vals[3] = data['humidity_outdoor']

	vals[5] = data['wind_speed']

	vals[7] = data['wind_direction']
	vals[8] = data['rain_hourly']
	vals[9] = data['rain_daily']
	vals[10] = data['pressure_relative']
	vals[11] = degToCompass(data['wind_direction'])

	vals[13] = data['wind_units']
	vals[14] = 'F' if data['temp_units'] == 'degF' else 'C'
	vals[15] = 'in' if data['pressure_units'] == 'inhg' else data['pressure_units']
	vals[16] = data['rain_units']

	vals[19] = data['rain_monthly']
	vals[20] = data['rain_yearly']

	vals[22] = data['temp_indoor']
	vals[23] = data['humidity_indoor']

	# Placeholders for missing data
	vals[26] = data['temp_outdoor_daily_high']
	vals[27] = data['temp_outdoor_daily_high_time'].strftime('%H:%M')
	vals[28] = data['temp_outdoor_daily_low']
	vals[29] = data['temp_outdoor_daily_low_time'].strftime('%H:%M')
	vals[30] = data['wind_speed_daily_max']
	vals[31] = data['wind_speed_daily_max_time'].strftime('%H:%M')
	vals[32] = data['wind_gust_daily_max']
	vals[33] = data['wind_gust_daily_max_time'].strftime('%H:%M')
	vals[34] = data['pressure_relative_daily_high']
	vals[35] = data['pressure_relative_daily_high_time'].strftime('%H:%M')
	vals[36] = data['pressure_relative_daily_low']
	vals[37] = data['pressure_relative_daily_low_time'].strftime('%H:%M')
	vals[38] = '1.8.7' # Cumulus Version (?)
	vals[39] = '819' # Cumuls build number (?)
	vals[53] = 'ft' # Cloud base units
	vals[55] = '0' # cumulative hours of sunshine today
	# End Placeholders

	vals[40] = data['wind_gust']

	vals[43] = data['uv_index']

	vals[45] = data['solar_radiation']

	vals[49] = '1' if data['uv'] > 0 else '0' # Is Daylight

	vals[51] = vals[11] # Copy from current wind

	vals[57] = '1' if data['uv'] > 500 else '0' # Is Sunny -- 500 arbitrarily chosen
	with open(CUMULUS_TXT_PATH, 'w') as file:
		file.write(' '.join([str(x) for x in vals]))


def get_aqi_breakpoints(pm25):
	if pm25 <= 12.0:
		return {'c_low': 0, 'c_high': 12, 'i_low': 0, 'i_high': 50}
	if pm25 <= 35.4:
		return {'c_low': 12.1, 'c_high': 35.4, 'i_low': 51, 'i_high': 100}
	if pm25 <= 55.4:
		return {'c_low': 35.5, 'c_high': 55.4, 'i_low': 101, 'i_high': 150}
	if pm25 <= 150.4:
		return {'c_low': 55.5, 'c_high': 150.4, 'i_low': 151, 'i_high': 200}
	if pm25 <= 250.4:
		return {'c_low': 150.5, 'c_high': 250.4, 'i_low': 201, 'i_high': 300}
	if pm25 <= 350.4:
		return {'c_low': 250.5, 'c_high': 350.4, 'i_low': 301, 'i_high': 400}
	else:
		return {'c_low': 350.5, 'c_high': 500.4, 'i_low': 401, 'i_high': 500}


def aqi_text(aqi):
	if aqi is None:
		return "Unknown"
	if aqi <= 50:
		return "Good"
	if aqi <= 100:
		return "Moderate"
	if aqi <= 150:
		return "USG"
	if aqi <= 200:
		return "Unhealthy"
	if aqi <= 300:
		return "Very Unhealthy"
	else:
		return "Hazardous"


def calculate_aqi(pm25):
	# pm25 in micrograms per cubic meter
	if pm25 is None:
		return None
	breakpoints = get_aqi_breakpoints(pm25)
	aqi = breakpoints['i_high'] - breakpoints['i_low']
	aqi = aqi / (breakpoints['c_high'] - breakpoints['c_low'])
	aqi = aqi * (pm25 - breakpoints['c_low'])
	return round(aqi + breakpoints['i_low'])


if __name__ == "__main__":
	try:
		data = fetch_data()
	except Exception as e:
		print("%s: Data Fetch Failed" % datetime.today())
		print(e)
		sys.exit(1)

	try:
		update_database(data)
	except Exception as e:
		print("%s: DB Update Failed: " % datetime.today())
		print(e)

	try:
		rebuild_cumulus_txt(data)
	except Exception as e:
		print("%s: Cumulus TXT Rebuild Failed" % datetime.today())
		print(e)

	try:
		rebuild_plain_html(data)
	except Exception as e:
		print("%s: Plain HTML Rebuild Failed" % datetime.today())
		print(e)
