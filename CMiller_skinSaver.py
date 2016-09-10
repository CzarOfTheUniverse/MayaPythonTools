from __future__ import division

import time
import ast
import json
import os
from maya import OpenMaya as om, OpenMayaUI as omUI, OpenMayaAnim as oma, cmds, mel
from PySide import QtGui, QtCore, QtUiTools
from shiboken import wrapInstance

myDir = os.path.dirname(os.path.abspath(__file__))
myFile = os.path.join(myDir, 'CMiller_SkinUI.ui')

'''
################################################
								~Skin Saving Procedures~
################################################
'''


def getNodeShape(node=''):
    if not node:
        node = cmds.ls(sl=1)[0]
        #print node
    # transform selected
    if cmds.nodeType(node) == 'transform':
        shape = cmds.listRelatives(node, s=1)
        return shape
    elif cmds.nodeType(node) in ['mesh', 'nurbsCurve', 'nurbsSurface']:
        return node
    else:
        cmds.warning('The hell did you select?')
        return None


class SkinCluster(object):
    skinFileExt = '.skinData'

    @classmethod
    def skinImport(cls, readPath=None, mesh=None, world=0, namespace=""):

        if not mesh:
            try:
                mesh = cmds.ls(sl=1)[0]
            except IndexError:
                cmds.warning('No object selected.')

        if readPath == None:
            readPath = cmds.fileDialog2(ds=2, fm=1, ff='Skin Files (*%s)' % SkinCluster.skinFileExt)[0]

        if not readPath:
            return

        # file read
        start_time = time.time()
        with open(readPath, 'rb') as file:
            data = json.load(file)

        if world == 0:
            # vert count check
            curVtxs = cmds.polyEvaluate(mesh, v=1)
            readVtxs = len(data['blendWeights'])
            if curVtxs != readVtxs:
                raise RuntimeError('Vert count mismatch: %d != %d' % (curVtxs, readVtxs))

        shape = getNodeShape(mesh)
        if cmds.listConnections([x for x in cmds.listHistory(shape,f=1) if cmds.nodeType(x) not in ['blendShape','set','objectSet','shadingEngine','hyperLayout']], t="skinCluster"):
            print "found skin"
            skinCluster = SkinCluster(mesh)
        else:
            jnts = data['weights'].keys()

            try:
                namespace = win.UI.namespace_enum.currentText()
            except:
                pass
            if namespace:
                if namespace != "*Empty*":
                    jnts = [namespace + ":" + x for x in jnts]

            skinClusterNew = cmds.skinCluster(jnts, mesh, tsb=1, nw=2, n=data['name'])
            print skinClusterNew
            print "made skin"
            cmds.refresh()
            cmds.dgdirty(mesh)
            cmds.dgeval(mesh)
            cmds.dgdirty(skinClusterNew)
            cmds.dgeval(skinClusterNew)
            cmds.refresh()
            skinCluster = SkinCluster(mesh)

        if world == 0:
            skinCluster.setData(data)
        elif world == 1:
            skinCluster.setWorldWeights(data, threshold=win.UI.threshold_inp.value())
        print 'Imported %s' % readPath
        end_time = time.time()
        total_time = end_time - start_time
        print("Elapsed time was %g seconds" % (total_time))

    @classmethod
    def export(cls, savePath=None, mesh=None):
        skin = SkinCluster(mesh)
        skin.exportSkinData(savePath)

    @classmethod
    def destroyNamespace(cls, name):
        parts = name.split('|')
        result = ''
        for i, p in enumerate(parts):
            if i > 0:
                result += '|'
            result += p.split(':')[-1]
        return result

    def __init__(self, mesh=None):
        if not mesh:
            try:
                mesh = cmds.ls(sl=1)[0]
            except IndexError:
                cmds.warning('No object selected.')

        self.mesh = mesh
        shape = getNodeShape(mesh)
        if not shape:
            raise RuntimeError('No shape connected to %s' % mesh)

        self.skinCluster = cmds.listConnections(cmds.listHistory(shape, f=1), t="skinCluster")
        if self.skinCluster:
            self.skinCluster = self.skinCluster[0]
        if not self.skinCluster:
            raise ValueError('No skin connected to %s' % shape)


        # API skin cluster grab
        selList = om.MSelectionList()
        selList.add(self.skinCluster)
        self.mObj = om.MObject()
        selList.getDependNode(0, self.mObj)
        self.mfnSkin = oma.MFnSkinCluster(self.mObj)
        self.data = {
            'weights': {},
            'worldSpace': {},
            'worldSpaceJoints': [],
            'blendWeights': [],
            'name': self.skinCluster,
        }

    def getData(self):
        dgPath, components = self.__getGeoComponents()

        self.getInfWeights(dgPath, components)

        self.getInfBlendWeights(dgPath, components)

        self.worldSpaceQuery(dgPath, components)

        for attr in ['skinningMethod', 'normalizeWeights']:
            self.data[attr] = cmds.getAttr('%s.%s' % (self.skinCluster, attr))
        #print self.data

    def __getGeoComponents(self):
        mfnSet = om.MFnSet(self.mfnSkin.deformerSet())
        mfnSetMembers = om.MSelectionList()
        mfnSet.getMembers(mfnSetMembers, False)
        dgPath = om.MDagPath()
        components = om.MObject()
        mfnSetMembers.getDagPath(0, dgPath, components)
        return dgPath, components

    def getInfWeights(self, dgPath, components):
        wgts = self.__getCurrentWeights(dgPath, components)

        infPaths = om.MDagPathArray()
        numInfs = self.mfnSkin.influenceObjects(infPaths)
        numComponentsPerInf = wgts.length() // numInfs

        for i in range(infPaths.length()):
            infName = infPaths[i].partialPathName()
            infPureName = SkinCluster.destroyNamespace(infName)

            self.data['weights'][infPureName] = [wgts[j * numInfs + i] for j in range(numComponentsPerInf)]

    def __getCurrentWeights(self, dgPath, components):
        wgts = om.MDoubleArray()
        util = om.MScriptUtil()
        util.createFromInt(0)
        pUInt = util.asUintPtr()
        self.mfnSkin.getWeights(dgPath, components, wgts, pUInt)
        return wgts

    def getInfBlendWeights(self, dgPath, components):
        wgts = om.MDoubleArray()
        self.mfnSkin.getBlendWeights(dgPath, components, wgts)
        self.data['blendWeights'] = [wgts[i] for i in range(wgts.length())]

    def exportSkinData(self, savePath=None):

        if savePath == None:
            savePath = cmds.fileDialog2(ds=2, fm=0, ff='Skin Files (*%s)' % SkinCluster.skinFileExt)[0]
        if not savePath:
            return
        if not savePath.endswith(SkinCluster.skinFileExt):
            savePath += SkinCluster.skinFileExt

        self.getData()

        with open(savePath, 'wb') as file:
            json.dump(self.data, file)
        print 'Exported skinCluster (%d influences, %d verts) %s' % (
        len(self.data['weights'].keys()), len(self.data['blendWeights']), savePath)

    def refreshNamespaceUI(self):
        nsList = cmds.namespaceInfo(lon=1) + ["*Empty*"]
        self.UI.namespace_enum.clear()
        self.UI.namespace_enum.addItems(nsList)

    def worldSpaceQuery(self, dgPath, components):
        inPointArray = om.MPointArray()
        inMfnMesh = om.MFnMesh(dgPath)
        inMfnMesh.getPoints(inPointArray, om.MSpace.kWorld)

        wgt = om.MDoubleArray()
        util = om.MScriptUtil()
        util.createFromInt(0)
        pUInt = util.asUintPtr()

        infPaths = om.MDagPathArray()
        infs = self.mfnSkin.influenceObjects(infPaths)

        self.jntList = []
        for ii in range(infPaths.length()):
            infName = infPaths[ii].partialPathName()
            infPureName = SkinCluster.destroyNamespace(infName)
            self.jntList.append(infPureName)

        self.data['worldSpaceJoints'] = str(self.jntList)

        pos = []
        geomIter = om.MItGeometry(dgPath)

        for i in range(inPointArray.length()):
            comp = geomIter.currentItem()
            pnt = geomIter.position(om.MSpace.kWorld)
            p0 = (float(int(pnt[0] * 1000)) / 1000)
            p1 = (float(int(pnt[1] * 1000)) / 1000)
            p2 = (float(int(pnt[2] * 1000)) / 1000)
            pos = [p0, p1, p2]

            self.mfnSkin.getWeights(dgPath, comp, wgt, pUInt)
            self.data['worldSpace'][str(pos)] = str(wgt)

            geomIter.next()

    def setData(self, data):
        dgPath, components = self.__getGeoComponents()
        self.data = data

        for attr in ['skinningMethod', 'normalizeWeights']:
            cmds.setAttr('%s.%s' % (self.skinCluster, attr), 0)

        self.setInfWeights(dgPath, components)
        self.setInfBlendWeights(dgPath, components)

        for attr in ['skinningMethod', 'normalizeWeights']:
            cmds.setAttr('%s.%s' % (self.skinCluster, attr), self.data[attr])

    def setInfWeights(self, dgPath, components):
        wgts = self.__getCurrentWeights(dgPath, components)

        infPaths = om.MDagPathArray()
        numInfs = self.mfnSkin.influenceObjects(infPaths)
        numComponentsPerInf = wgts.length() // numInfs

        try:
            win.progression(0)  # ;print 0.00
        except:
            print 0.00

        for importedInf, importedWgts in self.data['weights'].items():
            for i in range(infPaths.length()):
                infName = infPaths[i].partialPathName()
                infPureName = SkinCluster.destroyNamespace(infName)
                if infPureName == importedInf:
                    # gj! store values!
                    for j in range(numComponentsPerInf):
                        wgts.set(importedWgts[j], j * numInfs + i)
                    break
            else:
                #raise ValueError('Mismatched joint names')

                progress = (round(((i / infPaths.length()) * 100), 2))

                try:
                    win.progression(progress)  # ;print progress
                except:
                    print progress

        infIndices = om.MIntArray(numInfs)
        for ii in range(numInfs):
            infIndices.set(ii, ii)
        self.mfnSkin.setWeights(dgPath, components, infIndices, wgts, False)

        try:
            win.progression(100)  # ;print 100.00
        except:
            print 100.00

    def setInfBlendWeights(self, dgPath, components):
        blendWgts = om.MDoubleArray(len(self.data['blendWeights']))
        for i, w in enumerate(self.data['blendWeights']):
            blendWgts.set(w, i)
        self.mfnSkin.setBlendWeights(dgPath, components, blendWgts)

    def setWorldWeights(self, data, threshold):

        dgPath, components = self.__getGeoComponents()

        self.data = data

        if self.skinCluster:
            cmds.setAttr(self.skinCluster + '.nw', 0)

        inPointArray = om.MPointArray()
        inMfnMesh = om.MFnMesh(dgPath)
        inMfnMesh.getPoints(inPointArray, om.MSpace.kWorld)

        infPaths = om.MDagPathArray()
        numInfs = self.mfnSkin.influenceObjects(infPaths)
        inIntArray = om.MIntArray(self.mfnSkin.influenceObjects(infPaths))

        for x in range(inIntArray.length()):
            inIntArray.set(x, x)

        #wgts = om.MDoubleArray(numInfs)
        wgts = self.__getCurrentWeights(dgPath, components)

        pos = []
        geomIter = om.MItGeometry(dgPath)

        componentsEx = []

        importedLoc = self.data['worldSpace'].keys()
        importedWgts = self.data['worldSpace'].values()

        maxCount = inPointArray.length()

        try:
            win.progression(0)
        except:
            print 0.00

        unmatchedList = []
        counter=0
        for i in range(maxCount):
            comp = geomIter.currentItem()

            pnt = geomIter.position(om.MSpace.kWorld)
            p0 = (float(int(pnt[0] * 1000)) / 1000)
            p1 = (float(int(pnt[1] * 1000)) / 1000)
            p2 = (float(int(pnt[2] * 1000)) / 1000)
            pos = [p0, p1, p2]
            matched = False

            if pos in [json.loads(x) for x in importedLoc]:
                wList = json.loads(self.data['worldSpace'][str(pos)])
                # print "%s matches %s"%(pos, pList)
                for ll in range(numInfs):
                    wgts.set(wList[ll], ll+counter)

                    #self.mfnSkin.setWeights(dgPath, comp, inIntArray, wgts, False)
                matched = True

                #del self.data['worldSpace'][str(pos)]
            if matched == False and threshold > 0.0:
                for x, p in enumerate(importedLoc):
                    pList = json.loads(p)
                    tPos = [jj for ii, jj in enumerate(pList) if (pos[ii] + threshold) > jj > (pos[ii] - threshold)]

                    #So the idea here is to parse the dictionary, iterate over the keys/values, compare the positions within the threshold


                    if len(tPos) == 3:
                        wList = json.loads(importedWgts[x])
                        print tPos, "Success!"
                        for ll in range(numInfs):
                            wgts.set(wList[ll], ll)
                        self.mfnSkin.setWeights(dgPath, comp, inIntArray, wgts, False)
                        matched = True
                        del importedLoc[pList]
                        break
            '''
            for x, p in enumerate(importedLoc):
                pList = json.loads(p)
                if pos == pList:
                    wList = json.loads(importedWgts[x])
                    # print "%s matches %s"%(pos, pList)
                    for ll in range(numInfs):
                        wgts.set(wList[ll], ll)

                        self.mfnSkin.setWeights(dgPath, comp, inIntArray, wgts, False)
                    matched = True
                    del importedLoc[pList]
                    break

            if matched == False and threshold > 0.0:
                for x, p in enumerate(importedLoc):
                    pList = json.loads(p)
                    tPos = [jj for ii, jj in enumerate(pList) if (pos[ii] + threshold) > jj > (pos[ii] - threshold)]

                    if len(tPos) == 3:
                        wList = json.loads(importedWgts[x])
                        print tPos, "Success!"
                        for ll in range(numInfs):
                            wgts.set(wList[ll], ll)
                        self.mfnSkin.setWeights(dgPath, comp, inIntArray, wgts, False)
                        matched = True
                        del importedLoc[pList]
                        break
            '''
            if matched == False:
                unmatchedList.append(i)

            progress = (round(((i / maxCount) * 100), 2))

            try:
                win.progression(progress)
            except:
                print progress
            counter+=numInfs
            geomIter.next()
        #print dgPath, geomIter, inIntArray, wgts
        self.mfnSkin.setWeights(dgPath, components, inIntArray, wgts, False)
        # self.mfnSkin.setWeights(dgPath, components, inIntArray, wgts, False)



        cmds.select(d=1)
        for i in unmatchedList:
            cmds.select("%s.vtx[%d]" % (self.mesh, i), add=1)
        print "No match for %d vertices." % len(unmatchedList)
        if len(unmatchedList)>1:
            print "Applying automatic weighting to set."
            mel.eval("SmoothSkinWeights;")
            # cmds.select(d=1)

        try:
            win.progression(100)
        except:
            print 100.00
        if self.skinCluster:
            cmds.setAttr(self.skinCluster + '.nw', 1)

    def mirrorSkinWeights(self, axis='x', side='L'):

        """
        Steps:

        1. Find positions and values of "side"
        2. Find corresponding positions for other side
        3. Remap values from "side" joints to other
        4. Set new values


        5. compare abs worldspace values to find matching verts
        6. swap those


        """
        if axis == 'x':
            ax = 0

        dgPath, components = self.__getGeoComponents()
        geomIter = om.MItGeometry(dgPath)
        self.getData()

        infPaths = om.MDagPathArray()
        numInfs = self.mfnSkin.influenceObjects(infPaths)
        inIntArray = om.MIntArray(self.mfnSkin.influenceObjects(infPaths))

        # wgts = self.__getCurrentWeights(dgPath, components)
        wgts = om.MDoubleArray(numInfs)
        numComponentsPerInf = wgts.length() // numInfs

        for x in range(inIntArray.length()):
            inIntArray.set(x, x)

        util = om.MScriptUtil()
        util.createFromInt(0)
        pUInt = util.asUintPtr()

        jnts = ast.literal_eval(self.data['worldSpaceJoints'])
        vals = self.data['worldSpace'].values()
        positions = self.data['worldSpace'].keys()

        sL = []
        sR = []

        inPointArray = om.MPointArray()
        inMfnMesh = om.MFnMesh(dgPath)
        inMfnMesh.getPoints(inPointArray, om.MSpace.kWorld)

        for i in range(inPointArray.length()):

            comp = geomIter.currentItem()
            pnt = geomIter.position(om.MSpace.kWorld)
            p0 = (float(int(pnt[0] * 1000)) / 1000)
            p1 = (float(int(pnt[1] * 1000)) / 1000)
            p2 = (float(int(pnt[2] * 1000)) / 1000)
            pos = [p0, p1, p2]

            if pos[ax] > 0:
                sR.append([i, pos])
            elif pos[ax] < 0:
                sL.append([i, pos])
            else:
                pass
            geomIter.next()

        matchSet = {}

        for infoRt, infoLt in [(infoR, infoL) for infoR in sR for infoL in sL]:
            infoR = ['%.4f' % elem for elem in infoRt[1]]
            infoL = ['%.4f' % elem for elem in infoLt[1]]
            if [abs(float(infoR[0])), infoR[1:]] == [abs(float(infoL[0])), infoL[1:]]:
                matchSet[str(infoRt[0])] = str(infoLt[0])

        switchDict = {}

        lList = []
        rList = []
        lListIndxs = []
        rListIndxs = []

        for i, j in enumerate(jnts):
            if j[:2] == "L_":
                lList.append('%d|%s' % (i, j))
                lListIndxs.append(i)
            elif j[:2] == "R_":
                rList.append('%d|%s' % (i, j))
                rListIndxs.append(i)

        for lElement in lList:
            for rElement in rList:
                if lElement.split('|')[1][2:] == rElement.split('|')[1][2:]:
                    print "matched %s to %s" % (lElement, rElement)
                    switchDict[lElement] = rElement

        for num in matchSet.keys():
            trueVal = ast.literal_eval(vals[int(num)])
            for k, v in switchDict.items():
                trueVal[int(k[:1])], trueVal[int(v[:1])] = trueVal[int(v[:1])], trueVal[int(k[:1])]
            for ll in range(numInfs):
                wgts.set(trueVal[ll], ll)

            mItVtx = om.MItMeshVertex(dgPath)
            for i in range(inPointArray.length()):
                if mItVtx.index() == int(num):
                    comp = mItVtx.currentItem()
                    self.mfnSkin.setWeights(dgPath, comp, inIntArray, wgts, False)
                    break
                mItVtx.next()

        cmds.select(d=1)
        for i in sR:
            cmds.select("%s.vtx[%d]" % (self.mesh, i[0]), add=1)


