#! /usr/bin/env python3

import sqlite3
from secrets import randbelow
from time import localtime, mktime, struct_time, time

class DataBase:
  idlength = 10
  def __init__(self, memberdb='data/members.db', trxndb='data/trxn.db'):
    self.memberdb = memberdb
    with sqlite3.connect(memberdb) as conn:
      curs = conn.cursor()
      curs.execute('PRAGMA table_info(members)')
      schema = curs.fetchall()
    self.memberprotected = tuple(col[1] for col in schema if col[3] == 1)
    self.memberfieldtypes = {col[1]:col[2] for col in schema}
    self.memberdefaults = {col[1]:col[4] for col in schema}
    self.trxndb = trxndb
    with sqlite3.connect(trxndb) as conn:
      curs = conn.cursor()
      curs.execute('PRAGMA table_info(transactions)')
      schema = curs.fetchall()
    self.trxndefaults = {col[1]:col[4] for col in schema}

  def getmember(self, memberid):
    with sqlite3.connect(self.memberdb) as conn:
      curs = conn.cursor()
      curs.execute(f'SELECT * FROM members WHERE "Member ID"={memberid};')
      member = curs.fetchall()
      if len(member) == 0:
        return None
      curs.execute('PRAGMA table_info(members)')
      schema = curs.fetchall()
    member = {field[1]:value for field,value in zip(schema,member[0])}
    return member

  def generatememberid(self):
    with sqlite3.connect(self.memberdb) as conn:
      member = [1]
      while len(member) != 0:
        memberid = randbelow(10**(DataBase.idlength-2))
        memberid += (randbelow(9)+1) * 10**(DataBase.idlength-1)
        curs = conn.cursor()
        curs.execute(f'SELECT * FROM members WHERE "Member ID"={memberid};')
        member = curs.fetchall()
    return memberid

  def addmember(self, member):
    member['Member ID'] = self.generatememberid()
    member['Activation'] = round(time())
    cmd = 'INSERT INTO members ("Member ID",Name,Activation'
    for field in member:
      if field in ('Member ID','Name','Activation') or member[field] == '':
        continue
      cmd += f',"{field}"'
    cmd += ') VALUES('
    for i, field in enumerate(('Member ID','Name','Activation')):
      if i > 0:
        cmd += ','
      cmd += f'"{member[field]}"'
    for field in member:
      if field in ('Member ID','Name','Activation') or member[field] == '':
        continue
      cmd += f',"{member[field]}"'
    cmd += ')'
    with sqlite3.connect(self.memberdb) as conn:
      curs = conn.cursor()
      curs.execute(cmd)
      conn.commit()
    return member

  def deletemember(self, member):
    with sqlite3.connect(self.memberdb) as conn:
      curs = conn.cursor()
      curs.execute(f'DELETE FROM members WHERE "Member ID"={member}')
      conn.commit()

  def editmember(self, memberid, modified):
    cmd = f'UPDATE members SET('
    quote = lambda s: f'"{s}"' if ' ' in f'{s}' else f'{s}'
    for count, field in enumerate(modified):
      if count > 0:
        cmd += ', '
      cmd += f'{quote(field)}'
    cmd += ') = ('
    for count, field in enumerate(modified):
      if count > 0:
        cmd += ', '
      if modified[field] == '':
        modified[field] = self.memberdefaults[field]
      cmd += f'{quote(modified[field])}'
    cmd += f') WHERE "Member ID"={memberid};'
    with sqlite3.connect(self.memberdb) as conn:
      curs = conn.cursor()
      curs.execute(cmd)
      conn.commit()

  def startofday(self):
    now = localtime(time())
    now = ( now.tm_year, now.tm_mon,
            mow.tm_mday-1 if now.tm_hour < 2 else now.tm_mday,
            0, 0, 0, 0, 0, -1)
    now = mktime(struct_time(now))
    return round(now)

  def lastmemberdays(self, memberid):
    with sqlite3.connect(self.memberdb) as conn:
      curs = conn.cursor()
      cmd = f'SELECT "Last day" from members ' + \
            f'WHERE "Member ID"={memberid};'
      curs.execute(cmd)
      lastday = curs.fetchall()[0][0]
      cmd = f'SELECT "Last day" from members ' + \
            f'WHERE "Member ID"={memberid};'
      curs.execute(cmd)
      lastleagueday = curs.fetchall()[0][0]
    return lastday, lastleagueday

  def trxn(self, transaction):
    memberid = transaction['Member ID']
    transaction['Time'] = round(time())
    cmd = 'INSERT INTO transactions ('
    for count, col in enumerate(transaction):
      if count > 0:
        cmd += ', '
      cmd += f'"{col}"'
    cmd += ') VALUES ('
    for count, col in enumerate(transaction):
      if transaction[col] == '':
        transaction[col] = self.trxndefaults[col]
      if count > 0:
        cmd += ', '
      cmd += f'"{transaction[col]}"'
    cmd += ');'
    with sqlite3.connect(self.trxndb) as conn:
      curs = conn.cursor()
      curs.execute(cmd)
      conn.commit()
    now = self.startofday()
    lastday, lastleagueday = self.lastmemberdays(memberid)
    with sqlite3.connect(self.memberdb) as conn:
      curs = conn.cursor()
      cmd = 'UPDATE members SET "Transactions"="Transactions"+1'
      if now > lastday:
        cmd += ', "Days"="Days"+1'
        cmd += f', "Last day"="{now}"'
      if transaction['League day'] == 1 and now > lastleagueday:
        cmd += ', "League days"="League days"+1'
        cmd += f', "Last league day"="{now}"'
      if float(transaction['Total spent']) > 0:
        cmd += f', "Total spent"="Total spent"+{transaction["Total spent"]}'
      if float(transaction['Total hours']) > 0:
        cmd += f', "Total hours"="Total hours"+{transaction["Total hours"]}'
      cmd += f' WHERE "Member ID"={memberid}'
      curs.execute(cmd)
      conn.commit()
