#!/usr/bin/python

import wx
import os
import csv
from math import floor, ceil
#from wx_mpl_dynamic_graph import GraphFrame
import matplotlib
matplotlib.use('WXAgg',warn=False)
from matplotlib.backends.backend_wxagg import \
        FigureCanvasWxAgg as FigCanvas
from wx_mpl_dynamic_graph import BoundControlBox
import numpy as n
from time import sleep
import threading

def sampledata(around=680, with_peaks_at=(680,), lag=.2):
    x = n.arange(1024) - 512
    x = around + x* 150.0 / 512
    r = n.random.randn(len(x))
    for loc in with_peaks_at:
        r += 10*n.exp(-(x - loc)**2 / 100)
    sleep(lag)
    return x,r

# threading code mostly stolen from http://wiki.wxpython.org/LongRunningTasks

# Define notification event for thread completion
import wx.lib.newevent
ResultEvent, EVT_RESULT = wx.lib.newevent.NewEvent()

# Thread class that executes processing
class WorkerThread(threading.Thread):
    """Worker Thread Class."""
    def __init__(self, notify_window, func):
        """Init Worker Thread Class."""
        threading.Thread.__init__(self)
        self.func = func
        self._notify_window = notify_window
        self._want_abort = 0

    def run(self):
        """Run Worker Thread."""
        # This is the code executing in the new thread. 
        # peek at the abort variable once in a while to see if we should stop
        while True:
            if self._want_abort:
                # Use a result of None to acknowledge the abort
                wx.PostEvent(self._notify_window, ResultEvent(data=None))
                return
            # Send data to the parent thread
            data = self.func()
            wx.PostEvent(self._notify_window, ResultEvent(data=data))

    def abort(self):
        """abort worker thread."""
        # Method for use by main thread to signal an abort
        self._want_abort = 1

