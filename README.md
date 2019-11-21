# Monitoring Skript - Michael Muyakwa

[![license](https://img.shields.io/github/license/mashape/apistatus.svg?style=plastic)](https://github.com/mmuyakwa/bash-scripts/blob/master/LICENSE)

Ein kleines Tool um Systemwerte abzurufen.

Dieses Skript ist für 3 verschiedene Betriebssysteme ausgelegt.

- Linux
- Windows
- MacOS

Bisher ist nur der Part für **Linux** funktionstüchtig.

## Table of Contents

<!-- toc -->

* [Informationen zum Skript](#Informationen-zum-Skript)
* [Vorbereitung](#Vorbereitung)
* [Ausführung des Skript](#Ausführung-des-Skript)
* [Automatische Ausführung](#Automatische-Ausführung) 

<!-- toc stop -->

## Informationen zum Skript

Dieses Skript wurde in Python 3.7 geschrieben.

### Aufgaben dieses Tools
- Systemwerte auslesen:
    -   CPU
    -   Festplattenplatz
    -   RAM
- Logdatei schreiben (log.txt)
- INI-Datei auslesen mit den Schwellwerten und Email-Einstellungen (settings.ini)
- Alamierung via Email, wenn ein Schwellwert überschritten wurde

## Vorbereitung

Die Datei 'beispiel_settings.ini' muss umbenannt werden in 'settings.ini'.

Vor der Ausführung sollte die notwendigen Bibliotheken mit 'pip' geladen worden sein.

    pip install -r requirements.txt

In der "requirements.txt" sind derzeit 2 Bibliotheken aufgeführt.

- configparser==4.0.2
- psutil==5.6.3

## Ausführung des Skript

Das Skript kann mit dem Befehl:

    python run_monitor.py

ausgeführt werden.

## Automatische Ausführung 

### Linux via Cron

Durch editieren der Crontab
Crontab starten durch den Befehl:

    crontab -e

Zum Beispiel könnte das Skript alle 30 Minuten ausgeführt werden.

    30 * * * * python /pfad/zur/run_monitor.py > /dev/null 2>&1