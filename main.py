"""
# BSD 3-Clause License
# Copyright (c) 2022, Thomas Breitbach https://github.com/TomBric
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE

"""


from machine import ADC, Pin
import uasyncio
import display
import async_button
import time
from micropython import const
import config
import json


SET_TIME_MS = const(10000)      # time for two subsequent long presses before going into setup mode
DISPLAY_WAKEUP = const(50)      # number of refreshs after start, to get better contrast on the display
DIVIDER_R1 = 10000               # resistance in Ohms of R1 resistor connected to main power
DIVIDER_R2 = 1000                # resistance in Ohms of R2 resistor of voltage divider
VOLTAGE_FACTOR = 3.3 / 65536
RUDDER_TRIM = True              # True if also rudder trim is desired

# GLOBALS
start = time.ticks_ms()
user_status = 0
trim_value = 0
rudder_value = 0
main_power = 0   # power voltage of aircraft
trim_default = {'full_up': -100, 'neutral': 0, 'full_down': 100, 'rudder_left': -100, 'rudder_neutral': 0,
                'rudder_right': 100}
# settings for trim, initialized during setup (highest up, neutral, highest down)
trim_settings = {}
display_wakeup = DISPLAY_WAKEUP
led_onboard = Pin(25, Pin.OUT)


def calc_display_percent(value):
    diff = abs(trim_settings['neutral'] - value)
    if trim_settings['neutral'] > trim_settings['full_up']:  # full up is  lowest value
        if trim_value <= trim_settings['neutral']:  # positive trim
            display_percent = round(diff / (trim_settings['neutral'] - trim_settings['full_up']) * 100)
        else:  # negative trim
            display_percent = - round(diff / (trim_settings['full_down'] - trim_settings['neutral']) * 100)
    else:  # full down is lowest value
        if trim_value >= trim_settings['neutral']:  # positive trim
            display_percent = round(diff / (trim_settings['full_up'] - trim_settings['neutral']) * 100)
        else:  # negative trim
            display_percent = - round(diff / (trim_settings['neutral'] - trim_settings['full_down']) * 100)
    if display_percent > 100:
        return 100
    elif display_percent < -100:
        return -100
    return display_percent


def calc_rudder_percent(value):
    diff = abs(trim_settings['rudder_neutral'] - value)
    if trim_settings['rudder_neutral'] > trim_settings['rudder_left']:  # left is  lowest value
        if trim_value <= trim_settings['rudder_neutral']:
            percent = round(diff / (trim_settings['rudder_neutral'] - trim_settings['rudder_left']) * 100)
        else:  # negative trim
            percent = - round(diff / (trim_settings['rudder_right'] - trim_settings['rudder_neutral']) * 100)
    else:  # full down is lowest value
        if trim_value >= trim_settings['rudder_neutral']:  # positive trim
            percent = round(diff / (trim_settings['rudder_left'] - trim_settings['rudder_neutral']) * 100)
        else:  # negative trim
            percent = - round(diff / (trim_settings['rudder_neutral'] - trim_settings['rudder_right']) * 100)
    if percent > 100:
        return 100
    elif percent < -100:
        return -100
    return percent


async def display_driver():
    global display_wakeup
    global led_onboard

    old_value = 0
    old_rudder_value = 0
    print('Display driver running.')
    d = display.Display(RUDDER_TRIM)
    await uasyncio.sleep_ms(100)  # wait for other coros to finish their measurements
    while True:
        # print('Display driver: user status {:2d}'.format(user_status))
        if user_status == 0 or user_status == 1:
            display_percent = calc_display_percent(trim_value)
            rudder_percent = calc_rudder_percent(rudder_value)
            if display_percent != old_value or rudder_percent != old_rudder_value or display_wakeup > 0:
                led_onboard.off()   # do some flicker
                old_value = display_percent
                old_rudder_value = rudder_percent
                display_wakeup -= 1
                d.indicator(display_percent, rudder_percent, main_power, user_status)
                d.print()
                led_onboard.on()
            else:
                await uasyncio.sleep_ms(50)
        elif user_status == 2:   # setup trim full up
            d.indicator(100, 0, main_power, user_status)
            d.print()
        elif user_status == 3:   # setup trim neutral
            d.indicator(0, 0, main_power, user_status)
            d.print()
        elif user_status == 4:    # setup trim full down
            d.indicator(-100, 0, main_power, user_status)
            d.print()
        elif user_status == 5:    # setup rudder trim full left
            d.indicator(0, 100, main_power, user_status)
            d.print()
        elif user_status == 6:    # setup rudder trim neutral
            d.indicator(0, 0, main_power, user_status)
            d.print()
        elif user_status == 7:    # setup rudder trim full right
            d.indicator(0, -100, main_power, user_status)
            d.print()

        while d.busy():
            await uasyncio.sleep_ms(50)


def pin_press():
    global user_status
    global start
    global display_wakeup

    # print('Long pin pressed')
    display_wakeup = 1

    if user_status == 0:
        start = time.ticks_ms()  # get millisecond counter
        user_status = 1
    elif user_status == 1:
        user_status = 2


