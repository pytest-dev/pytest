import py
from py.__.test.tkinter import backend
from py.__.test.tkinter import util
from py.__.test.tkinter import event
Null = util.Null
Event = event.Event

import ScrolledText
from Tkinter import PhotoImage
import Tkinter
import re
import os

myfont = ('Helvetica', 12, 'normal')

class StatusBar(Tkinter.Frame):

    font = ('Helvetica', 14, 'normal')

    def __init__(self, master=None, **kw):
        if master is None:
            master = Tk()
        Tkinter.Frame.__init__(self, master, **kw)
        self.labels = {}
        self.callback = Null()
        self.tkvariable_dict = {'failed': Tkinter.BooleanVar(),
                                'skipped': Tkinter.BooleanVar(),
                                'passed_item': Tkinter.BooleanVar()}
        self.init_widgets()
        
    def init_widgets(self):
        def get_button(text, var):
            b = Tkinter.Checkbutton(self, text=text,
                                    variable=var,
                                    onvalue=True, offvalue=False,
                                    anchor=Tkinter.W,
                                    font=self.font, indicatoron = False,
                                    command = self.do_callback)
            b.select()
            return b
        
        self.add_widget('Failed',
                        get_button('Failed', self.tkvariable_dict['failed']))
        self._get_widget('Failed').configure(bg = 'Red3', fg = 'White',
                                             highlightcolor = 'Red',
                                             selectcolor = 'Red',
                                             activebackground= 'Red',
                                             activeforeground = 'White')
        self.add_widget('Skipped',
                        get_button('Skipped', self.tkvariable_dict['skipped']))
        self._get_widget('Skipped').configure(bg = 'Yellow3',
                                              highlightcolor = 'Yellow',
                                              selectcolor = 'Yellow',
                                              activebackground= 'Yellow')
        b = get_button('Passed', self.tkvariable_dict['passed_item'])
        b.deselect()
        self.add_widget('Passed', b)
        self._get_widget('Passed').configure(bg = 'Green3', fg = 'Black',
                                             highlightcolor = 'Black',
                                             selectcolor = 'Green',
                                             activeforeground = 'Black',
                                             activebackground= 'Green')
        
    def set_filter_args_callback(self, callback):
        self.callback = callback

    def do_callback(self,):
        kwargs = dict([(key, var.get())
                       for key, var in self.tkvariable_dict.items()])
        self.callback(**kwargs)
        
    def set_label(self, name, text='', side=Tkinter.LEFT):
        if not self.labels.has_key(name):
            label = Tkinter.Label(self, bd=1, relief=Tkinter.SUNKEN,
                                  anchor=Tkinter.W,
                                  font=self.font)
            self.add_widget(name, label, side)
        else:
            label = self.labels[name]
        label.config(text='%s:\t%s' % (name,text))

    def add_widget(self, name, widget, side=Tkinter.LEFT):
        widget.pack(side=side)
        self.labels[name] = widget

    def _get_widget(self, name):
        if not self.labels.has_key(name):
            self.set_label(name, 'NoText')
        return self.labels[name]

    def update_all(self, reportstore = Null(), ids = []):
        self.set_label('Failed', str(len(reportstore.get(failed = True))))
        self.set_label('Skipped', str(len(reportstore.get(skipped = True))))
        self.set_label('Passed',
                       str(len(reportstore.get(passed_item = True))))
        root_report =  reportstore.root
        if root_report.time < 7*24*60*60:
            self.set_label('Time', '%0.2f seconds' % root_report.time)
        else:
            self.set_label('Time', '%0.2f seconds' % 0.0)

