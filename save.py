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
import pylab as p
import numpy as n
from time import sleep

def sampledata(around=680, with_peaks_at=(680,)):
    x = n.arange(128) - 64
    x = around + x* 150.0 / 128
    r = n.random.randn(len(x))
    for loc in with_peaks_at:
        r += 10*n.exp(-(x - loc)**2 / 100)
    return x,r

class Graph(wx.Panel):

    def __init__(self,parent,datasource):
        wx.Panel.__init__(self, parent, -1) 

        self.datagen = datasource
        self.create_main_panel()
        self.paused = False

        self.redraw_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)
        self.redraw_timer.Start(100)


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
        self.axes.hold(False)
        
        x,y = self.datagen()
        self.lines = self.axes.plot(x,y)

    def update_plot(self):
        x,y = self.datagen()
        self.lines = self.axes.plot(x,y)
        self.set_bounds()

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
        file_choices = "CSV (*.csv)|*.csv"
        dlg = wx.FileDialog(
            self,
            message="Save data as...",
            defaultDir = os.getcwd(),
            defaultFile = "data.csv",
            wildcard=file_choices,
            style=wx.SAVE)

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            wrt = csv.writer(open(path,'w'))
            for i in range(len(self.lines)):
                x = self.lines[i].get_xdata()
                wrt.writerow(x)
                y = self.lines[i].get_ydata()
                wrt.writerow(y)


    def on_pause_button(self,event):
        self.paused = not self.paused

    def on_update_pause_button(self,event):
        label = "Resume" if self.paused else "Pause"
        self.pause_button.SetLabel(label)

    def on_redraw_timer(self,event):
        if not self.paused:
            self.update_plot()

class IntGraph(Graph):
    def __init__(self, parent, datasource):
        Graph.__init__(self,parent,datasource)
        self.integrating = False

    def update_plot(self):
        x,y = self.datagen()
        if self.integrating:
            y+= self.lines[0].get_ydata()
        self.lines = self.axes.plot(x,y)
        self.set_bounds()
        
    def create_control_bar(self):
        Graph.create_control_bar(self)
        self.int_button= wx.Button(self, -1, "Integration")
        self.Bind(wx.EVT_BUTTON, self.on_int_button, self.int_button)
        self.hbox1.AddSpacer(20)
        self.hbox1.Add(self.int_button, border=5, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL)

    def on_int_button(self,event):
        self.integrating = not self.integrating


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
