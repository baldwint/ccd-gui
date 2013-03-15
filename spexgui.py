import wx
from wanglib.instruments import spex750m

class SingleChoice(wx.Panel):
    def __init__(self, parent, initval, buttontext):
        wx.Panel.__init__(self, parent, -1) 
        
        # controls
        self.field = wx.TextCtrl(self, -1, size = (35,-1),
                                           value = str(initval))
        self.button = wx.Button(self, -1, buttontext)

        # layout
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.field, 1, flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.button, 0, flag=wx.ALIGN_CENTER_VERTICAL)

        self.SetSizer(sizer)
        sizer.Fit(self)

class Spectrometer(wx.Panel):
    """A WX panel providing controls for moving a spectrometer.
    pass the spectrometer instance to this when instantiating.
    """

    def __init__(self, parent, spectrometer_instance):
        wx.Panel.__init__(self, parent, -1) 

        # interface to the instrument.
        self.spec = spectrometer_instance

        # arrange controls vertically
        self.box = wx.StaticBox(self, -1)
        sizer = wx.StaticBoxSizer(self.box, wx.VERTICAL)
        self.update_label()

        # the most basic control: change the wavelength
        self.move = SingleChoice(self, self.spec.wavelength, "Move to")
        self.Bind(wx.EVT_BUTTON, self.on_move_button, self.move.button)
        sizer.Add(self.move, 0, wx.ALL|wx.EXPAND, 10)

        # if there is a calibration method, provide a control for it
        if hasattr(self.spec,"calibrate"):
            self.cal = SingleChoice(self, self.spec.wavelength, "Calibrate")
            self.Bind(wx.EVT_BUTTON, self.on_cal_button, self.cal.button)
            sizer.Add(self.cal, 0, wx.ALL|wx.EXPAND, 10)

        self.SetSizer(sizer)
        sizer.Fit(self)

    def update_label(self):
        self.box.SetLabel("%s at %.1fnm" % (self.spec, self.spec.wavelength))

    def on_move_button(self, event):
        self.wavelength = float(self.move.field.GetValue())
        self.spec.set_wavelength(self.wavelength)
        self.update_label()

    def on_cal_button(self, event):
        self.wavelength = float(self.cal.field.GetValue())
        self.spec.calibrate(self.wavelength)
        self.update_label()

class MainFrame(wx.Frame):

    def __init__(self,spectrometer_instance):
        wx.Frame.__init__(self, None, -1, "%s Control" % spectrometer_instance)

        self.panel = Spectrometer(self,spectrometer_instance)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.panel, 1, wx.EXPAND)

        self.SetSizer(self.sizer)
        self.sizer.Fit(self)

if __name__ == "__main__":
    app = wx.PySimpleApp()
    app.frame = MainFrame(spex750m('/dev/ttyUSB1'))
    app.frame.Show()
    app.MainLoop()
