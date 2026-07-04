# mellow-heeler-v2
[Wireless Access Point](https://en.wikipedia.org/wiki/Wireless_access_point) collection application.

## Introduction
A Mellow Heeler client observes [wireless beacons](https://en.wikipedia.org/wiki/Beacon_frame) and shares the observation w/a backend for storage and reporting.

Mellow Heeler collectors use [Raspberry Pi 3](https://www.raspberrypi.org/) augmented w/a USB WiFi adapter such as [TP Link AC1300](https://www.tp-link.com/us/home-networking/usb-adapter/archer-t3u-plus/).

## Notes
1. Autonomous collection of wireless beacons for 2.4 and 5 GHz using the iwlist(8) utility.

2. Each observation produces two output files: a copy of the current iwlist(8) output and a json summary of key features extracted from the iwlist(8) output along with observation metadata.

3. iwlist(8) must run from root crontab(1)

4. The collection pass runs from wombat crontab(1)

5. Output file directory is defined within config.yaml

## Sample JSON output
```
{
    "equipment": {
        "antenna": "whip",
        "receiverId": 2,
        "receiverType": "ac-1300",
        "hostName": "pi3b",
        "hostType": "rpi3"
    },
    "geoLoc": {
        "altitude": MSL in meters
        "latitude": +north decimal degress
        "longitude": +east decimal degrees
        "site": site name
    },
    "timeStamp": {
        "epochSeconds": collection time in seconds since epoch
        "iso8601": epochSeconds as a ISO861 string
    },
    "crate": "wombat04",
    "fileName": file name
    "mode": collection application (currently only "iwlist")
    "project": source project (currently "heeler-v2")
    "version": schema version (currently 1)
    "observations": [
        {
            "bssid": "E2:BB:9E:D0:B0:30",
            "frequency_mhz": 2437,
            "signal_dbm": -75,
            "ssid": "DIRECT-9ED03030",
            "capabilities": "wpa2-psk",
            "cipher_type": "CCMP"
        }
    ]
}
```