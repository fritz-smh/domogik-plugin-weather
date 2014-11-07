#!/usr/bin/python
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

Weather

Implements
==========

- WeatherManager

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2014 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.xplmessage import XplMessage
from domogik.xpl.common.plugin import XplPlugin

from domogik_packages.plugin_weather.lib.weather import Weather
#from domogik_packages.plugin_weather.lib.weather import WeatherException
import threading
import traceback


class WeatherManager(XplPlugin):
    """ Get weather informations
    """

    def __init__(self):
        """ Init plugin
        """
        XplPlugin.__init__(self, name='weather')

        # check if the plugin is configured. If not, this will stop the plugin and log an error
        #if not self.check_configured():
        #    return

        # get the devices list
        # for this plugin, if no devices are created we won't be able to use devices.
        self.devices = self.get_device_list(quit_if_no_device = True)


        self.weather_manager = Weather(self.log, 
                                       self.send_xpl_sensor_basic, 
                                       self.send_xpl_weather_forecast, 
                                       self.get_stop(), 
                                       self.get_parameter_for_feature)
        # Start getting weather informations
        weather_process = threading.Thread(None,
                                    self.weather_manager.start_loop,
                                    "weather-process",
                                    (self.devices,),
                                    {})
        self.register_thread(weather_process)
        weather_process.start()

        self.ready()

    def send_xpl_sensor_basic(self, w_device, w_type, w_value):
        """ Send xPL message on network
        """
        self.log.debug(u"Values for {0} on {1} : {2}".format(w_device, w_type, w_value))
        if w_value == "" or w_value is None:
            self.log.warning("Empty value for {0} on {1}. The xPL message will not be sent".format(w_device, w_type))
            return
        msg = XplMessage()
        msg.set_type("xpl-stat")
        msg.set_schema("sensor.basic")
        msg.add_data({"device" : w_device})
        msg.add_data({"type" : w_type})
        msg.add_data({"current" : w_value})
        self.myxpl.send(msg)

    def send_xpl_weather_forecast(self, data):
        """ Send xPL message on network
        """
        self.log.debug(u"Forecast data : {0}".format(data))
        msg = XplMessage()
        msg.set_type("xpl-stat")
        msg.set_schema("weather.forecast")
        msg.add_data({"provider" : "weather.com"})
        for key in data:
            val = data[key]
            if val != "":
                msg.add_data({key : val})
        self.myxpl.send(msg)

if __name__ == "__main__":
    WeatherManager()
