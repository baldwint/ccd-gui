from wx_mpl_dynamic_graph import GraphFrame
from save import Graph,IntGraph
#from spexgui import Spectrometer
from wanglib.instruments import spex750m
from wanglib.ccd import labview_client
import wx

# establish serial communication with the 750M.
# hopefully its wl property is already calibrated
# to whatever is shown in the window.
#spec = spex750m()

# temporarily just grab from command line
from sys import argv
wl = float(argv[1])

clnt = labview_client(center_wl = wl, host = "INSERT.IP.ADDRESS.HERE")
sumit = True
pickit = True

def fetch():
    x,y = clnt.get_spectrum()
    tr = 3  # truncate point
    if pickit:
        return x[tr:],y[6:9].sum(axis=0)[tr:]
    elif sumit:
        return x[tr:],y.sum(axis=0)[tr:]
    else:
        return x[tr:],y.transpose()[tr:]

class MainFrame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, -1, "CCD Client")

        self.disp = IntGraph(self,fetch)
#        self.control = Spectrometer(self,spec)

        # re-bind the buttons to new methods defined below.
        # this is necessary to inform the ccd program
        # note: to rebind something, use a "Bind" method
        # of the same instance from which it was bound before,
        # (hence self.control.Bind and not self.Bind below)
#        self.control.Bind(wx.EVT_BUTTON, self.on_move_button, self.control.move.button)
#        self.control.Bind(wx.EVT_BUTTON, self.on_cal_button, self.control.cal.button)
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.disp, 1, flag=wx.LEFT | wx.TOP | wx.GROW)
#        self.sizer.Add(self.control, 0, flag=wx.ALIGN_LEFT | wx.TOP | wx.EXPAND)

        self.SetSizer(self.sizer)
        self.sizer.Fit(self)

    def on_move_button(self,event):
        self.control.on_move_button(event)
        clnt.center_wl = spec.wavelength
        print clnt.center_wl

    def on_cal_button(self,event):
        self.control.on_cal_button(event)
        clnt.center_wl = spec.wavelength
        print clnt.center_wl

if __name__ == "__main__":
    app = wx.PySimpleApp()
    app.frame = MainFrame()
    app.frame.Show()
    app.MainLoop()
