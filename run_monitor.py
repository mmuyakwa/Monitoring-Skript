#!/bin/python

# title:         run_monitor.py
# description:   This script is meant for monitoring Linux-Computers.
# author:        Michael Muyakwa - IT8g
# created:       2019-11-02
# updated:       2019-11-07
# version:       1.0
# license:       MIT

# Imports der verwendeten Bibliotheken.
import os  # Betriebssystem-Informationen
import sys  # System-Informationen
import platform  # Platform-Informationen
import psutil  # Um Infos vom System zu erhalten. (Leider nicht 100% zuverlässige Informationen.)
import configparser  # Spezielle Bibliothek für INI-Files
import datetime  # Parsen und formatieren vom Datum
import smtplib  # Zum verschicken der Alarm-Email, wenn Schwellwerte überschritten wurden.
import email.utils
from email.mime.text import MIMEText # MIMEtypes für Email-Inhalt.
from email.header import Header # Header für Email.

# Setze Variablen auf, die im Verlauf verwendet werden. (Nur Variablen, die unter jeder Platform funktionieren.)

# Pfade zu den verwendeten Dateien.
pathname = os.path.dirname(os.path.realpath(__file__))  # Pfad vom Ordner in dem das Skript liegt.
iniFile = os.path.abspath(pathname) + '/settings.ini'  # Pfad zum INI-File
logFile = os.path.abspath(pathname) + '/log.txt'  # Pfad zum Log-File

# Handler für die INI-Datei.
config = configparser.ConfigParser()  # Objekt um mit dem INI-File zu arbeiten.
config.read(iniFile)  # Lese das INI-File ein.

hostname = platform.node() # Hostname

# Variable für das Logging
log_str = str(hostname + ': ' + (datetime.datetime.now()).strftime("%Y-%m-%d %H:%M:%S"))
alarm = False  # Wird auf True gesetzt wenn ein vorgegebener Schwellwert überschritten wurde.


# Funktionen

# Log-Funktion
def writeLog(logStr):
    f = open(logFile, "a+")  # Öffne Log-Datei im Append-Mode
    f.write(logStr)  # Schreibe in die Log-Datei.
    f.write('\n')  # Setze eine leere neue Zeile am Ende der Log-Datei.
    f.close()  # Gebe Zugriff auf das Log-File wieder frei.

# Funktion für Linux-Clients.
def mon_linux():
    print("This is a Linux-Environment.")

    # setze Variablen auf, die im Verlauf verwendet werden (Linux only).
    cpu_p = (round(float(
        os.popen('''grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage }' ''').readline()),
        2))
    v_memory = psutil.virtual_memory()[2]
    hdd_p = psutil.disk_usage('/')[3]
    ds = os.statvfs('/')
    tot_m, used_m, free_m = map(int, os.popen('free -t -m').readlines()[-1].split()[1:])
    num_processes = psutil.Process().children()
    disk_str = {"Used": ((ds.f_blocks - ds.f_bfree) * ds.f_frsize) / 10 ** 9,
                "Unused": (ds.f_bavail * ds.f_frsize) / 10 ** 9}

    print('CPU: %s' % cpu_p)
    print('Es laufen %s Prozesse' % num_processes)
    print('%s Ram' % v_memory)
    print(hdd_p)
    print(disk_str)
    mem_p = (used_m / tot_m * 100)
    print('Total Mem:%s Used Mem:%s Free Mem:%s - %.2f Prozent in Benutzung.' % (tot_m, used_m, free_m, mem_p))
    writeLog(log_str)

# Funktion zum prüfen ob Schwellwerte überschritten wurden.
def checkAlarm(cpu_p, hdd_p, mem_p):
    if (cpu_p > config['SCHWELLENWERTE']['CPU_P']) or (hdd_p > config['SCHWELLENWERTE']['HDD_P']) or (mem_p > config['SCHWELLENWERTE']['MEM_P']):
        alarm = True

# Funktion zum alamieren, wenn ein Schwellwert überschritten wurde.
def runAlarm():
    mail_host = config['EMAIL']['Smtp']
    mail_user = config['EMAIL']['Username']
    mail_pass = config['EMAIL']['Password']
    sender = config['EMAIL']['Absender']
    receivers = config['EMAIL']['Empfaenfger']
    message = MIMEText('Es wurde ein Alarm ausgelöst.', 'plain', 'utf-8')
    message['From'] = Header(sender, 'utf-8')
    message['To'] = Header(receivers, 'utf-8')
    message['Subject'] = Header('Es wurde ein Alarm ausgelöst.', 'utf-8')
    port = config['EMAIL']['Port']

    smtp_obj = smtplib.SMTP(mail_host, port)
    smtp_obj.set_debuglevel(True)

    try:
        # Kontakt mit dem SMTP aufnehmen um Verschlüsselung via TLS zu ermöglichen. First Handshake.
        # Fähigkeiten des SMTP-Server erfahren. (Erwarte Rückmeldung ob TLS unterstützt wird.)
        smtp_obj.ehlo()

        # Wenn der Server TLS unterstützt, mit TLS-Verschlüsselung weiter machen.
        if smtp_obj.has_extn('STARTTLS'):
            smtp_obj.starttls()
            smtp_obj.ehlo() # Erneut Kontakt aufnehmen MIT TLS-Verschlüsselung.

        smtp_obj.login(mail_user, mail_pass)
        smtp_obj.sendmail(sender, receivers, message.as_string())
        info_str = 'Alarm-Email wurde verschickt.'
        print(info_str)
        writeLog(info_str)
    except smtplib.SMTPException:
        err_str = 'Beim versenden der Email ist ein Fehler aufgetreten.'
        print(err_str); writeLog(err_str)
    finally:
        smtp_obj.quit()

# Hauptfunktion.
def main():
    # Prüfe das Betriebsystem. (Lin/Win)
    if platform.system() == "Linux":
        mon_linux()
    # Könnte das Skript hier auf Windows erweitern.
    elif platform.system() == "Windows":
        print("You are not running this Script on a Linux-Environment.")
        writeLog('This System is not a Linux-System.')
        sys.exit(1)
    # Könnte das Skript hier auf Mac erweitern mit 'elif platform.system() == "Mac":'.
    elif platform.system() == "Darwin":
        print("You are not running this Script on a Linux-Environment.")
        writeLog('This System is not a Linux-System.')
        sys.exit(1)
    # Falls doch ein komplett unbekanntes System vorgefunden wird. (NOT "Lin/Win/Mac")
    else:
        print("You are not running this Script on a Linux-Environment.")
        writeLog('This System is not a Linux-System.')
        sys.exit(1)
    # Prüfe ob ein Schwellwert überschritten wurde. Falls ja alamiere via Email.
    if alarm:
        runAlarm(); writeLog('Alarm! Ein Schwellwert wurde überschritten.')


# Ab hier startet der Lauf des Skript
if __name__ == '__main__':
    main()
