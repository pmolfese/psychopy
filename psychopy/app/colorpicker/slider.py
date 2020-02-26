#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Base class for the color slider."""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import wx
import platform


class ColorSlider(wx.Panel):
    """Base class for implementing sliders for picking color values."""
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.NO_BORDER):
        super(ColorSlider, self).__init__(parent, id, pos, size, style)

        # client draw style
        self.SetDoubleBuffered(True)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        # fill bitmap if cached
        self._fillBitmap = None

        # slider position in client window coordinates
        self.sliderPosX = 0
        # slider position in normalized coordinates
        self.sliderNormX = 0.0
        # function for scaling the output
        self._setScaleFunc = None
        self._getScaleFunc = None
        # quantization level for the picker, higher values give better
        # performance but coarser color gradations
        self._quantLevel = 5

        # callback function for when the slider position changes
        self._cbfunc = None

        # events
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouseEvent)

    def OnPaint(self, event):
        """Event called when the slider is redrawn."""
        dc = wx.AutoBufferedPaintDC(self)
        if platform.system() == 'Windows':
            dc.SetBackground(  # ugh...
                wx.Brush(self.GetParent().GetParent().GetThemeBackgroundColour()))
        else:
            dc.SetBackground(wx.Brush(self.GetParent().GetBackgroundColour()))
        dc.Clear()

        clientRect = self.GetClientRect()

        self.fill(dc, clientRect)
        self.drawBorder(dc, clientRect)

    def realize(self):
        """Call after sizing is done."""
        self.SetValue(0.0)

    def OnEraseBackground(self, event):
        """Called when the DC erases the background, does nothing by default."""
        pass

    def fill(self, dc, rect):
        """Art provider function for drawing the slider background. Subclasses
        can override this.

        Parameters
        ----------
        dc : AutoBufferedPaintDC
            Device context used by the control to draw the background.
        rect : wx.Rect
            Client positon and dimensions in window coordinates (x, y, w, h).

        """
        pass

    def drawBorder(self, dc, rect):
        """Draw a border around the control."""
        dc.SetPen(wx.BLACK_PEN)
        dc.SetBrush(wx.TRANSPARENT_BRUSH)
        dc.DrawRectangle(rect)

    def OnMouseEvent(self, event):
        """Event when the mouse is clicked or moved over the control."""
        if event.LeftIsDown():
            clientRect = self.GetClientRect()
            self.sliderPosX = event.GetX()

            padleft = 4
            padright = 4
            bgStart = padleft
            bgEnd = clientRect.width - padright - padleft

            # prevent invalid values
            if self.sliderPosX > bgEnd:
                self.sliderPosX = bgEnd
            elif self.sliderPosX < bgStart:
                self.sliderPosX = bgStart

            self.sliderNormX = (self.sliderPosX - padleft) / float(bgEnd - bgStart)

            # prevent invalid values
            if self.sliderNormX > 1.0:
                self.sliderNormX = 1.0
            elif self.sliderNormX < 0.0:
                self.sliderNormX = 0.0

        self.Refresh()  # redraw when changed
        self.OnValueChanged()

    def OnValueChanged(self):
        """Called after a value changes."""
        pass

    def setSliderChangedCallback(self, cbfunc):
        """Set the callback function for when a slider changes."""
        if not callable(cbfunc):
            raise TypeError("Value for `cbfunc` must be callable.")
        self._cbfunc = cbfunc

    def setGetScaleFunc(self, func):
        """Function for scaling the input value."""
        if not callable(func):
            raise TypeError("Value for `_getScaleFunc` must be callable.")

        self._getScaleFunc = func

    def setSetScaleFunc(self, func):
        """Function for scaling the output value."""
        if not callable(func):
            raise TypeError("Value for `_getSetScaleFunc` must be callable.")

        self._setScaleFunc = func

    def GetValue(self):
        """Get the current value of the slider."""
        return self._getScaleFunc(self.sliderNormX) \
            if self._getScaleFunc is not None else self.sliderNormX

    def SetValue(self, value):
        """Get the current value of the slider."""
        scaledVal = (self._setScaleFunc(value)
            if self._setScaleFunc is not None else value)

        self.sliderNormX = scaledVal
        w = self.GetClientRect().width

        # fit in range
        padleft = 4
        padright = 4
        bgStart = padleft
        bgEnd = w - padright - padleft
        self.sliderPosX = padleft + int((bgEnd - bgStart) * self.sliderNormX)

        self.Refresh()

        self.OnValueChanged()