class ReportListBox(Tkinter.LabelFrame):

    font = myfont

    def __init__(self, *args, **kwargs):
        Tkinter.LabelFrame.__init__(self, *args, **kwargs)
        self.callback = Null()
        self.data = {}
        self.filter_kwargs = {'skipped': True, 'failed': True}
        self.label = Tkinter.Label(self)
        self.label.configure(font = self.font, width = 80, anchor = Tkinter.W) 
        self.configure(labelwidget=self.label)
        self.createwidgets()
        self.label.configure(text = 'Idle')
        self.configure(font = myfont)
        
        
    def createwidgets(self):
        self.listbox = Tkinter.Listbox(self,  foreground='red',
                                   selectmode=Tkinter.SINGLE, font = self.font)

        self.scrollbar = Tkinter.Scrollbar(self, command=self.listbox.yview)
        self.scrollbar.pack(side = Tkinter.RIGHT, fill = Tkinter.Y,
                            anchor = Tkinter.N)
        self.listbox.pack(side = Tkinter.LEFT,
                          fill = Tkinter.BOTH, expand = Tkinter.YES,
                          anchor = Tkinter.NW)
        self.listbox.configure(yscrollcommand = self.scrollbar.set,
                               bg = 'White',selectbackground= 'Red',
                               takefocus= Tkinter.YES)

    def set_callback(self, callback):
        self.callback = callback
        self.listbox.bind('<Double-1>', self.do_callback)

    def do_callback(self, *args):
        report_ids = [self.data[self.listbox.get(int(item))]
                      for item in self.listbox.curselection()]
        for report_id in report_ids:
            self.callback(report_id)

    def set_filter_kwargs(self, **kwargs):
        self.filter_kwargs = kwargs
            
    def update_label(self, report):
        label = report.path
        if not label:
            label = 'Idle'
        self.label.configure(text = label)

    def update_list(self, reportstore):
        reports = reportstore.get(**self.filter_kwargs)
        old_selections = [self.listbox.get(int(sel))
                          for sel in self.listbox.curselection()]
        self.listbox.delete(0, Tkinter.END)
        self.data = {}
        for report in reports:
            label = '%s: %s' % (report.status, report.label)
            self.data[label] = report.full_id
            self.listbox.insert(Tkinter.END, label)
            if label in old_selections:
                self.listbox.select_set(Tkinter.END)
                self.listbox.see(Tkinter.END)
            
            
        

class LabelEntry(Tkinter.Frame):

    font = myfont

    def __init__(self, *args, **kwargs):    
        Tkinter.Frame.__init__(self, *args, **kwargs)
        self.label = Tkinter.Label(self)
        self.label.configure(font = self.font)
        self.label.pack(side = Tkinter.LEFT)
        self.entry = Tkinter.Entry(self)
        self.entry.configure(font = self.font)
        self.entry.pack(side = Tkinter.LEFT, expand = Tkinter.YES,
                        fill = Tkinter.X)

    def update(self, reportstore = Null(), ids = []):
        bgcolor = 'White'
        fgcolor = 'Black'
        root_status = reportstore.root.status
        if root_status == reportstore.ReportClass.Status.Passed():
            bgcolor = 'Green'
        elif root_status == reportstore.ReportClass.Status.Failed():
            bgcolor = 'Red'
            fgcolor = 'White'
        elif root_status == reportstore.ReportClass.Status.Skipped() :
            bgcolor = 'Yellow'
        self.entry.configure(bg = bgcolor, fg = fgcolor)

class ReportFrame(Tkinter.LabelFrame):
    font = myfont

    def __init__(self, *args, **kwargs):    
        Tkinter.LabelFrame.__init__(self, *args, **kwargs)
        self.report = Null()
        self.label = Tkinter.Label(self,foreground="red", justify=Tkinter.LEFT)
        self.label.pack(anchor=Tkinter.W)
        self.label.configure(font = self.font)
        self.configure(labelwidget = self.label)
        self.text = ScrolledText.ScrolledText(self)
        self.text.configure(bg = 'White', font = ('Helvetica', 11, 'normal'))
        self.text.tag_config('sel', relief=Tkinter.FLAT)
        self.text.pack(expand=Tkinter.YES, fill=Tkinter.BOTH,
                       side = Tkinter.TOP)

    def set_report(self, report):
        self.report = report
        self.label.configure(text ='%s: %s' % (self.report.status,
                                               self.report.label),
                             foreground="red", justify=Tkinter.LEFT)
        self.text['state'] = Tkinter.NORMAL
        self.text.delete(1.0, Tkinter.END)
        self.text.insert(Tkinter.END, self.report.error_report)
        self.text.yview_pickplace(Tkinter.END)
        self.text['state'] = Tkinter.DISABLED
        self.attacheditorhotspots(self.text)
        
    def clear(self):
        self.label.configure(text = '')
        self.text['state'] = Tkinter.NORMAL
        self.text.delete(1.0, Tkinter.END)
        self.text['state'] = Tkinter.DISABLED
        
    def launch_editor(self, file, line):
        editor = (py.std.os.environ.get('PYTHON_EDITOR', None) or
                  py.std.os.environ.get('EDITOR_REMOTE', None) or
                  os.environ.get('EDITOR', None) or "emacsclient --no-wait ")
        if editor:
            print "%s +%s %s" % (editor, line, file)
            #py.process.cmdexec('%s +%s %s' % (editor, line, file))
            os.system('%s +%s %s' % (editor, line, file))

    def attacheditorhotspots(self, text):
        # Attach clickable regions to a Text widget.
        filelink = re.compile(r"""\[(?:testcode\s*:)?\s*(.+):(\d+)\]""")
        skippedlink = re.compile(r"""in\s+(/.*):(\d+)\s+""")
        lines = text.get('1.0', Tkinter.END).splitlines(1)
        if not lines:
            return
        tagname = ''
        start, end = 0,0
        for index, line in enumerate(lines):
            match = filelink.search(line)
            if match is None:
                match = skippedlink.search(line)
            if match is None:
                continue
            file, line = match.group(1, 2)
            start, end = match.span()
            tagname = "ref%d" % index
            text.tag_add(tagname,
                         "%d.%d" % (index + 1, start),
                         "%d.%d" % (index + 1, end))
            text.tag_bind(tagname, "<Enter>",
                          lambda e, n=tagname:
                          e.widget.tag_config(n, underline=1))
            text.tag_bind(tagname, "<Leave>",
                          lambda e, n=tagname:
                          e.widget.tag_config(n, underline=0))
            text.tag_bind(tagname, "<Button-1>",
                          lambda e, self=self, f=file, l=line:
                          self.launch_editor(f, l))


