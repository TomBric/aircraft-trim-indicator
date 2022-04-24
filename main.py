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


SET_TIME_MS = const(10000)   # time for two subsequent long presses before going into setup mode
DISPLAY_WAKEUP = const(50)   # number of refreshs after start, to get better contrast on the display

# GLOBALS
start = time.ticks_ms()
user_status = 0
trim_value = 0
trim_default = {'full_up': 64000, 'neutral': 32000, 'full_down': 1000}
# settings for trim, initialized during setup (highest up, neutral, highest down)
trim_settings = {}
new_trim = {}
display_wakeup = DISPLAY_WAKEUP
led_onboard = Pin(25, Pin.OUT)


async def display_driver():
    global trim_value
    global user_status
    global display_wakeup
    global led_onboard

    old_value = 0
    print('Display driver running.')
    d = display.Display()
    await uasyncio.sleep_ms(100)  # wait for other coros to finish their measurements
    while True:
        # print('Display driver: user status {:2d}'.format(user_status))
        if user_status == 0 or user_status == 1:
            diff = abs(trim_settings['neutral'] - trim_value)
            if trim_settings['neutral'] > trim_settings['full_up']:   # full up is  lowest value
                if trim_value <= trim_settings['neutral']:    # positive trim
                    display_percent = round(diff / (trim_settings['neutral'] - trim_settings['full_up']) * 100)
                else:   # negative trim
                    display_percent = - round(diff / (trim_settings['full_down'] - trim_settings['neutral']) * 100)
            else:   # full down is lowest value
                if trim_value >= trim_settings['neutral']:    # positive trim
                    display_percent = round(diff / (trim_settings['full_up'] - trim_settings['neutral']) * 100)
                else:   # negative trim
                    display_percent = - round(diff / (trim_settings['neutral'] - trim_settings['full_down']) * 100)
            if display_percent > 100:
                display_percent = 100
            elif display_percent < -100:
                display_percent = -100
            # print('Percentage {:2d}'.format(display_percent))
            if display_percent != old_value or display_wakeup > 0:
                led_onboard.off()   # do some flicker
                old_value = display_percent
                display_wakeup -= 1
                d.indicator(display_percent, user_status)
                d.print()
                led_onboard.on()
            else:
                await uasyncio.sleep_ms(50)
        elif user_status == 2:   # setup trim full up
            d.indicator(0, 2)
            d.print()
        elif user_status == 3:   # setup trim neutral
            d.indicator(0, 3)
            d.print()
        elif user_status == 4:    # setup trim full down
            d.print()
            d.indicator(0, 4)

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
    global user_status
    global trim_settings
    global trim_value
    global new_trim
    global display_wakeup

    # print('Short pin pressed')
    display_wakeup = 1
    if user_status == 2:     # highest trim up
        user_status = 3
        new_trim['full_up'] = trim_value
    elif user_status == 3:   # neutral
        user_status = 4
        new_trim['neutral'] = trim_value
    elif user_status == 4:    # trim down
        user_status = 0
        new_trim['full_down'] = trim_value
        # set new trim values, do a sanity check, that neutral is between the two values
        if new_trim['full_down'] > new_trim['neutral'] > new_trim['full_up']:
            trim_settings = new_trim
            config.save(trim_settings)
        elif new_trim['full_down'] < new_trim['neutral'] < new_trim['full_up']:
            trim_settings = new_trim
            config.save(trim_settings)


async def user_interface():
    global user_status
    global start
    global led_onboard
    print('User interface running.')

    led_onboard.on()

    while True:
        await uasyncio.sleep_ms(100)
        if user_status == 1:   # first long press for setup
            if time.ticks_diff(time.ticks_ms(), start) > SET_TIME_MS:   # you waited too long
                print('setting user status back to 0')
                user_status = 0


async def sensor_reader():
    global trim_value
    adc = ADC(Pin(26))  # create ADC object on ADC pin
    print('Sensor reader running.')
    while True:
        trim_value = adc.read_u16()  # read value, 0-65535 across voltage range 0.0v - 3.3v
        # print('Value {:2d}'.format(trim_value))
        await uasyncio.sleep_ms(100)


async def main():
    global trim_settings

    configuration = config.load()
    trim_settings['full_up'] = configuration.get('full_up', trim_default['full_up'])
    trim_settings['neutral'] = configuration.get('neutral', trim_default['neutral'])
    trim_settings['full_down'] = configuration.get('full_down', trim_default['full_down'])
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
    print('Main: Starting async threads')
    uasyncio.run(main())
