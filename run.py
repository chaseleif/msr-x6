#! /usr/bin/env python3

from msr import MSRX6

def read():
  with MSRX6() as msr:
    msr.connect()
    if msr.version is None:
      return
    tracks = msr.read_tracks()
    if tracks is None:
      return
    print(f'{tracks=}')

def write(tracks=['51000013503246', '80425', '0']):
  with MSRX6() as msr:
    msr.connect()
    if msr.version is None:
      return
    msr.write_tracks(tracks)

def erase():
  with MSRX6() as msr:
    msr.connect()
    if msr.version is None:
      return
    msr.erase()

if __name__ == '__main__':
  while True:
    choice = input('1) Read\n2) Write\n3) Erase\n4) Quit\nChoice: ')
    if choice == '1':
      read()
    elif choice == '2':
      write()
    elif choice == '3':
      erase()
    else:
      break
