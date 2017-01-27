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
@copyright: (C) 2007-2017 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.xpl.common.plugin import Plugin

from domogik_packages.plugin_weather.lib.weather import Weather
#from domogik_packages.plugin_weather.lib.weather import WeatherException
import threading
import traceback


class WeatherManager(Plugin):
    """ Get weather informations
    """

    def __init__(self):
        """ Init plugin
        """
        Plugin.__init__(self, name='weather')

        # check if the plugin is configured. If not, this will stop the plugin and log an error
        #if not self.check_configured():
        #    return

        # get the devices list
        # for this plugin, if no devices are created we won't be able to use devices.
        self.devices = self.get_device_list(quit_if_no_device = True)
        self.sensors = self.get_sensors(self.devices)

        # Init the weather manager
        self.need_reload = threading.Event()
        self.weather_manager = Weather(self.log, 
                                       self.send_sensor,
                                       self.get_stop(), 
                                       self.get_parameter)
        self.weather_manager.set_devices(self.devices)

        # Start a thread to get weather informations
        weather_process = threading.Thread(None,
                                    self.weather_manager.start_loop,
                                    "weather-process",
                                    (),
                                    {})
        self.register_thread(weather_process)
        weather_process.start()

        # Call the start_engine function when there is some device added/deleted/updated
        self.register_cb_update_devices(self.reload_devices)
       

        self.ready()


    def reload_devices(self, devices):
        """ Called on startup or when some devices are added/deleted/updated
        """
        self.weather_manager.set_devices(devices)
        self.devices = devices
        self.sensors = self.get_sensors(devices)



    def send_sensor(self, device_id, sensor_values):
        """Send pub message over MQ
           @device_address : the device id
           @device_address : the sensor values : {'name' : value}
        """
        data = {}
        value = None
        try:
            for a_sensor in sensor_values:
                sensor_id = self.sensors[device_id][a_sensor]
                value = sensor_values[a_sensor]
                self.log.info(u"Preparing to send value for sensor id:{0}, name: {1}, value: {2}" .format(sensor_id, a_sensor, value))
                data[sensor_id] = value
        except:
            self.log.error(u"An error occured while preparing the sensor '{0}' value '{1}' to be send. The error is : {2}".format(a_sensor, value, traceback.format_exc()))
        self._pub.send_event('client.sensor', data)


if __name__ == "__main__":
    WeatherManager()
