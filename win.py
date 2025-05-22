#! /usr/bin/env python3

import os, pyglet, sys
import tkinter as tk
from tkinter import ttk
#from PIL import Image, ImageTk
from db import DataBase
from swipe import SwipeThread

try:
  pyglet.font.add_file(os.path.join(sys._MEIPASS,
                                    'resources', 'LiberationSans-Bold.ttf'))
  pyglet.font.add_file(os.path.join(sys._MEIPASS,
                                    'resources', 'LiberationSans-Regular.ttf'))
except AttributeError:
  pyglet.font.add_file(os.path.join('resources', 'LiberationSans-Bold.ttf'))
  pyglet.font.add_file(os.path.join('resources', 'LiberationSans-Regular.ttf'))

class SYTMembers(tk.Tk):
  width = 600
  height = 700
  rgb_bg = '#ccffff'
  rgb_ibutton = '#99ccff'
  rgb_hbutton = '#0066cc'
  font_regular = lambda size: ('LiberationSans-Regular', size)
  font_bold = lambda size: ('LiberationSans-Bold', size, 'bold')

  def __init__(self):
    super().__init__()
    self.title('SYT Sport Bar & Pool Hall Members')
    geometry = f'{SYTMembers.width}x{SYTMembers.height}'
    geometry += f'+{round(self.winfo_screenwidth()/2 - SYTMembers.width/2)}'
    geometry += f'+{round(self.winfo_screenheight()/2 - SYTMembers.height/2)}'
    self.geometry(geometry)
    self.frames = []
    for frame in ('mainframe',
                  'confirmframe',
                  'memberframe',
                  'checkinframe',
                  'swipeframe',
                  'findframe',
                  'findmemberframe',
                  'editmemberframe',
                  'newmemberframe'):
      blankframe = tk.Frame(self,
                            width=SYTMembers.width,
                            height=SYTMembers.height,
                            bg=SYTMembers.rgb_bg)
      exec(f'self.{frame} = blankframe')
      exec(f'self.{frame}.grid(row=0, column=0, sticky=\'nesw\')')
      exec(f'self.frames.append(self.{frame})')
    self.frames = tuple(self.frames)
    self.protocol('WM_DELETE_WINDOW',self.__del__)
    self.db = DataBase()
    self.fields = {}
    self.leagueday = tk.BooleanVar(value=False)
    self.member = None
    self.swipe = None
    self.tracktext = tk.StringVar()
    self.errortext = tk.StringVar()
    self.stringvars = (self.tracktext, self.errortext)
    self.swipebutton = None
    self.resizable(width=False, height=False)
    self.paint_main()
    self.mainloop()

  def __del__(self):
    if self.swipe is not None:
      self.swipe.stop()
    self.quit()

  def button(self, frame, text, command, state='normal'):
    return tk.Button( frame,
                      text=text,
                      font=SYTMembers.font_bold(20),
                      bg=SYTMembers.rgb_ibutton,
                      fg='black',
                      cursor='hand2',
                      state=state,
                      activebackground=SYTMembers.rgb_hbutton,
                      activeforeground='black',
                      command=command)

  def label(self, frame,
            text=None, textvariable=None,
            fg='black', size=16):
    params = { 'bg':SYTMembers.rgb_bg, 'fg':fg }
    if fg == 'black':
      params['font'] = SYTMembers.font_regular(size)
    else:
      params['font'] = SYTMembers.font_bold(size)
    if textvariable is None:
      params['text'] = text
    else:
      params['textvariable'] = textvariable
    return tk.Label(frame, **params)

  def entry(self, frame, text=None, textvariable=None, state='normal'):
    params = {'bg':SYTMembers.rgb_bg,
              'fg':'black',
              'disabledbackground':SYTMembers.rgb_bg,
              'disabledforeground':'#424242',
              'state':state,
              'font':SYTMembers.font_regular(15)}
    if textvariable is None:
      params['text'] = text
    else:
      params['textvariable'] = textvariable
    return tk.Entry(frame, **params)

  def renew_member(self):
    self.db.renewmember(self.member['Member ID'])
    self.paint_member(self.member, msg='Membership Renewed')

  def windowtitle(self, frame):
    titleframe = tk.Frame(frame,
                          width=SYTMembers.width,
                          height=SYTMembers.height,
                          bg=SYTMembers.rgb_bg)
    title = self.label( titleframe,
                        text='Shai Yo Thai Sport Bar & Pool Hall',
                        size=18)
    return titleframe, title

  def raisetitlegrid(self, frame, columns=1):
    self.clear_widgets()
    frame.tkraise()
    for column in range(columns):
      frame.columnconfigure(column, weight=1)
    frame.grid_propagate(False)
    titleframe, title = self.windowtitle(frame)
    title.grid(row=0, column=0, columnspan=columns, pady=10)
    titleframe.grid(row=0, column=0, columnspan=columns)
    return titleframe

  def paint_find(self, query=None):
    titleframe = self.raisetitlegrid(self.findmemberframe, columns=2)
    leftframe = tk.Frame( self.findmemberframe,
                          width=SYTMembers.width/2,
                          height=SYTMembers.height,
                          bg=SYTMembers.rgb_bg)
    leftframe.grid(row=1, column=0, pady=10)
    rightframe = tk.Frame(self.findmemberframe,
                          width=SYTMembers.width/2,
                          height=SYTMembers.height,
                          bg=SYTMembers.rgb_bg)
    rightframe.grid(row=1, column=1, pady=10)
    self.label(leftframe, text='Name').grid(row=0, column=0)
    name = tk.StringVar(rightframe)
    self.entry(rightframe, textvariable=name).grid(row=0, column=1)
    botframe = tk.Frame(self.findmemberframe,
                        width=SYTMembers.width,
                        height=SYTMembers.height,
                        bg=SYTMembers.rgb_bg)
    botframe.grid(row=2, column=0, columnspan=2, pady=10)
    searchbutton = self.button( botframe,
                                'Search',
                                lambda: self.paint_find(name.get()))
    searchbutton.grid(row=0, column=0, columnspan=2, pady=10)
    if query is not None:
      results = self.db.findmember(query)
      if len(results) == 0:
        self.label( botframe,
                    text='No results found'
                  ).grid(row=1, column=0, columnspan=2, pady=10)
      else:
        treeframe = tk.Frame( botframe,
                              width=SYTMembers.width,
                              bg=SYTMembers.rgb_bg)
        treeframe.grid(row=1, column=0, columnspan=2, pady=10, sticky='nsew')
        canvas = tk.Canvas( treeframe,
                            width=SYTMembers.width)
        h_scrollbar = ttk.Scrollbar(treeframe,
                                    orient=tk.HORIZONTAL,
                                    command=canvas.xview)
        canvas.configure(xscrollcommand=h_scrollbar.set)
        contentframe = ttk.Frame(canvas)
        contentframe.bind('<Configure>', lambda e:
                          canvas.configure(scrollregion=canvas.bbox('all')))
        cols = tuple(key for key in self.db.memberdefaults.keys())
        style = ttk.Style()
        style.configure('membertree.Treeview',
                        highlightthickness=0,
                        bd=0,
                        font=SYTMembers.font_regular(11))
        style.configure('membertree.Treeview.Heading',
                        font=SYTMembers.font_bold(11))
        membertree = ttk.Treeview(contentframe,
                                  columns=cols,
                                  style='membertree.Treeview',
                                  selectmode='browse',
                                  show='headings')
        v_scrollbar = ttk.Scrollbar(treeframe,
                                    orient=tk.VERTICAL,
                                    command=membertree.yview)
        membertree.configure(yscrollcommand=v_scrollbar.set)
        membertree.grid(row=0, column=1, columnspan=2, pady=10, padx=(0,10))
        for i, col in enumerate(cols):
          membertree.heading(col, text=col)
          maxlen = max([len(str(result[i])) for result in results])
          maxlen = max(maxlen*10, len(col)*12)
          membertree.column(col, width=maxlen, anchor=tk.CENTER)
        for i, result in enumerate(results):
          membertree.insert('', tk.END, values=[str(s) for s in result])
        treeframe.columnconfigure(0, weight=1)
        treeframe.columnconfigure(1, weight=1)
        treeframe.rowconfigure(0, weight=1)
        canvas.create_window((0, 0), window=contentframe, anchor='nw')
        canvas.grid(row=0, column=0, columnspan=2, sticky='nsew')
        v_scrollbar.grid(row=0, column=0, columnspan=2, sticky='nse')
        h_scrollbar.grid(row=0, column=0, columnspan=2, sticky='sew',
                          padx=(0,15))
        self.button(botframe,
                    'Select',
                    lambda: self.find_selection(membertree)
                    ).grid(row=2, column=0, columnspan=2, pady=10)
    self.button(botframe,
                'Return Home',
                self.paint_main
                ).grid(row=1 if query is None \
                              else 2 if len(results)==0 \
                              else 3,
                        column=0, columnspan=2, pady=10)

  def paint_create(self, member=None):
    memberid = None if member is None else str(member['Member ID'])
    titleframe = self.raisetitlegrid(self.newmemberframe, columns=2)
    errorlabel = self.label(titleframe,
                            textvariable=self.errortext,
                            fg='red')
    errorlabel.grid(row=1, column=0, columnspan=2, pady=10)
    leftframe = tk.Frame( self.newmemberframe,
                          width=SYTMembers.width/2,
                          height=SYTMembers.height,
                          bg=SYTMembers.rgb_bg)
    leftframe.grid(row=1, column=0, sticky='E', padx=(0,5))
    rightframe = tk.Frame(self.newmemberframe,
                          width=SYTMembers.width/2,
                          height=SYTMembers.height,
                          bg=SYTMembers.rgb_bg)
    rightframe.grid(row=1, column=1, sticky='W', padx=(5,0))
    row = 0
    for field in self.db.memberdefaults:
      if self.db.memberdefaults[field] is not None:
        continue
      if member is None and \
          field in self.db.memberprotected and field != 'Name':
        continue
      self.label(leftframe, text=field).grid(row=row, column=0, pady=3)
      value = tk.StringVar(rightframe, '' if member is None else member[field])
      self.entry( rightframe,
                  textvariable=value,
                  state='normal' if member is None else 'disabled'
                ).grid(row=row, column=1, pady=3)
      self.fields[field] = value
      row += 1
    botframe = tk.Frame(self.newmemberframe,
                        width=SYTMembers.width,
                        height=SYTMembers.height,
                        bg=SYTMembers.rgb_bg)
    botframe.grid(row=2, column=0, columnspan=2)
    program_button = self.button( botframe,
                                  'Program Card',
                                  lambda: self.paint_swipe(memberid=memberid),
                                  state='disabled' if member is None \
                                        else 'normal')
    self.button(botframe,
                'Create',
                lambda: self.create_member(program_button),
                state='normal' if member is None else 'disabled'
                ).grid(row=0, column=0, columnspan=2, pady=(30,10))
    program_button.grid(row=1, column=0, columnspan=2, pady=10)
    if member is not None:
      self.button(botframe,
                  'Delete Member',
                  lambda: self.delete_member(member)
                  ).grid(row=2, column=0, columnspan=2, pady=10)
    self.button(botframe,
                'Return Home',
                self.paint_main
                ).grid(row=2 if member is None else 3,
                        column=0, columnspan=2, pady=10)

  def find_selection(self, membertree):
    if membertree.selection():
      member = membertree.item(membertree.selection(), 'values')
      member = {key:val for key, val in zip(self.db.memberdefaults.keys(),
                                              member)}
      self.paint_editmember(member)

  def save_member(self, member):
    modified = {}
    for field in member:
      if field in self.db.memberprotected:
        pass
      elif str(member[field]) != self.fields[field].get():
        member[field] = modified[field] = self.fields[field].get()
    if len(modified) > 0:
      self.db.editmember(member['Member ID'], modified)

  def create_member(self, program_button):
    if self.fields['Name'].get() == '':
      self.errortext.set('Name is required')
      return
    member = {}
    for field in self.fields:
      member[field] = self.fields[field].get()
    member = self.db.addmember(member)
    self.paint_create(member)

  def delete_member(self, member):
    self.db.deletemember(member['Member ID'])
    self.paint_create()

  def clear_widgets(self, member=None):
    self.member = member
    self.fields = {}
    self.swipebutton = None
    for var in self.stringvars:
      for i in range(len(var.trace_info())-1,-1,-1):
        var.trace_remove(*var.trace_info()[i])
      var.set('')
    for frame in self.frames:
      for widget in frame.winfo_children():
        widget.destroy()

  def readswipe(self, button):
    self.swipe = SwipeThread(errortext=self.errortext,
                              tracktext=self.tracktext)
    button['state'] = tk.DISABLED
    self.swipe.start()

  def writeswipe(self, button):
    tracks = self.db.member2tracks(self.member)
    self.swipe = SwipeThread( tracks=tracks,
                              db=self.db,
                              errortext=self.errortext,
                              tracktext=self.tracktext)
    button['state'] = tk.DISABLED
    self.swipe.start()

  def swipecancel(self, fn):
    if self.swipe is not None:
      self.swipe.stop()
      self.swipe = None
    fn()

  def checkin_callback(self, var, index, mode):
    membertracks = self.tracktext.get().split('&')
    member = self.db.getmember(membertracks[0])
    if member is None:
      self.paint_checkin(errortext=f'Invalid Member ID: {membertracks[0]}')
      return
    error = self.db.verifymember(membertracks)
    if error is not None:
      self.paint_checkin(errortext=error)
    else:
      self.paint_checkin(memberid=membertracks[0])

  def checkin_error_callback(self, var, index, mode):
    self.paint_checkin(errortext=self.errortext.get())

  def read_callback(self, var, index, mode):
    membertracks = self.tracktext.get().split('&')
    member = self.db.getmember(membertracks[0])
    if member is None:
      self.paint_swipe(errortext=f'Invalid member ID: {membertracks[0]}')
      return
    error = self.db.verifymember(membertracks)
    self.paint_member(member, msg=error)

  def swipe_error_callback(self, var, index, mode):
    if self.errortext.get() == 'MSR X6 card reader/writer not found':
      self.paint_swipe( errortext=self.errortext.get(),
                        memberid=self.member)

  def paint_confirm(self, msg):
    titleframe = self.raisetitlegrid(self.confirmframe)
    bodyframe = tk.Frame( self.confirmframe,
                          width=SYTMembers.width,
                          height=SYTMembers.height,
                          bg=SYTMembers.rgb_bg)
    bodyframe.grid(row=1, column=0)
    for row, line in enumerate(msg.split('\n')):
      self.label( bodyframe,
                  text=line).grid(row=row, column=0, pady=5)
    botframe = tk.Frame(self.confirmframe,
                        width=SYTMembers.width,
                        height=SYTMembers.height,
                        bg=SYTMembers.rgb_bg)
    botframe.grid(row=2, column=0)
    self.button(botframe,
                'Return Home',
                self.paint_main).grid(row=0, column=0, pady=10)


  def paint_checkin(self, memberid=None, errortext=''):
    titleframe = self.raisetitlegrid(self.checkinframe)
    if errortext != '':
      self.errortext.set(errortext)
    bodyframe = tk.Frame( self.checkinframe,
                          width=SYTMembers.width,
                          height=SYTMembers.height,
                          bg=SYTMembers.rgb_bg)
    bodyframe.grid(row=1, column=0)
    if memberid is not None:
      lastswipe = self.db.membercheckin(memberid=memberid)
      lastswipe = [str(part) for part in lastswipe]
      msg = '\n'.join(['Checked in',
                        f'Last checkin: {lastswipe[0]}',
                        f'Prior checkins today: {lastswipe[1]}'])
      self.paint_confirm(msg)
      return
    self.swipebutton = self.button( bodyframe,
                                    'Swipe',
                                    None)
    self.swipebutton.grid(row=0, column=0, pady=10)
    self.button(bodyframe,
                'Return Home',
                lambda: self.swipecancel(self.paint_main)
                ).grid(row=1, column=0, pady=10)
    errorlabel = self.label(bodyframe,
                            textvariable=self.errortext,
                            fg='red')
    errorlabel.grid(row=2, column=0, pady=10)
    self.errortext.trace_add('write', callback=self.swipe_error_callback)
    self.tracktext.trace_add('write', callback=self.checkin_callback)
    if errortext == '':
      self.readswipe(self.swipebutton)
    else:
      self.swipebutton['command'] = lambda: self.readswipe(self.swipebutton)

  def paint_swipe(self, errortext='', memberid=None):
    titleframe = self.raisetitlegrid(self.swipeframe)
    if errortext != '':
      self.errortext.set(errortext)
    self.member = memberid
    bodyframe = tk.Frame( self.swipeframe,
                          width=SYTMembers.width,
                          height=SYTMembers.height,
                          bg=SYTMembers.rgb_bg)
    bodyframe.grid(row=1, column=0)
    self.swipebutton = self.button( bodyframe,
                                    'Swipe',
                                    None)
    self.swipebutton.grid(row=0, column=0, pady=10)
    self.button(bodyframe,
                'Cancel',
                lambda: self.swipecancel(self.paint_main)
                ).grid(row=1, column=0, pady=10)
    errorlabel = self.label(bodyframe,
                            textvariable=self.errortext,
                            fg='red')
    errorlabel.grid(row=2, column=0, pady=10)
    self.errortext.trace_add('write', callback=self.swipe_error_callback)
    self.tracktext.trace_add('write', callback=self.read_callback)
    if errortext == '':
      if memberid is None:
        self.readswipe(self.swipebutton)
      else:
        self.writeswipe(self.swipebutton)
    else:
      if memberid is None:
        self.swipebutton['command'] = lambda: self.readswipe(self.swipebutton)
      else:
        self.swipebutton['command'] = lambda: self.writeswipe(self.swipebutton)

  def paint_member(self, member, msg=None):
    titleframe = self.raisetitlegrid(self.memberframe, columns=2)
    if msg is not None:
      self.label( titleframe,
                  text=msg,
                  fg='dark blue'
                ).grid(row=1, column=0, columnspan=2, pady=10)
      if msg == 'Membership Renewed':
        member = self.db.getmember(member['Member ID'])
    self.member = member
    detailsframe = tk.Frame(self.memberframe,
                            width=SYTMembers.width,
                            height=SYTMembers.height,
                            bg=SYTMembers.rgb_bg)
    detailsframe.grid(row=1, column=0, columnspan=2)
    for row, field in enumerate( ('Name',
                                  'Member ID',
                                  'Activation',
                                  'Expiration',
                                  'Cards Issued',
                                  'Birthday',
                                  'Last Day',
                                  'Last Swipe',
                                  'Daily Swipes')):
      if member[field] is None:
        continue
      label = self.label(detailsframe, text=field + ':')
      label.grid(row=row, column=0, padx=(0,3), pady=5, sticky='E')
      value = self.label(detailsframe, text=member[field])
      value.grid(row=row, column=1, padx=(3,0), pady=5, sticky='W')
    botframe = tk.Frame(self.memberframe,
                        width=SYTMembers.width,
                        height=SYTMembers.height,
                        bg=SYTMembers.rgb_bg)
    botframe.grid(row=2, column=0, columnspan=2)
    buttons = { 'Edit Member':
                  lambda member=member: self.paint_editmember(member),
                'Extend Membership' if int(member['Active']) == 1 \
                                    else 'Reactivate Membership':
                  self.renew_member,
              }
    if msg is not None and 'card' in msg.lower():
      buttons['Issue New Card'] = \
                    lambda: self.paint_swipe(memberid=str(member['Member ID']))
    buttons['Return Home'] = self.paint_main
    for row, button in enumerate(buttons):
      self.button(botframe,
                  button,
                  lambda button=button: buttons[button]()
                  ).grid(row=row, column=0, pady=10)

  def paint_main(self):
    titleframe = self.raisetitlegrid(self.mainframe)
    bodyframe = tk.Frame( self.mainframe,
                          width=SYTMembers.width,
                          height=SYTMembers.height,
                          bg=SYTMembers.rgb_bg)
    bodyframe.grid(row=1, column=0)
    buttons = { 'Check In': self.paint_checkin,
                'Swipe Member': self.paint_swipe,
                'Search Members': self.paint_find,
                'Create Member': self.paint_create,
              }
    for row, button in enumerate(buttons):
      self.button(bodyframe,
                  button,
                  lambda button=button: buttons[button]()
                  ).grid(row=row, column=0, pady=20)

  def paint_editmember(self, member):
    titleframe = self.raisetitlegrid(self.editmemberframe, columns=2)
    detailsframe = tk.Frame(self.editmemberframe,
                            width=SYTMembers.width,
                            height=SYTMembers.height,
                            bg=SYTMembers.rgb_bg)
    detailsframe.grid(row=1, column=0, columnspan=2, padx=5)
    for row, field in enumerate(member):
      label = self.label( detailsframe,
                          text=field,
                          size=14)
      label.grid(row=row, column=0, pady=2, padx=(0,4), sticky='e')
      value = tk.StringVar(detailsframe, str(member[field]))
      self.entry( detailsframe,
                  textvariable=value,
                  state='disabled' if field in self.db.memberprotected \
                        else 'normal'
                ).grid(row=row, column=1, pady=1, padx=(4,0))
      self.fields[field] = value
    botframe = tk.Frame(self.editmemberframe,
                        width=SYTMembers.width,
                        height=SYTMembers.height,
                        bg=SYTMembers.rgb_bg)
    botframe.grid(row=2, column=0, columnspan=2)
    buttons = { 'Save':
                  lambda: self.save_member(member),
                'Issue New Card':
                  lambda: self.paint_swipe(memberid=str(member['Member ID'])),
                'Check In':
                  lambda: self.paint_member(member),
                'Return Home':
                  self.paint_main,
              }
    for row, button in enumerate(buttons):
      self.button(botframe,
                  button,
                  lambda button=button: buttons[button]()
                  ).grid(row=row, column=0, columnspan=2, pady=10)

if __name__=='__main__':
  window = SYTMembers()
