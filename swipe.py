#! /usr/bin/env python3

import threading
from msr import MSRX6

class SwipeThread:

  thread = None
  sigcancel = threading.Event()

  def __init__(self):
    pass

  ''' setmsg
      Helper function to set the text of a tkinter textvariable
      If a textvariable has gone out of scope set() will raise an Exception

      Returns True if able to set the text, otherwise False
  '''
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
        db is None or a reference to the DataBase instance
        errortext is a reference to the tkinter errortext variable
        tracktext is a reference to the tkinter tracktext variable

      If tracks is None then we are reading
      Else tracks is a list of 3 strings conforming to ISO specs:
        Track 1 <=  76 alphanumeric characters
        Track 2 <=  37 numeric characters
        Track 3 <= 104 numeric characters

      Returns True to indicate not to retry, either on success or fatal error
  '''
  def swipe(self, tracks, db, errortext, tracktext):
    with MSRX6() as msr:
      msr.connect()
      # Error connecting to device, communication error or not found
      if msr.errormsg:
        self.setmsg(errortext, msr.errormsg)
        return True
      # No tracks given, we are reading
      if tracks is None:
        tracks = msr.read_tracks()
        # Set the corresponding textvariable to the error message on error
        if msr.errormsg:
          # On failure to set the textvariable return True to quit the thread
          if not self.setmsg(errortext, msr.errormsg):
            return True
          # Return False to retry
          return False
        # We did not receive a response, i.e., no swipe
        if tracks is None:
          return False
        # Pass the tracks along to the tracktext variable
        self.setmsg(tracktext, '&'.join(tracks))
        return True
      # We are writing tracks to a card
      msr.write_tracks(tracks)
      # Handle an error message as with reading
      if msr.errormsg:
        if not self.setmsg(errortext, msr.errormsg):
          return True
        return False
      # Update the db on a successful write
      db.encoded(tracks)
      # and set the tracktext
      self.setmsg(tracktext, '&'.join(tracks))
      return True

  def idle(self, sigcancel, tracks, db, errortext, tracktext):
    while not sigcancel.is_set():
      if self.swipe(tracks, db, errortext, tracktext):
        break

  def start(self, tracks=None, db=None, errortext=None, tracktext=None):
    if SwipeThread.thread is not None:
      self.stop()
      self.join()
    SwipeThread.sigcancel.clear()
    SwipeThread.thread = threading.Thread(target=self.idle,
                                          args=(SwipeThread.sigcancel,
                                                tracks,
                                                db,
                                                errortext,
                                                tracktext))
    SwipeThread.thread.start()

  def stop(self):
    SwipeThread.sigcancel.set()

  def join(self):
    if SwipeThread.thread is not None:
      SwipeThread.thread.join()
      SwipeThread.thread = None
