# mellow-heeler-v2
[Wireless Access Point](https://en.wikipedia.org/wiki/Wireless_access_point) collection application for [Mellow Wombat](https://github.com/guycole/mellow-wombat) crates.

## Introduction
A Mellow Heeler client observes [wireless beacons](https://en.wikipedia.org/wiki/Beacon_frame) and shares the observation w/a backend for storage and reporting.

Mellow Heeler collectors use [Raspberry Pi 3](https://www.raspberrypi.org/) augmented w/a USB WiFi adapter such as [TP Link AC1300](https://www.tp-link.com/us/home-networking/usb-adapter/archer-t3u-plus/) because the onboard WiFi performance is poor.  

[Mellow Peccary](https://github.com/guycole/mellow-peccary) hosts provide the provide the long term storage and analysis of Heeler observations.

## Mellow Wombat services
1. Time synchronization and internet gateway access.

2. There is bootboy support for dynamic configuration of the collector, but a heeler typically will only have the USB WiFi adapter and not have a RTL-SDR radio connected.  Note that bootboy produces config.yaml which the collector relies upon.

3. Format validation of observation files.

4. Sharing latest observation with [Mellow Koala](https://github.com/guycole/mellow-koala).

5. Batching observation files into compressed tar files and uploading to AWS S3 (for archive and sharing with [Mellow Peccary](https://github.com/guycole/mellow-peccary)).

## Mellow Peccary services
1. Long term storage and analysis of Heeler observations

## Collection cycle
1. Autonomous collection of wireless beacons for 2.4 and 5 GHz using the iwlist(8) utility [iwlist-scan.sh](https://github.com/guycole/mellow-heeler-v2/blob/main/bin/iwlist-scan.sh) (must run as root).

2. [collector.sh](https://github.com/guycole/mellow-heeler-v2/blob/main/bin/collector.sh) is invoked from the wombat crontab(1).  Each observation produces two output files: a copy of the current iwlist(8) raw output and a json summary of key features extracted from the iwlist(8) output along with observation metadata.

3. The two output files are placed in the "fresh" directory where rsync(1) will move from collector to gateway.  "Fresh" file directory is defined within config.yaml

## Sample JSON output
[complete sample](https://github.com/guycole/mellow-heeler-v2/blob/readme_update/samples/fe1e8800-97f6-43fe-b601-cbc15b4ddb93.json)
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
        "siteName": site name
    },
    "job": {
        "mode": "iwlist",
        "project": "heeler-v2",
        "task": "heeler-v2-iwlist"
    },
    "timeStamp": {
        "epochSeconds": collection time in seconds since epoch
        "iso8601": epochSeconds as a ISO861 string
    },
    "crateName": "wombat04",
    "fileName": file name
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

## Wombat validation cycle
Validation is performed on the wombat gateway by [wombat_docker](https://github.com/guycole/mellow-heeler-v2/tree/main/src/wombat_docker).  

If both the "json" and "raw" files are present on the Wombat gateway, the json file is tested for readability and json schema correctness.  Failed files are moved to the "failure" directory and successful files go to "heeler/success" for additional processing.  

wombat_docker also updates postgres tables to keep simple statistics on collection.

[validator.sh](https://github.com/guycole/mellow-heeler-v2/blob/main/bin/validator.sh) is invoked from the wombat crontab and is the correct way to run the validator — it wraps the `docker run` invocation below.

Build and run from the `src/` directory:
```sh
# build
docker build --build-arg WOMBAT_UID=$(id -u wombat) --build-arg WOMBAT_GID=$(id -g wombat) \
  -f wombat_docker/Dockerfile -t wombat:latest .

# run validator
docker run -e stuntbox=validator -v /var/wombat:/mnt/wombat --name wombat wombat:latest

# run koala
docker run -e stuntbox=koala --name wombat wombat:latest
```

### Mellow Koala cycle
[Mellow Koala](https://github.com/guycole/mellow-koala) is only concerned about the most recent load cycle.  Every validation pass should find the most recent observation to write to "heeler/koala" and then invoke [koala-import.sh](https://github.com/guycole/mellow-heeler-v2/blob/main/bin/koala-import.sh) to consume the latest observation.

## Wombat archival cycle
[archiver.sh](https://github.com/guycole/mellow-heeler-v2/blob/main/bin/archiver.sh) collects the files from "heeler/success" and saves a tar file with both the json and raw files into the "heeler/archive" directory, then saves a tar file with only the json files into the "heeler/export" directory.  Export files are written to S3 and then deleted, while archive files remain on the gateway indefinitely.  

## Peccary import cycle
Peccary loading is performed by [peccary_docker](https://github.com/guycole/mellow-heeler-v2/tree/main/src/peccary_docker).  All of the collected observation is stored in postgres for future analysis.

Peccary imports heeler tar files from AWS S3 to load.

Build and run from the `src/` directory:
```sh
# build
docker build --build-arg WOMBAT_UID=$(id -u wombat) --build-arg WOMBAT_GID=$(id -g wombat) \
  -f peccary_docker/Dockerfile -t peccary:latest .

# run
docker run -v /var/peccary:/mnt/peccary --name peccary peccary:latest
```