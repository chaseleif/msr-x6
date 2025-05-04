#! /usr/bin/env python3

import pyglet
import tkinter as tk
from tkinter import ttk
#from PIL import Image, ImageTk
from db import DataBase
from swipe import SwipeThread

pyglet.font.add_file('resources/LiberationSans-Bold.ttf')
pyglet.font.add_file('resources/LiberationSans-Regular.ttf')

class SYTMembers(tk.Tk):
  width = 750
  height = 800
  rgb_bg = '#ccffff'
  rgb_ibutton = '#99ccff'
  rgb_hbutton = '#0066cc'
  font_regular = lambda size: ('LiberationSans-Regular', size)
  font_bold = lambda size: ('LiberationSans-Bold', size, 'bold')

  def __init__(self):
    super().__init__()
    self.title('SYT Sport Bar & Pool Hall Members')
    self.geometry(f'{SYTMembers.width}x{SYTMembers.height}')
    self.frames = []
    for frame in ('mainframe',
                  'trxnframe',
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

  def process_trxn(self):
    for field in self.fields:
      self.fields[field] = self.fields[field].get()
    self.fields['Member ID'] = self.member['Member ID']
    self.fields['League day'] = 1 if self.leagueday.get() else 0
    self.db.trxn(self.fields)
    self.paint_trxn(self.member, msg='Transactions updated')

  def windowtitle(self, frame):
    titleframe = tk.Frame(frame,
                          width=SYTMembers.width,
                          height=SYTMembers.height,
                          bg=SYTMembers.rgb_bg)
    title = tk.Label( titleframe,
                      text='Shai Yo Thai Sport Bar & Pool Hall',
                      bg=SYTMembers.rgb_bg,
                      fg='black',
                      font=SYTMembers.font_regular(18))
    return titleframe, title

  def raisetitlegrid(self, frame, columns=1):
    self.clear_widgets()
    frame.tkraise()
    for column in range(columns):
      frame.columnconfigure(column, weight=1)
    frame.grid_propagate(False)
    titleframe, title = self.windowtitle(frame)
    title.grid(row=0, column=0, columnspan=columns, pady=20)
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
    tk.Label( leftframe,
              text='Name',
              bg=SYTMembers.rgb_bg,
              fg='black',
              font=SYTMembers.font_regular(16)).grid(row=0, column=0)
    name = tk.StringVar(rightframe)
    tk.Entry( rightframe,
              textvariable=name,
              bg=SYTMembers.rgb_bg,
              fg='black',
              font=SYTMembers.font_regular(15)).grid(row=0, column=1)
    botframe = tk.Frame(self.findmemberframe,
                        width=SYTMembers.width,
                        height=SYTMembers.height,
                        bg=SYTMembers.rgb_bg)
    botframe.grid(row=2, column=0, columnspan=2, pady=10)
    searchbutton = tk.Button(botframe,
                              text='Search',
                              font=SYTMembers.font_bold(20),
                              bg=SYTMembers.rgb_ibutton,
                              fg='black',
                              cursor='hand2',
                              activebackground=SYTMembers.rgb_hbutton,
                              activeforeground='black',
                              command=lambda: self.paint_find(name.get()))
    searchbutton.grid(row=0, column=0, columnspan=2, pady=10)
    if query is not None:
      results = self.db.findmember(query)
      if len(results) == 0:
        tk.Label( botframe,
                  text='No results found',
                  bg=SYTMembers.rgb_bg,
                  font=SYTMembers.font_regular(16),
                  fg='black').grid(row=1, column=0, columnspan=2, pady=10)
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
        tk.Button(botframe,
                  text='Select',
                  font=SYTMembers.font_bold(20),
                  bg=SYTMembers.rgb_ibutton,
                  fg='black',
                  cursor='hand2',
                  activebackground=SYTMembers.rgb_hbutton,
                  activeforeground='black',
                  command=lambda: self.find_selection(membertree),
                  ).grid(row=2, column=0, columnspan=2, pady=10)
    tk.Button(botframe,
              text='Return to Home Screen',
              font=SYTMembers.font_bold(20),
              bg=SYTMembers.rgb_ibutton,
              fg='black',
              cursor='hand2',
              activebackground=SYTMembers.rgb_hbutton,
              activeforeground='black',
              command=self.paint_main,
              ).grid(row=1 if query is None else 2 if len(results) == 0 else 3,
                      column=0, columnspan=2, pady=10)

  def paint_create(self, member=None):
    memberid = None if member is None else str(member['Member ID'])
    titleframe = self.raisetitlegrid(self.newmemberframe, columns=2)
    errorlabel = tk.Label(titleframe,
                          textvariable=self.errortext,
                          bg=SYTMembers.rgb_bg,
                          fg='red',
                          font=SYTMembers.font_bold(16))
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
      tk.Label( leftframe,
                text=field,
                bg=SYTMembers.rgb_bg,
                fg='black',
                font=SYTMembers.font_regular(16)
              ).grid(row=row, column=0, pady=3)
      value = tk.StringVar(rightframe, '' if member is None else member[field])
      tk.Entry( rightframe,
                bg=SYTMembers.rgb_bg,
                font=SYTMembers.font_regular(15),
                state='normal' if member is None else 'disabled',
                textvariable=value).grid(row=row, column=1, pady=3)
      self.fields[field] = value
      row += 1
    botframe = tk.Frame(self.newmemberframe,
                        width=SYTMembers.width,
                        height=SYTMembers.height,
                        bg=SYTMembers.rgb_bg)
    botframe.grid(row=2, column=0, columnspan=2)
    program_button = tk.Button(botframe,
                              text='Program Card',
                              font=SYTMembers.font_bold(20),
                              bg=SYTMembers.rgb_ibutton,
                              fg='black',
                              cursor='hand2',
                              activebackground=SYTMembers.rgb_hbutton,
                              activeforeground='black',
                              state='disabled' if member is None else 'normal',
                              command=lambda: self.paint_swipe(memberid=memberid))
    tk.Button(botframe,
              text='Create',
              font=SYTMembers.font_bold(20),
              bg=SYTMembers.rgb_ibutton,
              fg='black',
              cursor='hand2',
              activebackground=SYTMembers.rgb_hbutton,
              activeforeground='black',
              state='normal' if member is None else 'disabled',
              command=lambda: self.create_member(program_button),
            ).grid(row=0, column=0, columnspan=2, pady=(30,10))
    program_button.grid(row=1, column=0, columnspan=2, pady=10)
    if member is not None:
      tk.Button(botframe,
                text='Delete Member',
                font=SYTMembers.font_bold(20),
                bg=SYTMembers.rgb_ibutton,
                fg='black',
                cursor='hand2',
                activebackground=SYTMembers.rgb_hbutton,
                activeforeground='black',
                command=lambda: self.delete_member(member),
              ).grid(row=2, column=0, columnspan=2, pady=10)
    tk.Button(botframe,
              text='Return to Home Screen',
              font=SYTMembers.font_bold(20),
              bg=SYTMembers.rgb_ibutton,
              fg='black',
              cursor='hand2',
              activebackground=SYTMembers.rgb_hbutton,
              activeforeground='black',
              command=lambda: self.paint_main(),
            ).grid(row=2 if member is None else 3,
                    column=0, columnspan=2, pady=10)
    self.eval('tk::PlaceWindow . center')

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
    self.swipe = SwipeThread(errortext=self.errortext,
                              tracktext=self.tracktext,
                              tracks=[self.member,'0','0'])
    button['state'] = tk.DISABLED
    self.swipe.start()

  def swipecancel(self, fn):
    if self.swipe is not None:
      self.swipe.stop()
      self.swipe = None
    fn()

  def read_callback(self, var, index, mode):
    memberid = self.tracktext.get().split('&')[0]
    member = self.db.getmember(memberid)
    if member is None:
      self.paint_swipe(errortext=f'Invalid member ID: {memberid}')
      return
    self.paint_trxn(member)

  def swipe_error_callback(self, var, index, mode):
    if self.errortext.get() == 'MSR X6 card reader/writer not found':
      self.paint_swipe( errortext=self.errortext.get(),
                        memberid=self.member)

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
    self.swipebutton = tk.Button( bodyframe,
                                  text='Swipe',
                                  font=SYTMembers.font_bold(20),
                                  bg=SYTMembers.rgb_ibutton,
                                  fg='black',
                                  cursor='hand2',
                                  activebackground=SYTMembers.rgb_hbutton,
                                  activeforeground='black',
                                  command=lambda: errortext,
                                  state=tk.NORMAL,
                                )
    self.swipebutton.grid(row=0, column=0, pady=10)
    if memberid is None:
      self.swipebutton['command'] = lambda: self.readswipe(self.swipebutton)
    else:
      self.swipebutton['command'] = lambda: self.writeswipe(self.swipebutton)
    tk.Button(bodyframe,
              text='Cancel',
              font=SYTMembers.font_bold(20),
              bg=SYTMembers.rgb_ibutton,
              fg='black',
              cursor='hand2',
              activebackground=SYTMembers.rgb_hbutton,
              activeforeground='black',
              command=lambda: self.swipecancel(self.paint_main),
            ).grid(row=1, column=0, pady=10)
    errorlabel = tk.Label(bodyframe,
                          textvariable=self.errortext,
                          bg=SYTMembers.rgb_bg,
                          fg='red',
                          font=SYTMembers.font_bold(16))
    errorlabel.grid(row=2, column=0, pady=10)
    self.errortext.trace_add('write', callback=self.swipe_error_callback)
    self.tracktext.trace_add('write', callback=self.read_callback)
    self.eval('tk::PlaceWindow . center')

  def paint_trxn(self, member, msg=None):
    titleframe = self.raisetitlegrid(self.trxnframe, columns=2)
    if msg is not None:
      tk.Label( titleframe,
                text=msg,
                bg=SYTMembers.rgb_bg,
                fg='dark blue',
                font=SYTMembers.font_bold(16)).grid(row=1,
                                                              column=0,
                                                              pady=10,
                                                              columnspan=2)
    self.member = member
    leftframe = tk.Frame( self.trxnframe,
                          width=SYTMembers.width/2,
                          height=SYTMembers.height,
                          bg=SYTMembers.rgb_bg)
    leftframe.grid(row=1, column=0, sticky='E', padx=(0,5))
    rightframe = tk.Frame(self.trxnframe,
                          width=SYTMembers.width/2,
                          height=SYTMembers.height,
                          bg=SYTMembers.rgb_bg)
    rightframe.grid(row=1, column=1, sticky='W', padx=(5,0))
    tk.Label( leftframe,
              text=member['Name'],
              bg=SYTMembers.rgb_bg,
              fg='black',
              font=SYTMembers.font_bold(16)).grid(row=0,
                                                            column=0,
                                                            pady=10)
    tk.Label( rightframe,
              text=member['Member ID'],
              bg=SYTMembers.rgb_bg,
              fg='black',
              font=SYTMembers.font_bold(16)).grid(row=0,
                                                            column=1,
                                                            pady=10)
    self.fields = { 'Total spent':None,
                    'Total hours':None }
    row = 1
    for field in self.fields:
      tk.Label( leftframe,
                text=field,
                bg=SYTMembers.rgb_bg,
                fg='black',
                font=SYTMembers.font_regular(16)
              ).grid(row=row, column=0, pady=10)
      value = tk.StringVar(rightframe)
      tk.Entry( rightframe,
                textvariable=value,
                bg=SYTMembers.rgb_bg,
                fg='black',
                font=SYTMembers.font_regular(15)).grid(row=row, column=1,
                                                          pady=10)
      self.fields[field] = value
      row += 1
    leagueday = tk.Checkbutton( self.trxnframe,
                                text='League day',
                                variable=self.leagueday,
                                bg=SYTMembers.rgb_bg,
                                activebackground=SYTMembers.rgb_bg,
                                cursor='hand2',
                                font=SYTMembers.font_regular(16))
    leagueday.grid(row=row, column=0, pady=10, columnspan=2)
    row += 1
    tk.Button(self.trxnframe,
              text='Process transaction',
              font=SYTMembers.font_bold(20),
              bg=SYTMembers.rgb_ibutton,
              fg='black',
              cursor='hand2',
              activebackground=SYTMembers.rgb_hbutton,
              activeforeground='black',
              command=lambda: self.process_trxn()).grid(row=row, column=0,
                                                        pady=10, columnspan=2)
    row += 1
    tk.Button(self.trxnframe,
              text='Return to Home Screen',
              font=SYTMembers.font_bold(20),
              bg=SYTMembers.rgb_ibutton,
              fg='black',
              cursor='hand2',
              activebackground=SYTMembers.rgb_hbutton,
              activeforeground='black',
              command=self.paint_main).grid(row=row, column=0,
                                            pady=10, columnspan=2)
    self.eval('tk::PlaceWindow . center')

  def paint_main(self):
    titleframe = self.raisetitlegrid(self.mainframe)
    bodyframe = tk.Frame( self.mainframe,
                          width=SYTMembers.width,
                          height=SYTMembers.height,
                          bg=SYTMembers.rgb_bg)
    bodyframe.grid(row=1, column=0)
    buttons = { 'Transaction': self.paint_swipe,
                'Search Members': self.paint_find,
                'Create Member': self.paint_create,
              }
    for row, button in enumerate(buttons):
      tk.Button(bodyframe,
                text=button,
                font=SYTMembers.font_bold(20),
                bg=SYTMembers.rgb_ibutton,
                fg='black',
                cursor='hand2',
                activebackground=SYTMembers.rgb_hbutton,
                activeforeground='black',
                command=lambda button=button: buttons[button](),
              ).grid(row=row, column=0, pady=20)
    self.eval('tk::PlaceWindow . center')

  def paint_editmember(self, member):
    titleframe = self.raisetitlegrid(self.editmemberframe, columns=2)
    leftframe = tk.Frame(self.editmemberframe,
                          width=SYTMembers.width/2,
                          height=SYTMembers.height,
                          bg=SYTMembers.rgb_bg)
    leftframe.grid(row=1, column=0, sticky='E', padx=(0,5))
    rightframe = tk.Frame(self.editmemberframe,
                          width=SYTMembers.width/2,
                          height=SYTMembers.height,
                          bg=SYTMembers.rgb_bg)
    rightframe.grid(row=1, column=1, sticky='W', padx=(5,0))
    for row, field in enumerate(member):
      tk.Label( leftframe,
                text=field,
                bg=SYTMembers.rgb_bg,
                fg='black',
                font=SYTMembers.font_regular(16)
              ).grid(row=row, column=0, pady=3)
      value = tk.StringVar(rightframe, str(member[field]))
      tk.Entry( rightframe,
                state=('disabled' \
                        if field in self.db.memberprotected \
                        else 'normal'),
                bg=SYTMembers.rgb_bg,
                disabledbackground=SYTMembers.rgb_bg,
                disabledforeground='#424242',
                font=SYTMembers.font_regular(15),
                textvariable=value).grid(row=row, columns=1, pady=3)
      self.fields[field] = value
    botframe = tk.Frame(self.editmemberframe,
                        width=SYTMembers.width,
                        height=SYTMembers.height,
                        bg=SYTMembers.rgb_bg)
    botframe.grid(row=2, column=0, columnspan=2)
    buttons = { 'Save': lambda: self.save_member(member),
                'Return to Home Screen': self.paint_main,
              }
    for row, button in enumerate(buttons):
      tk.Button(
          botframe,
          text=button,
          font=SYTMembers.font_bold(20),
          bg=SYTMembers.rgb_ibutton,
          fg='black',
          cursor='hand2',
          activebackground=SYTMembers.rgb_hbutton,
          activeforeground='black',
          command=lambda button=button: buttons[button](),
        ).grid(row=row, column=0, columnspan=2, pady=10)
    self.eval('tk::PlaceWindow . center')

if __name__=='__main__':
  window = SYTMembers()
