#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import mysql

def list_users():
    user_list = []
    files = [f for f in os.listdir('.') if os.path.isfile(f)]
    for f in files:
        if f.endswith(".db"):
	    user = f.replace("_fitbit.db", "")
	    if ".db" not in user:
	        user_list.append(user)
    return user_list
  
def create_user(user):
    mysql.crear_tabla(user + '_fitbit.db')

#create_user('amaia')
#print list_users()