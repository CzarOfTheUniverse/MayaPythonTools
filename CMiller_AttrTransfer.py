from maya import OpenMayaUI as omUI, cmds
from PySide import QtGui, QtCore, QtUiTools
from shiboken import wrapInstance
import sys,os

sys.path.append(r"R:\Pipeline\Tools\Maya\Scripts\python")

myDir = os.path.dirname(os.path.abspath(__file__))
myFile = os.path.join(myDir, 'CMiller_AttrTransfer.ui')

def cmmTransferAttr(source="",dest=[],delFromSource=0, customAttrs=[]):

    if not dest:
        dest = cmds.ls(sl=1)

    if not customAttrs:
        customAttrs = cmds.listAttr(source, ud=1)

    for de in dest:
        for ca in customAttrs:
            if cmds.attributeQuery(ca,node=source,ex=1):
                attrType = cmds.getAttr("%s.%s"%(source,ca),typ=1)
                attrVal = cmds.getAttr("%s.%s"%(source,ca))
                attrConns = cmds.listConnections("%s.%s"%(source,ca),p=1)
                attrKeyable = cmds.getAttr("%s.%s"%(source,ca),k=1)
                attrCB = cmds.getAttr("%s.%s"%(source,ca),cb=1)
                attrLock = cmds.getAttr("%s.%s"%(source,ca),l=1)

                parents  = cmds.attributeQuery(ca,node=source,lp=1)
                kids = cmds.attributeQuery(ca,node=source,lc=1)

                print attrType

                if parents:
                    pass
                else:
                    if not cmds.attributeQuery(ca,node=de,ex=1):
                        if kids:
                            cmds.addAttr(de,ln=ca,at=attrType,k=attrKeyable)
                            for child in kids:
                                atKid = cmds.getAttr("%s.%s"%(source,child),typ=1)
                                cmds.addAttr(de,ln=child, attributeType=atKid, parent=ca, k=attrKeyable )
                            for child in kids:
                                atValKid = cmds.getAttr("%s.%s"%(source,child))
                                cmds.setAttr("%s.%s"%(de,child),atValKid,l=attrLock)
                        elif attrType=='enum':
                            enumList = cmds.attributeQuery(ca,node=source,le=1)[0]
                            cmds.addAttr(de,ln=ca,at=attrType,en=enumList,k=attrKeyable)
                            cmds.setAttr("%s.%s"%(de,ca),attrVal,l=attrLock)
                        elif attrType in ["double","float","long"]:
                            cmds.addAttr(de,ln=ca,at=attrType,k=attrKeyable)
                            cmds.setAttr("%s.%s"%(de,ca),attrVal,l=attrLock)
                        elif attrType=='string':
                            cmds.addAttr(de,ln=ca,dt="string",k=attrKeyable)
                            if attrVal:
                                cmds.setAttr("%s.%s"%(de,ca),attrVal,type='string',l=attrLock)
                        elif attrType=='bool':
                            cmds.addAttr(de,ln=ca,at=attrType,k=attrKeyable)
                            cmds.setAttr("%s.%s"%(de,ca),attrVal,l=attrLock)




                if attrKeyable==0:
                    cmds.setAttr("%s.%s"%(de,ca),cb=attrCB)


                if attrConns:
                    for conn in attrConns:
                        cmds.connectAttr("%s.%s"%(de,ca),conn,f=1)

        if delFromSource:
            for ca in customAttrs:
                if cmds.attributeQuery(ca,node=source,ex=1):
                    cmds.setAttr("%s.%s"%(source,ca),l=0)
                    cmds.deleteAttr("%s.%s"%(source,ca))




'''
################################################
                                ~User Interface~
################################################
'''


class KeyPressEater(QtCore.QObject):
    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress:
            # Filter out Shift, Control, Alt
            if event.key() in [QtCore.Qt.Key_Shift, QtCore.Qt.Key_Control, QtCore.Qt.Key_Alt, QtCore.Qt.Key_CapsLock,
                               QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
                return True
        else:
            # Standard event processing
            return QtCore.QObject.eventFilter(self, obj, event)


def addFilter(ui):
    keyPressEater = KeyPressEater(ui)
    ui.installEventFilter(keyPressEater)


def getMayaWindow():
    """Return Maya main window"""
    ptr = omUI.MQtUtil.mainWindow()
    if ptr is not None:
        return wrapInstance(long(ptr), QtGui.QMainWindow)


class CMiller_AttrTransfer(QtGui.QDialog):
    def __init__(self, parent=getMayaWindow()):
        """Initialize the class, load the UI file"""
        super(CMiller_AttrTransfer, self).__init__(parent)
        self.loader = QtUiTools.QUiLoader(self)
        self.UI = self.loader.load(myFile, self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        addFilter(self.UI)

        # Connect the elements
        self.UI.newSource_pushButton.clicked.connect(self.loadNewSource)
        self.UI.transferAttrs_pushButton.clicked.connect(self.transferAttrs)

        # Show the window
        self.UI.show()


    def loadNewSource(self):

        self.UI.attrs_listWidget.clear()
        self.UI.type_listWidget.clear()

        sel = cmds.ls(sl=1)[0]
        self.UI.curSource_lineEdit.setText(sel)

        attrs = cmds.listAttr(sel, ud=1)
        attrTypes = [cmds.getAttr("%s.%s"%(sel,attr),typ=1) for attr in attrs]

        self.UI.attrs_listWidget.addItems(attrs)
        self.UI.type_listWidget.addItems(attrTypes)



    def transferAttrs(self):
        src = self.UI.curSource_lineEdit.text()
        delVal = self.UI.delete_checkBox.isChecked()
        dst = cmds.ls(sl=1)
        selectedAttrs = self.UI.attrs_listWidget.selectedItems()
        if selectedAttrs:
            attrsToSend = [i.text() for i in selectedAttrs]
        else:
            attrsToSend=None


        cmmTransferAttr(source=src,dest=dst,delFromSource=delVal,customAttrs=attrsToSend)


def run():
    """Run the UI"""
    global CMiller_AttrTransferWin
    try:
        CMiller_AttrTransferWin.close()
    except:
        pass
    CMiller_AttrTransferWin = CMiller_AttrTransfer()