def pin_press_short():
    global new_trim
    global user_status
    global trim_settings
    global trim_value
    global display_wakeup

    # print('Short pin pressed. User status was {:2d} trim_value {:2d}'.format(user_status, trim_value))
    display_wakeup = 1
    if user_status == 2:     # start setup sequence, highest trim up
        new_trim = trim_settings.copy()  # start with old values
        new_trim['full_up'] = trim_value
        user_status = 3
    elif user_status == 3:   # neutral
        new_trim['neutral'] = trim_value
        user_status = 4
    elif user_status == 4:    # trim down
        new_trim['full_down'] = trim_value
        # set new trim values, do a sanity check, that neutral is between the two values
        if new_trim['full_down'] > new_trim['neutral'] > new_trim['full_up'] or \
                new_trim['full_down'] < new_trim['neutral'] < new_trim['full_up']:
            trim_settings = new_trim.copy()
            config.save(trim_settings)
            print('Setting new trim settings: {:s}'.format(json.dumps(trim_settings)))
        if RUDDER_TRIM:
            user_status = 5
        else:
            user_status = 0
    elif user_status == 5:     # highest right
        new_trim['rudder_right'] = rudder_value
        user_status = 6
    elif user_status == 6:   # neutral
        new_trim['rudder_neutral'] = rudder_value
        user_status = 7
    elif user_status == 7:    # highest left
        new_trim['rudder_left'] = rudder_value
        # set new trim values, do a sanity check, that neutral is between the two values
        if new_trim['rudder_left'] > new_trim['rudder_neutral'] > new_trim['rudder_right'] or \
                new_trim['rudder_left'] < new_trim['rudder_neutral'] < new_trim['rudder_right']:
            trim_settings = new_trim.copy()
            config.save(trim_settings)
            print('Setting new trim settings: {:s}'.format(json.dumps(trim_settings)))
        user_status = 0
    # print('New User status {:2d}'.format(user_status))


async def user_interface():
    global user_status
    global start
    global led_onboard
    print('User interface running.')

    led_onboard.on()

    while True:
        await uasyncio.sleep_ms(100)
        if user_status == 1:   # first long press for setup was done
            if time.ticks_diff(time.ticks_ms(), start) > SET_TIME_MS:   # you waited too long
                print('setting user status back to 0')
                user_status = 0


async def sensor_reader():
    global trim_value
    global rudder_value
    global main_power

    adc_trim = ADC(Pin(26))  # create ADC object on ADC pin
    adc_power = ADC(Pin(27))
    adc_rudder = ADC(Pin(28))
    print('Sensor reader running.')
    while True:
        v_trim = adc_trim.read_u16() * VOLTAGE_FACTOR    # read value, 0-65535 across voltage range 0.0v - 3.3v
        v_rudder = adc_rudder.read_u16() * VOLTAGE_FACTOR  # read value, 0-65535 across voltage range 0.0v - 3.3v
        v_power = adc_power.read_u16() * VOLTAGE_FACTOR  # value for power
        trim_value = round((v_power - v_trim) * 200 / v_power) - 100  # calculates the trim position from -100% to 100%
        rudder_value = round((v_power - v_rudder) * 200 / v_power) - 100  # calculates the trim position in %
        main_power = v_power * (DIVIDER_R1 + DIVIDER_R2) / DIVIDER_R2
        # print('v_trim {:2f.3} v_rudder {:2f.3} v_power {:2f} trim {:2d}% rudder {:2d}% power {:2f.1}'.
        #       format(v_trim, v_rudder, v_power, trim_value, rudder_value, main_power))
        await uasyncio.sleep_ms(100)


async def main():
    global trim_settings

    configuration = config.load()
    trim_settings['full_up'] = configuration.get('full_up', trim_default['full_up'])
    trim_settings['neutral'] = configuration.get('neutral', trim_default['neutral'])
    trim_settings['full_down'] = configuration.get('full_down', trim_default['full_down'])
    trim_settings['rudder_left'] = configuration.get('rudder_left', trim_default['rudder_left'])
    trim_settings['rudder_neutral'] = configuration.get('rudder_neutral', trim_default['rudder_neutral'])
    trim_settings['rudder_right'] = configuration.get('rudder_right', trim_default['rudder_right'])
    print('Trim settings: {:s}'.format(json.dumps(trim_settings)))

    tasks = [uasyncio.create_task(display_driver()),
             uasyncio.create_task(user_interface()),
             uasyncio.create_task(sensor_reader())]
    button = async_button.Pushbutton(Pin(13, Pin.IN, Pin.PULL_UP))
    button.long_func(pin_press)
    button.press_func(pin_press_short)
    try:
        await uasyncio.gather(*tasks, return_exceptions=True)   # should never return
    except uasyncio.TimeoutError:
        print('Timeout')
    except uasyncio.CancelledError:
        print('Cancelled')
    except KeyboardInterrupt:
        print('Keyboard interrupt.')


if __name__ == "__main__":
    print('Trim Indicator starting ...')
    uasyncio.run(main())
