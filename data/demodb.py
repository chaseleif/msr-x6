#! /usr/bin/env python3

import sqlite3
from time import time
try:
  with sqlite3.connect('members.db') as conn:
    curs = conn.cursor()
    for i in range(20):
      curs.execute('INSERT INTO members ("Member ID","Name","Activation","Expiration")' + \
                      f'VALUES(51{i}013503246,"Chase LP",{round(time())},{i})')
    conn.commit()
except sqlite3.IntegrityError:
  pass

with sqlite3.connect('members.db') as conn:
  curs = conn.cursor()
  curs.execute('PRAGMA table_info(members)')
  schema = curs.fetchall()
  curs.execute('SELECT * from members')
  members = curs.fetchall()

print(schema)
for member in members:
  for field, value in zip(schema, member):
    print(field[1], '=', value)

print(schema[0])
'''
for field in schema:
  for i, name in enumerate(['row', 'name', 'type', 'notnull', 'default', 'pk']):
    print(name, field[i], end=', ')
  print()
'''

with sqlite3.connect('members.db') as conn:
  curs = conn.cursor()
  name = 'chase'
  #curs.execute('SELECT * from members')
  curs.execute(f'SELECT * from members WHERE "Name" LIKE "%{name}%"')
  results = curs.fetchall()

print(results)

for result in results:
  print(result)

with sqlite3.connect('encodings.db') as conn:
  curs = conn.cursor()
  curs.execute('PRAGMA table_info(cards)')
  schema = curs.fetchall()
  curs.execute('SELECT * from cards')
  encodings = curs.fetchall()

print(schema)
for encoding in encodings:
  for field, value in zip(schema, encoding):
    print(field[1],'=',value)
