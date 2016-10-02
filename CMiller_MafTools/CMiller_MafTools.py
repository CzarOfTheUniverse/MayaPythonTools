__author__ = 'cmiller'

'''

Tool for anim exporting and importing between rigs for Hulk Show and expandable to others.

Also houses similar tools for baking final animation for Lighting export



1. Option to delete the keys
'''

# Imports
import getpass, os, os.path, json, sys
from maya import OpenMayaUI as omUI, cmds
from PySide import QtGui, QtCore, QtUiTools
from shiboken import wrapInstance

myDir = os.path.dirname(os.path.abspath(__file__))
myFile = os.path.join(myDir, 'CMiller_MafTools.ui')

print myDir
print myFile


class ExImFuncs(object):
    def __init__(self):
        cmds.selectPref(tso=1)
        self.importOnly=True
        # Variables
        self.__FullPath__ = cmds.file(q=1, sn=1)

    # Functions

    def setAnim(self,par='',ctlData={},startFrame=0.0,endFrame=1.0,animLayer=""):


        parSplit = par.split(":")[-1].split("|")[-1]

        print parSplit
        if parSplit in ctlData.keys():
            print "par found: "+parSplit
            attrs = ctlData[parSplit]
            for attr in attrs.keys():
                shortAttr = attr.split('.')[-1]
                fullAttr = par+"."+shortAttr

                if animLayer:
                    cmds.select(par,r=1)
                    cmds.animLayer(animLayer,e=1,aso=1)
                    cmds.select(cl=1)
                tD = attrs[attr][0]
                vD = attrs[attr][1]
                weightedTanD = attrs[attr][2]
                inTanD = attrs[attr][3]
                outTanD = attrs[attr][4]
                lockTanD = attrs[attr][5]
                weightLockD = attrs[attr][6]
                inAngleD = attrs[attr][7]
                outAngleD = attrs[attr][8]
                inWeightD = attrs[attr][9]
                outWeightD = attrs[attr][10]

                if cmds.attributeQuery(shortAttr,node=par,ex=1):
                    for ii in xrange(len(tD['time'])):

                        if startFrame <= tD['time'][ii] <= endFrame:
                            if animLayer:
                                cmds.setKeyframe(par, t=tD['time'][ii], v=float(vD['value'][ii]), at=shortAttr, al=animLayer, breakdown=False, hierarchy='none', controlPoints=False, shape=False)
                            else:

                                cmds.setKeyframe(par, t=tD['time'][ii], v=float(vD['value'][ii]), at=shortAttr, breakdown=False, hierarchy='none', controlPoints=False, shape=False)

                    if weightedTanD:
                        try:
                            cmds.keyTangent(par, e=1,wt=int(weightedTanD['weightedTan'][0]),at=shortAttr)
                        except:
                            pass

                        for ii in xrange(len(tD['time'])):
                            if startFrame <= tD['time'][ii] <= endFrame:
                                try:
                                    cmds.keyTangent(par+"."+shortAttr, e=1, t=(tD['time'][ii], tD['time'][ii]),
                                                    ia=inAngleD['inAngle'][ii], iw=inWeightD['inWeight'][ii],
                                                    oa=outAngleD['outAngle'][ii], ow=outWeightD['outWeight'][ii])

                                    cmds.keyTangent(par+"."+shortAttr, e=1, t=(tD['time'][ii], tD['time'][ii]),itt=inTanD['inTan'][ii], ott=outTanD['outTan'][ii])


                                    cmds.keyTangent(par+"."+shortAttr, e=1, t=(tD['time'][ii], tD['time'][ii]),lock=lockTanD['lockTan'][ii])


                                    if weightedTanD['weightedTan'][0]:
                                        cmds.keyTangent(par+"."+shortAttr, e=1, t=(tD['time'][ii], tD['time'][ii]),lock=weightLockD['weightLock'][ii])

                                except:
                                    print "tangent wtf at "+parSplit+"."+shortAttr

            print "done with "+parSplit



    def getAnim(self,par='',startFrame=0.0,endFrame=1.0):

        attrsKeyable = cmds.listAnimatable(par)
        attrDict = {}
        for attr in attrsKeyable:
            tv = cmds.keyframe(attr, q=1, timeChange=1, valueChange=1, a=1, t=(startFrame, endFrame))
            shortAttr = attr.split(':')[-1].split('|')[-1]
            if not tv:
                sVal = cmds.getAttr(attr, t=startFrame)
                tv = [startFrame, sVal]

            weightedTan = cmds.keyTangent(attr, q=1, weightedTangents=1, t=(startFrame, endFrame))
            inTan = cmds.keyTangent(attr, q=1, itt=1, t=(startFrame, endFrame))
            outTan = cmds.keyTangent(attr, q=1, ott=1, t=(startFrame, endFrame))
            lockTan = cmds.keyTangent(attr, q=1, lock=1, t=(startFrame, endFrame))
            weightLock = cmds.keyTangent(attr, q=1, weightLock=1, t=(startFrame, endFrame))

            inAngle = cmds.keyTangent(attr, q=1, inAngle=1, t=(startFrame, endFrame))
            outAngle = cmds.keyTangent(attr, q=1, outAngle=1, t=(startFrame, endFrame))
            inWeight = cmds.keyTangent(attr, q=1, inWeight=1, t=(startFrame, endFrame))
            outWeight = cmds.keyTangent(attr, q=1, outWeight=1, t=(startFrame, endFrame))
            attrDict[shortAttr] = [{'time': tv[0::2]}, {'value': tv[1::2]}, {'weightedTan': weightedTan},
                                   {'inTan': inTan}, {'outTan': outTan}, {'lockTan': lockTan},
                                   {'weightLock': weightLock}, {'inAngle': inAngle}, {'outAngle': outAngle},
                                   {'inWeight': inWeight}, {'outWeight': outWeight}]
        return attrDict

    def constraintBake(self,obj,ex='none'):
        """Valid ex arguments (hierarchy) are: above, below, both, none """
        startFrame = int(cmds.playbackOptions(q=1, min=1))
        endFrame = int(cmds.playbackOptions(q=1, max=1))
        cons = cmds.listConnections(obj,type="constraint",c=1)
        if cons:
            cmds.bakeResults(cons[0::2],t=(startFrame,endFrame),sm=1,hi=ex)
            conList = list(set(cons[1::2]))
            cmds.delete(conList)

    def exportAnim(self, variant=""):
        curSelection = cmds.ls(sl=1)
        for topNode in curSelection:

            savePath, startFrame, endFrame, aeDirPath = self.getFilePath(topNode, variant)

            if os.path.exists(savePath):
                myChoice = cmds.confirmDialog(title='File Exists!!',
                                              message='This wip version already has an animMAF file. Do you want to overwrite?',
                                              button=['Yes', 'No'], defaultButton='No', cancelButton='No',
                                              dismissString='No')
                if myChoice == 'No':
                    sys.exit(0)
            cmds.warning('Currently Writing Out Frames %d to %d for object %s. You have not crashed.' % (startFrame, endFrame, topNode))
            cmds.refresh()

            masterDict = {}
            ctlDict = {}

            initT = cmds.getAttr(topNode + ".t")
            initR = cmds.getAttr(topNode + ".r")
            initS = cmds.getAttr(topNode + ".s")
            initPos = initT + initR + initS

            parList = cmds.listRelatives(topNode, ad=1, f=1, type="transform")
            #parList = list(set([cmds.listRelatives(i,f=1,p=1)[0] for i in hi]))
            for par in parList:
                self.constraintBake(par)
                #off = cmds.listRelatives(par,p=1)[0]
                shortPar = par.split(':')[-1].split('|')[-1]

                #shortOff = off.split(':')[-1].split('|')[-1]
                if shortPar=='MASTER_CONTROL':
                    if initT==[(0.0, 0.0, 0.0)]:

                        initT = cmds.getAttr(par + ".t", t=startFrame)
                        initR = cmds.getAttr(par + ".r", t=startFrame)
                        initS = cmds.getAttr(par + ".s", t=startFrame)

                        initPos = initT + initR + initS

                elif "tranRot_CTL" in shortPar:
                    if initT==[(0.0, 0.0, 0.0)]:

                        initT = cmds.getAttr(par + ".t", t=startFrame)
                        initR = cmds.getAttr(par + ".r", t=startFrame)
                        initS = cmds.getAttr(par + ".s", t=startFrame)

                        initPos = initT + initR + initS


                '''
                So somewhere in here, I need to check if the offset is constrained, and bake it if so.
                Or maybe just have an option. But these people generally don't bake the constraints down.
                1st world python problems...
                '''
                # is animated?
                numKeys = cmds.keyframe(par, q=1, kc=1, t=(startFrame, endFrame))
                if numKeys > 0:
                    # animated
                    print shortPar
                    shortParAttrDict = self.getAnim(par,startFrame,endFrame)
                    ctlDict[shortPar] = shortParAttrDict

                '''
                offKeys = cmds.keyframe(off, q=1, kc=1, t=(startFrame, endFrame))
                if offKeys > 0:

                    shortOffAttrDict = self.getAnim(off,startFrame,endFrame)
                    ctlDict[shortOff] = shortOffAttrDict

                    # attrDict.keys()
                    # ctlDict.keys() ctlDict['x_ctrl']
                    # masterDict.keys()
                '''
            topNodeShort = topNode.split(":")[-1]
            masterDict[topNodeShort] = ctlDict
            masterDict['_init'] = initPos
            with open(savePath, 'w') as file:
                data = json.dump(masterDict, file)

            print(savePath)
            return savePath

    def importAnim(self,animLayer='',murderKeys=False,dataFile=None):
        topNode = cmds.ls(sl=1)[0]
        savePath, startFrame, endFrame, aeDirPath = self.getFilePath(topNode)
        if dataFile:
            initPos = dataFile[0]
            ctlData = dataFile[1]
        else:
            savePath = cmds.fileDialog2(ds=2, fm=1, ff='MAF Files (*.animMAF)')[0]
            with open(savePath, 'r') as file:
                data = json.load(file)

            if data.keys()[0] == '_init':
                initPos = data[data.keys()[0]]
                ctlData = data[data.keys()[1]]
            else:
                initPos = data[data.keys()[1]]
                ctlData = data[data.keys()[0]]


        parList = cmds.listRelatives(cmds.ls(sl=1)[0], ad=1, f=1, type="transform")
        #parList = list(set([cmds.listRelatives(i,f=1,p=1)[0] for i in hi]))
        for par in parList:
            shortPar = par.split(':')[-1]

            if shortPar=='MASTER_CONTROL':
                cmds.setAttr(par + '.t', initPos[0][0], initPos[0][1], initPos[0][2])
                cmds.setAttr(par + '.r', initPos[1][0], initPos[1][1], initPos[1][2])
                cmds.setAttr(par + '.s', initPos[2][0], initPos[2][1], initPos[2][2])
            elif "tranRot_CTL" in shortPar:
                cmds.setAttr(par + '.t', initPos[0][0], initPos[0][1], initPos[0][2])
                cmds.setAttr(par + '.r', initPos[1][0], initPos[1][1], initPos[1][2])
                cmds.setAttr(par + '.s', initPos[2][0], initPos[2][1], initPos[2][2])

            #off = cmds.listRelatives(par,p=1)[0]

            if murderKeys:
                cmds.cutKey( par, time=(startFrame,endFrame), cl=1, option="keys")
                #cmds.cutKey( off, time=(startFrame,endFrame), cl=1, option="keys")

            self.setAnim(par,ctlData,startFrame,endFrame,animLayer)
            #self.setAnim(off,ctlData,startFrame,endFrame,animLayer)
        print "IMPORT COMPLETE!"


    def replaceTarget(self,dataFile,old,new):
        """Replaces data object"""
        dataFile[new] = dataFile.pop(old)
        ctlList = dataFile.keys()
        ctlList.sort()
        return dataFile, ctlList


    def getFilePath(self, obj, variant=""):
        startFrame = int(cmds.playbackOptions(q=1, min=1))
        endFrame = int(cmds.playbackOptions(q=1, max=1))
        ae = cmds.fileDialog2(cap="Please choose a .animMAF file",fm=0,okc="Load",dir=cmds.file(q=1,sn=1),ff=".animMAF (*.animMAF)")
        if ae:
            aeDirPath = os.path.dirname(ae)
            savePath = os.path.basename(ae)

        return savePath, startFrame, endFrame, aeDirPath

    def processStart(self):
        self.topNode = cmds.ls(sl=1)[0]
        self.startFrame = int(cmds.playbackOptions(q=1, min=1))
        self.endFrame = int(cmds.playbackOptions(q=1, max=1))

        if self.checkRigid(self.topNode):
            self.bakeObjectsAction(self.topNode)
            cmds.refresh()
            self.exportBakedDataToFile(self.topNode)

    def checkRigid(self, topNode):
        pNode = cmds.listRelatives(topNode, p=1)[0]
        if pNode.split(":")[-1] == "Model":
            # We need to check where the constraint driver is
            kids = cmds.listRelatives(pNode, c=1)
            ctl=""
            for kid in kids:
                if "parentConstraint" in kid:
                    modelCon = kid
                    ctl = [x for x in list(set(cmds.listConnections(kid, s=1, d=0))) if "CTL" in x][0]
                    tgtWgt = cmds.parentConstraint(kid, q=1, wal=1)[0]
                    # We've determined this is a Generic prop rig and the constraint is on a parent node
                    # We have the constraint as well as
                    break
            if ctl:
                # There is a constraint on the Model group, we'll need to emulate it.
                self.tempCon = cmds.parentConstraint(ctl, topNode, mo=1)
                cmds.setAttr("%s.%s" % (modelCon, tgtWgt), 0)

        conns = cmds.listConnections(topNode)
        if conns:
            if len([x for x in conns if "parentConstraint" in x]) > 0:
                # A parent constraint is attached to the object now, we may proceed
                return True
        else:
            # Either a constraint is lower in the hierarchy, or this object is not even rigged. Let's quickly check:
            if len([p for p in cmds.listRelatives(topNode, p=1, f=1)[0].split("|") if "Rig" in p]) > 0:
                # We have a rig, let's proceed
                return True

            else:
                # This isn't even a rigged object unless someone named it wrong. We need to abort and alert the user
                cmds.warning("Object does not appear to be rigged. Skipping.")
                return False

    def bakeObjectsAction(self, obj):
        numBaked = cmds.bakeResults(obj, simulation=1, t=(self.startFrame, self.endFrame), hi="below", sb=1, dic=1, sac=0,
                                    pok=1, ral=0, bol=0, mr=1, cp=0, s=1)
        print (str(numBaked) + " channels baked")
        return numBaked

    def exportBakedDataToFile(self, topNode, variant=""):
        pass
        # range star to end
        # make dict
        masterDict = {}
        ctlDict = {}

        savePath, startFrame, endFrame, aeDirPath = self.getFilePath(topNode, variant)


        initT = cmds.getAttr(topNode + ".t")
        initR = cmds.getAttr(topNode + ".r")
        initS = cmds.getAttr(topNode + ".s")
        initPos = initT + initR + initS
        # add to dict with key time
        hi = cmds.listRelatives(topNode, ad=1, f=1)
        parList = list(set([cmds.listRelatives(i,f=1,p=1)[0] for i in hi]))
        for par in parList:

            shortParAttrDict = self.getAnim(par,startFrame,endFrame)
            ctlDict[par] = shortParAttrDict


        masterDict[topNode] = ctlDict
        masterDict['_init'] = initPos
        with open(savePath, 'w') as file:
            data = json.dump(masterDict, file)

        print(savePath)
        return savePath



    def bakeOutWorldData(self):
        pass
        bakeList = []
        conList = []

        for par in parList:

            ctl = cmds.circle(n="%s" %(par.split("|")[-1].split(":")[-1]))[0]
            pCon = cmds.parentConstraint(par,ctl,mo=0)[0]
            bakeList.append(ctl)
            conList.append(pCon)

        print "Ready to bake"
        cmds.bakeResults(bakeList, t=(startFrame,endFrame))
        return bakeList
        print "finished bake"
        # parent to world
        # rename to orig
        # bake
        # createCurves for every obj
        # parent to world
        # rename to orig
        # bake



        # cmds.file(savePath, f=1, typ="animExport", es=1, options="precision=8;intValue=17;nodeNames=1;verboseUnits=0;whichRange=2;range=%d:%d;options=keys;hierarchy=below;controlPoints=0;shapes=1;helpPictures=0;useChannelBox=0;copyKeyCmd=-animation objects -time >%d:%d> -float >%d:%d> -option keys -hierarchy below -controlPoints 0 -shape 1 "%(startFrame,endFrame,startFrame,endFrame,startFrame,endFrame))


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

