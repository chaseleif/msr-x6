#! /usr/bin/env python3

import threading
from msr import MSRX6

class SwipeThread:
  def __init__(self, tracks=None, errortext=None, tracktext=None):
    super().__init__()
    self.sigcancel = threading.Event()
    self.thread = threading.Thread(target=self.idle,
                                    args=(self.sigcancel,
                                          tracks,
                                          errortext,
                                          tracktext))

  def setmsg(self, text, msg):
    try:
      text.set(msg)
    except:
      return False
    return True

  ''' swipe
      Thread action, performs a swipe request with MSRX6 to read or encode
      
      Arguments:
        tracks is None or a list of 3 strings
        errortext is a reference to the tkinter errortext variable
        tracktext is a reference to the tkinter tracktext variable

      If tracks is None then we are reading
      Else tracks is a list of 3 strings conforming to ISO specs:
        Track 1 <=  76 alphanumeric characters
        Track 2 <=  37 numeric characters
        Track 3 <= 104 numeric characters

      Returns True to indicate not to retry, either on success or fatal error
  '''
  def swipe(self, tracks, errortext, tracktext):
    with MSRX6() as msr:
      msr.connect()
      if msr.errormsg:
        self.setmsg(errortext, msr.errormsg)
        return True
      if tracks is None:
        tracks = msr.read_tracks()
        if msr.errormsg:
          if not self.setmsg(errortext, msr.errormsg):
            return True
          return False
        if tracks is None:
          return False
        self.setmsg(tracktext, '&'.join(tracks))
        return True
      msr.write_tracks(tracks)
      if msr.errormsg:
        if not self.setmsg(errortext, msr.errormsg):
          return True
        return False
      self.setmsg(tracktext, '&'.join(tracks))
      return True

  def idle(self, sigcancel, tracks, errortext, tracktext):
    while not sigcancel.is_set():
      if self.swipe(tracks, errortext, tracktext):
        break

  def start(self):
    self.thread.start()

  def stop(self):
    self.sigcancel.set()
