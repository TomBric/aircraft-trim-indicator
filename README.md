# Aircraft trim indicator
Trim indicator to display trim settings of aircraft. Based on Pi Pico with an 1.54 epaper display.

Can be used as replacement for older trim indicators, e.g. from MAC or others. Investment should be around 25 Euros in total.
It is possible to use it only as indicator for elevator trim (up/down) or also together with rudder trim (left/right).

|  |  |  |
| --- | --- | --- |
| ![0](https://github.com/TomBric/aircraft-trim-indicator/blob/main/.github/Trim1-resized.jpg) | ![-22](https://github.com/TomBric/aircraft-trim-indicator/blob/main/.github/Trim2-resized.jpg) | ![-100](https://github.com/TomBric/aircraft-trim-indicator/blob/main/.github/Trim3-resized.jpg) |


## Required Hardware
- Raspberry Pi Pico microcontroller (approx. 5 Euros), e.g. [welectron](https://www.welectron.com/Raspberry-Pi-Pico)
- Waveshare 1.54 epaper module v2 (waveshare Waveshare 12955, 16 Euros), e.g. [welectron](https://www.welectron.com/Waveshare-12955-154inch-e-Paper-Module)
- Step down converter MP1584EN, fixed output 5V, multiple suppliers (approx. 3 Euros)
- Resistors 10 kOhms and 1000 Ohms
- Pushbutton (microswitch), 6 mm, 0.50 Euros, many suppliers


## Hardware installation
### Outside connection of the instrument
The trim indicator has 3 wires to connect it:
 + Power (5 to 28 volts), connect this to your aircraft power
 + Ground, connect this to your aircraft ground
 + Indicator line elevator trim: typically the green line of the trim sensor inside the trim servo. If there is the option for another two connections a the trim sensor, connect it like the manufactorer proposed with +Power and Ground. Remark: the trim sensor typically is a potentiometer (e.g. 10K Ohms) with the indicator connection as a voltage divider.
 + Indicator line rudder trim (optional)

### Internal connections when building the instrument
1. Connect Power and Ground to the step-down converter. If not preset, set the converter to an update of 5 volts.
2. Connect output +5V from the converter to VSYS (Pin #38) on the pico. Connect output - to GND (PIN#37) on the pico
3. Connect the 1.54 epaper display

| Display  | Cable color from display | Pi Pico pin name | Pico pin# |
|:-----------:|:------------------:|:-----------:|:-------:|
| VCC	 | grey		| 3,3V		| 36 |
| GND	| brown	|	GND	|		13 |
| DIN	| blue	|	GP11	|	15 |
| CLK | yellow	|	GP10	|	14 |
| CS	| orange	|	GP6	|		9 |
| DC	| green	|	GP7	|		10 |
| RST | white	|	GP9	|		12 |
| Busy | magenta	| GP12	|	16 |

4. Connect the trim indicator: Use resistors 10 kOhms and 1000 Ohms as voltage divider: 
Connect 10kOhms to the trim incicator cable, then this output to the ADC0 input GP26_A0 at the Pico. 
From there connect resistor and ADC input via 1000 Ohms to GND (this voltage divider makes sure that your analog input 
line does not get more than 3.3 volts even if your trim sensor would supply full power voltage).
Connect elevator trim to GP26_A0 and rudder trim to GP28_A2.

5. Connect the reference voltage: Since the aircraft voltage may vary (12-14 V DC typically) we need to know this to
reliably measure the trim potentiometer. So use as well two resistors 10 kOhms and 1000 Ohms. Connect Connect 10kOhms 
to the aircraft voltage (+5 to +28V), then this output to the ADC1 input GP27_A1 at the Pico. From there connect 
resistor and ADC1 input via 1000 Ohms to GND.
The aircraft main voltage will also be displayed in the upper left corner. If you change the resistor values, 
please also modify the constants in the program.

## Installation
1. Connect the pi pico via micro usb to your PC
2. Install pyCharm and install pi pico extension to be ready to push python files on the Pico, see here for an setup guide (https://themachineshop.uk/getting-started-with-the-pi-pico-and-pycharm/)
3. If you also want to use elevator trim: Set RUDDER_TRIM = True in line 49 in main.py. 
3. Copy all files to your pc and "Run flash xxx" for all files to your Pico. At the last step flash main.py and the microcontroller will start.

## Configuration
By using the switch you can configure your trim display after installation in your aircraft. This has to be done once. 
The configuration will be stored.

1. Do a long push (more than one second) at the button. The text "Setup?" will come up on the display. Within another 10 seconds do a long push again (this is to protect from accidentally changing the configuration). The display will now show "Setup".
2. The display will now show the position that should be indicated. It starts with elevator trim full up. Move your trim to this position and push (shortly) the button once.
3. The next indication will be neutral trim. Move your trim neutral and short push the button again.
4. The last indication will be full down trim. Move your trim again and short push the button.
5. If rudder trim is set to True, same will happen for the trim positions of the rudder.

Configuration is now finished and the indicator should display your current trim optically.
If desired you can repeat the configuration.

Thats all, have fun and give me some feedback or a coffee, if you are having fun ....

## Wiring Diagram
![Wiring](https://github.com/TomBric/aircraft-trim-indicator/blob/main/.github/TrimDisplayWithRudder.jpg)

## 3D Printed Cases
... to follow. I am working on OpenScad 3D print files to print your instrument. It will fit into a 2 1/4 inch instrument hole.