'''
################################################
								~User Interface~
################################################
'''


def getMayaWindow():
    """Return Maya main window"""
    ptr = omUI.MQtUtil.mainWindow()
    if ptr is not None:
        return wrapInstance(long(ptr), QtGui.QMainWindow)


class designerUI(QtGui.QDialog, SkinCluster):
    def __init__(self, parent=getMayaWindow()):
        """Initialize the class, load the UI file"""
        super(designerUI, self).__init__(parent)
        self.loader = QtUiTools.QUiLoader(self)
        self.UI = self.loader.load(myFile, self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        # Connect the elements
        self.UI.saveWeights_btn.clicked.connect(self.saveWeights)
        self.UI.loadReg_btn.clicked.connect(self.loadWeights)
        self.UI.loadWorld_btn.clicked.connect(self.loadWorldWeights)
        self.UI.refresh_btn.clicked.connect(self.refreshNamespaceUI)

        self.refreshNamespaceUI()

        # Show the window
        self.UI.show()

    def saveWeights(self):
        """Saves the skin weights"""
        self.export()

    def loadWeights(self):
        """Loads the local space skin weights"""
        self.skinImport()

    def loadWorldWeights(self):
        """Loads the world space skin weights"""
        self.skinImport(world=1)

    def progression(self, progress):
        """Runs a progress bar update"""
        self.UI.percentage_pcn.setValue(progress)


def run():
    """Run the UI"""
    global win
    try:
        win.close()
    except:
        pass
    win = designerUI()
