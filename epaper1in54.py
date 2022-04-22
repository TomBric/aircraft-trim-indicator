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

Based on work from Waveshare and Mike Causer
Copyright (c) 2017 Waveshare
Copyright (c) 2018 Mike Causer https://github.com/mcauser/micropython-waveshare-epaper
"""

from micropython import const
from time import sleep_ms

# Display resolution
EPD_WIDTH = const(200)
EPD_HEIGHT = const(200)

# Display commands
DRIVER_OUTPUT_CONTROL           = const(0x01)
BOOSTER_SOFT_START_CONTROL      = const(0x0C)
# GATE_SCAN_START_POSITION       = const(0x0F)
DEEP_SLEEP_MODE                 = const(0x10)
DATA_ENTRY_MODE_SETTING         = const(0x11)
SW_RESET                        = const(0x12)
# TEMPERATURE_SENSOR_CONTROL     = const(0x1A)
MASTER_ACTIVATION               = const(0x20)
# DISPLAY_UPDATE_CONTROL_1       = const(0x21)
DISPLAY_UPDATE_CONTROL_2         = const(0x22)
WRITE_RAM                        = const(0x24)
WRITE_VCOM_REGISTER              = const(0x2C)
WRITE_LUT_REGISTER               = const(0x32)
SET_DUMMY_LINE_PERIOD            = const(0x3A)
SET_GATE_TIME                    = const(0x3B)   # not in datasheet
BORDER_WAVEFORM_CONTROL          = const(0x3C)
SET_RAM_X_ADDRESS_START_END_POSITION = const(0x44)
SET_RAM_Y_ADDRESS_START_END_POSITION = const(0x45)
SET_RAM_X_ADDRESS_COUNTER            = const(0x4E)
SET_RAM_Y_ADDRESS_COUNTER            = const(0x4F)
TERMINATE_FRAME_READ_WRITE           = const(0xFF)   # aka NOOP

BUSY = const(1)  # 1=busy, 0=idle


class EPD:
    def __init__(self, spi, cs, dc, rst, busy):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.rst = rst
        self.busy = busy
        self.cs.init(self.cs.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        self.rst.init(self.rst.OUT, value=0)
        self.busy.init(self.busy.IN)
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

    LUT_FULL_UPDATE = bytearray(b'\x80\x48\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                b'\x40\x48\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                b'\x80\x48\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                b'\x40\x48\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                b'\x0A\x00\x00\x00\x00\x00\x00'
                                b'\x08\x01\x00\x08\x01\x00\x02'
                                b'\x0A\x00\x00\x00\x00\x00\x00'
                                b'\x00\x00\x00\x00\x00\x00\x00'
                                b'\x00\x00\x00\x00\x00\x00\x00'
                                b'\x00\x00\x00\x00\x00\x00\x00'
                                b'\x00\x00\x00\x00\x00\x00\x00'
                                b'\x00\x00\x00\x00\x00\x00\x00'
                                b'\x00\x00\x00\x00\x00\x00\x00'
                                b'\x00\x00\x00\x00\x00\x00\x00'
                                b'\x00\x00\x00\x00\x00\x00\x00'
                                b'\x00\x00\x00\x00\x00\x00\x00'
                                b'\x22\x22\x22\x22\x22\x22\x00\x00\x00'
                                b'\x22\x17\x41\x00\x32\x20')
    LUT_PARTIAL_UPDATE = bytearray(b'\x00\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x80\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x40\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x0F\x00\x00\x00\x00\x00\x00'
                                   b'\x01\x01\x00\x00\x00\x00\x00'
                                   b'\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x00\x00\x00\x00\x00\x00\x00'
                                   b'\x22\x22\x22\x22\x22\x22\x00\x00\x00'
                                   b'\x02\x17\x41\xB0\x32\x28')

    def _command(self, command, data=None):
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([command]))
        self.cs(1)
        if data is not None:
            self._data(data)

    def _data(self, data):   # write full bytearray
        self.dc(1)
        self.cs(0)
        self.spi.write(data)
        self.cs(1)

    def send_data(self, data):   # write single byte
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([data]))
        self.cs(1)

    def set_windows(self, xstart, ystart, xend, yend):
        self._command(SET_RAM_X_ADDRESS_START_END_POSITION)
        self.send_data((xstart >> 3) & 0xFF)
        self.send_data((xend >> 3) & 0xFF)

        self._command(SET_RAM_Y_ADDRESS_START_END_POSITION)
        self.send_data(ystart & 0xFF)
        self.send_data((ystart >> 8) & 0xFF)
        self.send_data(yend & 0xFF)
        self.send_data((yend >> 8) & 0xFF)

    def set_cursor(self, xstart, ystart):
        self._command(SET_RAM_X_ADDRESS_COUNTER)
        self.send_data(xstart & 0xFF)
        self._command(SET_RAM_Y_ADDRESS_COUNTER)
        self.send_data(ystart & 0xFF)
        self.send_data((ystart >> 8) & 0xFF)

    def init(self, partial):
        if partial:
            self.reset()
            self.wait_until_idle()
            self.set_lut(self.LUT_PARTIAL_UPDATE)
            self._command(0x37, bytearray(b'\x00\x00\x00\x00\x00\x40\x00\x00\x00\x00'))
            self._command(BORDER_WAVEFORM_CONTROL, b'\x80')
            self._command(DISPLAY_UPDATE_CONTROL_2, b'\xC0')
            self._command(MASTER_ACTIVATION)
            self.wait_until_idle()
        else:
            # EPD hardware init start
            self.reset()
            self.wait_until_idle()
            self._command(SW_RESET)
            self.wait_until_idle()

            self._command(DRIVER_OUTPUT_CONTROL, b'\xC7\x00\x01')
            self._command(DATA_ENTRY_MODE_SETTING, b'\x01')
            self.set_windows(0, self.height - 1, self.width - 1, 0)
            self._command(BORDER_WAVEFORM_CONTROL, b'\x01')
            self._command(0x18, b'\x80')
            self._command(DISPLAY_UPDATE_CONTROL_2, b'\xB1')
            self._command(MASTER_ACTIVATION)
            self.set_cursor(0, self.height - 1)
            self.wait_until_idle()
            self.set_lut(self.LUT_FULL_UPDATE)

    def wait_until_idle(self):
        while self.busy.value() == BUSY:
            sleep_ms(100)

    def busy(self):
        return self.busy.value() == BUSY

    def reset(self):  # ok
        self.rst(1)
        sleep_ms(200)
        self.rst(0)
        sleep_ms(5)
        self.rst(1)
        sleep_ms(200)

    def lut(self, lut):  # ok
        self._command(WRITE_LUT_REGISTER, lut)

    def set_lut(self, lut):   # ok
        self.lut(lut[0:153])
        self._command(0x3f, lut[153:154])
        self._command(0x03, lut[154:155])
        self._command(0x04, lut[155:158])
        self._command(0x2c, lut[158:159])

    def turn_on_display(self):
        self._command(DISPLAY_UPDATE_CONTROL_2)
        self.send_data(0xC7)
        self._command(MASTER_ACTIVATION)
        self.wait_until_idle()

    def turn_on_display_part(self):
        self._command(DISPLAY_UPDATE_CONTROL_2)
        # self.send_data(0xCF)
        self.send_data(0xFF)
        self._command(MASTER_ACTIVATION)

    def clear(self, color):
        self._command(0x24)
        for j in range(0, self.height):
            for i in range(0, int(self.width / 8)):
                self.send_data(color)
        self.turn_on_display()

    def display_part(self, buf):    # partial update with sync waiting to measure time once in init
        self._command(0x24)
        self._data(buf)
        self.turn_on_display_part()

    # to wake call reset() or init()
    def sleep(self):
        self._command(DEEP_SLEEP_MODE, b'\x01')  # enter deep sleep A0=1, A0=0 power on
        self.wait_until_idle()
