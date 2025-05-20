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
                                                'Expiration',
                                                'Last Day',
                                                'Last Swipe')
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
    self.encodingcols = {col:idx for idx,col in enumerate(self.encodingcols)}

  def epoch2str(self, ts):
    if ts == 0:
      return 'Never'
    ts = localtime(ts)
    s = f'{ts.tm_mon}/{ts.tm_mday}/{ts.tm_year} '
    if ts.tm_hour > 12:
      s += f'{ts.tm_hour-12}'
    elif ts.tm_hour == 0:
      s += '12'
    else:
      s += f'{ts.tm_hour}'
    s += f':{ts.tm_min:02d}'
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

  def member2tracks(self, memberid):
    with sqlite3.connect(self.encodingsdb) as conn:
      curs = conn.cursor()
      curs.execute( f'SELECT MAX("Card Number") FROM cards ' + \
                    f'WHERE "Member ID"={memberid};')
      cardnum = curs.fetchone()
    cardnum = 1 if cardnum[0] is None else cardnum[0] + 1
    encodetime = round(time())
    return [memberid, str(cardnum), str(encodetime)]

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
      if card[self.encodingcols['Encoding Time']] == int(membertracks[2]):
        if card[self.encodingcols['Deactivation Time']] == 0:
          if card[self.encodingcols['Card Number']] != int(membertracks[1]):
            return 'Card doesn\'t appear to be deactivated but is corrupted'
          break
        deactivation = card[self.encodingcols['Deactivation Time']]
        deactivation = self.epoch2str(deactivation)
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

  def encoded(self, tracks):
    deactivation = f'UPDATE cards SET "Deactivation Time"={tracks[2]} '
    deactivation += f'WHERE "Member ID"={tracks[0]} AND "Deactivation Time"=0;'
    activation = 'INSERT INTO cards ' + \
                  '("Member ID", "Card Number", "Encoding Time") '
    activation += f'VALUES({tracks[0]}, {tracks[1]}, {tracks[2]});'
    with sqlite3.connect(self.encodingsdb) as conn:
      curs = conn.cursor()
      curs.execute(deactivation)
      curs.execute(activation)
      conn.commit()
    with sqlite3.connect(self.memberdb) as conn:
      curs = conn.cursor()
      curs.execute( f'UPDATE members SET "Cards Issued"={tracks[1]} ' + \
                    f'WHERE "Member ID"={tracks[0]}')
      conn.commit()
