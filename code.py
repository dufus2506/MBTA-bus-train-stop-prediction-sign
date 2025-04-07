# Next MBTA Ride Sign
# 2025 Paul M
# SPDX-License-Identifier: MIT

# Creates a sign that shows when the next bus or train will arrive at an MBTA stop
# Stops can be commuter rail stops, subway stations, or bus stops

import time
import board
import terminalio
from adafruit_matrixportal.matrixportal import MatrixPortal
import json
from adafruit_datetime import datetime
import supervisor

# Configure one of these examples to create a sign for a stop or station
# Use only one set of LABEL, DIRECTION, ROUTE, and STOP_ID array variables
# Each comma separated and quoted entry set of
# LABEL, DIRECTION, ROUTE, and STOP_ID defines a SIGN
# ARRAY_VARIABLE = ["Sign0","Sign1","Sign2","Etc"]

# Makes three signs for routes at two different stops with scrolling labels for each route sign
# The sign changes to a new bus route when CYCLE_SIGN is True
# LABEL = ["Next 108 bus to Malden Center ","Next 411 bus to Malden Center  ","Next 430 bus to Saugus Center  "]
# DIRECTION = ["1","1","0"]         # Stop ID directions of travel
# ROUTE = ["108","411","430"]       # Train or bus routes for your sign
# STOP_ID = ["9021","9021","9063"]  # Stop ID(s) from the MBTA https://api-v3.mbta.com/stops

# Makes two signs for the Malden center subway station showing arriving trains in both directions
# The scrolling sign changes direction while CYCLE_SIGN is True
# LABEL = ["Forest Hills  ","Oak Grove  "]  # Direction of travel labels
# DIRECTION = ["0","1"]                     # Stop direction of travel
# ROUTE = ["Orange","Orange"]               # Train line for your sign
# STOP_ID = ["place-mlmnl","place-mlmnl"]   # Stop ID(s) from the MBTA

# Makes a single sign for one or more routes at a stop
# Set CYCLE_SIGN to false so that the scroll won't reset and restart
# The scroll will pause during sign updates, but not restart
LABEL = ["Next bus to Malden Center  "]  # Stop scroll, set CYCLE_SIGN to False when there's only one
DIRECTION = ["1"]                        # Stop direction of travel
ROUTE = ["108,411,430"]                  # Bus route(s) for your sign
STOP_ID = ["9021"]                       # Stop ID(s) from the MBTA

# Pick an image that's appropriate for your sign
BACKGROUND_IMAGE = "/t_bus.bmp"  # t_bus, t_blu, t_orn, t_red, t_grn, t_crl, or t_slv
CYCLE_SIGN = "False"  # If True, cycle through the defined SIGNs, set to False if you make a single sign
UPDATE_INTERVAL = 30  # Seconds between sign updates

network = None        # Force a network connect at startup
last_time_sync = None # Force a time sync at startup
sync_interval = 3600  # Reset the time every hour
current_ride = 0      # Start with ride 0

# Set debug to True to see sign changes in the serial monitor
matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=False)

# Requires an adafruit AIO account to properly work
# and a settings.toml file with the proper credentials and timezone
if network is None:
    network = (matrixportal.network)

matrixportal.set_background(BACKGROUND_IMAGE) # Maybe make this part of 30 second updates too?

matrixportal.add_text(     # Add text for the label line at the top
    text_font=terminalio.FONT,
    text_position=(18,6),  # Adjust to center a static label if scrolling is False
    text_scale=1,
    text_color=0xFFAC1C,
    scrolling=True,        # Scrolls the sign label, can also be False if your label fits on the sign
)
matrixportal.add_text(     # Add text for the first ride time
    text_font=terminalio.FONT,
    text_position=(22, 16),
    text_scale=1,
)
matrixportal.add_text(     # Add text for the second ride time
    text_font=terminalio.FONT,
    text_position=(22, 26),
    text_scale=1,
    text=("Loading")
)

def get_arrival_in_minutes_from_now(now, date_str):
    # print(f"now: {now}, date_str: {date_str}")  # Uncomment to troubleshoot date and time setting problems
    ride_date = datetime.fromisoformat(date_str).replace(tzinfo=None)
    return round((ride_date - now).total_seconds() / 60.0)

def get_next_ride_times(current_ride):
    times = []
    now = datetime.now()
    try:
        # Add a page limit to the line below if you get large fetch results from the API to keep your sign from having memory problems
        DATA_SOURCE = f"https://api-v3.mbta.com/predictions?filter[stop]={STOP_ID[current_ride]}&filter[route]={ROUTE[current_ride]}&sort=departure_time"# &page[limit]=3"
        response = network.fetch_data(DATA_SOURCE + f"&filter[direction_id]={DIRECTION[current_ride]}")
        # print(DATA_SOURCE + f"&filter[direction_id]={DIRECTION[current_ride]}")  # Uncomment to troubleshoot API format problems
        data = json.loads(response)
        num_avail_times = len(data["data"])
        if num_avail_times < 1:
            return []
        for i in range(len(data["data"])):
            try:
                departure_time = data["data"][i]["attributes"]["departure_time"]
                if departure_time:
                    minute_difference = get_arrival_in_minutes_from_now(now, departure_time)
                    if (minute_difference > 0):  # Only add positive times to avoid erroneous old values (sometimes the api returns these)
                        times.append(minute_difference)
                        if len(times) == 3 or len(times) >= num_avail_times:
                            break
            except (KeyError, IndexError):
                # TODO maybe do more error handling here for bad fetch
                # Right now just skips to the next departure_time
                continue
    except Exception as e:
        print(f"Error fetching or parsing data: {e}")
        supervisor.reload()
    return times  # Return the calculated time(s) in an array variable with one or more entries

last_update = time.monotonic() - UPDATE_INTERVAL
matrixportal.set_text(f"{LABEL[current_ride]}", 0)  # Set the initial sign scroll

while True:
    if time.monotonic() - last_update >= UPDATE_INTERVAL:
        if last_time_sync is None or time.monotonic() - last_time_sync >= sync_interval:
            try:
                # Set the device time from the network
                # Be sure to include
                # timezone = "America/New_York"
                # in settings.toml or the system time may be set to GMT (UTC? Zulu?)
                network.get_local_time()
                last_time_sync = time.monotonic()
            except Exception as e:
                print("Failed to get the current time, error:", e)
                supervisor.reload()
        now = datetime.now()
        ride_times = get_next_ride_times(current_ride)
        matrixportal.set_text(f"{ride_times[0]:2d} min" if len(ride_times) > 0 else "None", 1)  # Update the first ride time
        matrixportal.set_text(f"{ride_times[1]:2d} min" if len(ride_times) > 1 else "", 2)      # Update the second ride time
        last_update = time.monotonic()
        if CYCLE_SIGN == "True":
            matrixportal.set_text(f"{LABEL[current_ride]}", 0)  # Update the sign scroll
        if current_ride < (len(ROUTE)-1):
            current_ride += 1
        else:
            current_ride = 0
        continue
    matrixportal.scroll()
    time.sleep(0.05)  # Change the scroll speed here, larger numbers are slower
