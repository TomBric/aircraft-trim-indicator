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

import epaper1in54
from machine import SPI, Pin
import framebuf
import math
import font8x8

# Connection of the display
#   Display   Board name   Board number
# 	VCC	grey		3,3V		36
# 	GND	brown		GND			13
# 	DIN	blue		GP11		15
# 	CLK yellow		GP10		14
#   CS	orange		GP6			9
#   DC	green		GP7			10
# 	RST white		GP9			12
# 	Busy magenta	GP12		16

# GLOBALS
black = 0
white = 1

# Settings
INDICATOR_LINE = 4
INDICATOR_END = 16
INDICATOR_NEUTRAL = 16
SIZE_VOLT = 16
SIZE_TRIANGLE = 30
SIZE_TRIANGLE_POINTER = 12

# seven segment numbers for display
nums = ((1, 3, 4, 5, 6, 7), (6, 7), (1, 6, 2, 5, 3), (1, 6, 2, 7, 3), (4, 6, 2, 7), (1, 4, 2, 7, 3), (1, 4, 2, 7, 5, 3),
        (1, 6, 7), (1, 2, 3, 4, 5, 6, 7), (1, 4, 6, 2, 7, 3))


# Default assignment: sck=Pin(10), mosi=Pin(11), miso=Pin(8)
class Display:
    def __init__(self, rudder_trim):
        spi = SPI(1, 32000000, polarity=0, phase=0, sck=Pin(10), mosi=Pin(11), miso=Pin(8))
        cs = Pin(6)
        dc = Pin(7)
        rst = Pin(9)
        busy = Pin(12)

        self.e = epaper1in54.EPD(spi, cs, dc, rst, busy)
        self.e.init(False)
        self.e.clear(0xFF)  # necessary to overwrite everything
        self.e.init(True)
        self.e.clear(0xFF)  # necessary to overwrite everything
        self.buf = bytearray(self.e.width * self.e.height // 8)
        self.fb = framebuf.FrameBuffer(self.buf, self.e.width, self.e.height, framebuf.MONO_HLSB)
        self.fb.fill(white)

        if rudder_trim:
            self.indicator_hor = self.e.width - 10  # horizontal position of line on the right
            self.indicator_up = 10  # start of indicator line
            self.indicator_down = 150  # where indicator stops
        else:
            self.indicator_hor = self.e.width - 20  # horizontal position of line on the right
            self.indicator_up = 10  # start of indicator line
            self.indicator_down = self.e.height - 10  # where indicator stops
        self.indicate_rudder = rudder_trim

    def print(self):
        self.e.display_part(self.buf)

    # self.fb.fill_rect(0, 0 self.e.width, self.e.height, white)

    def busy(self):
        return self.e.busy()

    def seven_seg_char(self, x, y, size, thick, character):
        if character == '+':
            self.fb.fill_rect(x, y + size // 2 - thick // 2, size // 2, thick, black)  # "-" part
            self.fb.fill_rect(x + size // 4 - thick // 2, y + size // 4, thick, size // 2, black)  # "|" part
        elif character == '-':
            self.fb.fill_rect(x, y + size // 2 - thick // 2, size // 2, thick, black)
        elif character == '.':
            self.fb.fill_rect(x + size // 4 - thick // 2, y + size - thick // 2, thick, thick, black)
        elif '0' <= character <= '9':
            number = ord(character) - ord('0')
            for led in nums[number]:
                if led == 1:
                    self.fb.fill_rect(x, y, size // 2 + thick, thick, black)
                elif led == 2:
                    self.fb.fill_rect(x, y + size // 2, size // 2 + thick, thick, black)
                elif led == 3:
                    self.fb.fill_rect(x, y + 2 * size // 2, size // 2 + thick, thick, black)
                elif led == 4:
                    self.fb.fill_rect(x, y, thick, size // 2 + thick, black)
                elif led == 5:
                    self.fb.fill_rect(x, y + size // 2, thick, size // 2 + thick, black)
                elif led == 6:
                    self.fb.fill_rect(x + size // 2, y, thick, size // 2 + thick, black)
                elif led == 7:
                    self.fb.fill_rect(x + size // 2, y + size // 2, thick, size // 2 + thick, black)

    def seven_seg_number(self, x, y, size, format_string, number):  # print an int value as seven segments
        # example seven_seg_float(10,30, 10,'{:+2.1}', 12.7)
        s = format_string.format(number)
        xpos = x
        for c in s:
            self.seven_seg_char(xpos, y, size, size // 8, c)
            xpos += size // 2 + size // 4

    def text(self, t, xpos, ypos, size):  # print a text at x y position, size should be a multiple of 8
        pixelsize = size // 8
        for i in range(0, len(t)):
            if 'A' <= t[i] <= 'Z':
                font = font8x8.font8x8_capitals
                index = ord(t[i]) - ord('A')
            elif 'a' <= t[i] <= 'z':
                font = font8x8.font8x8_smalls
                index = ord(t[i]) - ord('a')
            elif '0' <= t[i] <= '9':
                font = font8x8.font8x8_numbers
                index = ord(t[i]) - ord('0')
            elif '!' <= t[i] <= '&':
                font = font8x8.font8x8_specials
                index = ord(t[i]) - ord('!')
            elif t[i] == '?':
                font = font8x8.font8x8_specials
                index = 1    # '?' is not in ascii iteration, so handle it special
            else:
                continue

            for y in range(0, 8):
                for x in range(0, 8):
                    if font[index * 8 + y] & (128 >> x):
                        self.fb.fill_rect(xpos + x * pixelsize, ypos + y * pixelsize, pixelsize, pixelsize, black)
            xpos += 8 * pixelsize

    def indicator(self, percentage, rudder_percentage, power, setupmode):

        self.fb.fill(white)
        # self.fb.fill_rect(0, 0, self.e.width, self.e.height, white)

        self.text('Trim', 5, 5, 24)
        self.text('Ind', 17, 32, 24)
        self.seven_seg_number(13, 90, SIZE_VOLT, '{:+2.1f}', power)
        self.text('V', 78, 92, 16)

        if setupmode == 0 or setupmode == 1:
            self.elevator_indicator(percentage)
            if self.indicate_rudder:
                self.rudder_indicator(rudder_percentage)
            if setupmode == 1:  # indicate waiting for another button press
                self.text('Setup?', 5, 120, 16)
        if setupmode >= 2:  # indicate setup mode
            # self.fb.fill_rect(5, 0, 15, 15, black)   # black indication left upper corner
            self.text('Setup', 5, 120, 16)
            if setupmode == 2:  # setup trim up
                self.elevator_indicator(+100)
            elif setupmode == 3:  # setup trim neutral
                self.elevator_indicator(0)
            elif setupmode == 4:  # setup trim down
                self.elevator_indicator(-100)
            elif setupmode == 5:  # setup rudder left
                self.rudder_indicator(+100)
            elif setupmode == 6:  # setup rudder neutral
                self.rudder_indicator(0)
            elif setupmode == 7:  # setup rudder right
                self.rudder_indicator(-100)

    def elevator_indicator(self, percentage):
        zeroy = self.indicator_up + math.floor((self.indicator_down - self.indicator_up) / 2)
        length_indicator = self.indicator_down - self.indicator_up
        self.fb.fill_rect(self.indicator_hor - INDICATOR_LINE, self.indicator_up, INDICATOR_LINE,
                          length_indicator, black)
        self.fb.fill_rect(self.indicator_hor - INDICATOR_END, self.indicator_up - INDICATOR_LINE//2,
                          INDICATOR_END, INDICATOR_LINE, black)  # upper end line
        self.text('DN', self.indicator_hor - INDICATOR_END - 2 * 16 - 4, self.indicator_up, 16)
        self.fb.fill_rect(self.indicator_hor - INDICATOR_END, self.indicator_down - INDICATOR_LINE//2,
                          INDICATOR_END, INDICATOR_LINE, black)  # down end line
        self.text('UP', self.indicator_hor - INDICATOR_END - 2 * 16 - 4, self.indicator_down - 12, 16)
        self.fb.fill_rect(self.indicator_hor - INDICATOR_END, zeroy - INDICATOR_LINE // 2, INDICATOR_END,
                          INDICATOR_LINE, black)  # neutral line

        posy = zeroy + math.floor(length_indicator / 200 * percentage)

        for i in range(0, SIZE_TRIANGLE // 4):
            self.fb.fill_rect(self.indicator_hor - SIZE_TRIANGLE - SIZE_TRIANGLE_POINTER + i * 4,
                              posy - SIZE_TRIANGLE // 2 + i * 2, 4, SIZE_TRIANGLE - i * 4, black)
        self.fb.fill_rect(self.indicator_hor - SIZE_TRIANGLE_POINTER - INDICATOR_LINE, posy - INDICATOR_LINE // 2,
                          SIZE_TRIANGLE_POINTER, INDICATOR_LINE, black)

    def rudder_indicator(self, percentage):
        self.text('L', 0, self.e.height - 16, 16)
        self.text('R', self.e.width - 16, self.e.height - 16, 16)
        self.fb.fill_rect(16, self.e.height - INDICATOR_LINE, self.e.width - 1 - 2 * 16,
                          INDICATOR_LINE, black)  # long line
        self.fb.fill_rect(16, self.e.height - 1 - INDICATOR_END, INDICATOR_LINE, INDICATOR_END, black)  # end line left
        self.fb.fill_rect(self.e.width - 1 - 16 - INDICATOR_LINE, self.e.height - 1 - INDICATOR_END, INDICATOR_LINE,
                          INDICATOR_END, black)
        # end line right
        self.fb.fill_rect(self.e.width // 2 - INDICATOR_LINE // 2, self.e.height - 1 - INDICATOR_NEUTRAL,
                          INDICATOR_LINE, INDICATOR_NEUTRAL, black)
        # neutral line

        posx = 16 + INDICATOR_LINE + math.floor(((self.e.width - 32 - 2 * INDICATOR_LINE) // 2) +
                                                percentage / 100 * ((self.e.width - 32 - 2 * INDICATOR_LINE) // 2))
        for i in range(0, SIZE_TRIANGLE // 4):
            self.fb.fill_rect(posx - SIZE_TRIANGLE // 2 + i * 2,
                              self.e.height - 1 - SIZE_TRIANGLE_POINTER - SIZE_TRIANGLE + i * 4,
                              SIZE_TRIANGLE - i * 4, 4, black)
        self.fb.fill_rect(posx - INDICATOR_LINE // 2, self.e.height - 1 - INDICATOR_LINE - SIZE_TRIANGLE_POINTER,
                          INDICATOR_LINE, SIZE_TRIANGLE_POINTER, black)
