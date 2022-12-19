#!/usr/bin/env python3

#
# Imports
#
import sys
try:
    import requests
except ImportError as ie:
    print(ie)
    # python3 -m pip install requests
    sys.exit("Please install python-requests!")
try:
    import urllib3
except ImportError as ie:
    print(ie)
    # This comes as dependency of requests, so should always be there.
    # python3 -m pip install urllib3
    sys.exit("Please install urllib3!")
import argparse
import getpass
import re
import json
import csv
import datetime
#import pdb

def omnivista_login(ov_hostname, ov_username, ov_password, ov_header, check_certs):
    ov_login_data = {"userName" : ov_username, "password" : ov_password}

    omnivista_login = requests.post(f"https://{ov_hostname}/rest-api/login",
                                    headers=ov_header,
                                    json=ov_login_data,
                                    verify=check_certs)
    if omnivista_login.status_code == 200:
        return f"Bearer {omnivista_login.json()['accessToken']}"
    else:
        sys.exit(f"Login to OmniVista @ {ov_hostname} failed with message: {omnivista_login.json()['message']}")

def omnivista_logout(ov_hostname, ov_header, check_certs):
    omnivista_logout = requests.get(f"https://{ov_hostname}/rest-api/logout",
                                    headers=ov_header,
                                    verify=check_certs)

def get_ap_detail(ov_hostname, ov_header, check_certs, ap_mac):
    ap_detail = requests.get(f"https://{ov_hostname}/api/wma/accessPoint/getAPByAPMac?apMac={ap_mac}",
                            headers=ov_header,
                            verify=check_certs)
    if ap_detail.json()["data"]:
        return ap_detail.json()["data"]
    else:
        return False

def update_ap_detail(ov_hostname, ov_header, check_certs, ap_update_details):
    ap_update = requests.post(f"https://{ov_hostname}/api/wma/accessPoint/editAP",
                            headers=ov_header,
                            json=ap_update_details,
                            verify=check_certs)
    if ap_update.json()["data"]:
        return ap_update.json()["data"]
    else:
        return False

def main():
    print("Stellar Wireless CSV2AP API helper by Benny Eggerstedt (2022)")

    parser = argparse.ArgumentParser()
    ovinfo = parser.add_mutually_exclusive_group()
    ovinfo.add_argument("-i", "--ov-ip", help="IPv4 address of OmniVista 2500/Cirrus 4.x", required=False)
    ovinfo.add_argument("-f", "--ov-fqdn", help="FQDN of OmniVista 2500/Cirrus 4.x", required=False)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-k", "--insecure", action="store_true", help="If specified the HTTPS/TLS certificate will NOT be validated (Default)", required=False)
    group.add_argument("-c", "--check-certificates", action="store_true", help="If specified the HTTPS/TLS certificate will be validated", required=False)
    parser.add_argument("-u", "--ov-username", help="Username to be used for the login to OmniVista 2500/Cirrus 4.x (Default=admin)", required=False)
    parser.add_argument("-p", "--ov-password", help="Password to be used for the login to OmniVista 2500/Cirrrus 4.x (Default=ASK_INTERACTIVE)", required=False)
    parser.add_argument("-x", "--csv-input-file", help="CSV input file that expects \"column 1 AP-MAC, column 2 AP-Location\"", required=True)
    parser.add_argument("-d", "--csv-delimiter", help="CSV delimiter to be used (DEFAULT: \",\")", required=False)
    args = parser.parse_args()

    # If TLS certificates should be checked or use default "False"
    if args.check_certificates:
        check_certs = True
    else:
        # Ignore self-signed certificate warnings
        check_certs = False
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Get OV user from args or use default "admin"
    if args.ov_username:
        ov_username = args.ov_username
    else:
        ov_username = "admin"

    # Get OV password from args (bad idea, please mind your console history) or interactive
    if args.ov_password:
        ov_password = args.ov_password
    else:
        ov_password = getpass.getpass()

    # Get our target OV IP/FQDN
    if args.ov_ip:
        ov_hostname = args.ov_ip
    else:
        ov_hostname = args.ov_fqdn
    
    # Get CSV delimiter from args or set default
    if args.csv_delimiter:
        csv_delimiter = args.csv_delimiter
    else:
        csv_delimiter = ","

    # Sanitise OV_HOSTNAME input
    p = re.compile("^(?:http:\/\/|https:\/\/)?([\w\.\-]*)\/?$")
    m = p.match(ov_hostname)
    if ov_hostname == m.group(1):
        pass
    elif len(m.group(1)) > 0:
        print(f"Updated OV_HOSTNAME from {ov_hostname} to {m.group(1)}")
        ov_hostname = m.group(1)
    else:
        sys.exit("Could not sanitise OV IP/FQDN! Please review your input! It should read like 1.2.3.4 or omnivista.home!")

    # Prepare ov_header for all following activities
    ov_header = {"Content-Type": "application/json"}

    # Login to OmniVista and obtain accessToken
    ov_header["Authorization"] = omnivista_login(ov_hostname, ov_username, ov_password, ov_header, check_certs)

    csv_output_file = open(f"results_{datetime.datetime.now().strftime('%d%m%Y_%H%M%S')}.csv", "w")
    csvwriter = csv.writer(csv_output_file, delimiter=csv_delimiter)
    csvwriter.writerow(["apMac", "apLocation-OLD", "apLocation-NEW", "Result"])

    with open(args.csv_input_file) as csv_input_file:
        csv_has_header = csv.Sniffer().has_header(csv_input_file.read(1024))
        csv_input_file.seek(0)
        csvreader = csv.reader(csv_input_file, delimiter=csv_delimiter)
        if csv_has_header:
            print("Header row was detected in CSV input file, skipping first row!")
            next(csvreader, None)
        
        for row in csvreader:
            ap_detail = get_ap_detail(ov_hostname, ov_header, check_certs, row[0])
            if ap_detail:
                ap_detail = json.loads(json.dumps(ap_detail))
                ap_update_details = {
                    "apMac":ap_detail['macAddress'],
                    "apLocation":row[1],
                    "groupName":ap_detail['apGroups']['groupName'],
                    "apName":ap_detail['apName'],
                    "lldpSwitch":ap_detail['lldpSwitch']
                }
                # Handle the case of a specific RF profile
                if ap_detail['profile']:
                    ap_update_details['profileId'] = ap_detail['profile']['id']
                
                # Handle the case of a specific geo location
                if ap_detail['geoLocation']:
                    ap_update_details['geoLocation'] = ap_detail['geoLocation']

                update_ap_detail_resp = update_ap_detail(ov_hostname, ov_header, check_certs, ap_update_details)
                if update_ap_detail_resp[0]['success']:
                    csvwriter.writerow([ap_detail['macAddress'],ap_detail['location'],row[1],"SUCCESS"])
                    print(f"Update for AP {ap_detail['macAddress']}/{ap_detail['apName']} location to {row[1]} successful!")
                else:
                    csvwriter.writerow([ap_detail['macAddress'],ap_detail['location'],row[1],"FAILED"])
                    print(f"Changing location for AP {ap_detail['macAddress']}/{ap_detail['apName']} to {row[1]} failed!")
            else:
                csvwriter.writerow([row[0],"","","AP_NOT_FOUND"])
                print(f"AP {row[0]} couldn't be found!")

    csv_output_file.close()
    omnivista_logout(ov_hostname, ov_header, check_certs)
    print("Work finished!")

if __name__ == "__main__":
    main()
