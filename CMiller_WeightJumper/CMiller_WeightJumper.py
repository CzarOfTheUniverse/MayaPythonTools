"""
~ Weight Jumper Tool ~ Christopher M. Miller ~ 2016/10/25

Small utility for quickly transferring weights between influences.
Originally used to fix skin weighted to IK instead of Bind joints.
Additionally allows weight transfer via selected vertices.

Written and maintained by Christopher M. Miller


v.3 Added prelim mirror weights
v.2 Added Percentage option, GUI
v.1 Initial Release to transfer weight values as command line.

"""


from maya import OpenMayaUI as omUI, cmds, mel, OpenMaya as om
import maya.OpenMayaAnim as omAnim

from PySide import QtGui, QtCore, QtUiTools
from shiboken import wrapInstance
import os

myDir = os.path.dirname(os.path.abspath(__file__))
myFile = os.path.join(myDir, 'CMiller_WeightJumper.ui')

def weightJumper(skin,jointSource="",jointTarget="",selVerts=False, percent=100):
    """

    :param skin: The skinCluster to affect.
    :param jointSource: Influence currently holding the weight values.
    :param jointTarget: Influence where the weights will be transferred (added) to.
    :param selVerts: Boolean for transferring entire influence or only affecting selected vertices.
    :param percent: Int 0 to 100 for the percentage of weights to transfer.
    :return: None
    """

    if not jointSource:
        jointSource = cmds.ls(sl=1)[0]
    if not jointTarget:
        jointTarget = cmds.ls(sl=1)[1]

    normalVal = cmds.getAttr("%s.normalizeWeights"%skin)
    cmds.setAttr("%s.normalizeWeights"%skin,0)


    # Query skinCluster object
    selectionList = om.MSelectionList()
    selectionList.add( skin )
    node = om.MObject()
    selectionList.getDependNode( 0, node )
    skinClusterNode = omAnim.MFnSkinCluster(node)

    # Use magic to find the components
    mfnSet = om.MFnSet(skinClusterNode.deformerSet())
    mfnSetMembers = om.MSelectionList()
    mfnSet.getMembers(mfnSetMembers, False)
    dgPath = om.MDagPath()
    components = om.MObject()
    mfnSetMembers.getDagPath(0, dgPath, components)

    if selVerts:
        # Get selected verts
        vertSelList = om.MSelectionList()
        om.MGlobal.getActiveSelectionList(vertSelList)
        selection_iter = om.MItSelectionList(vertSelList,om.MFn.kMeshVertComponent)
        selection_DagPath = om.MDagPath()
        componentSel = om.MObject()

        selection_iter.getDagPath(selection_DagPath, componentSel)
        finalComponents = componentSel
    else:
        finalComponents = components

    transPercent = percent*.01
    keepPercent = (100-percent)*.01

    # Get the number of influences that affect the skinCluster
    infs = om.MDagPathArray()
    numInfs = skinClusterNode.influenceObjects(infs)

    # Get dagPath for the skinCluster at index 0
    skinPath = om.MDagPath()
    index = 0
    skinClusterNode.indexForOutputConnection(index)
    skinClusterNode.getPathAtIndex(index,skinPath)

    # Find joints
    myCountIndex = 0
    myWinIndex = 0
    for counter in range(0,numInfs,1):
        infName = infs[counter].partialPathName()
        if infName==jointSource:
            myCountIndex=counter
        elif infName==jointTarget:
            myWinIndex=counter

    # Find current weights
    myInflArray = om.MIntArray(1,myWinIndex)
    myOtherInflArray = om.MIntArray(1,myCountIndex)

    jointSourceWeights = om.MDoubleArray()
    skinClusterNode.getWeights(skinPath,finalComponents,myOtherInflArray,jointSourceWeights)

    jointDestWeights = om.MDoubleArray()
    skinClusterNode.getWeights(skinPath,finalComponents,myInflArray,jointDestWeights)

    jointTargetFinalWeights = om.MDoubleArray(len(jointDestWeights))
    bigOldWeightList = [(x*transPercent) + y for x, y in zip(jointSourceWeights, jointDestWeights)]

    for i in xrange(len(jointDestWeights)):
        jointTargetFinalWeights.set(bigOldWeightList[i],i)


    jointSourceNewWeights = om.MDoubleArray(len(jointDestWeights))
    if percent != 100:
        keepWeightList = [x*keepPercent for x in jointSourceWeights]
        for i in xrange(len(jointDestWeights)):
            jointSourceNewWeights.set(keepWeightList[i],i)


    # Set new weights
    skinClusterNode.setWeights(skinPath,finalComponents,myInflArray,jointTargetFinalWeights,False)
    skinClusterNode.setWeights(skinPath,finalComponents,myOtherInflArray,jointSourceNewWeights,False)

    cmds.setAttr("%s.normalizeWeights"%skin,normalVal)
    
    
