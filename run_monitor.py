#!/bin/python

# title:         run_monitor.py
# description:   This script is meant for monitoring Linux-Computers.
# author:        Michael Muyakwa - IT8g
# created:       2019-11-02
# updated:       2019-11-21
# version:       1.4
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

# Funktion um sowohl ins Log, wie auch als Ausgabe zu schreiben.
def splitPL(termStr):
    print(termStr)
    termStr = str(log_str + '\n' + termStr)
    writeLog(termStr)

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

    Ausgabe = ('CPU: %s' % cpu_p)
    Ausgabe += (' - Es laufen %s Prozesse' % num_processes)
    Ausgabe += ('\n%s Ram' % v_memory)
    Ausgabe += ('\n%s' % hdd_p)
    Ausgabe += (' - %s' % disk_str)
    mem_p = (used_m / tot_m * 100)

    values=psutil.virtual_memory()
    total_size = get_human_readable_size(values.total)
    Ausgabe += (' - Virtual Memory: %s' % (total_size))

    Ausgabe += (' - Total Mem:%s Used Mem:%s Free Mem:%s - %.2f Prozent in Benutzung.' % (tot_m, used_m, free_m, mem_p))
    splitPL(Ausgabe)
    checkAlarm(cpu_p, hdd_p, mem_p)

# Funktion zum prüfen ob Schwellwerte überschritten wurden.
def checkAlarm(cpu_p, hdd_p, mem_p):
    cpu_p = float(cpu_p)
    hdd_p = float(hdd_p)
    mem_p = float(hdd_p)
    if (cpu_p > (float(config['SCHWELLENWERTE']['CPU_P']))) or (hdd_p > (float(config['SCHWELLENWERTE']['HDD_P']))) or (mem_p > (float(config['SCHWELLENWERTE']['MEM_P']))):
        alarm = True
    # Prüfe ob ein Schwellwert überschritten wurde. Falls ja alamiere via Email.
    if alarm:
        writeLog('Alarm! Ein Schwellwert wurde überschritten.')
        runAlarm(cpu_p, hdd_p, mem_p); 

# Funktion zum alamieren, wenn ein Schwellwert überschritten wurde.
def runAlarm(cpu_p, hdd_p, mem_p):
    mail_host = config['EMAIL']['Smtp']
    mail_user = config['EMAIL']['Username']
    mail_pass = config['EMAIL']['Password']
    sender = config['EMAIL']['Absender']
    receivers = config['EMAIL']['Empfaenfger']
    daten = 'Es wurde ein Alarm ausgelöst. \nCPU: %s, HDD: %s, Mem: %s' % (cpu_p, hdd_p, mem_p)
    message = MIMEText(daten, 'plain', 'utf-8')
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

# Wandelt Werte aus PSUtils in brauchbare (gerundete) Größen um.
def get_human_readable_size(num):
    # Die verschiedenen Größenangaben in einer Variable.
    exp_str = [ (0, 'B'), (10, 'KB'),(20, 'MB'),(30, 'GB'),(40, 'TB'), (50, 'PB'),]               
    i = 0
    #While-Schleife prüft ob die nächst große Größenangabe sinnvoller ist.
    while i+1 < len(exp_str) and num >= (2 ** exp_str[i+1][0]):
        i += 1
        rounded_val = round(float(num) / 2 ** exp_str[i][0], 2)
    return '%s %s' % (int(rounded_val), exp_str[i][1])

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
    


# Ab hier startet der Lauf des Skript
if __name__ == '__main__':
    main()
