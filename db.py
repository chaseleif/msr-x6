#! /usr/bin/env python3

import os, sqlite3, sys
from secrets import randbelow
from time import localtime, mktime, struct_time, time

class DataBase:
  idlength = 10
  def __init__(self,
                memberdb=os.path.join('data', 'members.db'),
                encodingsdb=os.path.join('data', 'encodings.db')):
    try:
      self.memberdb = os.path.join(sys._MEIPASS, memberdb)
    except AttributeError:
      self.memberdb = memberdb
    with sqlite3.connect(self.memberdb) as conn:
      curs = conn.cursor()
      curs.execute('PRAGMA table_info(members);')
      schema = curs.fetchall()
    self.memberprotected = tuple(col[1] for col in schema if col[3] == 1)
    self.memberfieldtypes = {col[1]:col[2] for col in schema}
    self.memberdefaults = {col[1]:col[4] for col in schema}
    self.member_timeidx = tuple(idx for idx,field \
                                  in enumerate(self.memberdefaults.keys()) \
                                  if field in ( 'Activation',
                                                'Expiration'
                                                'Last day',
                                                'Last swipe')
                                )
    try:
      self.encodingsdb = os.path.join(sys._MEIPASS, encodingsdb)
    except AttributeError:
      self.encodingsdb = encodingsdb
    with sqlite3.connect(self.encodingsdb) as conn:
      curs = conn.cursor()
      curs.execute('PRAGMA table_info(cards);')
      schema = curs.fetchall()
    self.encodingcols = tuple([col[1] for col in schema])

  def epoch2str(self, ts):
    if ts == 0:
      return 'Never'
    ts = localtime(ts)
    s = f'{ts.tm_mon}/{ts.tm_mday}/{ts.tm_year} '
    s += f'{ts.tm_hour-12 if ts.tm_hour>12 else ts.tm_hour}:{ts.tm_min:02d}'
    s += 'AM' if ts.tm_hour < 12 else 'PM'
    return s

  def findmember(self, query):
    with sqlite3.connect(self.memberdb) as conn:
      curs = conn.cursor()
      curs.execute(f'SELECT * FROM members WHERE "Name" LIKE "%{query}%";')
      results = curs.fetchall()
    for i in range(len(results)):
      results[i] = tuple( self.epoch2str(field)
                            if idx in self.member_timeidx \
                            else field \
                            for idx, field in enumerate(results[i])
                        )
    return results

  def getmember(self, memberid):
    with sqlite3.connect(self.memberdb) as conn:
      curs = conn.cursor()
      curs.execute(f'SELECT * FROM members WHERE "Member ID"={memberid};')
      member = curs.fetchall()
      if len(member) == 0:
        return None
      curs.execute('PRAGMA table_info(members);')
      schema = curs.fetchall()
    member = {field[1]:value for field,value in zip(schema,member[0])}
    for idx in self.member_timeidx:
      member[list(self.memberdefaults.keys())[idx]] = \
        self.epoch2str(member[list(self.memberdefaults.keys())[idx]])
    return member

  def verifymember(self, membertracks):
    with sqlite3.connect(self.encodingsdb) as conn:
      curs = conn.cursor()
      curs.execute(f'SELECT * FROM cards WHERE "Member ID"={membertracks[0]};')
      cards = curs.fetchall()
    if len(cards) == 0:
      return f'No cards have been issued for Member ID {membertracks[0]}'
    if len(cards) == 0:
      return None
    for card in cards:
      print(f'{card=}')
      if card['Encoding time'] == int(membertracks[2]):
        if card['Deactivation time'] == 0:
          print('Card hasn\'t been deactivated')
          if card['Card number'] != int(membertracks[1]):
            return 'Card doesn\'t appear to be deactivated but is corrupted'
          break
        deactivation = self.epoch2str(card['Deactivation time'])
        return f'Card deactivated on {deactivation}'
    return None

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
    expiration = localtime(time())
    expiration = (expiration.tm_year+1, expiration.tm_mon,
                  expiration.tm_mday+1,
                  0, 0, 0, 0, 0, -1)
    expiration = mktime(struct_time(expiration))
    member['Expiration'] = expiration
    cmd = 'INSERT INTO members ("Member ID"'
    #',Name,Activation,Expiration'
    for field in member:
      if field == 'Member ID' or member[field] == '':
        continue
      cmd += f',"{field}"'
    cmd += f') VALUES("{member["Member ID"]}"'
    for field in member:
      if field == 'Member ID' or member[field] == '':
        continue
      cmd += f',"{member[field]}"'
    cmd += ');'
    with sqlite3.connect(self.memberdb) as conn:
      curs = conn.cursor()
      curs.execute(cmd)
      conn.commit()
    return member

  def deletemember(self, member):
    with sqlite3.connect(self.memberdb) as conn:
      curs = conn.cursor()
      curs.execute(f'DELETE FROM members WHERE "Member ID"={member};')
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
            now.tm_mday-1 if now.tm_hour < 3 else now.tm_mday,
            0, 0, 0, 0, 0, -1)
    now = mktime(struct_time(now))
    return round(now)

  def encodings(self, transaction):
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
        transaction[col] = self.encodingsdefaults[col]
      if count > 0:
        cmd += ', '
      cmd += f'"{transaction[col]}"'
    cmd += ');'
    with sqlite3.connect(self.encodingsdb) as conn:
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
      cmd += f' WHERE "Member ID"={memberid};'
      curs.execute(cmd)
      conn.commit()
