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

# seven segment numbers for display
nums = ((1,3,4,5,6,7),(6,7), (1,6,2,5,3), (1,6,2,7,3), (4,6,2,7), (1,4,2,7,3), (1,4,2,7,5,3),
		(1,6,7), (1,2,3,4,5,6,7), (1,4,6,2,7,3))

# Default assignment: sck=Pin(10), mosi=Pin(11), miso=Pin(8)
class Display:
	def __init__(self):
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

	def print(self):
		self.e.display_part(self.buf)
		# self.fb.fill_rect(0, 0, self.e.width, self.e.height, white)

	def busy(self):
		return self.e.busy()

	def seven_seg(self, x, y, size, thick, number):
		for led in nums[number]:
			if led == 1:
				self.fb.fill_rect(x, y, size+thick, thick, black)
			elif led == 2:
				self.fb.fill_rect(x, y+size, size+thick, thick, black)
			elif led == 3:
				self.fb.fill_rect(x, y+2*size, size+thick, thick, black)
			elif led == 4:
				self.fb.fill_rect(x, y, thick, size+thick, black)
			elif led == 5:
				self.fb.fill_rect(x, y+size, thick, size+thick, black)
			elif led == 6:
				self.fb.fill_rect(x+size, y, thick, size+thick, black)
			elif led == 7:
				self.fb.fill_rect(x+size, y+size, thick, size+thick, black)


	def indicator(self, percentage, setupmode = 0):
		# self.fb.fill_rect(0, 0, self.e.width, self.e.height, white)
		self.fb.fill(white)
		s = 4  # size of out frame
		sb = 16  # size of indicator
		size = 16  # size of numbers
		thick = 4  # thickness of numbers

		self.fb.fill_rect(100, 0, self.e.width-1-100, self.e.height-1, black)
		self.fb.fill_rect(100+s, s, self.e.width-1-100-2*s, self.e.height-1-2*s, white)
		self.fb.fill_rect(100+s, 100-s//2, self.e.width-1-100-2*s, s, black)

		if setupmode == 0 or setupmode == 1:
			position = math.floor((self.e.height-2*s-sb) / 200 * percentage) + 100
			self.fb.fill_rect(100+4*s, position-sb//2, 100-8*s, sb, black)
			posy = 100 + s
			if percentage > 0:  # plus sign
				self.fb.fill_rect(0, posy-thick//2, size, thick, black)
				self.fb.fill_rect(0+size//2-thick//2, posy-size//2, thick, size, black)
			elif percentage < 0: # minus sign
				self.fb.fill_rect(0, posy - thick // 2, size, thick, black)
				percentage = - percentage   # for the right calculations below
			posy = posy - size - thick
			h = percentage // 100
			if h > 0:
				self.seven_seg(20, posy, size, thick, h)
			t = (percentage % 100) // 10
			if h > 0 or t > 0:
				self.seven_seg(45, posy, size, thick, t)
			self.seven_seg(70, posy, size, thick, percentage % 10)

		if setupmode >= 1:    # indicate setup mode
			self.fb.fill_rect(5, 0, 15, 15, black)   # black indication left upper corner
			if setupmode == 2:
				self.fb.fill_rect(30, self.e.height - sb, 100 - 8 * s, sb, black)
			elif setupmode == 3:
				self.fb.fill_rect(30, 100-sb//2, 100 - 8 * s, sb, black)
			elif setupmode == 4:
				self.fb.fill_rect(30, 0, 100 - 8 * s, sb, black)