def weightMirror(skin):

    normalVal = cmds.getAttr("%s.normalizeWeights"%skin)
    #print normalVal
    cmds.setAttr("%s.normalizeWeights"%skin,0)
    cmds.setAttr("%s.envelope"%skin,0)

    # Query skinCluster object
    selectionList = om.MSelectionList()
    selectionList.add( skin )
    node = om.MObject()
    selectionList.getDependNode( 0, node )
    skinClusterNode = omAnim.MFnSkinCluster(node)

    # Use magic to find the components
    mfnSet = om.MFnSet(skinClusterNode.deformerSet())
    mfnSetMembers = om.MSelectionList()
    mfnSet.getMembers(mfnSetMembers, False)
    dgPath = om.MDagPath()
    components = om.MObject()
    mfnSetMembers.getDagPath(0, dgPath, components)

    # Get the number of influences that affect the skinCluster
    infs = om.MDagPathArray()
    numInfs = skinClusterNode.influenceObjects(infs)

    # Get dagPath for the skinCluster at index 0
    skinPath = om.MDagPath()
    index = 0
    skinClusterNode.indexForOutputConnection(index)
    skinClusterNode.getPathAtIndex(index,skinPath)

    wgts = om.MDoubleArray()
    util = om.MScriptUtil()
    util.createFromInt(0)
    pUInt = util.asUintPtr()
    skinClusterNode.getWeights(dgPath, components, wgts, pUInt)

    finalLen = wgts.length()

    inPointArray = om.MPointArray()
    inMfnMesh = om.MFnMesh(dgPath)
    inMfnMesh.getPoints(inPointArray, om.MSpace.kWorld)
    maxCount = inPointArray.length()

    geomIter = om.MItGeometry(dgPath)

    counter=0
    mirrorFromList = {}
    mirrorToList = {}
    mirrorStayList = {}
    for i in range(maxCount):
        comp = geomIter.currentItem()

        pnt = geomIter.position(om.MSpace.kWorld)
        p0 = (float(int(pnt[0] * 1000)) / 1000)
        p1 = (float(int(pnt[1] * 1000)) / 1000)
        p2 = (float(int(pnt[2] * 1000)) / 1000)
        pos = [p0, p1, p2]

        #print i, pos

        #pos x
        if p0>0:
            mirrorFromList[i] = pos
        elif p0<0:
            mirrorToList[i] = pos
        else:
            mirrorStayList[i] = pos


        counter+=1
        geomIter.next()

    #print mirrorFromList
    #print mirrorToList
    #print mirrorStayList
    matchSet = {}

    for ff,posF in mirrorFromList.items():
        for tt,posT in mirrorToList.items():
            if [abs(posF[0]),posF[1],posF[2]] == [abs(posT[0]),posT[1],posT[2]]:
                matchSet[ff] = tt
    for ss,posS in mirrorStayList.items():
        matchSet[ss] = ss

    #print matchSet

    #print components
    #print wgts

    infNames = []
    for i in range(infs.length()):
        infName = infs[i].partialPathName()
        infNames.append(infName)

    #print infNames

    jntSourceList = {}
    jntDestList = {}
    for i,n in enumerate(infNames):
        #print n
        if "L_" in n:
            jntSourceList[i] = n
            #print "Found the L"
        elif "R_" in n:
            jntDestList[i] = n
            #print "Found the R"
    
    switchDict = {}
    for si,sj in jntSourceList.items():
        for di,dj in jntDestList.items():
            if sj.replace("L_","") == dj.replace("R_",""):
                print "matched %s to %s" % (sj, dj)

                switchDict[si] = di

    #print switchDict

    for k,v in matchSet.items():
        index = v*numInfs

        startWeight = wgts[k*numInfs:k*numInfs+numInfs]
        #print startWeight
        postWeight = startWeight
        for kk,vv in switchDict.items():
            postWeight[kk], postWeight[vv] = startWeight[vv], startWeight[kk]

        for ll,postW in enumerate(postWeight):
            tempNum = ll+index
            wgts.set(postW,tempNum)
        #print postWeight
    #print wgts
    
    for ss in mirrorStayList.keys():
        index = ss*numInfs
        startWeight = wgts[ss*numInfs:ss*numInfs+numInfs]
        
        postWeight = startWeight
        
        for kk,vv in switchDict.items():
            
            postWeight[kk] = startWeight[vv]

        #Here we're going to manually normalize the weights
        maxVal = sum(postWeight)
        postWeightN = [p/maxVal for p in postWeight]
        
        for ll,postW in enumerate(postWeightN):
            tempNum = ll+index
            wgts.set(postW,tempNum)

    #print wgts
    
    infIndices = om.MIntArray(numInfs)
    for ii in range(numInfs):
        infIndices.set(ii, ii)

    skinClusterNode.setWeights(dgPath, components, infIndices, wgts, False)

    cmds.setAttr("%s.normalizeWeights"%skin,normalVal)
    cmds.setAttr("%s.envelope"%skin,1)
    
    #cmds.skinCluster("Shirt_02_Driver_skinCluster",e=1,fnw=1)
    
    



