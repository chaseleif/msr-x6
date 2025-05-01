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

  def swipe(self, sigcancel, tracks, errortext, tracktext):
    with MSRX6() as msr:
      msr.connect()
      if msr.errormsg:
        errortext.set(msr.errormsg)
        return True
      if tracks is None:
        tracks = msr.read_tracks()
        if msr.errormsg:
          errortext.set(msr.errormsg)
          return False
        if tracks is None:
          return False
        tracktext.set('&'.join(tracks))
        return True
      msr.write_tracks(tracks)
      if msr.errormsg:
        errortext.set(msr.errormsg)
        return False
      tracktext.set('&'.join(tracks))
      return True

  def idle(self, sigcancel, tracks, errortext, tracktext):
    while not sigcancel.is_set():
      if self.swipe(sigcancel, tracks, errortext, tracktext):
        break

  def start(self):
    self.thread.start()

  def stop(self):
    self.sigcancel.set()
