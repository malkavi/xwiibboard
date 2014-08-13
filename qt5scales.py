#!/usr/bin/python
"""scalesgui.py
"""

import sys, random
import select
from threading import Thread
import threading
import mysql

try:
    from PyQt4 import QtGui, QtCore
except:
	print "Sorry, I can't seem to import pyQt4 for some reason."
	sys.exit(1)
	
try:
    import xwiimote
except:
	print "Sorry, I can't seem to import xwiimote for some reason."
	print "Please check that it and it's python bindings are installed"
	sys.exit(1)

import balanceboard

class Example(QtGui.QMainWindow):
    
    def __init__(self):
        super(Example, self).__init__()
        
        self.initUI()
        
    def initUI(self):      
        
        self.tboard = Board(self)
        self.setCentralWidget(self.tboard)
        
        self.statusbar = self.statusBar()        
        self.tboard.msg2Statusbar[str].connect(self.statusbar.showMessage)
        
        self.tboard.start()
        
        self.setGeometry(0, 0, 1280, 720)
        self.setWindowTitle('Mi peso')
        self.center()
        
        self.show()
        
        self.statusBar().showMessage('Iniciando')
	
    def closeEvent(self, event):
        print("event")
        reply = QtGui.QMessageBox.question(self, 'Message', "Are you sure to quit?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)

        if reply == QtGui.QMessageBox.Yes:
            self.tboard.pararHilo = False
            event.accept()
        else:
            event.ignore()
            
    def center(self):
        screen = QtGui.QDesktopWidget().screenGeometry()
        size =  self.geometry()
        print "Window Width: %d" % size.width()
        print "Window Height: %d" % size.height()
        print "Screen Width: %d" % screen.width()
        print "Screen Height: %d" % screen.height()
        self.move((screen.width()-size.width())/2, (screen.height()-size.height())/2)
	
class Board(QtGui.QFrame):
    msg2Statusbar = QtCore.pyqtSignal(str)
    Speed = 300
    NumCalibraciones = 100
    NumLecturas = 10
    named_zero = { 'right_top': 0,
		    'right_bottom': 0,
		    'left_top': 0,
		    'left_bottom': 0,
    }
	
    def __init__(self, parent):
        super(Board, self).__init__(parent)
        self.initBoard()

    def initBoard(self):
        global xwiimote
        global iface
        global p
	
        if len(sys.argv) == 2:
            wiimote = sys.argv[1]
        else:
            wiimote = balanceboard.wait_for_balanceboard()

        iface = xwiimote.iface(wiimote)
        iface.open(xwiimote.IFACE_BALANCE_BOARD)
        p = select.epoll.fromfd(iface.get_fd())
        
        self.bateria = balanceboard.stado_inicial(iface, p)
        
        maximo = 15000
        minimo = 0
        while (maximo - minimo) > 20:
            self.named_calibration, maximo, minimo  = balanceboard.leerSensores(iface, p, Board.NumCalibraciones)
            print(self.named_calibration)
	    print("Max " + str(maximo) + " min " + str(minimo))
	    print("Dif " + str(maximo - minimo))

        self.named_wii = self.named_calibration
        
        self.xpos = 0
        self.ypos = 0
        self.timer = QtCore.QBasicTimer()
        
        self.weight = 0
        self.weightText = ""
        self.lock = threading.Lock()
        self.pararHilo = True
        
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.start()
        self.lanzarHilo()

    def lanzarHilo( self ):
        self.weightText = ""
        self.pararHilo = True
        try:
            t = Thread(target=self.calcWeight, args=('Hilo',))
            t.start()
        except KeyboardInterrupt:
            print "Ctrl-c received! Sending kill to threads..."
            self.pararHilo = False
        except:
            print "Error: unable to start thread"
            sys.exit(app.exec_())
	  
    def calcWeight(self, threadName):
        print threadName
        while self.pararHilo:
            #Leemos los sensores
            self.lock.acquire()
            self.named_wii, maximo, minimo  = balanceboard.leerSensores(iface, p, Board.NumLecturas)
            self.lock.release()
            self.weight = balanceboard.calcweight(self.named_wii, self.named_calibration) / 100.0
            
        
    def drawPoints(self, qp):
        #qp.setPen(QtGui.QPen(QtCore.Qt.red, 10))
        qp.setBrush(QtGui.QColor(255, 0, 0))
        #size = self.size()
        #qp.drawPoint(self.xpos, self.ypos)   
        qp.drawEllipse(QtCore.QPoint(self.xpos, self.ypos), 20, 20)
	
    def drawLines(self, qp):
        pen = QtGui.QPen(QtCore.Qt.black, 2, QtCore.Qt.SolidLine)
        qp.setPen(pen)
        size = self.size()
        qp.drawLine(0, size.height() / 2, size.width(), size.height() / 2)
        qp.drawLine(size.width() / 2, 0, size.width() / 2, size.height())
        
    def drawText(self, event, qp):
        #qp.setPen(QtGui.QColor(168, 34, 3))
        #Qrect (x, y, tamx, tamy)
        size = self.size()
        # Escribir peso
        qp.setPen(QtCore.Qt.magenta)
        rectPeso = QtCore.QRect(size.height() / 2, 0, 4 * 80, 2 * 80)
        qp.drawRect(rectPeso)
        qp.setPen(QtCore.Qt.black)
        #qp.setPen(QtGui.black())
        qp.setFont(QtGui.QFont('Decorative', 70))
        #qp.drawText(0,0,size.height() ,size.width() / 2, QtCore.Qt.AlignCenter, str(self.weight) + self.weightText)
        qp.drawText(rectPeso, QtCore.Qt.AlignCenter, str(self.weight) + "\n" + self.weightText)
        
        # Escribir bateria
        qp.setPen(QtCore.Qt.blue)
        rectInfo = QtCore.QRect(0, 0,  3 * 30, 30)
        qp.drawRect(rectInfo)
        qp.setPen(QtCore.Qt.green)
        qp.setFont(QtGui.QFont('Decorative', 30))
        #qp.drawText(0,0,size.height() / 2,size.width() / 2, QtCore.Qt.AlignCenter, str(self.bateria))
        qp.drawText(rectInfo, QtCore.Qt.AlignCenter, str(self.bateria) + "%")
        
    def calcXY(self):
        readings = self.named_wii
        self.msg2Statusbar.emit(str(self.weight))
        #usar_cal = False
        if self.weight > 0.5:
	    right_sens = (float(balanceboard.gsc(readings,'right_top', self.named_calibration)+balanceboard.gsc(readings, 'right_bottom', self.named_calibration)))
	    left_sens = (float(balanceboard.gsc(readings,'left_top', self.named_calibration)+balanceboard.gsc(readings,'left_bottom', self.named_calibration)))
	    top_sens = (float(balanceboard.gsc(readings,'left_top', self.named_calibration)+balanceboard.gsc(readings,'right_top', self.named_calibration)))
	    bottom_sens = (float(balanceboard.gsc(readings,'left_bottom', self.named_calibration)+balanceboard.gsc(readings,'right_bottom', self.named_calibration)))
        else:
  	    right_sens = (float(balanceboard.gsc(readings,'right_top')+balanceboard.gsc(readings, 'right_bottom')))
	    left_sens = (float(balanceboard.gsc(readings,'left_top')+balanceboard.gsc(readings,'left_bottom')))
	    top_sens = (float(balanceboard.gsc(readings,'left_top')+balanceboard.gsc(readings,'right_top')))
	    bottom_sens = (float(balanceboard.gsc(readings,'left_bottom')+balanceboard.gsc(readings,'right_bottom')))
	    right_sens, left_sens, top_sens, bottom_sens = 0, 0, 0, 0
        
        if right_sens <= 0:
            if left_sens <= 0:
                x_balance = 0.5
            else:
                x_balance = 0
        elif left_sens <= 0:
            x_balance = 1
        else:
            try:
                x_balance = float(right_sens / (right_sens + left_sens))
            except:
                x_balance = 0.5
        
        if top_sens <= 0:
            if bottom_sens <= 0:
                y_balance = 0.5
            else:
                y_balance = 0
        elif bottom_sens <= 0:
            y_balance = 1
        else:
            try:
                y_balance = float(bottom_sens / (top_sens + bottom_sens))
            except:
                y_balance = 0.5
        
        self.xpos = x_balance
        self.ypos = y_balance

    def start(self):
        self.timer.start(Board.Speed, self)

    def paintEvent(self, event):
        #painter = QtGui.QPainter(self)
        #rect = self.contentsRect()
        #boardTop = rect.bottom() - Board.BoardHeight * self.squareHeight()
        qp = QtGui.QPainter()
        qp.begin(self)
        self.drawLines(qp)
        self.drawPoints(qp)
        self.drawText(event, qp)
        qp.end()

    def closeEvent(self, event):
        reply = QtGui.QMessageBox.question(self, 'Message',
        "Quieres salir?", QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        if reply == QtGui.QMessageBox.Yes:
            self.pararHilo = False
            event.accept()
        else:
            event.ignore()
                    
    def keyPressEvent(self, event):
        
        key = event.key()
            
        if key == QtCore.Qt.Key_Q:
            print "saliendo"
            self.pararHilo = False
            sys.exit(0)
            
        elif key == QtCore.Qt.Key_Space:
            self.pararHilo = False
            self.timer.stop()
            self.lock.acquire()
            maximo = 10000
            minimo = 0
            while (maximo - minimo) > 50:
                self.named_wii, maximo, minimo = balanceboard.leerSensores(iface, p, Board.NumLecturas * 20)
                print(self.named_wii)
		print("Max " + str(maximo) + " min " + str(minimo))
		print("Dif " + str(maximo - minimo))
            self.lock.release()
            self.weight = balanceboard.calcweight(self.named_wii, self.named_calibration) / 100.0
            self.weightText = " kg +/- " + str((maximo - minimo) / 200)
            self.update()
            mysql.guardar_peso(self.weight)

        elif key == QtCore.Qt.Key_C:
            self.timer.stop()
            self.lock.acquire()
            print "CALIBRANDO"
            maximo = 10000
            minimo = 0
            while (maximo - minimo) > 20:
                self.named_calibration, maximo, minimo  = balanceboard.leerSensores(iface, p, Board.NumCalibraciones)
                print(self.named_calibration)
		print("Max " + str(maximo) + " min " + str(minimo))
		print("Dif " + str(maximo - minimo))
            self.lock.release()
            self.named_wii = self.named_calibration
            self.timer.start(Board.Speed, self)
            self.update()
            print "FIN CALIBRACION"
            if self.pararHilo == False:
                self.lanzarHilo()
	       
        else:
            super(Board, self).keyPressEvent(event)
                

    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            self.calcXY()
            size = self.size()
            #self.xpos = random.randint(1, size.width()-1)
            #self.ypos = random.randint(1, size.height()-1)
            self.xpos = self.xpos * size.width()
            self.ypos = self.ypos * size.height()
            self.update()
        else:
            super(Board, self).timerEvent(event)

def main():
    app = QtGui.QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())
    self.pararHilo = False

if __name__ == '__main__':
    main()
