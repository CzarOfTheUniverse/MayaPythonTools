"""
~ Attribute Transfer Tool ~ Christopher M. Miller ~ 2016/07/19

An interface for transferring attributes. Originally written to supplement
functionality from the defunct AttributeManager script, this tool allows
the user to manipulate attributes on objects.

Written and maintained by Christopher M. Miller




v.2 Added Channel Box functionality
v.1 Initial Release to copy and transfer attributes.

"""

from maya import OpenMayaUI as omUI, cmds, mel
from PySide import QtGui, QtCore, QtUiTools
from shiboken import wrapInstance
import os

myDir = os.path.dirname(os.path.abspath(__file__))
myFile = os.path.join(myDir, 'CMiller_AttrTransfer.ui')


def cmmConnectChannels(source="", dest=[], sourceAttr=""):
    """ Can connect attributes between two objects using Channel Box selection.

    :param source: The Object that will control the others.
    :param dest: A list of objects to be controlled.
    :param sourceAttr: Optional argument to specify an attribute, otherwise Channel Box selection is used.
    :return: None
    """
    if not source:
        source = cmds.ls(sl=1)[0]
    if not dest:
        dest = cmds.ls(sl=1)[1:]

    channelBox = mel.eval(
        'global string $gChannelBoxName; $temp=$gChannelBoxName;')  # Get Maya's Main ChannelBox

    for de in dest:
        attrs = cmds.channelBox(channelBox, q=True, sma=True)

        for at in attrs:
            if sourceAttr:
                sAtt = sourceAttr
            else:
                sAtt = at
            cmds.connectAttr("%s.%s" % (source, sAtt), "%s.%s" % (de, at), f=1)


def cmmMoveAttrProc(source, at=""):
    """ Function for moving a single attribute to the bottom.

    :param source: Object to affect.
    :param at: Attribute to move.
    :return: None
    """
    bigP = cmds.attributeQuery(at, node=source, lp=1)
    if bigP:
        cmds.deleteAttr("%s.%s" % (source, bigP[0]))
        cmds.undo()
    else:
        lStat = cmds.getAttr("%s.%s" % (source, at), l=1)
        cmds.setAttr("%s.%s" % (source, at), l=0)
        cmds.deleteAttr("%s.%s" % (source, at))
        cmds.undo()
        cmds.setAttr("%s.%s" % (source, at), l=lStat)


def cmmMoveAttr(source, at, up=1):
    """ Moves an attribute up or down in the Channel Box.

    :param source: Object to affect.
    :param at: Attribute to move.
    :param up: Moves attribute up (1) or down (0)
    :return: None
    """
    ats = cmds.listAttr(source, ud=1)
    ind = ats.index(at)
    if up == 1:
        if ind == 0:
            return
        else:
            moveNum = -1
            for i, at in enumerate(ats):
                if i == ind + moveNum:
                    cmmMoveAttrProc(source, at)

            for i, at in enumerate(ats):
                if i > ind:
                    cmmMoveAttrProc(source, at)

                    # ats = cmds.listAttr(source, ud=1)
                    # ind2 = ats.index(at)
                    # if ind2==ind:
                    #    cmmMoveAttr(source, at, up=1)


    else:
        if ind == len(ats) - 1:
            return
        else:
            moveNum = 1
            for i, at in enumerate(ats):
                if i == ind:
                    cmmMoveAttrProc(source, at)
            for i, at in enumerate(ats):
                if i > ind + moveNum:
                    parents = cmds.attributeQuery(at, node=source, lp=1)
                    if parents:
                        cmmMoveAttrProc(source, parents[0])
                    else:
                        cmmMoveAttrProc(source, at)

                        # ats = cmds.listAttr(source, ud=1)
                        # ind2 = ats.index(at)
                        # if ind2==ind:
                        #    cmmMoveAttr(source, at, up=0)


