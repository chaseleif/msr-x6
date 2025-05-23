#! /usr/bin/env python3

import usb.core, usb.util

class MSRX6:
  dev = None
  hid = None
  version = None
  errormsg = None

  def __init__(self):
    pass

  def __enter__(self):
    for classvar in ('dev','hid','version','errormsg'):
      exec(f'{type(self).__name__}.{classvar} = None')
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    if self.dev is not None:
      self.dev.reset()
      usb.util.dispose_resources(self.dev)

  def reset(self):
    try:
      self.hid.read(256, timeout=10)
    except usb.core.USBTimeoutError:
      pass
    self.send_message(b'\x1ba')
    try:
      self.hid.read(256, timeout=10)
    except usb.core.USBTimeoutError:
      pass

  def fail(self, msg=None):
    if msg:
      MSRX6.errormsg = msg
    try:
      self.reset()
    except:
      pass
    return None

  def clearbuffer(self):
    self.send_message(b'\x1br')
    self.reset()

  def connect(self):
    self.dev = usb.core.find(idVendor=0x0801, idProduct=0x0003)
    if self.dev is None:
      MSRX6.errormsg = 'MSR X6 card reader/writer not found'
      return
    try:
      if self.dev.is_kernel_driver_active(0):
        self.dev.detach_kernel_driver(0)
    except NotImplementedError:
      pass
    try:
      self.dev.set_configuration()
    except usb.core.USBError as e:
      return self.fail(str(e))
    usb.util.claim_interface(self.dev, 0)
    config = self.dev.get_active_configuration()
    intf = config.interfaces()[0]
    self.hid = intf.endpoints()[0]
    self.reset()
    self.send_message(b'\x1bv')
    ret = self.recv_message(timeout=500)
    if ret is None or ret[0] != 0x1b:
      return self.fail('Did not receive valid version string from scanner')
    else:
      self.version = ret[1:].decode()

  def send_message(self, message):
    message = bytes([len(message)|0xc0]) + message + b'\0' * (63-len(message))
    self.dev.ctrl_transfer( 0x21,
                            9,
                            wValue=0x0300,
                            wIndex=0,
                            data_or_wLength=message )

  def recv_message(self, timeout=3000):
    try:
      message = bytes(self.hid.read(64, timeout=timeout))
    except usb.core.USBTimeoutError:
      self.reset()
      return None
    length = message[0] & 0x3f
    return message[1:1+length]

  def read_tracks(self):
    self.clearbuffer()
    self.send_message(b'\x1br')
    try:
      ret = self.recv_message()
    except usb.core.USBError as e:
      return self.fail(str(e))
    if ret is None:
      return self.fail()
    if ret[0] != 0x1b:
      return self.fail('Received invalid response from scanner')
    ret = ret[1:].decode().split('?')
    if ret[-1][-1] != '0':
      return self.fail(f'Read error, error code {ret[-1][-1]}')
    if len(ret) < 3:
      return self.fail('Did not read all 3 expected tracks')
    ret= [ret[0].split('%')[-1], ret[1].split(';')[-1], ret[2].split(';')[-1]]
    return ret

  def write_tracks(self, tracks):
    self.clearbuffer()
    self.send_message(b'\x1bx')
    ret = self.recv_message()
    if ret is None:
      return self.fail()
    if ret[0] != 0x1b:
      return self.fail('Received invalid acknowledgement from scanner')
    self.send_message(b'\x1bw\x1bs' +
                      b'\x1b\x01' + tracks[0].encode() +
                      b'\x1b\x02' + tracks[1].encode() +
                      b'\x1b\x03' + tracks[2].encode() + b'?\x1c')
    ret = self.recv_message()
    if ret is None:
      return self.fail('Bad swipe')
    if ret[0:1] != b'\x1b':
      return self.fail('Received invalid write confirmation from scanner')
    ret = ret[1:].decode()
    if ret != '0':
      return self.fail(f'Write failed, error code {ret}')

  def erase(self):
    self.clearbuffer()
    self.send_message(b'\x1bc7')
    ret = self.recv_message()
    if ret[0] != 0x1b:
      return self.fail('Received invalid command acknowledgement from scanner')
    ret = ret[1:].decode()
    if ret != '0':
      return self.fail(f'Erase failed, error code {ret}')
