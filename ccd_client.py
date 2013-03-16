"""GUI client program for Jobin-Yvon CCD in the Wang Lab.

Downloads spectra from the LabView CCD program running on another computer.
"""

from wx_mpl_dynamic_graph import GraphFrame
from save import Graph, IntGraph, sampledata
from spexgui import Spectrometer
from wanglib.instruments import spex750m
from wanglib.ccd import labview_client
import wx
from argparse import ArgumentParser
from numpy import array

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
            x,y = sampledata(self.center_wl, peak_locs)
            grid.append(y)
        return x, array(grid)

class MainFrame(wx.Frame):

    def __init__(self, clnt, spex=None):
        wx.Frame.__init__(self, None, -1, "CCD Client")

        def fetch():
            x,y = clnt.get_spectrum()
            tr = 3  # truncate point
            return x[tr:],y[6:9].sum(axis=0)[tr:] # only sum the middle rows
            #return x[tr:],y.sum(axis=0)[tr:] # sum all CCD rows
            #return x[tr:],y.transpose()[tr:] # full grid

        self.disp = IntGraph(self,fetch)
        if spex is not None:
            self.control = Spectrometer(self,spec)
            self.disp.hbox2.Add(self.control, 1, border=5, flag=wx.ALL|wx.EXPAND)

            # re-bind the buttons to new methods defined below.
            # this is necessary to inform the ccd program
            # note: to rebind something, use a "Bind" method
            # of the same instance from which it was bound before,
            # (hence self.control.Bind and not self.Bind below)
            self.control.Bind(wx.EVT_BUTTON, self.on_move_button, self.control.move.button)
            self.control.Bind(wx.EVT_BUTTON, self.on_cal_button, self.control.cal.button)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.disp, 1, flag=wx.LEFT | wx.TOP | wx.GROW)

        self.SetSizer(self.sizer)
        self.sizer.Fit(self)

    def on_move_button(self,event):
        self.control.on_move_button(event)
        clnt.center_wl = spec.wavelength

    def on_cal_button(self,event):
        self.control.on_cal_button(event)
        clnt.center_wl = spec.wavelength

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

    app = wx.PySimpleApp()
    app.frame = MainFrame(clnt, spec)
    app.frame.Show()
    app.MainLoop()
