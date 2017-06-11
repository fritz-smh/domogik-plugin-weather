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
@copyright: (C) 2007-2017 Domogik project
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

def mph_to_kmh(s):
    # yahoo return some values in mph but in fact they are in km/h... so I commented the conversion
    #return float(s)/1.6093
    return float(s)

def fahrenheit_to_celcius(f):
    # convert fahrenheit to celcius
    return "{0:.0f}".format((float(f)-32)/1.8)

class Weather:
    """ Weather.com
    """

    def __init__(self, log, callback_send_sensor, stop, get_parameter):
        """ Init Weather object
            @param log : log instance
            @param callback_send_sensor : callback to send valeus to domogik
            @param stop : Event of the plugin to handle plugin stop
            @param get_parameter : a callback to a plugin core function
        """
        self.log = log
        self._callback_send_sensor = callback_send_sensor
        self._stop = stop
        self._get_parameter = get_parameter
        # the interval is hardcoded as we use an online service
        self._interval = 15 # minutes
        self.reload_request = True

    def set_devices(self, devices):
        """ Called by the bin part when starting or devices added/deleted/updated
        """
        self.devices = devices
        # to restart the loop
        self.reload_request = True

        self.log.info(u"Devices reloaded. The new devices will be checked in less than 30 seconds.")

    def start_loop(self):
        # To allow a quick devices reload, we split the X minutes interval in smaller interval.

        num_30seconds = 0
        max_num_30seconds = self._interval * 2
        while not self._stop.isSet():
            try:
                num_30seconds += 1
                if num_30seconds >= max_num_30seconds or self.reload_request:
                    num_30seconds = 0
                    self.reload_request = False
                    self.get_weather()
                    self.log.info(u"Wait for {0} minutes (unless some device change happen)".format(self._interval))
            except:
                self.log.error(u"Error while calling get_weather : {0}".format(traceback.format_exc()))
            self._stop.wait(30)

    def get_weather(self):
        for a_device in self.devices:
            nb_try = 0
            max_try = 3
            ok = False
            while nb_try < max_try and not ok:
                # as some time yahoo returns some empty result, we try several times with a small delay between the tries
                nb_try += 1

                try: 
                    ### Grab data
                    # get the device address in the 'current_temperature' sensor. Keep in mind that all the sensors 
                    # for the device type 'weather.weather' has the same address, so we can take the one we want!
                    address = self._get_parameter(a_device, "device")
                    if address == None:
                        self.log.warning(u"You may still have old devices for this plugin. This plugin have been migrated to no xpl since the release 1.8. Please delete the old devices and create new ones")
                        continue

                    self.log.info(u"Start getting weather for {0} ({1}). Try number '{2}/{3}'".format(a_device['name'], address, nb_try, max_try))
    
                    # grab weather data
    
                    # More informations here : https://developer.yahoo.com/weather/#get-started
                    # 04/2016 : we do the query in the english metric and convert them manually instead of doing the query in metric system
                    # We do this because yahoo weather was giving badly converted values in metric system
                    query = "select * from weather.forecast where woeid = {0} and u = 'f'".format(address)
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
                        continue
    
    
                    ### send current data over xPL
                    if (data['query']['results'] == None):
                        self.log.warning(u"The data returned by Yahoo is empty. This happens... not sure why, but this happens :(. Waiting 10 seconds before retrying...")

                        if nb_try != max_try:
                            self._stop.wait(10)
                        continue

                    ok = True
    
    
    
                    cur = data['query']['results']['channel']
    
                    try:
                        sunset_time = None
                        sunrise_time = None

                        # current_sunset
                        sunset = cur['astronomy']['sunset']
                        sunset_time = self.convert_to_24(sunset)
    
                        # current_sunrise
                        sunrise = cur['astronomy']['sunrise']
                        sunrise_time = self.convert_to_24(sunrise)
                    except:
                        self.log.error(u"Error while getting sunset and sunrise times... This may occur with API changes") 
                        # it happened several time.... cf fixes in releases 1.7 and 1.9
    
    
                    ### send_data
                    self._callback_send_sensor(a_device['id'], 
                                                       { 'current_barometer_value' :  cur['atmosphere']['pressure'],
                                                         'current_feels_like' :  fahrenheit_to_celcius(cur['wind']['chill']),
                                                         'current_humidity' :  cur['atmosphere']['humidity'],
                                                         'current_last_updated' :  cur['lastBuildDate'],
                                                         'current_station' :  "{0} ({1})".format(cur['location']['city'], cur['location']['country']),
                                                         'current_temperature' :  fahrenheit_to_celcius(cur['item']['condition']['temp']),
                                                         'current_text' :  cur['item']['condition']['text'],
                                                         'current_code' :  cur['item']['condition']['code'],
                                                         'current_visibility' :  mph_to_kmh(cur['atmosphere']['visibility']),
                                                         'current_wind_direction' :  cur['wind']['direction'],
                                                         'current_wind_speed' :  mph_to_kmh(cur['wind']['speed']),
                                                         'current_sunset' :  sunset_time,
                                                         'current_sunrise' :  sunrise_time
                                                       })



                    ### send forecast data 
                    day_num = 0
                    for day in data['query']['results']['channel']['item']['forecast']:
                        num = day_num
                        data = {'forecast_{0}_day'.format(num) : day['day'],
                                'forecast_{0}_temperature_high'.format(num) : fahrenheit_to_celcius(day['high']),
                                'forecast_{0}_temperature_low'.format(num) : fahrenheit_to_celcius(day['low']),
                                'forecast_{0}_condition_text'.format(num) : day['text'],
                                'forecast_{0}_condition_code'.format(num) : day['code']}
                        self._callback_send_sensor(a_device['id'], data)
                        day_num += 1
    
                    self.log.info(u"Data successfully sent for {0}".format(address))
                except:
                    self.log.error(u"Error while getting data from Yahoo weather : {0}".format(traceback.format_exc()))

    def convert_to_24(self,time):
        """Converts 12 hours time format to 24 hours
        """
        time = time.replace(' ', '')
        time, half_day = time[:-2], time[-2:].lower()
        hours, minutes = time.split(":")
        if int(minutes) < 10:
            minutes = "0" + time[2:]
        if half_day == 'am':
            return str(time[:2] + minutes)
        elif half_day == 'pm':
            split = time.find(':')
            if split == -1:
                split = None
            return str(int(time[:split]) + 12) + ":" +minutes
        else:
            raise ValueError("Didn't finish with AM or PM.")