def weightMirrorMultiObject(skin1,skin2):

    normalVal = cmds.getAttr("%s.normalizeWeights"%skin2)
    cmds.setAttr("%s.normalizeWeights"%skin2,0)

    # Query skinCluster1 object
    selectionList1 = om.MSelectionList()
    selectionList1.add( skin1 )
    node1 = om.MObject()
    selectionList1.getDependNode( 0, node1 )
    skinClusterNode1 = omAnim.MFnSkinCluster(node1)

    # Query skinCluster2 object
    selectionList2 = om.MSelectionList()
    selectionList2.add( skin2 )
    node2 = om.MObject()
    selectionList2.getDependNode( 0, node2 )
    skinClusterNode2 = omAnim.MFnSkinCluster(node2)    
    
    
    # Use magic to find the components
    mfnSet1 = om.MFnSet(skinClusterNode1.deformerSet())
    mfnSetMembers1 = om.MSelectionList()
    mfnSet1.getMembers(mfnSetMembers1, False)
    dgPath1 = om.MDagPath()
    components1 = om.MObject()
    mfnSetMembers1.getDagPath(0, dgPath1, components1)
    
    # Use magic to find the components
    mfnSet2 = om.MFnSet(skinClusterNode2.deformerSet())
    mfnSetMembers2 = om.MSelectionList()
    mfnSet2.getMembers(mfnSetMembers2, False)
    dgPath2 = om.MDagPath()
    components2 = om.MObject()
    mfnSetMembers2.getDagPath(0, dgPath2, components2)    

    # Get the number of influences that affect the skinCluster
    infs1 = om.MDagPathArray()
    numInfs1 = skinClusterNode1.influenceObjects(infs1)
    
    # Get the number of influences that affect the skinCluster
    infs2 = om.MDagPathArray()
    numInfs2 = skinClusterNode2.influenceObjects(infs2)    

    
    
    
    
    # Get dagPath for the skinCluster at index 0
    skinPath1 = om.MDagPath()
    index = 0
    skinClusterNode1.indexForOutputConnection(index)
    skinClusterNode1.getPathAtIndex(index,skinPath1)

    wgts1 = om.MDoubleArray()
    util = om.MScriptUtil()
    util.createFromInt(0)
    pUInt = util.asUintPtr()
    skinClusterNode1.getWeights(dgPath1, components1, wgts1, pUInt)

    finalLen1 = wgts1.length()

    inPointArray1 = om.MPointArray()
    inMfnMesh1 = om.MFnMesh(dgPath1)
    inMfnMesh1.getPoints(inPointArray1, om.MSpace.kWorld)
    maxCount1 = inPointArray1.length()

    geomIter1 = om.MItGeometry(dgPath1)

    # Get dagPath for the skinCluster at index 0
    skinPath2 = om.MDagPath()
    index = 0
    skinClusterNode2.indexForOutputConnection(index)
    skinClusterNode2.getPathAtIndex(index,skinPath2)

    wgts2 = om.MDoubleArray()
    util = om.MScriptUtil()
    util.createFromInt(0)
    pUInt = util.asUintPtr()
    skinClusterNode2.getWeights(dgPath2, components2, wgts2, pUInt)

    finalLen2 = wgts2.length()

    inPointArray2 = om.MPointArray()
    inMfnMesh2 = om.MFnMesh(dgPath2)
    inMfnMesh2.getPoints(inPointArray2, om.MSpace.kWorld)
    maxCount2 = inPointArray2.length()

    geomIter2 = om.MItGeometry(dgPath2)    
    
    
    
    
    
    counter1=0
    counter2=0
    mirrorFromList = {}
    mirrorToList = {}
    mirrorStayList = {}
    for i in range(maxCount1):
        comp = geomIter1.currentItem()

        pnt = geomIter1.position(om.MSpace.kWorld)
        p0 = (float(int(pnt[0] * 1000)) / 1000)
        p1 = (float(int(pnt[1] * 1000)) / 1000)
        p2 = (float(int(pnt[2] * 1000)) / 1000)
        pos = [p0, p1, p2]

        #pos x
        if p0>0:
            mirrorFromList[i] = pos
        elif p0<0:
            mirrorToList[i] = pos
        else:
            mirrorStayList[i] = pos


        counter1+=1
        geomIter1.next()

    for i in range(maxCount2):
        comp = geomIter2.currentItem()

        pnt = geomIter2.position(om.MSpace.kWorld)
        p0 = (float(int(pnt[0] * 1000)) / 1000)
        p1 = (float(int(pnt[1] * 1000)) / 1000)
        p2 = (float(int(pnt[2] * 1000)) / 1000)
        pos = [p0, p1, p2]

        #pos x
        if p0>0:
            mirrorFromList[i] = pos
        elif p0<0:
            mirrorToList[i] = pos
        else:
            mirrorStayList[i] = pos


        counter2+=1
        geomIter2.next()
        
        
        
        
        
    matchSet = {}

    for ff,posF in mirrorFromList.items():
        for tt,posT in mirrorToList.items():
            if [abs(posF[0]),posF[1],posF[2]] == [abs(posT[0]),posT[1],posT[2]]:
                matchSet[ff] = tt
    for ss,posS in mirrorStayList.items():
        matchSet[ss] = ss



    infNames1 = []
    for i in range(infs1.length()):
        infName = infs1[i].partialPathName()
        infNames1.append(infName)

    infNames2 = []
    for i in range(infs2.length()):
        infName = infs2[i].partialPathName()
        infNames2.append(infName)        
        
        
    #print infNames

    jntSourceList = {}
    jntDestList = {}
    for i,n in enumerate(infNames1):
        #print n
        if "L_" in n:
            jntSourceList[i] = n
            #print "Found the L"
        elif "R_" in n:
            jntDestList[i] = n
            #print "Found the R"
    for i,n in enumerate(infNames2):
        #print n
        if "L_" in n:
            jntSourceList[i] = n
            #print "Found the L"
        elif "R_" in n:
            jntDestList[i] = n
            #print "Found the R"
    
    
    
    
    
    
    
    
    
    
    switchDict = {}
    for si,sj in jntSourceList.items():
        for di,dj in jntDestList.items():
            if sj.replace("L_","") == dj.replace("R_",""):
                print "matched %s to %s" % (sj, dj)

                switchDict[si] = di

    print switchDict

    for k,v in matchSet.items():
        index = v*numInfs2

        startWeight = wgts2[k*numInfs2:k*numInfs2+numInfs2]
        #print startWeight
        postWeight = startWeight
        for kk,vv in switchDict.items():
            postWeight[kk], postWeight[vv] = startWeight[vv], startWeight[kk]

        for ll,postW in enumerate(postWeight):
            tempNum = ll+index
            wgts2.set(postW,tempNum)
        #print postWeight
    #print wgts
    
    for ss in mirrorStayList.keys():
        index = ss*numInfs2
        startWeight = wgts2[ss*numInfs2:ss*numInfs+numInfs2]
        
        postWeight = startWeight
        
        for kk,vv in switchDict.items():
            
            postWeight[kk] = startWeight[vv]

        #Here we're going to manually normalize the weights
        maxVal = sum(postWeight)
        postWeightN = [p/maxVal for p in postWeight]
        
        for ll,postW in enumerate(postWeightN):
            tempNum = ll+index
            wgts2.set(postW,tempNum)

    #print wgts
    
    infIndices = om.MIntArray(numInfs2)
    for ii in range(numInfs2):
        infIndices.set(ii, ii)

    skinClusterNode2.setWeights(dgPath2, components2, infIndices, wgts2, False)

    cmds.setAttr("%s.normalizeWeights"%skin2,normalVal)
    
    #cmds.skinCluster("Shirt_02_Driver_skinCluster",e=1,fnw=1)
    

    
    
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


