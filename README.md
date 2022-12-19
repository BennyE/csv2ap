# csv2ap

CSV2AP allows to set certain parameters starting with AP Location from a CSV via OmniVista 2500 / Cirrus 4.x API

## Usage (-h)

```
$ python3 csv2ap.py -h
Stellar Wireless CSV2AP API helper by Benny Eggerstedt (2022)
usage: csv2ap.py [-h] [-i OV_IP | -f OV_FQDN] [-k | -c] [-u OV_USERNAME] [-p OV_PASSWORD] -x CSV_INPUT_FILE [-d CSV_DELIMITER]

options:
  -h, --help            show this help message and exit
  -i OV_IP, --ov-ip OV_IP
                        IPv4 address of OmniVista 2500/Cirrus 4.x
  -f OV_FQDN, --ov-fqdn OV_FQDN
                        FQDN of OmniVista 2500/Cirrus 4.x
  -k, --insecure        If specified the HTTPS/TLS certificate will NOT be validated (Default)
  -c, --check-certificates
                        If specified the HTTPS/TLS certificate will be validated
  -u OV_USERNAME, --ov-username OV_USERNAME
                        Username to be used for the login to OmniVista 2500/Cirrus 4.x (Default=admin)
  -p OV_PASSWORD, --ov-password OV_PASSWORD
                        Password to be used for the login to OmniVista 2500/Cirrrus 4.x (Default=ASK_INTERACTIVE)
  -x CSV_INPUT_FILE, --csv-input-file CSV_INPUT_FILE
                        CSV input file that expects "column 1 AP-MAC, column 2 AP-Location"
  -d CSV_DELIMITER, --csv-delimiter CSV_DELIMITER
                        CSV delimiter to be used (DEFAULT: ",")
```

## Example

Note: The communication will always be HTTPS, the example below intends to showcase the sanitation of input paramters
```
$ python3 csv2ap.py --ov-fqdn http://omnivista.home --csv-input-file AP_Location.csv
Stellar Wireless CSV2AP API helper by Benny Eggerstedt (2022)
Password: 
Updated OV_HOSTNAME from http://omnivista.home to omnivista.home
Header row was detected in CSV input file, skipping first row!
AP dc:08:56:aa:aa:aa couldn't be found!
Update for AP dc:08:56:bb:bb:bb/TestAP location to Wohnzimmer successful!
...
Work finished!
```

### Example CSV_INPUT_FILE

```
MAC,AP_Location
dc:08:56:aa:aa:aa,New-LocationA
dc:08:56:bb:bb:bb,New-LocationB
```

## Features

- CSV2AP.py allows you to ignore self-signed certificates, thus works with on-premises VAs
- CSV2AP.py requires a CSV_INPUT_FILE with column-1 with AP-MAC and column-2 with desired new AP-Location
  - Note that setting the AP location manually is a corner-case, as usually you'd want to discover this via LLDP from upstream OmniSwitch
- CSV2AP.py will discover other AP-specific settings (such as RF profile & geoLocation) and maintain them while setting the new AP location
- CSV2AP.py allows you to specify your desired CSV_DELIMITER and will use this also for the resulting output CSV
- CSV2AP.py will write a results_date_time.csv as shown below to let you track the changes

```
apMac,apLocation-OLD,apLocation-NEW,Result
dc:08:56:09:4e:90,,,AP_NOT_FOUND
dc:08:56:bb:bb:bb,Wohnzimmer-Test2,Wohnzimmer,SUCCESS
dc:08:56:cc:cc:cc,,,AP_NOT_FOUND
dc:08:56:dd:dd:dd,,,AP_NOT_FOUND
```

## TODO

- CSV2AP.py doesn't currently work with Multi-Tenancy managed OmniVista Cirrus tenants
  - Login directly to the corresponding tenant as a workaround
- CSV2AP.py doesn't currently support the authentication to 2FA-enabled tenants
  - Raise an issue here or vote if this is needed, then I'll spend time to implement this
