"""GUI client program for Jobin-Yvon CCD in the Wang Lab.

Downloads spectra from the LabView CCD program running on another computer.
"""

from wx_mpl_dynamic_graph import GraphFrame
from save import SpecGraph, sampledata
from spexgui import Spectrometer
from wanglib.instruments import spex750m
from wanglib.ccd import labview_client, InstrumentError
import wx
from argparse import ArgumentParser
import numpy

# define command line arguments
parser = ArgumentParser(description=__doc__)
parser.add_argument('--ip', dest='ip', metavar='ADDRESS',
        help="IP address of the computer running the LabView program.")
parser.add_argument('--spec', dest='spec_addr',  metavar='ADDRESS',
        help="Spectrometer RS232 address")
parser.add_argument('--wl', dest='wl', type=int,
        help="If --spec is not given, provide the wavelength displayed in Spex750M window, in nm.")

class Fake_Client(object):
    """ Imitates a wanglib.ccd.labview_client object """

    center_wl = 680

    def get_spectrum(self):
        grid = []
        peak_locs = range(600, 1000, 100)
        for i in range(10):
            x,y = sampledata(self.center_wl, peak_locs, lag=.02)
            grid.append(y)
        return x, numpy.array(grid)

class CalData(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)

        # arrange controls vertically
        self.box = wx.StaticBox(self, -1)
        self.box.SetLabel('Reference lines')
        sizer = wx.StaticBoxSizer(self.box, wx.VERTICAL)

        # add checkboxes
        self.ne = wx.CheckBox(self, -1, 'Ne')
        sizer.Add(self.ne, 0, flag=wx.ALIGN_CENTER_VERTICAL)
        self.ar = wx.CheckBox(self, -1, 'Ar')
        sizer.Add(self.ar, 0, flag=wx.ALIGN_CENTER_VERTICAL)

        # bind to events
        self.Bind(wx.EVT_CHECKBOX, self.on_ne, self.ne)
        self.Bind(wx.EVT_CHECKBOX, self.on_ar, self.ar)

        self.SetSizer(sizer)
        sizer.Fit(self)

    data = None

    @staticmethod
    def read_NIST(filename):
        """
        ascii data from http://physics.nist.gov/cgi-bin/ASD/lines1.pl

        columns of returned array are observed wl, relative int, and aki (?)
        """
        a = numpy.genfromtxt(filename, delimiter='|',
                skip_header=6, skip_footer=1)
        data = a[:,1:4] # select location, relative int, and aki (?)
        mask = numpy.isnan(data[:,0]) # some lines are blank
        return data[~mask]

    def on_ar(self, event):
        if event.Checked():
            #load up the data
            wls, rel_int, aki = self.read_NIST('caldata/Ar.txt').T
            self.data = wls[rel_int > 1e4]
        event.Skip() # pass it up the chain

    def on_ne(self, event):
        if event.Checked():
            #load up the data
            wls, rel_int, aki = self.read_NIST('caldata/Ne.txt').T
            self.data = wls[rel_int > 1e4]
        event.Skip() # pass it up the chain

class MainFrame(wx.Frame):

    def __init__(self, clnt, spex=None):
        wx.Frame.__init__(self, None, -1, "CCD Client")

        def fetch():
            try:
                x,y = clnt.get_spectrum()
            except InstrumentError:
                clnt.connect() # try reconnecting
                x,y = clnt.get_spectrum()
            y = y.sum(axis=0) # collapse to 1D
            tr = 3  # truncate point
            return x[tr:], y[tr:]

        self.disp = SpecGraph(self,fetch)
        self.centerline = None
        self.spexlines = {}

        # cal data viewer
        self.caldata = CalData(self)
        self.disp.hbox2.Add(self.caldata, 1, border=5, flag=wx.ALL)
        self.Bind(wx.EVT_CHECKBOX, self.on_ne_checkbox, self.caldata.ne)
        self.Bind(wx.EVT_CHECKBOX, self.on_ar_checkbox, self.caldata.ar)

        if spex is not None:
            self.control = Spectrometer(self,spec)
            self.disp.hbox2.Add(self.control, 1, border=5, flag=wx.ALL|wx.EXPAND)

            # re-bind the buttons to new methods defined below.
            # this is necessary to inform the ccd program
            # note: to rebind something, use a "Bind" method
            # of the same instance from which it was bound before,
            # (hence self.control.Bind and not self.Bind below)
            self.control.Bind(wx.EVT_BUTTON, self.on_move_button, self.control.move.button)
            self.control.Bind(wx.EVT_TEXT_ENTER, self.on_move_button, self.control.move.field)
            self.control.Bind(wx.EVT_BUTTON, self.on_cal_button, self.control.cal.button)
            self.control.Bind(wx.EVT_TEXT_ENTER, self.on_cal_button, self.control.cal.field)

            # draw center line
            self.draw_centerline()

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.disp, 1, flag=wx.LEFT | wx.TOP | wx.GROW)

        self.SetSizer(self.sizer)
        self.sizer.Fit(self)

    def on_move_button(self,event):
        self.control.on_move_button(event)
        clnt.center_wl = spec.wavelength
        self.draw_centerline()

    def on_cal_button(self,event):
        self.control.on_cal_button(event)
        clnt.center_wl = spec.wavelength
        self.draw_centerline()

    def draw_centerline(self):
        if self.centerline is not None:
            self.centerline.remove()
        self.centerline = self.disp.axes.axvline(spec.wl, c='k', ls='--')

    def on_ne_checkbox(self, event):
        if event.Checked():
            self.spexlines['Ne'] = self.draw_spexlines(self.caldata.data, 'r')
        else:
            for line in self.spexlines['Ne']:
                line.remove()

    def on_ar_checkbox(self, event):
        if event.Checked():
            self.spexlines['Ar'] = self.draw_spexlines(self.caldata.data, 'm')
        else:
            for line in self.spexlines['Ar']:
                line.remove()

    def draw_spexlines(self, locs, color):
        return [self.disp.axes.axvline(wl, c=color, ls=':') for wl in locs]


if __name__ == "__main__":
    # get command line args
    args = parser.parse_args()

    # if --spec is provided, open connection to spex
    if args.spec_addr is not None:
        spec = spex750m(args.spec_addr)
        initial_wl = spec.get_wl()
    else:
        spec = None
        initial_wl = args.wl

    if args.ip is not None:
        clnt = labview_client(center_wl=initial_wl, host=args.ip)
    else:
        print 'No IP address provided'
        print 'proceeding with FAKE DATA'
        clnt = Fake_Client()
        if spec is not None:
            clnt.center_wl = spec.wl

    app = wx.App(False)
    app.frame = MainFrame(clnt, spec)
    app.frame.Show()
    app.MainLoop()