class Graph(wx.Panel):

    def __init__(self,parent,datasource):
        wx.Panel.__init__(self, parent, -1) 

        self.datagen = datasource
        self.create_main_panel()

        self.paused = True
        #self.start_worker()

        self.Bind(EVT_RESULT, self.on_result)

    def start_worker(self):
        self.worker = WorkerThread(self, self.datagen)
        self.worker.start()

    def create_control_bar(self):
        self.pause_button = wx.Button(self, -1, "Pause")
        self.Bind(wx.EVT_BUTTON, self.on_pause_button, self.pause_button)
        self.Bind(wx.EVT_UPDATE_UI, self.on_update_pause_button, self.pause_button)
        self.save_button = wx.Button(self, -1, "Save data")
        self.Bind(wx.EVT_BUTTON, self.on_save_button, self.save_button)

        self.hbox1 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox1.Add(self.pause_button, border=5, flag=wx.ALL |
                       wx.ALIGN_CENTER_VERTICAL)
        self.hbox1.AddSpacer(20)
        self.hbox1.Add(self.save_button, border=5, flag=wx.ALL |
                       wx.ALIGN_CENTER_VERTICAL)

    def create_main_panel(self):
        # define the displays and controls
        self.init_plot()
        self.canvas = FigCanvas(self, -1, self.fig)

        self.create_control_bar()

        self.xmin_control = BoundControlBox(self, -1, "X min", 0)
        self.xmin_control.radio_auto.SetValue(True)
        self.xmax_control = BoundControlBox(self, -1, "X max", 50)
        self.xmax_control.radio_auto.SetValue(True)
        self.ymin_control = BoundControlBox(self, -1, "Y min", 0)
        self.ymin_control.radio_auto.SetValue(True)
        self.ymax_control = BoundControlBox(self, -1, "Y max", 100)
        self.ymax_control.radio_auto.SetValue(True)
        
        # lay displays and controls out on the page
        self.hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        self.hbox2.Add(self.xmin_control, border=5, flag=wx.ALL)
        self.hbox2.Add(self.xmax_control, border=5, flag=wx.ALL)
        self.hbox2.Add(self.ymin_control, border=5, flag=wx.ALL)
        self.hbox2.Add(self.ymax_control, border=5, flag=wx.ALL)

        self.vbox = wx.BoxSizer(wx.VERTICAL)
        self.vbox.Add(self.canvas, 1, flag=wx.LEFT | wx.TOP | wx.GROW)
        self.vbox.Add(self.hbox1, 0, flag=wx.ALIGN_LEFT | wx.TOP | wx.EXPAND)
        self.vbox.Add(self.hbox2, 0, flag=wx.ALIGN_LEFT | wx.TOP | wx.EXPAND)

        self.SetSizer(self.vbox)
        self.vbox.Fit(self)

    def init_plot(self):
        self.fig = matplotlib.figure.Figure()
        self.axes = self.fig.add_subplot(111)
        
        x,y = self.datagen()
        self.lines = self.axes.plot(x,y)

    def on_result(self, event):
        if event.data is None:
            pass
        else:
            x,y = event.data
            self.update_plot(x,y)
            self.set_bounds()

    def update_plot(self, x, y):
        self.lines[0].set_data(x,y)
        self.axes.relim()
        self.axes.autoscale_view()

    def set_bounds(self):
        if not self.xmax_control.is_auto():
            xmax = float(self.xmax_control.manual_value())
            self.axes.set_xbound(upper = xmax)
        if not self.xmin_control.is_auto():
            xmin = float(self.xmin_control.manual_value())
            self.axes.set_xbound(lower = xmin)

        if not self.ymax_control.is_auto():
            ymax = float(self.ymax_control.manual_value())
            self.axes.set_ybound(upper = ymax)
        if not self.ymin_control.is_auto():
            ymin = float(self.ymin_control.manual_value())
            self.axes.set_ybound(lower = ymin)

        self.canvas.draw()

    # define event handlers

    def on_save_button(self, event):
        file_choices = "CSV (*.csv)|*.csv|Numpy (*.npy)|*.npy"
        dlg = wx.FileDialog(
            self,
            message="Save data as...",
            defaultDir = os.getcwd(),
            defaultFile = "data.csv",
            wildcard=file_choices,
            style=wx.SAVE|wx.OVERWRITE_PROMPT)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            # verify extension
            extensions = ('.csv', '.npy')
            ext = extensions[dlg.GetFilterIndex()]
            if type(path) is unicode:
                ext = unicode(ext)
            base, userext = os.path.splitext(path)
            if not userext == ext:
                path += ext
            if str(ext) == '.csv':
                self.save_csv(path)
            elif str(ext) == '.npy':
                self.save_npy(path)

    def save_csv(self, path):
        wrt = csv.writer(open(path,'w'))
        def cols(lines):
            for line in lines:
                yield line.get_xdata()
                yield line.get_ydata()
        for row in zip(*cols(self.lines)):
            wrt.writerow(row)

    def save_npy(self, path):
        lines = self.lines
        if len(lines) == 1:
            n.save(path, lines[0].get_data())
        else:
            n.save(path, [l.get_data() for l in lines])

    def on_pause_button(self,event):
        self.paused = not self.paused
        if not self.paused:
            self.start_worker()
        else:
            self.worker._want_abort = True

    def on_update_pause_button(self,event):
        label = "Resume" if self.paused else "Pause"
        self.pause_button.SetLabel(label)

class IntGraph(Graph):
    def __init__(self, parent, datasource):
        Graph.__init__(self,parent,datasource)
        self.integrating = False

    def update_plot(self, x, y):
        if self.integrating:
            y+= self.lines[0].get_ydata()
        super(IntGraph, self).update_plot(x, y)

    def create_control_bar(self):
        Graph.create_control_bar(self)
        self.int_button= wx.Button(self, -1, "Integration")
        self.Bind(wx.EVT_BUTTON, self.on_int_button, self.int_button)
        self.hbox1.AddSpacer(20)
        self.hbox1.Add(self.int_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)

    def on_int_button(self,event):
        self.integrating = not self.integrating

class SpecGraph(IntGraph):

    def init_plot(self):
        super(SpecGraph, self).init_plot()
        self.add_dualtick()

    def add_dualtick(self):
        # add a second x axis enumerated in eV
        xconv = lambda wl: 1240. / wl
        self.axes2 = self.axes.twiny()
        self.axes2.set_xlim(xconv(x) for x in self.axes.get_xlim())
        self.axes2.set_ylim(self.axes.get_ylim())

    def update_plot(self, x, y):
        self.axes.figure.delaxes(self.axes2)
        super(SpecGraph, self).update_plot(x, y)
        self.add_dualtick()


class MainFrame(wx.Frame):

    title = "Data Graph"
    
    def __init__(self,datasource):
        wx.Frame.__init__(self, None, -1, self.title)
        self.panel = IntGraph(self,datasource)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.panel, 1, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.sizer.Fit(self)

if __name__ == "__main__":
    app = wx.PySimpleApp()
    app.frame = MainFrame(sampledata)
    app.frame.Show()
    app.MainLoop()
