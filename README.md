# MBTA-bus-train-stop-predictions
An LED matrix device to show predictions of arriving buses and trains using the MBTA v3 API 

Built on the excellent work of dotslashjack and jegamboafuentes, I've designed my own MBTA
sign to tell you when the bus or train will be leaving a stop.  Your sign can show predictions for
for bus lines, subway stations, and commuter rail stations.

This is designed to be used on the Adafruit Matrixportal M4 running Circuitpython
https://learn.adafruit.com/adafruit-matrixportal-m4
and using a 64x32 RGB LED matrix.  https://www.adafruit.com/category/327
Pick whatever size you like.

I worked hard to keep the code very small, and with a minimum number of libraries so the
limited memory of the M4 would not be a problem. And I improved on the code comments a bit
to make it easier for you to configure your own sign.

I removed all but the most essential libraries from the board. I have only the following
libraries on my board:

![image](https://github.com/user-attachments/assets/a1ed95b0-af7f-498b-87b5-e3b47133c442)

Apart from that I tried to make the sign as useful as possible with the ability to see predictions
for more than one stop or bus route. You can add as many stops/routes/lines to a sign as you need, though it's
not very practical if the sign has too many.  You don't want to be waiting too long
for sign updates to see when your ride is leaving.  

Because the sign updates every thirty seconds, you won't need an MBTA API Key to make it work. 
You need one if your project will be checking the API multiple times a second.  That's not very
practical for this sign, so no API key necessary here. But you will need an Adafruit AIO 
account so that you can set the clock properly. The free level is just fine for clock setting. 
Get one here:  https://io.adafruit.com/

Your settings.toml file should have the following entries:

CIRCUITPY_WIFI_SSID = "Your_SSID"

CIRCUITPY_WIFI_PASSWORD = "Your_Password"

AIO_USERNAME = "Your_AIO_Username"

AIO_KEY      = "aio_Your_Really_Long_AIO_User_Key"

timezone = "America/New_York"

Don't forget the timezone entry, or your clock may be set to GMT.  WiFi settings are case
sensitive in the settings.toml file, so be sure to match everything correctly for your WiFi network.

When I was done I had the following files/directories on my board:

![image](https://github.com/user-attachments/assets/616f7d56-dc94-4faf-a10c-c8f14137a8a1)

All but the lib directory were empty.

See the code.py file for configuration examples.  You only want one set of array variables for your
configuration. You'll need some stop information to make the correct entries in your array variables. 
You can find the necessary settings here: https://api-v3.mbta.com/stops Click the "pretty print" 
box when the page opens, and search for your stop.
