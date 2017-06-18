#!/usr/bin/python

import sqlite3
import urllib2
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta
import sys
from string import Template

DB_PATH = '/home/kyle/weather/weather.db'
SENSOR_URL = 'http://weather/livedata.htm'
UNITS_URL = 'http://weather/station.htm'
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
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	""", ordered_data)

	db.commit()
	fetch_aggregate_data(data, cursor)
	db.close()

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

	response = urllib2.urlopen(UNITS_URL).read()
	soup = BeautifulSoup(response, 'html.parser')

	data['wind_units'] = soup.find('select', attrs={'name':'unit_Wind'}).find('option', selected=True).string
	data['rain_units'] = soup.find('select', attrs={'name':'u_Rainfall'}).find('option', selected=True).string
	data['pressure_units'] = soup.find('select', attrs={'name':'unit_Pressure'}).find('option', selected=True).string 
	data['temp_units'] = soup.find('select', attrs={'name':'u_Temperature'}).find('option', selected=True).string
	data['solar_radiation_units'] = soup.find('select', attrs={'name':'unit_Solar'}).find('option', selected=True).string

	response = urllib2.urlopen(SENSOR_URL).read()
	soup = BeautifulSoup(response, 'html.parser')
	
	data['datetime'] = datetime.strptime(soup.find('input', attrs={'name':'CurrTime'})['value'], '%H:%M %m/%d/%Y')

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

	return data

def degToCompass(num):
    val=int((num/22.5)+.5)
    arr=["N","NNE","NE","ENE","E","ESE", "SE", "SSE","S","SSW","SW","WSW","W","WNW","NW","NNW"]
    return arr[(val % 16)]

def rebuild_plain_html(data):
	data2 = data.copy()
	data2['temp_units'] = 'F' if data['temp_units'] == 'degF' else 'C'
	data2['wind_direction'] = degToCompass(data['wind_direction'])
	template = Template('''<html>
	<head>
		<title>Dickerson Weather</title>
	</head>
	<body>
		<h1>Dickerson Weather</h1>
		<h2>${datetime}</h2>

		<h3>Outside</h3>
		<table><tbody>
			<tr><td>Temperature</td><td>${temp_outdoor} ${temp_units}</td></tr>
			<tr><td>Daily High</td><td>${temp_outdoor_daily_high} ${temp_units}</td></tr>
			<tr><td>Daily Low</td><td>${temp_outdoor_daily_low} ${temp_units}</td></tr>
			<tr><td>Relative Humidity</td><td>${humidity_outdoor} %</td></tr>
			<tr><td>Pressure</td><td>${pressure_relative} ${pressure_units}</td></tr>
			<tr><td>Wind</td><td>${wind_speed} ${wind_units} ${wind_direction}</td></tr>
			<tr><td>Solar Radiation</td><td>${solar_radiation} ${solar_radiation_units}</td></tr>
			<tr><td>UV</td><td>${uv} (Index: ${uv_index})</td></tr>
			<tr><td>Hourly Rain</td><td>${rain_hourly} ${rain_units}</td></tr>
			<tr><td>Daily Rain</td><td>${rain_daily} ${rain_units}</td></tr>
		</tbody></table>

		<h3>Inside</h3>
		<table><tbody>
			<tr><td>Temperature</td><td>${temp_indoor} ${temp_units}</td></tr>
			<tr><td>Daily High</td><td>${temp_indoor_daily_high} ${temp_units}</td></tr>
			<tr><td>Daily Low</td><td>${temp_indoor_daily_low} ${temp_units}</td></tr>
			<tr><td>Relative Humidity</td><td>${humidity_indoor} %</td></tr>
		</tbody></table>
	</body>
	</html>''')
	html = template.substitute(data2)
	with open(PLAIN_HTML_PATH, 'w') as file:
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