class MinimalButton(Tkinter.Button):

    format_string = '%dF / %dS / %dP'
    
    def __init__(self, *args, **kwargs):
        Tkinter.Button.__init__(self, *args, **kwargs)
        self.configure(text = 'Start/Stop') #self.format_string % (0,0,0))

    def update_label(self, reportstore):
        failed = len(reportstore.get(failed = True))
        skipped = len(reportstore.get(skipped = True))
        passed = len(reportstore.get(passed_item = True))
        #self.configure(text = self.format_string % (failed, skipped, passed))
        bgcolor = 'Green'
        fgcolor = 'Black'
        highlightcolor = 'Green',
        activebackground= 'Green',
        activeforeground = 'Black'
        
        if skipped > 0:
            bgcolor = 'Yellow'
            activebackground = 'Yellow'
        if failed > 0:
            bgcolor = 'Red'
            fgcolor = 'White'
            activebackground= 'Red',
            activeforeground = 'White'
            
        self.configure(bg = bgcolor, fg = fgcolor,
                       highlightcolor = highlightcolor,
                       activeforeground = activeforeground,
                       activebackground = activebackground)
        
class LayoutManager:

    def __init__(self):
        self.current_layout = 0
        self.layout_dict = {}
        
    def add(self, widget, layout_ids, **kwargs):
        for id in layout_ids:
            list = self.layout_dict.setdefault(id, [])
            list.append((widget, kwargs))
    
    def set_layout(self, layout = 0):
        if self.current_layout != layout:
            widget_list = self.layout_dict.get(self.current_layout, [])
            for widget, kwargs in widget_list:
                widget.pack_forget()
        self.current_layout = layout
        widget_list = self.layout_dict.get(self.current_layout, [])
        for widget, kwargs in widget_list:
            widget.pack(**kwargs)
        
                      
