#! /usr/bin/env python3

import sqlite3
'''
from time import time
try:
  with sqlite3.connect('members.db') as conn:
    curs = conn.cursor()
    curs.execute('INSERT INTO members ("Member ID","Name","Activation")' + \
                    f'VALUES(51000013503246,\'Chase LP\',{round(time())})')
    curs.execute('INSERT INTO members ("Member ID","Name","Activation")' + \
                    f'VALUES(98765,\'Bob\',{round(time())+1})')
    conn.commit()
except sqlite3.IntegrityError:
  pass
'''
with sqlite3.connect('members.db') as conn:
  curs = conn.cursor()
  curs.execute('PRAGMA table_info(members)')
  schema = curs.fetchall()
  curs.execute('SELECT * from members')
  members = curs.fetchall()

print(schema)
for member in members:
  member = {field[1]:value for field, value in zip(schema, member)}
  print(member)

print(schema[0])
'''
for field in schema:
  for i, name in enumerate(['row', 'name', 'type', 'notnull', 'default', 'pk']):
    print(name, field[i], end=', ')
  print()
'''

with sqlite3.connect('trxn.db') as conn:
  curs = conn.cursor()
  curs.execute('PRAGMA table_info(transactions)')
  schema = curs.fetchall()
  curs.execute('SELECT * from transactions')
  transactions = curs.fetchall()

print(schema)
for transaction in transactions:
  print(transaction)
