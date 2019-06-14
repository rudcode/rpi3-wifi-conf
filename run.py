#!/usr/bin/env python3

import os
import subprocess
import time
from bluetooth import *

wpa_supplicant_conf = "/etc/wpa_supplicant/wpa_supplicant.conf"
sudo_mode = "sudo "

def wifi_connect(ssid, psk):
    # write wifi config to file
    with open('wifi.conf', 'w') as f:
        f.write('country=ID\n')
        f.write('ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev\n')
        f.write('update_config=1\n')
        f.write('\n')
        f.write('network={\n')
        f.write('    ssid="%s"\n' % ssid)
        f.write('    psk="%s"\n' % psk)
        f.write('}\n')

    cmd = 'mv wifi.conf %s' % wpa_supplicant_conf
    cmd_result = os.system(cmd)
    print("%s - %d" % (cmd, cmd_result))

    # restart wifi adapter
    cmd = sudo_mode + 'ip link set wlan0 down'
    cmd_result = os.system(cmd)
    print("%s - %d" % (cmd, cmd_result))

    time.sleep(2)

    cmd = sudo_mode + 'ip link set wlan0 up'
    cmd_result = os.system(cmd)
    print("%s - %d" % (cmd, cmd_result))

    ip_address = "Not Set (Time Out)"
    time_out = time.time() + 25
    
    while True:
        if time.time() < time_out:
            p = subprocess.Popen(['ifconfig', 'wlan0'], stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            out, err = p.communicate()
            out = out.decode()
            #print(out)
            for l in out.split('\n'):
                if l.strip().startswith("inet "):
                    ip_address = l.strip().split(' ')[1]
                    return ip_address
            time.sleep(1)
        else:
            break
    return ip_address

def handle_client(client_sock):
    try:
        client_sock.send("waiting command!")
        print("Waiting for Command...")
        command = client_sock.recv(1024).decode()
        print(command)
        if command == "network":
            # get ssid
            client_sock.send("waiting ssid!")
            print("Waiting for SSID...")

            ssid = client_sock.recv(1024).decode()
            if ssid == '' :
                return

            print("ssid received")
            print(ssid)

            # get psk
            client_sock.send("waiting-psk!")
            print("Waiting for PSK...")

            psk = client_sock.recv(1024).decode()
            if psk == '' :
                return

            print("psk received")
            print(psk)
            
            ip_address = wifi_connect(ssid, psk)

            print("ip address: " + ip_address)

            client_sock.send("ip-addres:" + ip_address + "!")

    except Exception as ex:
        print(ex)

    return

try:
    while True:
        try:
            server_sock = BluetoothSocket( RFCOMM )
            server_sock.bind(("",PORT_ANY))
            server_sock.listen(1)

            port = server_sock.getsockname()[1]
            
            uuid = "815425a5-bfac-47bf-9321-c5ff980b5e11"

            advertise_service( server_sock, "RPi Wifi config",
                               service_id = uuid,
                               service_classes = [ uuid, SERIAL_PORT_CLASS ],
                               profiles = [ SERIAL_PORT_PROFILE ])

            
            print("Waiting for connection on RFCOMM channel %d" % port)

            client_sock, client_info = server_sock.accept()
            print("Accepted connection from ", client_info)

            handle_client(client_sock)

            client_sock.close()
            server_sock.close()

            # finished config
            print("Finished configuration\n")
            
        except Exception as ex:
            print(ex)

except (KeyboardInterrupt, SystemExit):
    print("\nExiting\n")