class CMiller_WeightJumper(QtGui.QDialog):
    def __init__(self, parent=getMayaWindow()):
        """Initialize the class, load the UI file.

        """
        super(CMiller_WeightJumper, self).__init__(parent)
        self.loader = QtUiTools.QUiLoader(self)
        self.UI = self.loader.load(myFile, self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        addFilter(self.UI)

        # Connect the elements
        self.UI.loadSource_pushButton.clicked.connect(self.loadNew)
        self.UI.loadDest_pushButton.clicked.connect(self.loadNew)
        self.UI.transferWeights_pushButton.clicked.connect(self.transferWeights)

        self.UI.loadSourceMesh_pushButton.clicked.connect(self.loadNew)
        self.UI.mirrorWeights_pushButton.clicked.connect(self.mirrorWeights)

        # Show the window
        self.UI.show()


    def loadNew(self):
        """ Loads a new source object into the UI.

        :return: None
        """
        sender = self.sender().objectName()
        self.UI.skinCluster_listWidget.clear()
        sel = cmds.ls(sl=1)[0]

        if sender=="loadSource_pushButton":
            self.UI.sourceJoint_lineEdit.setText(sel)
            skinClust = list(set(cmds.listConnections(sel,type="skinCluster")))
        elif sender=="loadDest_pushButton":
            self.UI.destJoint_lineEdit.setText(sel)
            skinClust = list(set(cmds.listConnections(sel,type="skinCluster")))
        elif sender=="loadSourceMesh_pushButton":
            self.UI.sourceMesh_lineEdit.setText(sel)
            skinClust = list([mel.eval("findRelatedSkinCluster %s"%sel)])

        self.UI.skinCluster_listWidget.addItems(skinClust)
        self.UI.skinCluster_listWidget.setCurrentRow(0)



    def transferWeights(self):
        """ Transfers attributes based on UI selections.

        :return: None
        """
        src = self.UI.sourceJoint_lineEdit.text()
        prc = self.UI.percentage_SpinBox.value()
        dst = self.UI.destJoint_lineEdit.text()
        skn = [a.text() for a in self.UI.skinCluster_listWidget.selectedItems()][0]
        sel = self.UI.selVerts_checkBox.isChecked()


        weightJumper(skn,jointSource=src,jointTarget=dst,selVerts=sel, percent=prc)


    def mirrorWeights(self):

        skn = [a.text() for a in self.UI.skinCluster_listWidget.selectedItems()][0]
        weightMirror(skn)


def run():
    """ Run the UI.

    """
    global CMiller_WeightJumperWin
    try:
        CMiller_WeightJumperWin.close()
    except:
        pass
    CMiller_WeightJumperWin = CMiller_WeightJumper()