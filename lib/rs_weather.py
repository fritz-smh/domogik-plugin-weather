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

Librairy for the weather brain part

Implements
==========

@author: Fritz <fritz.smh@gmail.com>
@copyright: (C) 2007-2015 Domogik project
@license: GPL(v3)
@organization: Domogik
"""

from domogik.butler.brain import get_sensor_value
import datetime

def get_forecast(cfg_i18n, args, log):
    """ Function for the brain part
    """

    # i18n
    locale = cfg_i18n['locale']
    condition_text_list = cfg_i18n['condition_text_list']
    days_absolute = cfg_i18n['days_absolute']
    days_relative = cfg_i18n['days_relative']
    ERROR_UNKNOWN_DAY = cfg_i18n['ERROR_UNKNOWN_DAY']
    ERROR_UNKNOWN_LOCATION = cfg_i18n['ERROR_UNKNOWN_LOCATION']
    SEPARATOR = cfg_i18n['SEPARATOR']
    TXT_IN_LOCATION = cfg_i18n['TXT_IN_LOCATION']
    TXT_CONDITION_AND_TEMPERATURES = cfg_i18n['TXT_CONDITION_AND_TEMPERATURES']


    tab_args = ' '.join(args).split(SEPARATOR)
    day = tab_args[0]
    # si on ne precise pas le lieu, on suppose qu'un seul device existe
    if len(tab_args) == 1:
        device_name = None
    else:
        device_name = tab_args[1]
    
    # if the user give a fullname day... we translate to a number
    if day in days_absolute:
        current_day = datetime.datetime.today().weekday()
        day = (days_absolute[day] - current_day) % 7

    # if the user five a full relative day... we translate to a number
    if day in days_relative:
        day = days_relative[day]

    # we check if we are able to give the information about the requested day
    try:
        day = int(day)
        print(day)
    except:
        import traceback
        print(traceback.format_exc())
        return ERROR_UNKNOWN_DAY
    if day not in [0, 1, 2, 3, 4]:
        return ERROR_UNKNOWN_DAY
        


    temp_high = get_sensor_value(log, locale, "DT_Temp", device_name, "forecast_{0}_temperature_high".format(day))
    # no such device
    if temp_high == None:
        return ERROR_UNKNOWN_LOCATION

    temp_low = get_sensor_value(log, locale, "DT_Temp", device_name, "forecast_{0}_temperature_low".format(day))
    condition_code = get_sensor_value(log, locale, "DT_String", device_name, "forecast_{0}_condition_code".format(day))
    condition_text = condition_text_list[int(condition_code)]

    # find the day label
    for a_day in days_relative:
        if days_relative[a_day] == day:
            day_label = a_day
            break

    # i18n
    txt = u"{0}, ".format(day_label)
    if device_name != None:
        txt += TXT_IN_LOCATION.format(device_name)
    txt += TXT_CONDITION_AND_TEMPERATURES.format(condition_text, temp_low, temp_high)

    return txt



