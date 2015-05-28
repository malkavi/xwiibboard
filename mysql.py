#!/usr/bin/python
# -*- coding: utf-8 -*-

import sqlite3 as lite
import sys

def guardar_peso(usuario, peso):
    con = lite.connect(usuario + '_fitbit.db')

    with con:

        cur = con.cursor()
        #weight table
        #cur.execute("CREATE TABLE IF NOT EXISTS weight(CURRENT_DATE DATETIME PRIMARY KEY NOT NULL  DEFAULT (CURRENT_DATE), weight REAL)")
        cur.execute("INSERT OR REPLACE INTO weight (CURRENT_DATE, weight) VALUES (DATE('now'), "+str(peso)+")")

def crear_tabla(db_file):
    con = lite.connect(db_file)

    with con:

        cur = con.cursor()
        #weight table
        cur.execute("CREATE TABLE IF NOT EXISTS weight(CURRENT_DATE DATETIME PRIMARY KEY NOT NULL  DEFAULT (CURRENT_DATE), weight REAL)")
        #cur.execute("INSERT OR REPLACE INTO weight (CURRENT_DATE, weight) VALUES (DATE('now'), "+str(peso)+")")