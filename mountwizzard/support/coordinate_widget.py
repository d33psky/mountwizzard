############################################################
# -*- coding: utf-8 -*-
#
# Python-based Tool for interaction with the 10micron mounts
# GUI with PyQT5 for python
# Python  v3.5
#
# Michael Würtenberger
# (c) 2016, 2017
#
# Licence APL2.0
#
############################################################
# standard solutions
import logging
import datetime
import copy
# import for the PyQt5 Framework
from PyQt5 import QtCore
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from support.mw_widget import MwWidget
from support.coordinate_dialog_ui import Ui_CoordinateDialog


def getXYRectangle(az, width, border):
    x = (az - 15) * (width - 2 * border) / 360 + border
    y = border
    return int(x + 0.5), int(y + 0.5)


def getXY(az, alt, height, width, border):                                                                                  # calculation of the position
    x = border + (az / 360 * (width - 2 * border))
    y = height - border - (alt / 90 * (height - 2 * border))
    return int(x + 0.5), int(y + 0.5)

BORDER_VIEW = 20                                                                                                            # 20 point from graphics border
TEXTHEIGHT_VIEW = 10                                                                                                        # text size for drawing
ELLIPSE_VIEW = 12                                                                                                           # size of the circles of points


class ShowCoordinatePopup(MwWidget):
    logger = logging.getLogger(__name__)

    def __init__(self, app):
        super(ShowCoordinatePopup, self).__init__()
        self.app = app
        self.pointerAzAlt = QGraphicsItemGroup()                                                                            # object placeholder for AzAlt Pointer
        self.pointerTrack = QGraphicsItemGroup()                                                                            # same for tracking widget
        self.pointerTrackLine = []                                                                                          # same for Track line
        self.itemFlipTime = QGraphicsItemGroup()                                                                            # same for flip indicator
        self.itemFlipTimeText = QGraphicsTextItem('')                                                                       # and the flip time
        self.pointerDome = QGraphicsRectItem(0, 0, 0, 0)                                                                    # shape for the Dome
        self.showStatus = False                                                                                             # show coordinate window
        self.ui = Ui_CoordinateDialog()                                                                                     # PyQt5 dialog ui
        self.ui.setupUi(self)                                                                                               # setup the ui
        self.initUI()                                                                                                       # adaptions to ui setup
        self.ui.windowTitle.setPalette(self.palette)                                                                        # set windows palette
        self.app.mount.signalMountAzAltPointer.connect(self.setAzAltPointer)                                                # connect signal for AzAlt pointer
        self.app.mount.signalMountTrackPreview.connect(self.drawTrackPreview)                                               # same for track preview
        self.app.ui.checkRunTrackingWidget.toggled.connect(self.changeStatusTrackingWidget)                                 # if tracking widget is switched on / off, here is the signal for it
        self.app.model.signalModelRedraw.connect(self.redrawCoordinateWindow)                                               # signal for redrawing the window content
        self.app.dome.signalDomPointer.connect(self.setDomePointer)                                                         # signal for redrawing the dome
        self.ui.btn_selectClose.clicked.connect(self.hideCoordinateWindow)                                                  # signal for closing (not destroying) the window
        self.redrawCoordinateWindow()                                                                                       # at the beginning, initialize the content
        self.show()                                                                                                         # construct the window
        self.setVisible(False)                                                                                              # but hide it first

    def hideCoordinateWindow(self):                                                                                         # method for switching visibility
        self.showStatus = False                                                                                             # status = off
        self.setVisible(False)                                                                                              # hide it

    @QtCore.Slot(float, float)
    def setAzAltPointer(self, az, alt):                                                                                     # method for pointer drawing
        x, y = getXY(az, alt, self.ui.modelPointsPlot.height(), self.ui.modelPointsPlot.width(), BORDER_VIEW)               # get the right coordinates
        self.pointerAzAlt.setPos(x, y)                                                                                      # set it position
        self.pointerAzAlt.setVisible(True)                                                                                  # show it
        self.pointerAzAlt.update()
        self.ui.modelPointsPlot.viewport().update()
        QApplication.processEvents()

    @QtCore.Slot(float)
    def setDomePointer(self, az):                                                                                           # same for dome
        width = self.ui.modelPointsPlot.width()
        x, y = getXYRectangle(az, width, BORDER_VIEW)
        self.pointerDome.setPos(x, y)
        self.pointerDome.setVisible(True)
        self.pointerDome.update()
        self.ui.modelPointsPlot.viewport().update()
        QApplication.processEvents()

    def changeStatusTrackingWidget(self):                                                                                   # method for enable / disable tracking widget
        if self.app.ui.checkRunTrackingWidget.isChecked():
            self.drawTrackPreview()
        else:
            self.pointerTrack.setVisible(False)

    def drawTrackPreview(self):                                                                                             # method for drawing the track
        if not self.app.ui.checkRunTrackingWidget.isChecked():
            return
        raCopy = copy.copy(self.app.mount.ra)                                                                               # start wit the actual coordinates of the mount
        decCopy = copy.copy(self.app.mount.dec)                                                                             # but copy it (otherwise it will be changes during the calculation -> python object model)
        width = self.ui.modelPointsPlot.width()                                                                             # get data from ui
        height = self.ui.modelPointsPlot.height()
        self.pointerTrack.setVisible(True)
        for i in range(0, 50):                                                                                              # round model point from actual az alt position 24 hours
            ra = raCopy - float(i) * 10 / 50                                                                                # 12 hours line max
            az, alt = self.app.mount.transformNovas(ra, decCopy, 1)                                                         # transform to az alt
            x, y = getXY(az, alt, height, width, BORDER_VIEW)
            self.pointerTrackLine[i].setPos(x, y)
            if alt > 0:
                self.pointerTrackLine[i].setVisible(True)
            else:
                self.pointerTrackLine[i].setVisible(False)
        az, alt = self.app.mount.transformNovas(self.app.mount.ra - float(self.app.mount.timeToFlip) / 60, decCopy, 1)       # transform to az alt
        x, y = getXY(az, alt, height, width, BORDER_VIEW)
        self.itemFlipTime.setPos(x, y)
        delta = float(self.app.mount.timeToFlip)
        fliptime = datetime.datetime.now() + datetime.timedelta(minutes=delta)
        self.itemFlipTimeText.setPlainText(' {0:%H:%M}\n{1:03.0f} min'.format(fliptime, delta))
        self.pointerTrack.update()
        self.ui.modelPointsPlot.viewport().update()
        QApplication.processEvents()

    def constructTrackWidget(self, esize):
        group = QGraphicsItemGroup()
        groupFlipTime = QGraphicsItemGroup()
        track = []
        group.setVisible(False)
        poly = QPolygonF()
        poly.append(QPointF(0, 0))
        poly.append(QPointF(45, 0))
        poly.append(QPointF(45, 35))
        poly.append(QPointF(0, 35))
        poly.append(QPointF(0, 0))
        item = QGraphicsPolygonItem(poly)
        pen = QPen(self.COLOR_BACKGROUND, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        item.setPen(pen)
        item.setBrush(QBrush(self.COLOR_BACKGROUND))
        item.setOpacity(0.8)
        groupFlipTime.addToGroup(item)
        pen = QPen(self.COLOR_TRACKWIDGETPOINTS, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        for i in range(0, 50):
            item = QGraphicsEllipseItem(-esize / 8, -esize / 8, esize / 4, esize / 4)
            item.setPen(pen)
            group.addToGroup(item)
            track.append(item)
        itemText = QGraphicsTextItem(' 19:20\n000 min', None)
        itemText.setDefaultTextColor(self.COLOR_TRACKWIDGETTEXT)
        groupFlipTime.addToGroup(itemText)
        pen = QPen(self.COLOR_WHITE, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        item = QGraphicsEllipseItem(- esize / 4, -esize / 4, esize / 2, esize / 2)
        item.setPen(pen)
        groupFlipTime.addToGroup(item)
        item = QGraphicsRectItem(0, -esize, 0, 2 * esize)
        item.setPen(pen)
        groupFlipTime.addToGroup(item)
        group.addToGroup(groupFlipTime)
        return group, groupFlipTime, itemText, track

    def constructHorizon(self, scene, horizon, height, width, border):
        if len(horizon) == 0:
            return scene
        pen = QPen(self.COLOR_GREEN_HORIZON, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                      # define the pen style thickness 3
        poly = QPolygonF()
        x, y = getXY(0, 0, height, width, border)
        poly.append(QPointF(x, y))
        x, y = getXY(0, horizon[0][1], height, width, border)
        poly.append(QPointF(x, y))
        for i, p in enumerate(horizon):
            x, y = getXY(horizon[i][0], horizon[i][1], height, width, border)
            poly.append(QPointF(x, y))
        x, y = getXY(360, horizon[len(horizon)-1][1], height, width, border)
        poly.append(QPointF(x, y))
        x, y = getXY(360, 0, height, width, border)
        poly.append(QPointF(x, y))
        scene.addPolygon(poly, pen, self.COLOR_GREEN_HORIZON_DARK)
        return scene

    def constructModelGrid(self, height, width, border, textheight, scene):                                                 # adding the plot area
        scene.setBackgroundBrush(self.COLOR_WINDOW)                                                                         # background color
        pen = QPen(self.COLOR_BACKGROUND, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                       # building the grid of the plot and the axes
        for i in range(0, 361, 30):                                                                                         # set az ticks
            scene.addLine(border + int(i / 360 * (width - 2 * border)), height - border,
                          border + int(i / 360 * (width - 2 * border)), border, pen)
        for i in range(0, 91, 10):                                                                                          # set alt ticks
            scene.addLine(border, height - border - int(i * (height - 2 * border) / 90),
                          width - border, height - border - int(i * (height - 2*border) / 90), pen)
        scene.addRect(border, border, width - 2*border, height - 2*border, pen)                                             # set frame around graphics
        for i in range(0, 361, 30):                                                                                         # now the texts at the plot x
            text_item = QGraphicsTextItem('{0:03d}'.format(i), None)                                                        # set labels
            text_item.setDefaultTextColor(self.COLOR_ASTRO)                                                                 # coloring of label
            text_item.setPos(int(border / 2) + int(i / 360 * (width - 2 * border)), height - border)                        # placing the text
            scene.addItem(text_item)                                                                                        # adding item to scene to be shown
        for i in range(10, 91, 10):                                                                                         # now the texts at the plot y
            text_item = QGraphicsTextItem('{0:02d}'.format(i), None)
            text_item.setDefaultTextColor(self.COLOR_ASTRO)
            text_item.setPos(width - border, height - border - textheight - int(i * (height - 2 * border) / 90))
            scene.addItem(text_item)
            text_item = QGraphicsTextItem('{0:02d}'.format(i), None)
            text_item.setDefaultTextColor(self.COLOR_ASTRO)
            text_item.setPos(0, height - border - textheight - int(i * (height - 2 * border) / 90))
            scene.addItem(text_item)
        return scene

    def constructAzAltPointer(self, esize):
        group = QGraphicsItemGroup()
        group.setVisible(False)
        pen = QPen(self.COLOR_POINTER, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        item = QGraphicsEllipseItem(-esize, -esize, 2 * esize, 2 * esize)
        item.setPen(pen)
        group.addToGroup(item)
        pen = QPen(self.COLOR_POINTER, 1, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        item = QGraphicsLineItem(-esize, 0, -esize / 2, 0)
        item.setPen(pen)
        group.addToGroup(item)
        item = QGraphicsLineItem(0, -esize, 0, -esize / 2)
        item.setPen(pen)
        group.addToGroup(item)
        item = QGraphicsLineItem(esize / 2, 0, esize, 0)
        item.setPen(pen)
        group.addToGroup(item)
        item = QGraphicsLineItem(0, esize / 2, 0, esize)
        item.setPen(pen)
        group.addToGroup(item)
        return group

    def redrawCoordinateWindow(self):
        height = self.ui.modelPointsPlot.height()
        width = self.ui.modelPointsPlot.width()
        scene = QGraphicsScene(0, 0, width-2, height-2)                                                                     # set the size of the scene to to not scrolled
        pen = QPen(self.COLOR_WHITE, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                            # outer circle is white
        brush = QBrush(self.COLOR_BACKGROUND)
        self.pointerDome = scene.addRect(0, 0, int((width - 2 * BORDER_VIEW) * 30 / 360), int(height - 2 * BORDER_VIEW), pen, brush)
        self.pointerDome.setVisible(False)
        self.pointerDome.setOpacity(0.5)
        scene = self.constructModelGrid(height, width, BORDER_VIEW, TEXTHEIGHT_VIEW, scene)
        scene = self.constructHorizon(scene, self.app.model.horizonPoints, height, width, BORDER_VIEW)
        for i, p in enumerate(self.app.model.BasePoints):                                                                   # show the points
            pen = QPen(self.COLOR_RED, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                          # outer circle is white
            x, y = getXY(p[0], p[1], height, width, BORDER_VIEW)
            scene.addEllipse(x - ELLIPSE_VIEW / 2, y - ELLIPSE_VIEW / 2, ELLIPSE_VIEW, ELLIPSE_VIEW, pen)
            pen = QPen(self.COLOR_YELLOW, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                       # inner circle -> after modelling green or red
            x, y = getXY(p[0], p[1], height, width, BORDER_VIEW)
            item = scene.addEllipse(-ELLIPSE_VIEW / 4, -ELLIPSE_VIEW / 4, ELLIPSE_VIEW/2, ELLIPSE_VIEW/2, pen)
            item.setPos(x, y)
            text_item = QGraphicsTextItem('{0:02d}'.format(i+1), None)                                                      # put the enumerating number to the circle
            text_item.setDefaultTextColor(self.COLOR_ASTRO)
            text_item.setPos(x - ELLIPSE_VIEW / 8, y - ELLIPSE_VIEW / 8)
            scene.addItem(text_item)
            self.app.model.BasePoints[i] = (p[0], p[1], item, True)                                                         # storing the objects in the list
        for i, p in enumerate(self.app.model.RefinementPoints):                                                             # show the points
            pen = QPen(self.COLOR_GREEN, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                        # outer circle is white
            x, y = getXY(p[0], p[1], height, width, BORDER_VIEW)
            scene.addEllipse(x - ELLIPSE_VIEW / 2, y - ELLIPSE_VIEW / 2, ELLIPSE_VIEW, ELLIPSE_VIEW, pen)
            pen = QPen(self.COLOR_YELLOW, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)                                       # inner circle -> after modelling green or red
            x, y = getXY(p[0], p[1], height, width, BORDER_VIEW)
            item = scene.addEllipse(-ELLIPSE_VIEW/4, -ELLIPSE_VIEW/4, ELLIPSE_VIEW/2, ELLIPSE_VIEW/2, pen)
            item.setPos(x, y)
            text_item = QGraphicsTextItem('{0:02d}'.format(i+1), None)                                                      # put the enumerating number to the circle
            text_item.setDefaultTextColor(self.COLOR_WHITE)
            text_item.setPos(x - ELLIPSE_VIEW / 8, y - ELLIPSE_VIEW / 8)
            scene.addItem(text_item)
            self.app.model.RefinementPoints[i] = (p[0], p[1], item, True)                                                   # storing the objects in the list
        self.pointerAzAlt = self.constructAzAltPointer(ELLIPSE_VIEW)
        self.pointerTrack, self.itemFlipTime, self.itemFlipTimeText, self.pointerTrackLine = self.constructTrackWidget(ELLIPSE_VIEW)
        scene.addItem(self.pointerAzAlt)
        scene.addItem(self.pointerTrack)
        self.ui.modelPointsPlot.setScene(scene)
