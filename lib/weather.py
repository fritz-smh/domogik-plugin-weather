# -*- coding: utf-8 -*-

""" This file is part of B{Domogik} project (U{http://www.domogik.org}).

License
=======

B{Domogik} is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

B{Domogik} is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Domogik. If not, see U{http://www.gnu.org/licenses}.

Plugin purpose
==============

Sent weather informations from yahoo weather

Implements
==========

- Weather

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2014 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

import os
import traceback
import json
import time
# python 2 and 3
try:
    from urllib.request import urlopen
except ImportError:
    from urllib import urlopen

YAHOO_WEATHER_URL = "https://query.yahooapis.com/v1/public/yql?q="

class Weather:
    """ Weather.com
    """

    def __init__(self, log, callback_sensor_basic, callback_weather_forecast, stop, get_parameter_for_feature):
        """ Init Weather object
            @param log : log instance
            @param callback_sensor_basic : callback to send a sensor.basic xpl message
            @param callback_weather_forecast : callback to send a weather.forecast xpl message
        """
        self.log = log
        self._callback_sensor_basic = callback_sensor_basic
        self._callback_weather_forecast = callback_weather_forecast
        self._stop = stop
        self._get_parameter_for_feature = get_parameter_for_feature
        # the interval is hardcoded as we use an online service
        self._interval = 15 # minutes

    def start_loop(self, devices):
        while not self._stop.isSet():
            try:
                self.get_weather(devices)
            except:
                self.log.error(u"Error while call get_weather : {1}".format(traceback.format_exc()))
            self.log.info(u"Wait for {0} minutes".format(self._interval))
            self._stop.wait(self._interval*60)

    def get_weather(self, devices):
        for a_device in devices:
            try: 
                ### Grab data
                # get the device address in the 'current_temperature' sensor. Keep in mind that all the sensors 
                # for the device type 'weather.weather' has the same address, so we can take the one we want!
                address = self._get_parameter_for_feature(a_device, "xpl_stats", "current_temperature", "device")
                self.log.info(u"Start getting weather for {0} ({1})".format(a_device['name'], address))

                # grab weather data

                # More informations here : https://developer.yahoo.com/weather/#get-started
                query = "select * from weather.forecast where woeid = {0} and u = 'c'".format(address)
                weather_url = "{0}{1}&format=json".format(YAHOO_WEATHER_URL, query)
                self.log.debug(u"Url called is {0}".format(weather_url))
                response = urlopen(weather_url)
                raw_data = response.read().decode('utf-8')
                data = json.loads(raw_data)
                self.log.debug(u"Raw data for {0} : {1}".format(address, data))

                # Check that the location is a good one !
                # Example of a response to a bad location code : Raw data for BEXX0032 : {u'error': {u'lang': u'en-US', u'description': u'Invalid identfier BEXX0032. me AND me.ip are the only supported identifier in this context'}}
                if 'error' in data:
                    self.log.error("Error raised by Yahoo weather : {0}".format(data['error']))
                    return


                ### send current data over xPL
                cur = data['query']['results']['channel']
                # current_barometer_value
                # weather.com # self._callback_sensor_basic(address, "pressure", cur['barometer']['reading'])
                self._callback_sensor_basic(address, "pressure", cur['atmosphere']['pressure'])

                # current_barometer_direction
                # weather.com # self._callback_sensor_basic(address, "barometer_direction", cur['barometer']['direction'])
                # yahoo weather # N/A

                # current_dewpoint
                # weather.com # self._callback_sensor_basic(address, "temp_dewpoint", cur['dewpoint'])
                # yahoo weather # N/A

                # current_feels_like
                # weather.com # self._callback_sensor_basic(address, "temp_feels_like", cur['feels_like'])
                self._callback_sensor_basic(address, "temp_feels_like", cur['wind']['chill'])

                # current_humidity
                # weather.com # self._callback_sensor_basic(address, "humidity", cur['humidity'])
                self._callback_sensor_basic(address, "humidity", cur['atmosphere']['humidity'])

                # current_last_updated
                # weather.com # self._callback_sensor_basic(address, "last_updated", cur['last_updated'])
                self._callback_sensor_basic(address, "last_updated", cur['lastBuildDate'])

                # current_moon_phase
                # weather.com # self._callback_sensor_basic(address, "moon_phase", cur['moon_phase']['text'])
                # yahoo weather # N/A

                # current_station
                # weather.com # self._callback_sensor_basic(address, "current_station", cur['station'])
                self._callback_sensor_basic(address, "current_station", "{0} ({1})".format(cur['location']['city'], cur['location']['country']))

                # current_temperature
                # weather.com # self._callback_sensor_basic(address, "temp", cur['temperature'])
                self._callback_sensor_basic(address, "temp", cur['item']['condition']['temp'])

                # current_text
                # weather.com # self._callback_sensor_basic(address, "text", cur['text'])
                self._callback_sensor_basic(address, "text", cur['item']['condition']['text'])

                # current_code
                # weather.com # N/A
                self._callback_sensor_basic(address, "code", cur['item']['condition']['code'])

                # current_uv
                # weather.com # self._callback_sensor_basic(address, "uv", cur['uv']['index'])
                # yahoo weather # N/A

                # current_visibility
                # weather.com # self._callback_sensor_basic(address, "visibility", cur['visibility'])
                self._callback_sensor_basic(address, "visibility", cur['atmosphere']['visibility'])

                # current_wind_direction
                # weather.com # self._callback_sensor_basic(address, "direction", cur['wind']['direction'])
                self._callback_sensor_basic(address, "direction", cur['wind']['direction'])

                # current_wind_gust
                # weather.com # self._callback_sensor_basic(address, "speed_gust", cur['wind']['gust'])
                # yahoo weather # N/A

                # current_wind_speed
                # weather.com # self._callback_sensor_basic(address, "speed", cur['wind']['speed'])
                self._callback_sensor_basic(address, "speed", cur['wind']['speed'])

                # current_wind_text
                # weather.com # self._callback_sensor_basic(address, "wind_text", cur['wind']['text'])
                # yahoo weather # N/A

                # current_sunset
                # weather.com # self._callback_sensor_basic(address, "wind_text", cur['wind']['text'])
                #self._callback_sensor_basic(address, "sunset", cur['astronomy']['sunset'])
                sunset = cur['astronomy']['sunset']
                sunset_time = time.strftime("%H:%M:%S", time.strptime(sunset, "%I:%M %p"))
                self._callback_sensor_basic(address, "sunset", sunset_time)

                # current_sunrise
                # weather.com # self._callback_sensor_basic(address, "wind_text", cur['wind']['text'])
                #self._callback_sensor_basic(address, "sunrise", cur['astronomy']['sunrise'])
                sunrise = cur['astronomy']['sunrise']
                sunrise_time = time.strftime("%H:%M:%S", time.strptime(sunrise, "%I:%M %p"))
                self._callback_sensor_basic(address, "sunrise", sunrise_time)


                ### send forecast data over xPL
                day_num = 0
                for day in data['query']['results']['channel']['item']['forecast']:
                    print day
                    data = {'day' : day_num,
                            'device' : address,
                            'day-name' : day['day'],
                            'temperature-high' : day['high'],
                            'temperature-low' : day['low'],
                            'condition-text' : day['text'],
                            'condition-code' : day['code']}
                    self._callback_weather_forecast(data)
                    day_num += 1

                self.log.info(u"Data successfully sent for {0}".format(address))
            except:
                self.log.error(u"Error while getting data from Yahoo weather : {0}".format(traceback.format_exc()))
