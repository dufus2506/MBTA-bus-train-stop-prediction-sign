# Next Ride
# Paul Moran

# Shows when the next bus or subway train will arrive at an MBTA stop
# Stops can be subway stations or bus stops
# Subway times can show in both directions from a station
# Buses only travel in one direction away from a stop

import time
import board
import terminalio
from adafruit_matrixportal.matrixportal import MatrixPortal
import json
from adafruit_datetime import datetime
import supervisor

# Change one of these examples to watch a stop or station
# Use only one set of LABELS, DIRECTIONS, ROUTES, and STOP_IDS

# This set of array variables will show individual routes at different stops with scrolling labels for each route
# Labels cyle through all in the array when CYCLE_LABEL is True
# LABELS = ["Next 108 bus to Malden Center ","Next 411 bus to Malden Center  ","Next 430 bus to Saugus Center  "]
# DIRECTIONS = ["1","1","0"] # Stop ID directions of travel
# ROUTES = ["108","411","430"]  # Train or bus routes you want to watch
# STOP_IDS = ["9021", "9021", "9063"]  # Stop IDs from the MBTA https://api-v3.mbta.com/stops
#
# This set of variables watches Malden center subway station for arriving trains in both directions
# Labels swap if CYCLE_LABEL is True
# LABELS = ["Forest Hills  ", "Oak Grove  "]  # Direction of travel labels
# DIRECTIONS = ["0", "1"]  # Stop direction of travel
# ROUTES = ["Orange","Orange"]  # Train line you want to watch
# STOP_IDS = ["place-mlmnl","place-mlmnl"]  # Stop IDs from the MBTA https://api-v3.mbta.com/stops
#
# This set of variables watches a single stop for any listed route that might be coming
LABELS = ["Next bus to Malden Center  "]  # Stop label, set CYCLE_LABEL to False when there's only one
DIRECTIONS = ["1"]  # Stop direction of travel
ROUTES = ["108,411,430"]  # Bus routes you want to watch
STOP_IDS = ["9021"]  # Stop IDs from the MBTA,  You can find them on Google maps
#
# Pick an image that fits what you want to watch
BACKGROUND_IMAGE = "/t_bus.bmp"  # t_bus, t_blu, t_orn, t_red, t_grn, or t_slv
CYCLE_LABEL = "False"  # If True, cycle through the array LABELS, set as False if there's only one
#
# These are gennerally ok, and you shouldn't have to change them
UPDATE_INTERVAL = 30  # Seconds between updates
TIME_ZONE_OFFSET = -5 * 3600  # Convert hours to seconds for eastern UTC offset

network = None
last_time_sync = None
sync_interval = 3600  # Reset time every hour
current_ride = 0  # Start with ride 0

matrixportal = MatrixPortal(status_neopixel=board.NEOPIXEL, debug=False) # Set debug to True to see sign changes in the serial feed

if network is None:
    network = (matrixportal.network)  # Requires an adafruit account to properly work (and a settings.toml file with the proper credentials)

matrixportal.set_background(BACKGROUND_IMAGE) # Maybe make this update too

matrixportal.add_text(  # Add text for the label line at the top
    text_font=terminalio.FONT,
    text_position=(18,6),  # Adjust to center a static label if scrolling is False
    text_scale=1,
    text_color=0xFFAC1C,
    scrolling=True,  # Scrolls the sign label
)
matrixportal.add_text(  # Add text for the first ride time
    text_font=terminalio.FONT,
    text_position=(22, 16),
    text_scale=1,
)
matrixportal.add_text(  # Add text for the second ride time
    text_font=terminalio.FONT,
    text_position=(22, 26),
    text_scale=1,
    text=("Loading")
)

def get_arrival_in_minutes_from_now(now, date_str):
    # print(f"now: {now}, date_str: {date_str}")  # Uncomment to troubleshoot date and time setting problems
    ride_date = datetime.fromisoformat(date_str).replace(tzinfo=None)
    # print(f"ride_date: {ride_date}")
    return round((ride_date - now).total_seconds() / 60.0)

def get_next_ride_times(current_ride):
    times = []
    now = datetime.now()
    try:
        DATA_SOURCE = f"https://api-v3.mbta.com/predictions?filter[stop]={STOP_IDS[current_ride]}&filter[route]={ROUTES[current_ride]}&sort=departure_time&page[limit]=3"
        response = network.fetch_data(DATA_SOURCE + f"&filter[direction_id]={DIRECTIONS[current_ride]}")
        # print(DATA_SOURCE + f"&filter[direction_id]={DIRECTIONS[current_ride]}")  # Uncomment to troubleshoot API format problems
        data = json.loads(response)
        num_avail_times = len(data["data"])
        if num_avail_times < 1:
            return [ ]
        for i in range(len(data["data"])):
            try:
                departure_time = data["data"][i]["attributes"]["departure_time"]
                if departure_time:
                    minute_difference = get_arrival_in_minutes_from_now(now, departure_time)
                    if (minute_difference > 0):  # Only add positive times to avoid erroneous old values (sometimes api returns these)
                        times.append(minute_difference)
                        if len(times) == 3 or len(times) >= num_avail_times:
                            break
            except (KeyError, IndexError):
                # TODO maybe do more error handling here for overnight errors
                # right now just skips to the next departure_time
                continue
    except Exception as e:
        print(f"Error fetching or parsing data: {e}")
        supervisor.reload()
    return times  # Return the calculated time(s) in an array variable with one or two entries

last_update = time.monotonic() - UPDATE_INTERVAL
matrixportal.set_text(f"{LABELS[current_ride]}", 0)  # Set the initial scrolling station, stop, or direction name

while True:
    if time.monotonic() - last_update >= UPDATE_INTERVAL:
        if last_time_sync is None or time.monotonic() - last_time_sync >= sync_interval:
            try:
                # Set the device time from the network
                network.get_local_time()
                last_time_sync = time.monotonic()
            except Exception as e:
                print("Failed to get the current time, error:", e)
                supervisor.reload()

        now = datetime.now()
        ride_times = get_next_ride_times(current_ride)
        matrixportal.set_text(f"{ride_times[0]:2d} min" if len(ride_times) > 0 else "None", 1)  # Update the first ride time, format the time to two digits
        matrixportal.set_text(f"{ride_times[1]:2d} min" if len(ride_times) > 1 else "", 2)  # Update the second ride time, format the time to two digits
        last_update = time.monotonic()

        if CYCLE_LABEL == "True":
            matrixportal.set_text(f"{LABELS[current_ride]}", 0)  # Update the scroll message, oththerwise show the first label

        if current_ride < (len(ROUTES)-1):
            current_ride += 1
        else:
            current_ride = 0
        continue

    matrixportal.scroll()
    time.sleep(0.05)  # Change the scroll speed here, larger numbers are slower