def cmmTransferAttr(source="", dest=[], delFromSource=0, customAttrs=[]):
    """ Transfers attributes between objects. Can either clone attributes to multiple objects,
     or move attributes to a single object including the attribute's connections.

    :param source: Object that has the attribute(s) currently.
    :param dest: List of object(s) to transfer attribute(s) to.
    :param delFromSource: Boolean. Whether to "move" the attribute, including the connections.
    :param customAttrs: List of attribute(s) to be transferred.
    :return: None
    """
    if not dest:
        dest = cmds.ls(sl=1)

    if not customAttrs:
        customAttrs = cmds.listAttr(source, ud=1)

    for de in dest:
        for ca in customAttrs:
            if cmds.attributeQuery(ca, node=source, ex=1):
                attrType = cmds.getAttr("%s.%s" % (source, ca), typ=1)
                attrVal = cmds.getAttr("%s.%s" % (source, ca))
                attrConns = cmds.listConnections("%s.%s" % (source, ca), p=1)
                attrKeyable = cmds.getAttr("%s.%s" % (source, ca), k=1)
                attrCB = cmds.getAttr("%s.%s" % (source, ca), cb=1)
                attrLock = cmds.getAttr("%s.%s" % (source, ca), l=1)

                parents = cmds.attributeQuery(ca, node=source, lp=1)
                kids = cmds.attributeQuery(ca, node=source, lc=1)

                print attrType

                if parents:
                    pass
                else:
                    if not cmds.attributeQuery(ca, node=de, ex=1):
                        if kids:
                            cmds.addAttr(de, ln=ca, at=attrType, k=attrKeyable)
                            for child in kids:
                                atKid = cmds.getAttr("%s.%s" % (source, child), typ=1)
                                cmds.addAttr(de, ln=child, attributeType=atKid, parent=ca, k=attrKeyable)
                            for child in kids:
                                atValKid = cmds.getAttr("%s.%s" % (source, child))
                                cmds.setAttr("%s.%s" % (de, child), atValKid, l=attrLock)
                        elif attrType == 'enum':
                            enumList = cmds.attributeQuery(ca, node=source, le=1)[0]
                            cmds.addAttr(de, ln=ca, at=attrType, en=enumList, k=attrKeyable)
                            cmds.setAttr("%s.%s" % (de, ca), attrVal, l=attrLock)
                        elif attrType in ["double", "float", "long"]:
                            cmds.addAttr(de, ln=ca, at=attrType, k=attrKeyable)
                            cmds.setAttr("%s.%s" % (de, ca), attrVal, l=attrLock)
                            if cmds.attributeQuery(ca, node=source, mxe=1):
                                attrMax = cmds.attributeQuery(ca, node=source, max=1)[0]
                                cmds.addAttr("%s.%s" % (de, ca), e=1, max=attrMax)
                            if cmds.attributeQuery(ca, node=source, mne=1):
                                attrMin = cmds.attributeQuery(ca, node=source, min=1)[0]
                                cmds.addAttr("%s.%s" % (de, ca), e=1, min=attrMin)
                        elif attrType == 'string':
                            cmds.addAttr(de, ln=ca, dt="string", k=attrKeyable)
                            if attrVal:
                                cmds.setAttr("%s.%s" % (de, ca), attrVal, type='string', l=attrLock)
                        elif attrType == 'bool':
                            cmds.addAttr(de, ln=ca, at=attrType, k=attrKeyable)
                            cmds.setAttr("%s.%s" % (de, ca), attrVal, l=attrLock)

                if attrKeyable == 0:
                    cmds.setAttr("%s.%s" % (de, ca), cb=attrCB)

                if attrConns:
                    for conn in attrConns:
                        cmds.connectAttr("%s.%s" % (de, ca), conn, f=1)

        if delFromSource:
            for ca in customAttrs:
                if cmds.attributeQuery(ca, node=source, ex=1):
                    cmds.setAttr("%s.%s" % (source, ca), l=0)
                    cmds.deleteAttr("%s.%s" % (source, ca))


'''
################################################
                                ~User Interface~
################################################
'''