class TkGui:

    font = ('Helvetica', 9, 'normal')
    
    def __init__(self, parent, config):
        self._parent = parent
        self._config = config
        self._should_stop = False
        #XXX needed?
        self._paths = []
        self.backend = backend.ReportBackend(config)
        self._layoutmanager = LayoutManager()

        self._layout_toggle_var = Tkinter.StringVar()
        self._layout_toggle_var.set('<')
        # events
        self.on_report_updated = Event()
        self.on_report_store_updated = Event()
        self.on_show_report = Event()
        self.on_run_tests = Event()

        self.createwidgets()
        self.timer_update()
        self.report_window = Null()
        self.report_frame = Null()


    def createwidgets(self):
        add = self._layoutmanager.add
        self._buttonframe = Tkinter.Frame(self._parent)
        self._layoutbutton = Tkinter.Button(self._buttonframe, padx=0,
                                            relief=Tkinter.GROOVE,
                                            textvariable=self._layout_toggle_var,
                                            command=self.toggle_layout)        
        add(self._layoutbutton, [0,1], side= Tkinter.LEFT)
        self._entry = LabelEntry(self._buttonframe)
        self._entry.label.configure(text = 'Enter test name:')
        self._entry.entry.bind('<Return>', self.start_tests)
        add(self._entry, [0], side = Tkinter.LEFT, fill = Tkinter.X,
            expand = Tkinter.YES)

        self._run_stop_button = Tkinter.Button(self._buttonframe, text = 'Run',
                               command = self.toggle_action, font = self.font)
        add(self._run_stop_button, [0], side = Tkinter.RIGHT)

        self._minimalbutton = MinimalButton(self._buttonframe, font = self.font,
                                            command = self.toggle_action)
        add(self._minimalbutton, [1], side = Tkinter.RIGHT,
            fill = Tkinter.X, expand = Tkinter.YES)
        add(self._buttonframe, [0,1], side = Tkinter.TOP, fill = Tkinter.X)

        self._statusbar = StatusBar(self._parent)
        self._statusbar.set_filter_args_callback(self.filter_args_changed)
        add(self._statusbar, [0,1], side= Tkinter.BOTTOM, fill=Tkinter.X)

        self._reportlist = ReportListBox(self._parent)
        add(self._reportlist, [0], side = Tkinter.TOP, fill = Tkinter.BOTH,
            expand = Tkinter.YES)
        self._reportlist.set_callback(self.show_report)
        self._report_frame = ReportFrame(self._parent)
        add(self._report_frame, [0], side = Tkinter.TOP, fill = Tkinter.BOTH,
            expand = Tkinter.YES)
        
        #self.on_show_report.subscribe(self.show_report)
        self.on_report_updated.subscribe(self._reportlist.update_label)
        self.on_report_store_updated.subscribe(self._reportlist.update_list)
        self.on_report_store_updated.subscribe(self._minimalbutton.update_label)
        self.on_report_store_updated.subscribe(self.update_status)

        self._layoutmanager.set_layout(0)        
        self.update_status(self.backend.get_store())
        self.messages_callback(None)
        
    def toggle_layout(self):
        if self._layout_toggle_var.get() == '>':
            self._layout_toggle_var.set('<')
            self._layoutmanager.set_layout(0)
        else:
            self._layout_toggle_var.set('>')
            self._layoutmanager.set_layout(1)
        self._parent.geometry('')

    def filter_args_changed(self, **kwargs):
        self._reportlist.set_filter_kwargs(**kwargs)
        self._reportlist.update_list(self.backend.get_store())

    def show_report(self, report_id):
        if report_id is None:
            self._report_frame.clear()
        else:
            report = self.backend.get_store().get(id = report_id)[0]
            self._report_frame.set_report(report)

    def show_error_window(self, report_id):
        report = self.backend.get_store().get(id = report_id)[0]
        if not self.report_window:
            self.report_window = Tkinter.Toplevel(self._parent)
            self.report_window.protocol('WM_DELETE_WINDOW',
                                        self.report_window.withdraw)
            b = Tkinter.Button(self.report_window, text="Close",
                               command=self.report_window.withdraw)
            b.pack(side=Tkinter.BOTTOM)
            #b.focus_set()
            self.report_frame = ReportFrame(self.report_window)
            self.report_frame.pack()
        elif self.report_window.state() != Tkinter.NORMAL:
            self.report_window.deiconify()
            
        self.report_window.title(report.label)    
        self.report_frame.set_report(report)


    def timer_update(self):
        self.backend.update()
        if self.backend.running:
            action = 'Stop'
        else:
            action = 'Run'
        self._run_stop_button.configure(text = action)
        self._minimalbutton.configure(text = action)
        self._parent.after(200, self.timer_update)

    def start_tests(self, dont_care_event=None):
        if self.backend.running:
            return
        paths = [path.strip() for path in self._entry.entry.get().split(',')]
        self.backend.set_messages_callback(self.messages_callback)
        self.backend.set_message_callback(self.message_callback)
        self.backend.start_tests(args = paths)

        self.show_report(None)

    def update_status(self, reportstore):
        self._statusbar.update_all(reportstore = reportstore, ids = [])
        self._entry.update(reportstore = reportstore, ids = [])
                
    def messages_callback(self, report_ids):
        if not report_ids:
            return
        self.on_report_store_updated(self.backend.get_store())

    def message_callback(self, report_id):
        if report_id is None:
            report = Null()
        else:
            report = self.backend.get_store().get(id = report_id)[0]
        self.on_report_updated(report)
        
    def set_paths(self, paths):
        self._paths = paths
        self._entry.entry.insert(Tkinter.END, ', '.join(paths))

    def toggle_action(self):
        if self.backend.running:
            self.stop()
        else:
            self.start_tests()

    def stop(self):
        self.backend.shutdown()
        self.backend.update()
        self.messages_callback([None])
        self.message_callback(None)

    def shutdown(self):
        self.should_stop = True
        self.backend.shutdown()
        py.std.sys.exit()