class cmmAnimExportToolUI(QtGui.QDialog, ExImFuncs):
    def __init__(self, parent=getMayaWindow()):
        """Initialize the class, load the UI file"""
        self.loadedData=None
        self.dataFile=None

        super(cmmAnimExportToolUI, self).__init__(parent)
        self.loadedData=None
        self.dataFile=None
        self.loadedInit=None

        #super(cmmAnimExportToolUI, self).keyPressEvent()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.loader = QtUiTools.QUiLoader(self)
        self.UI = self.loader.load(myFile, self)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.ExImFuncs = ExImFuncs()

        #keyPressEater = KeyPressEater(self)
        #keyPressEater =_UITools.KeyPressEater(self)
        #self.UI.installEventFilter(keyPressEater)
        addFilter(self.UI)

        #QtCore.QObject.installEventFilter()
        #shortcut = QtGui.QShortcut(QtGui.QKeySequence(QtCore.Qt.Key.Key_Shift),self.UI.replaceMAFData_lineEdit)
        #shortcut.activated.connect(self.skipIt)

        # Connect the elements
        self.UI.curDirContents_pushButton.clicked.connect(self.dirListing)
        self.UI.exportAnim_pushButton.clicked.connect(self.exportButtonAction)
        self.UI.importAnim_pushButton.clicked.connect(self.importButtonAction)

        #self.keyPressEvent(self.UI.keyPressEvent)

        self.UI.loadMAFData_pushButton.clicked.connect(self.loadButtonAction)
        self.UI.replaceMAFData_pushButton.clicked.connect(self.replaceButtonAction)
        self.UI.saveMAFData_pushButton.clicked.connect(self.saveButtonAction)

        if self.ExImFuncs.importOnly==True:
            self.UI.exportTab.setEnabled(False)

        print(self.UI.keyPressEvent)
        #self.UI.keyPressEvent(self.keyPressEvent())
        '''
        self.UI.curDirContents_listWidget.clicked.connect(self.saveWeights)
        self.UI.loadReg_btn.clicked.connect(self.loadWeights)
        self.UI.loadWorld_btn.clicked.connect(self.loadWorldWeights)
        self.UI.refresh_btn.clicked.connect(self.refreshNamespaceUI)

        self.refreshNamespaceUI()
        '''
        # Show the window
        self.UI.show()

    def exportButtonAction(self):
        var = self.UI.fileAppend_lineEdit.text()
        #world = self.UI.worldSpaceBake_checkBox.isChecked()
        fp = self.ExImFuncs.exportAnim(var)

        if fp:
            self.UI.outputPath_label.setText('<a href="%s">%s</a>'%(str("/".join(fp.split('/')[:-1])),str(fp)))


    def importButtonAction(self):
        animLayer = self.UI.targetAnimLayer_lineEdit.text()#get this val from UI
        delKeys = self.UI.deleteAnim_checkBox.isChecked()
        if self.loadedData:
            self.ExImFuncs.importAnim(animLayer,delKeys,[self.loadedInit,self.loadedData])
            self.loadedData=None
            self.dataFile=None
            self.loadedInit=None
            self.UI.loadedMAF_listWidget.clear()
            self.UI.saveMAFData_pushButton.setEnabled(False)

        else:
            self.ExImFuncs.importAnim(animLayer,delKeys)

    def loadButtonAction(self):
        savePath = cmds.fileDialog2(ds=2, fm=1, ff='MAF Files (*.animMAF)')[0]
        with open(savePath, 'r') as file:
            data = json.load(file)

        if data.keys()[0] == '_init':
            initPos = data[data.keys()[0]]
            ctlData = data[data.keys()[1]]
        else:
            initPos = data[data.keys()[1]]
            ctlData = data[data.keys()[0]]

        ctlList = ctlData.keys()
        ctlList.sort()
        self.loadedListPopulate(ctlList)
        self.loadedData = ctlData
        self.loadedInit = initPos
        self.dataFile = data

        #enable save BUTTON
        self.UI.saveMAFData_pushButton.setEnabled(True)

    def saveButtonAction(self):
        savePath = cmds.fileDialog2(ds=2, fm=1, ff='MAF Files (*.animMAF)')[0]
        newMasterDict = {}
        topNode = cmds.ls(sl=1)[0]
        topNodeShort = topNode.split(":")[-1]

        newMasterDict[topNodeShort] = self.loadedData
        newMasterDict['_init'] = self.loadedInit

        self.saveNewMAF(savePath,newMasterDict)


    def saveNewMAF(self,dataFile,data):
        with open(dataFile, 'w') as file:
            data = json.dump(data, file)

    def loadedListPopulate(self,ctlList):
        self.UI.loadedMAF_listWidget.clear()
        self.UI.loadedMAF_listWidget.addItems(ctlList)

    def replaceButtonAction(self):
        oldObj = self.UI.loadedMAF_listWidget.currentItem().text()
        newObj = self.UI.replaceMAFData_lineEdit.text()
        newData, ctlList = self.ExImFuncs.replaceTarget(self.loadedData,oldObj,newObj)
        self.UI.replaceMAFData_lineEdit.clear()
        self.loadedData = newData
        self.loadedListPopulate(ctlList)

    def dirListing(self):
        curSel = cmds.ls(sl=1)[0]
        if curSel:
            fpReturns = self.ExImFuncs.getFilePath(curSel)

        if fpReturns[3]:
            if os.path.exists(fpReturns[3]):
                dirList = os.listdir(fpReturns[3])
                self.UI.curDirContents_listWidget.clear()
                self.UI.curDirContents_listWidget.addItem("-None-")
                for i in dirList:
                    if i.endswith(".animMAF"):
                        self.UI.curDirContents_listWidget.addItem(i)

def run():
    """Run the UI"""
    global cmmAnimExportToolWin
    try:
        cmmAnimExportToolWin.close()
    except:
        pass
    cmmAnimExportToolWin = cmmAnimExportToolUI()