class KeyPressEater(QtCore.QObject):
    """ I'm just fixing the stupid QT bugs in Maya where you lose focus with a modifier key.

    """

    def eventFilter(self, obj, event):
        """ Override the eventFilter to keep focus on windows by ignoring the first press of certain keys.

        """
        if event.type() == QtCore.QEvent.KeyPress:
            # Filter out Shift, Control, Alt
            if event.key() in [QtCore.Qt.Key_Shift, QtCore.Qt.Key_Control, QtCore.Qt.Key_Alt, QtCore.Qt.Key_CapsLock,
                               QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
                return True
        else:
            # Standard event processing
            return QtCore.QObject.eventFilter(self, obj, event)


def addFilter(ui):
    """ Push the event filter into the UI.

    """
    keyPressEater = KeyPressEater(ui)
    ui.installEventFilter(keyPressEater)


def getMayaWindow():
    """ Return Maya's main window.

    """
    ptr = omUI.MQtUtil.mainWindow()
    if ptr is not None:
        return wrapInstance(long(ptr), QtGui.QMainWindow)


class CMiller_AttrTransfer(QtGui.QDialog):
    def __init__(self, parent=getMayaWindow()):
        """Initialize the class, load the UI file.

        """
        super(CMiller_AttrTransfer, self).__init__(parent)
        self.loader = QtUiTools.QUiLoader(self)
        self.UI = self.loader.load(myFile, self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        addFilter(self.UI)

        # Connect the elements
        self.UI.newSource_pushButton.clicked.connect(self.loadNewSource)
        self.UI.transferAttrs_pushButton.clicked.connect(self.transferAttrs)
        self.UI.connectAttrs_pushButton.clicked.connect(self.connectChannels)
        self.UI.moveUp_pushButton.clicked.connect(self.moveAttrs)
        self.UI.moveDown_pushButton.clicked.connect(self.moveAttrs)

        # Show the window
        self.UI.show()

    def loadNewSource(self):
        """ Loads a new source object into the UI.

        :return: None
        """

        self.UI.attrs_listWidget.clear()
        self.UI.type_listWidget.clear()

        sel = cmds.ls(sl=1)[0]
        self.UI.curSource_lineEdit.setText(sel)

        attrs = cmds.listAttr(sel, ud=1)
        attrTypes = [cmds.getAttr("%s.%s" % (sel, attr), typ=1) for attr in attrs]

        self.UI.attrs_listWidget.addItems(attrs)
        self.UI.type_listWidget.addItems(attrTypes)

    def moveAttrs(self):
        """ Moves attributes based on UI button press.

        :return: None
        """
        sender = self.sender().objectName()
        s = cmds.ls(sl=1)[0]
        at = cmds.channelBox("mainChannelBox", q=1, sma=1)[0]
        if sender == "moveUp_pushButton":
            cmmMoveAttr(source=s, at=at, up=1)
        elif sender == "moveDown_pushButton":
            cmmMoveAttr(source=s, at=at, up=0)

        self.loadNewSource()

    def connectChannels(self):
        """ GUI command variant of cmmConnectChannels.

        """
        cmmConnectChannels()

    def transferAttrs(self):
        """ Transfers attributes based on UI selections.

        :return: None
        """
        src = self.UI.curSource_lineEdit.text()
        delVal = self.UI.delete_checkBox.isChecked()
        dst = cmds.ls(sl=1)
        selectedAttrs = self.UI.attrs_listWidget.selectedItems()
        if selectedAttrs:
            attrsToSend = [i.text() for i in selectedAttrs]
        else:
            attrsToSend = None

        cmmTransferAttr(source=src, dest=dst, delFromSource=delVal, customAttrs=attrsToSend)


def run():
    """ Run the UI.

    """
    global CMiller_AttrTransferWin
    try:
        CMiller_AttrTransferWin.close()
    except:
        pass
    CMiller_AttrTransferWin = CMiller_AttrTransfer()
