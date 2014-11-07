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

Sent weather informations from weather.com

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
import domogik_packages.plugin_weather.lib.pywapi as pywapi
import pprint


class Weather:
    """ Weather.com
    """

    def __init__(self, log, callback_sensor_basic, callback_weather_forecast, stop, get_parameter_for_feature):
        """ Init Disk object
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
        self._interval = 30 # minutes

    def start_loop(self, devices):
        while not self._stop.isSet():
            try:
                self.get_weather(devices)
            except:
                self.log.error(u"Error while call get_weather : {1}".format(traceback.format_exc()))
            self.log.info("Wait for {0} minutes".format(self._interval))
            self._stop.wait(self._interval*60)

    def get_weather(self, devices):
        for a_device in devices:
            try: 
                ### Grab data
                # get the device address in the 'current_temperature' sensor. Keep in mind that all the sensors 
                # for the device type 'weather.weather' has the same address, so we can take the one we want!
                address = self._get_parameter_for_feature(a_device, "xpl_stats", "current_temperature", "device")
                self.log.info("Start getting weather for {0} ({1})".format(a_device['name'], address))

                # grab weather.com data
                data = pywapi.get_weather_from_weather_com(address) 
                self.log.debug("Raw data for {0} : {1}".format(address, data))

                ### send current data over xPL
                cur = data['current_conditions']
                # current_barometer_value
                self._callback_sensor_basic(address, "pressure", cur['barometer']['reading'])
                # current_barometer_direction
                self._callback_sensor_basic(address, "barometer_direction", cur['barometer']['direction'])
                # current_dewpoint
                self._callback_sensor_basic(address, "temp_dewpoint", cur['dewpoint'])
                # current_feels_like
                self._callback_sensor_basic(address, "temp_feels_like", cur['feels_like'])
                # current_humidity
                self._callback_sensor_basic(address, "humidity", cur['humidity'])
                # current_last_updated
                self._callback_sensor_basic(address, "last_updated", cur['last_updated'])
                # current_moon_phase
                self._callback_sensor_basic(address, "moon_phase", cur['moon_phase']['text'])
                # current_station
                self._callback_sensor_basic(address, "current_station", cur['station'])
                # current_temperature
                self._callback_sensor_basic(address, "temp", cur['temperature'])
                # current_text
                self._callback_sensor_basic(address, "text", cur['text'])
                # current_uv
                self._callback_sensor_basic(address, "uv", cur['uv']['index'])
                # current_visibility
                self._callback_sensor_basic(address, "visibility", cur['visibility'])
                # current_wind_direction
                self._callback_sensor_basic(address, "direction", cur['wind']['direction'])
                # current_wind_gust
                self._callback_sensor_basic(address, "speed_gust", cur['wind']['gust'])
                # current_wind_speed"],
                self._callback_sensor_basic(address, "speed", cur['wind']['speed'])
                # current_wind_text"],
                self._callback_sensor_basic(address, "wind_text", cur['wind']['text'])

                ### send forecast data over xPL
                day_num = 0
                for day in data['forecasts']:
                    print day
                    data = {'day' : day_num,
                            'device' : address,
                            'day-name' : day['day_of_week'],
                            'temperature-high' : day['high'],
                            'temperature-low' : day['low'],
                            'sunset' : day['sunset'],
                            'sunrise' : day['sunrise'],
                            'day-humidity' : day['day']['humidity'],
                            'day-text' : day['day']['text'],
                            'day-precip' : day['day']['chance_precip'],
                            'night-humidity' : day['night']['humidity'],
                            'night-text' : day['night']['text'],
                            'night-precip' : day['night']['chance_precip']}
                    self._callback_weather_forecast(data)
                    day_num += 1

                self.log.info("Data successfully sent for {0}".format(address))
            except:
                self.log.error("Error while getting data from weather.com : {0}".format(traceback.format_exc()))
