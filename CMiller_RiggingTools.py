"""
~ CMiller Rigging Tools ~ Christopher M. Miller ~ 2015/04/10

A collection of functions for various Rigging tools with a nifty UI.

Written and maintained by Christopher M. Miller

v002 - Redesigned UI, new functions
v001 - Initial creation
"""

from maya import OpenMayaUI as omUI, cmds, mel
from PySide import QtGui, QtCore, QtUiTools
from shiboken import wrapInstance
import os, json

myDir = os.path.dirname(os.path.abspath(__file__))
myFile = os.path.join(myDir, 'CMiller_RiggingToolsUI.ui')
myIconFile = os.path.join(myDir, 'CMiller_RiggingToolsUI.iconfile')


class CMiller_RiggingToolsFuncs(object):
    def __init__(self):
        cmds.selectPref(tso=1)


    ##########################
    #
    # Variables
    #
    ##########################

    skinToggle = 1
    controlSuffix = "_CTL"


    ##########################
    #
    # Functions
    #
    ##########################

    def resetCTL(self):
        """ Grabs the _CTL controllers and resets them.
        :return: None
        """
        ctlSelect = cmds.ls("*_CTL");
        for CTL in ctlSelect:
            allAttrs = cmds.listAttr(CTL, k=1);
            for attr in allAttrs:
                if ('translate' in attr or 'rotate' in attr):
                    try:
                        cmds.setAttr('%s.%s' % (CTL, attr), 0);
                    except:
                        pass
                else:
                    dv = cmds.attributeQuery(attr, node=CTL, ld=1)[0]
                    try:
                        cmds.setAttr('%s.%s' % (CTL, attr), dv);
                    except:
                        pass

    def cmmCenterJointOnSel(self, chain=True, name="default"):
        """ Creates a joint at the center of the selections. Can optionally chain together.
        :param chain: Whether or not to chain the joints together.
        :param name: The name of the joint(s).
        :return: None
        """
        i = 0
        sel = cmds.ls(sl=1)
        jntList = []
        for s in sel:
            if ".e" in s:
                s = "%s.vtx%s" % (s.split(".e")[0], s.split(".e")[1])
            cmds.select(s, r=1)
            a = cmds.cluster()[1]
            cmds.select(d=1)
            if chain is True:
                if (len(jntList) > 0):
                    cmds.select(jntList[i])
                    i += 1
            j = cmds.joint(name="%s#" % (name))
            jntList.append(j)
            c = cmds.parentConstraint(a, j, mo=0)
            cmds.delete(c, a)

    def cmmCreateController(self, name="", type="parent", target=[], guiCtl=False, guiName="default"):
        """ Creates new controller icon with pads on the selected or passed object(s).
        :param name: The optional name for the new controller.
        :param type: The constraint type to apply. Valid arguments are ("parent","point","orient").
        :param target: Optional list of targets to create individual controllers on, otherwise uses selection.
        :param guiCtl: Optionally passed on gui creation. Type of icon to use.
        :param guiName: Optionally passed on gui creation. Name override.
        :return: Controller name
        """
        if not target:
            target = cmds.ls(sl=1)

        if not isinstance(target, list):
            target = [target]
        if guiName == "":
            guiName = name
        for i in target:
            if guiCtl == False:
                ctl = cmds.circle(n="%s#" % (i), nr=(1, 0, 0))[0]
                ctl = cmds.rename(ctl, ctl + "_CTL")
            if guiCtl == True:
                if os.path.exists(myIconFile):
                    with open(myIconFile, 'rb') as file:
                        currentData = json.load(file)
                        buildObject = currentData[name]
                        print buildObject
                        cvs = buildObject['cvs']
                        spans = buildObject['spans']
                        deg = buildObject['deg']
                        ctl = cmds.curve(p=cvs, n=guiName + "#", d=deg)
                        ctl = cmds.rename(ctl, ctl + "_CTL")
                    print ctl

            pad = self.cmmOffsetPad(selList=[ctl])
            con = cmds.parentConstraint(i, pad, mo=0)
            cmds.delete(con)

            if type == "parent":
                con = cmds.parentConstraint(ctl, i, mo=0)
            elif type == "point":
                con = cmds.pointConstraint(ctl, i, mo=0)
            elif type == "orient":
                con = cmds.orientConstraint(ctl, i, mo=0)

        return ctl

    def createGimbalPads(self, sel=""):
        """ Creates additional hidden gimbal controllers on existing nodes.
        :param sel: Optional list of targets to create gimbal controllers on, otherwise uses selection.
        :return: None
        """
        if not sel:
            selCtls = cmds.ls(sl=1)

        for ctl in selCtls:

            if not cmds.getAttr("%s.rotateX" % ctl, l=1):
                gimbalCtl = cmds.duplicate(ctl, rc=1, n="%s_Gimbal_CTL" % ctl.split("_CTL")[0])[0]
                if cmds.listRelatives(gimbalCtl, ad=1, typ="transform"):
                    cmds.delete(cmds.listRelatives(gimbalCtl, ad=1, typ="transform"))
                wasLocked = 0
                if cmds.getAttr("%s.scale" % gimbalCtl, l=1):
                    wasLocked = 1
                    cmds.setAttr("%s.scale" % gimbalCtl, l=0)
                cmds.setAttr("%s.scale" % gimbalCtl, 1.2, 1.2, 1.2)
                cmds.makeIdentity(gimbalCtl, a=1, s=1)
                if wasLocked:
                    cmds.setAttr("%s.overrideEnabled" % gimbalCtl, 1)
                cmds.setAttr("%s.overrideColor" % gimbalCtl, 21)
                cmds.parent(ctl, gimbalCtl)

                # create connections

                gimbalCtlShapes = cmds.listRelatives(gimbalCtl, s=1)

                cmds.addAttr(ctl, ln="showGimbal", k=0, at="bool")
                cmds.setAttr("%s.showGimbal" % ctl, cb=1)

                for gimbalCtlShape in gimbalCtlShapes:
                    cmds.connectAttr("%s.showGimbal" % ctl, "%s.visibility" % gimbalCtlShape)


    def resetSelected(self):
        """ Simple Translate and Rotate reset.
        :return: None
        """
        cmds.ls(sl=1)
        cmds.xform(os=1, ro=(0, 0, 0), t=(0, 0, 0))

    def toggleSkinClusters(self):
        """ Simple function to toggle all skinClusters on/off.
        :return: None
        """
        self.skinToggle ^= 1
        print self.skinToggle
        skins = cmds.ls(type="skinCluster")
        for skin in skins:
            cmds.setAttr("%s.envelope" % skin, self.skinToggle)

    def kaSetMaker(self):
        """ Creates a KeyAll Set.
        :return: None
        """
        allSet = cmds.ls('KeyAll', sets=True)

        objN = cmds.ls(type="transform")

        if allSet:  # if allSet == True
            print "KEYALL set Exists"
            targetSet = allSet[0]

        else:

            targetSet = cmds.sets(n="KeyAll")

        for objects in objN:
            if objects.endswith("_CTL"):
                cmds.sets(objects, add=targetSet)
                print "KeyAll Set Made"

    def cmmSplitJoint(self,numSplits=4,chain=True):
        """ Select two joints to split between, or select a single joint to split.
        :param numSplits: How many new joints/splits to create.
        :param chain: Whether to chain the joints together or leave them floating.
        :return: None
        """
        curSelection = cmds.ls(sl=1)

        if len(curSelection)==1:
            baseJoint = curSelection[0]
            children = cmds.listRelatives(baseJoint,c=1,type="joint")
            if len(children)==1:
                endJoint = children[0]
            elif len(children)>1:
                #select child?
                cmds.warning("There are too many children, please select Start and End joints")
                return
        elif len(curSelection)==2:
            baseJoint = curSelection[0]
            endJoint = curSelection[1]

        else:
            cmds.warning("I legitimately don't know what you're trying to do.")
            return

        j1Loc = cmds.xform(baseJoint, q=1, t=1, ws=1, a=1)
        j2Loc = cmds.xform(endJoint, q=1, t=1, ws=1, a=1)

        iterAmt = [(y - x)/(numSplits+1) for x, y in zip(j1Loc, j2Loc)]

        cmds.select(d=1)
        cmds.select(baseJoint)

        for i in xrange(numSplits):
            iterLoc = [x*(i+1) for x in iterAmt]
            newPos = [x + y for x, y in zip(j1Loc, iterLoc)]
            nj = cmds.joint(a=1, p=(newPos))
            if not chain:
                cmds.select(d=1)
                cmds.select(baseJoint)

        if cmds.listRelatives(endJoint,p=1,type="joint")[0] == baseJoint:
            cmds.parent(endJoint, nj)


    def cmmCreateJoint(self):
        """ Select components or objects to create joints at.
        :return: None
        """
        selList = cmds.ls(os=1)
        for item in selList:
            if not CMiller_RiggingToolsWin.UI.createJoints_cb.isChecked():
                cmds.select(d=1)
            iTrans = cmds.xform(item, q=1, t=1, ws=1)
            cmds.joint(p=iTrans, radius=.5)

    def connectChannels(self):
        """ Connects two selected objects via highlighted Channel Box attributes.
        :return: None
        """
        sel = cmds.ls(sl=1)
        if len(sel) == 2:
            s, t = sel
            channelBox = mel.eval(
                'global string $gChannelBoxName; $temp=$gChannelBoxName;')  # fetch maya's main channelbox
            attrs = cmds.channelBox(channelBox, q=True, sma=True)
            for at in attrs:
                cmds.connectAttr("%s.%s" % (s, at), "%s.%s" % (t, at))

    def cmmOffsetPad(self, selList=[]):
        """ Creates offset pads above the selected object(s).
        :param selList: Optional argument to pass a list of objects, otherwise uses selection.
        :return: List of created top level groups created.
        """
        if not selList:
            selList = cmds.ls(sl=1)
        # if selList != []:
        #	selList = [selList]

        pads = []
        for i in selList:
            cmds.select(d=1)
            print i
            offset3 = cmds.group(em=1, name=i + "_Offset3")
            offset2 = cmds.group(em=1, name=i + "_Offset2", p=offset3)
            offset1 = cmds.group(em=1, name=i + "_Offset1", p=offset2)
            pad = cmds.group(offset3, name=i + "_Pad")
            pc1 = cmds.parentConstraint(i, pad, mo=0)
            cmds.delete(pc1)
            # cmds.makeIdentity(a=1)
            if cmds.listRelatives(i, p=1):
                iParent = cmds.listRelatives(i, p=1, f=1)[0]
                cmds.parent(pad, iParent)
            cmds.parent(i, offset1)
            pads.append(pad)
        return pads

    def cmmDrawLine(self):
        """ Draws a visual line between two targets. Useful for poleVectors.
        :return: None
        """
        targets = cmds.ls(sl=1)
        lineGrp = cmds.group(em=1, n="%s_lineGrp" % targets[0])
        clusGrp = cmds.group(em=1, n="%s_clusGrp" % targets[0])
        line = cmds.curve(p=[(0, 0, 0), (3, 5, 6)], d=1, n="%s_PVline" % targets[0])
        for i in xrange(2):
            clus = cmds.cluster("%s.cv[%d]" % (line, i), n="%s_PVcluster" % targets[i])[1]
            cmds.parentConstraint(targets[i], clus, mo=0)
            cmds.parent(clus, clusGrp)
        cmds.parent(line, lineGrp)
        cmds.parent(clusGrp, lineGrp)
        cmds.setAttr("%s.visibility" % clusGrp, 0)

    def colorControls(self, num=0, ctlSel=None):
        """ Colors the selected objects or optionally passed list.
        :param num: Sets the color for the controllers. Valid index 0-31.
        :param ctlSel: Optional list to affect, otherwise uses selection.
        :return: None
        """
        if not ctlSel:
            ctlSel = cmds.ls(sl=1)
        for ctl in ctlSel:
            ctlShape = cmds.listRelatives(ctlSel, s=1, f=1)[0]
            cmds.setAttr("%s.overrideColor" % ctlShape, num)
            cmds.setAttr("%s.overrideEnabled" % ctlShape, 1)

    def cmmFollicleMaker(self, obj=None, uPos=0.5, vPos=0.5):
        """ Create a follicle on the selected object.
        :param obj: Optional object to affect, otherwise uses selection.
        :param uPos: The U coordinate to use.
        :param vPos: The V coordinate to use.
        :return: The generated follicle.
        """
        if obj == "":
            try:
                obj = cmds.ls(sl=1)[0]
                print "Using Selected Object"
            except:
                print "Nothing input or selected... try again?"
        if obj:
            objType = cmds.objectType(obj)
            if objType == "transform":
                objShape = cmds.listRelatives(obj, s=1)[0]
                objType = cmds.objectType(objShape)
            if objType == "nurbsSurface":
                objInput = "local"
                objOutput = "inputSurface"
            elif objType == "mesh":
                objInput = "outMesh"
                objOutput = "inputMesh"

            folName = '_'.join((obj, 'follicle', '#'.zfill(3)))
            folShapeName = '_'.join((obj, 'follicleShape', '#'.zfill(3)))

            fol = cmds.createNode('follicle', name=folShapeName)
            folP = cmds.listRelatives(fol, p=1)[0]

            cmds.connectAttr("%s.%s" % (obj, objInput), "%s.%s" % (fol, objOutput))
            cmds.connectAttr("%s.worldMatrix[0]" % (obj), "%s.inputWorldMatrix" % (fol))
            cmds.connectAttr("%s.outRotate" % (fol), "%s.rotate" % (folP))
            cmds.connectAttr("%s.outTranslate" % (fol), "%s.translate" % (folP))

            cmds.setAttr("%s.parameterU" % fol, uPos)
            cmds.setAttr("%s.parameterV" % fol, vPos)

            cmds.setAttr("%s.t" % folP, lock=1)
            cmds.setAttr("%s.r" % folP, lock=1)

            return fol

    def sphereIcon(self, name="Default", size=1):
        """ Creates a simple sphere icon.
        :param name: Name of the created object.
        :param size: Scale of the created object.
        :return: The created object.
        """
        c1 = cmds.circle()[0]
        c2 = cmds.circle()[0]
        c3 = cmds.circle()[0]

        cmds.xform(c2, ro=(0, 90, 0))
        cmds.xform(c3, ro=(90, 0, 0))
        cmds.scale(size, size, size, c1, c2, c3)
        cmds.makeIdentity(c1, c2, c3, t=1, r=1, s=1, a=1)
        cmds.delete(c1, c2, c3, ch=1)
        grp = cmds.group(em=1, n="%s#" % name)
        shapes = cmds.listRelatives(c1, c2, c3, s=1)
        cmds.parent(shapes, grp, r=1, s=1)
        cmds.delete(c1, c2, c3)

        return grp

    def cmmFaceCurves(self, cp=5, foff=.4, cb=0, name="UpperLip"):
        """ *BETA* Face Curves generation.
        :param cp: Number of control points to use.
        :param foff: Radius of the falloff.
        :param cb: Whether to lock the weights.
        :param name: Name of the face curve.
        :return: None
        """
        if name[0].isdigit():
            cmds.warning("Invalid Maya Name! Please Don't Start With A Number")
            return

        selMesh = cmds.ls(sl=1)[0].split(".")[0]
        selMeshName = selMesh.split("_")[0]
        # 1. create Curve and clusters
        crv, inputEdge = cmds.polyToCurve(form=2, degree=3, n="%s_CRV" % name)
        data = cmds.rebuildCurve(crv, rt=0, s=(cp - 2), d=2, kep=1, rpo=1)
        ridesrf = cmds.extrude(crv, ch=1, rn=1, po=0, et=0, upn=1, length=0.1, rotation=0, scale=1, dl=3,
                               n="%s_Ride_SURF" % name)[0]
        srf = \
        cmds.extrude(crv, ch=1, rn=1, po=0, et=0, upn=1, length=0.1, rotation=0, scale=1, dl=3, n="%s_SURF" % name)[0]
        cmds.delete(srf, ch=1)

        clstrList = []
        clstrJntList = []
        clstrJntPadList = []
        ctlList = []
        ctlPadList = []
        pmaList = []

        for i in xrange(cp):
            clstr = cmds.cluster("%s.cv[%d][0:3]" % (srf, i), n="%s_CLST#" % name)[1]  # cmds.joint(n="%s_CLST#"%name)
            clstrList.append(clstr)
            ctl = self.sphereIcon(name, .1)
            ctlList.append(ctl)

            cmds.select(d=1)
            offset = cmds.group(em=1, name=ctl + "_Offset")
            pad = cmds.group(offset, name=ctl + "_Pad")
            pc1 = cmds.parentConstraint(ctl, pad, mo=0)
            cmds.delete(pc1)
            # cmds.makeIdentity(a=1)
            if cmds.listRelatives(ctl, p=1):
                iParent = cmds.listRelatives(ctl, p=1, f=1)[0]
                cmds.parent(pad, iParent)
            cmds.parent(ctl, cmds.listRelatives(ctl, c=1, f=1)[0])
            ctlPadList.append(pad)

            con = cmds.parentConstraint(clstr, pad, mo=0)
            cmds.delete(con)

            ctlCMDV = cmds.createNode("multiplyDivide", n="%s_CounterDT_MDV" % ctl)
            ctlCPMA = cmds.createNode("plusMinusAverage", n="%s_CounterDT_PMA" % ctl)
            pmaList.append(ctlCPMA)
            cmds.connectAttr("%s.translate" % ctl, "%s.input1" % ctlCMDV)
            cmds.connectAttr("%s.output" % ctlCMDV, "%s.input3D[0]" % ctlCPMA)
            cmds.connectAttr("%s.output3D" % ctlCPMA, "%s.translate" % pad)
            cmds.setAttr("%s.input2" % ctlCMDV, -1, -1, -1)

            clstrJnt = cmds.joint(n="%s_JNT#" % name)
            clstrJntPad = self.cmmOffsetPad([clstrJnt])[0]

            # con2 = cmds.parentConstraint(ctl,clstrJntPad,mo=0)
            # cmds.delete(con2)

            clstrJntList.append(clstrJnt)
            clstrJntPadList.append(clstrJntPad)
            # cmds.makeIdentity(pad,t=1,r=1,s=1,a=1,n=0,pn=1)


        # 2. Create blend mesh
        if not cmds.ls("%s_Face_Driver_Mesh" % selMeshName):

            # [x for x in cmds.listHistory(selMesh,pdo=1) if "skinCluster" in x]
            skin = mel.eval("findRelatedSkinCluster %s;" % selMesh)
            if skin:
                cmds.setAttr("%s.envelope" % skin, 0)
                blendMesh = cmds.duplicate(selMesh, n="%s_Face_Driver_Mesh" % selMeshName)[0]
                cmds.setAttr("%s.envelope" % skin, 1)
            else:
                blendMesh = cmds.duplicate(selMesh, n="%s_Face_Driver_Mesh" % selMeshName)[0]

            try:
                cmds.parent(blendMesh, w=1)
            except:
                pass


        else:
            blendMesh = cmds.ls("%s_Face_Driver_Mesh" % selMeshName)[0]
            bs_skin = mel.eval("findRelatedSkinCluster %s;" % blendMesh)
            print bs_skin
            outMeshSkn = cmds.listConnections("%s.outputGeometry" % bs_skin)[0]
            cmds.connectAttr("%s.outMesh" % outMeshSkn, "%s.inputPolymesh" % inputEdge, f=1)
            cmds.connectAttr("%s.worldMatrix[0]" % outMeshSkn, "%s.inputMat" % inputEdge, f=1)

        # 3. create Joint and bind
        if not cmds.ls("%s_BS_Joint" % selMeshName):
            bsJ = cmds.createNode("joint", n="%s_BS_Joint" % selMeshName)
            bsJg = cmds.group(bsJ, n="%s_Face_BS_Grp" % selMeshName, w=1)
            bs_skin = cmds.skinCluster(bsJ, blendMesh)[0]
            outMeshSkn = cmds.listConnections("%s.outputGeometry" % bs_skin)[0]
            cmds.connectAttr("%s.outMesh" % outMeshSkn, "%s.inputPolymesh" % inputEdge, f=1)
            cmds.connectAttr("%s.worldMatrix[0]" % outMeshSkn, "%s.inputMat" % inputEdge, f=1)

        else:
            bsJ = cmds.ls("%s_BS_Joint" % selMeshName)[0]
            bsJg = cmds.ls("%s_Face_BS_Grp" % selMeshName)[0]


            # bs_skin = mel.eval("findRelatedSkinCluster %s;"%blendMesh)

        cmds.parent(srf, bsJg)
        # cmds.parent("%sBase"%srf,bsJg)
        # cmds.skinPercent( bs_skin,'%s.vtx[*]'%blendMesh,transformValue=[(bsJ, 1),(srf, 0)] )


        # 4. add BS to mesh
        if cmds.ls("%s_FaceShapes_BSNode" % selMeshName):
            bsNode = cmds.ls("%s_FaceShapes_BSNode" % selMeshName)[0]
            # tgLen = cmds.blendShape(bsNode,q=1,wc=1)
            # cmds.blendShape(bsNode,e=1,t=(selMesh, tgLen+1, blendMesh, 1.0) )

        else:
            bsNode = cmds.blendShape(blendMesh, selMesh, n="%s_FaceShapes_BSNode" % selMeshName, foc=1, w=[(0, 1)])

        # 5. cleanup
        clstrGrp = cmds.group(clstrList, n="%s_Clusters" % name)
        clstrJntGrp = cmds.group(clstrJntPadList, n="%s_Clusters" % name)

        # cmds.delete(crv,c1,c2)
        ctlPadGrp = cmds.group(em=1, n="%s_Controls" % name)
        for ctl in ctlList:
            cmds.parent("%s_Pad" % ctl, ctlPadGrp)
        cmds.parent([blendMesh, clstrJntGrp, clstrGrp, ridesrf, crv], bsJg)
        if not cmds.ls("%s_Face_BS_Controls" % selMeshName):
            ctlsGrp = cmds.group(ctlPadGrp, n="%s_Face_BS_Controls" % selMeshName)
        else:
            ctlsGrp = cmds.ls("%s_Face_BS_Controls" % selMeshName)[0]
            cmds.parent(ctlPadGrp, ctlsGrp)
        cmds.setAttr("%s.visibility" % bsJg, 0)


        # 6. follicle the controls
        folGrp = cmds.group(em=1, n="%s_Follicles" % name, w=1)
        for i in xrange(cp):
            # LOL DIVIDE BY ZERO BUG FIX THIS
            uVal = i * (1.0 / max(1, (cp - 1)))
            fol = self.cmmFollicleMaker(obj=ridesrf, uPos=uVal)
            cmds.connectAttr("%s.outTranslate" % fol, "%s.translate" % ctlPadList[i],
                             f=1)  # "%s.input3D[1]"%pmaList[i])
            # cmds.connectAttr("%s.outRotate"%fol,"%s.rotate"%ctlPadList[i],f=1)#"%s.input3D[1]"%pmaList[i])

            fCon = cmds.parentConstraint(ctlList[i], clstrJntPadList[i], mo=0)

            cmds.delete(fCon)
            # cmds.makeIdentity(clstrJntList[i],a=1)
            cmds.parent(fol, folGrp)

        cmds.parent(folGrp, bsJg)
        if not cmds.ls("%s_Face_BS_Rig" % selMeshName):
            cmds.group(bsJg, ctlsGrp, n="%s_Face_BS_Rig" % selMeshName)

        for i, ctl in enumerate(ctlList):
            cmds.connectAttr("%s.t" % (ctl), "%s.t" % (clstrJntList[i]))
            cmds.connectAttr("%s.r" % (ctl), "%s.r" % (clstrJntList[i]))
            cmds.connectAttr("%s.s" % (ctl), "%s.s" % (clstrJntList[i]))
        '''
        for i in xrange(cp):
            j = cmds.createNode("joint")
            cmds.parentConstraint()


        #7. Create double transform counter
        # create multipleDivide times -0.5
        #connect to offset? plusminusaverage into pad?

        control.translate > multiplyDivide -.5 > plusMinusAverage SUM follicle.outTranslate > controlPad
        '''

        if cb == 0:
            cmds.skinCluster(bs_skin, e=1, ai=clstrJntList, ug=1, ps=0, ns=cp, dr=foff)
        elif cb == 1:
            cmds.skinCluster(bs_skin, e=1, ai=clstrJntList, ug=1, ps=0, ns=cp, dr=foff, lw=cb, wt=0.0)
        # cmds.setAttr("%s.useComponents"%bs_skin, 1)


        if not "%s_BS" % blendMesh in cmds.listConnections(cmds.listRelatives(blendMesh, s=1), s=1):
            print "FOUND"

            ret = self.cmmCreateBS(blendMesh, 1, newNode="%s_BSNode" % selMeshName)
            node = ret[0][0]
            tns = ret[1]
            cmds.connectAttr("%s.outputGeometry[0]" % node, "%s.inputPolymesh" % inputEdge, f=1)

            cmds.parent(tns, bsJg)
        else:
            ss = cmds.listRelatives("%s_BS" % blendMesh, s=1)
            node = cmds.listConnections(ss, type="blendShape")[0]
            cmds.connectAttr("%s.outputGeometry[0]" % node, "%s.inputPolymesh" % inputEdge, f=1)

    def cmmCreateBS(self, mesh=None, numShapes=2, connect=True, connectNode=None, newNode=None):
        """ Generates connected Blendshapes quickly for a selected mesh.
        :param mesh: Optional mesh to affect, otherwise uses selection.
        :param numShapes: How many blendshapes to create.
        :param connect:
        :param connectNode:
        :param newNode:
        :return: The connected node and the transform.
        """
        # grab selected mesh
        if not mesh:
            try:
                mesh = cmds.ls(sl=1)[0]
            except:
                cmds.warning("Please select a mesh.")

        origShape = [x for x in cmds.listRelatives(mesh, s=1, fullPath=1) if "Orig" in x]
        if origShape:
            meshShape = origShape[0]
        else:
            meshShape = cmds.listRelatives(mesh, s=1, fullPath=1)[0]

        # create shapes for each BS needed
        for i in xrange(numShapes):
            shape = cmds.createNode("mesh", n="%s_BSShape" % mesh)
            transform = cmds.listRelatives(shape, p=1, fullPath=1)[0]
            cmds.connectAttr("%s.outMesh" % meshShape, "%s.inMesh" % shape)
            cmds.xform(transform, t=((i + 1) * 20, 0, 0))

            # optional shape connection
            if connect == True:
                print connectNode


                if connectNode:
                    ind = len(cmds.blendShape(connectNode, q=1, t=1))
                    cmds.blendShape(connectNode, e=1, t=(mesh, ind, transform, 1.0), w=[ind, 1.0], foc=1)
                    #return connectNode, transform
                elif newNode:
                    connectNode = cmds.blendShape(transform, mesh, n=newNode, w=[i, 1.0], foc=1)
                    #return connectNode, transform
                else:
                    cmds.warning("No connection available.")
                    #pass
        return connectNode, transform

    def wingSpanMaker(self):
        """ Select 2 joints. Script will create and weight plane between them and then subdivide for use as an influence object.
        This is minutely slower than a wrap, but allows you to dynamically change the mesh after creation using the polySmooth node.
        :return: None
        """

        sel = cmds.ls(sl=1, l=1)
        name = sel[0].split("|")[-1] + "_planeBind"
        pplane = cmds.polyPlane(sx=1, sy=1, n=name)[0]

        c1 = cmds.listRelatives(sel[0], c=1, f=1)[0]
        c2 = cmds.listRelatives(sel[1], c=1, f=1)[0]

        jList = [sel[0], c1, sel[1], c2]

        for i, j in enumerate(jList):
            dist = cmds.xform(jList[i], q=1, ws=1, t=1)
            cmds.xform("%s.vtx[%d]" % (pplane, i), ws=1, t=dist)

        cmds.xform(pplane, cp=1)
        cmds.makeIdentity(pplane, a=1)
        cmds.delete(pplane, ch=1)

        skin = cmds.skinCluster(pplane, jList[0], jList[1], jList[2], jList[3], tsb=1, sm=0)[0]

        for i, j in enumerate(jList):
            cmds.skinPercent(skin, "%s.vtx[%d]" % (pplane, i), transformValue=[("%s" % j, 1)])

        cmds.polySmooth(pplane, dv=2)


    def blendShapeWrapCreation(self, target, bsNode):
        """ Creates Blendshape duplicates using wrapped target mesh.
        :param target: The mesh to affect with the new blendshapes.
        :param bsNode: The blendshape node to work from.
        :return: None
        """
        bsList = cmds.blendShape(bsNode, q=1, w=1)
        nameList = cmds.listAttr(bsNode + ".w", m=1)
        for i, t in enumerate(bsList):
            if i > 5:
                cmds.blendShape(bsNode, e=1, w=[(i - 1, 0), (i, 1)])
                cmds.duplicate(target, n=nameList[i])


    ##########################
    #
    # GUI Specific Functions
    #
    ##########################


    def cmmIconSaver(self):
        """ Saves custom drawn controller icons to an ICONFILE.
        :return: None
        """
        cCurve = (cmds.ls(sl=1)[0])
        cDegree = cmds.getAttr('%s.degree' % cCurve)
        cSpans = cmds.getAttr('%s.spans' % cCurve)
        cNumCVs = cDegree + cSpans
        cForm = cmds.getAttr('%s.form' % cCurve)
        cCVs = cmds.getAttr('%s.cv[*]' % cCurve)
        cCPs = ''
        for i in cmds.listHistory(cmds.ls(sl=1)[0]):
            if "makeNurbCircle" in i:
                cInfo = cmds.createNode('curveInfo')
                cmds.connectAttr('%s.worldSpace' % cmds.listRelatives(cCurve, s=1)[0], '%s.inputCurve' % cInfo)
                cCPs = cmds.getAttr('%s.cp[*]' % cInfo)

        iconDict = {"name": cCurve, "deg": cDegree, "spans": cSpans, "cvNum": cNumCVs, "cvs": cCVs, "form": cForm}
        if cCPs:
            iconDict["cCPs"] = cCPs

        iconData = {cCurve: iconDict}

        if os.path.exists(myIconFile):
            with open(myIconFile, 'rb') as file:
                currentData = json.load(file)
                print currentData.keys()
                if cCurve in currentData.keys():
                    print "yes"
                    choice = cmds.confirmDialog(
                        m="Icon Name Exists!\n\nConfirm to *OVERWITE* or Close and change name.", ma="center")

                    if choice == 'Confirm':
                        iconData.update(currentData)
                        with open(myIconFile, 'wb') as file:
                            json.dump(iconData, file)
                    else:
                        print 'passed'

                else:
                    print "no"
                    iconData.update(currentData)
                    with open(myIconFile, 'wb') as file:
                        json.dump(iconData, file)

        else:
            with open(myIconFile, 'wb') as file:
                json.dump(iconData, file)

        spacer = "\n------------------------------\n"
        print "%sThe following data was written to file: \n%s%s" % (spacer, iconDict, spacer)

        icons = self.iconListing()
        self.UI.iconList_enum.clear()
        self.UI.iconList_enum.addItems(icons)

    def cmmIconBuilder(self):
        """ Creates an icon using the ICONFILE.
        :return: None
        """
        sender = self.sender().objectName()
        iconName = self.UI.iconList_enum.currentText()
        customName = self.UI.createIcon_txt.text()
        if customName == "":
            customName = iconName
        print iconName
        if sender == "basicIcon_btn":
            print "basic"
            if os.path.exists(myIconFile):
                with open(myIconFile, 'rb') as file:
                    currentData = json.load(file)
                    buildObject = currentData[iconName]
                    print buildObject
                cvs = buildObject['cvs']
                spans = buildObject['spans']
                deg = buildObject['deg']
                ctl = cmds.curve(p=cvs, n=customName + "#", d=deg)
                ctl = cmds.rename(ctl, ctl + "_Ctl")
        elif sender == "controllerIcon_btn":
            print "controller"
            if CMiller_RiggingToolsWin.UI.createIcon_orientRadio.isChecked():
                self.cmmCreateController(name=iconName, type="orient", guiCtl=True, guiName=customName)
            elif CMiller_RiggingToolsWin.UI.createIcon_parentRadio.isChecked():
                self.cmmCreateController(name=iconName, type="parent", guiCtl=True, guiName=customName)
            elif CMiller_RiggingToolsWin.UI.createIcon_pointRadio.isChecked():
                self.cmmCreateController(name=iconName, type="point", guiCtl=True, guiName=customName)

    def guiSplitJoint(self):
        """ GUI command variant of cmmSplitJoint.
        """
        num = self.UI.splitJoints_sb.value()
        chainCheck = self.UI.splitJoints_cb.isChecked()
        self.cmmSplitJoint(numSplits=num,chain=chainCheck)

    def guiCenterJointOnSel(self):
        """ GUI command variant of cmmCenterJointOnSel.
        """
        jntName = CMiller_RiggingToolsWin.UI.createJoints_txt.text()
        hierVal = CMiller_RiggingToolsWin.UI.createJoints_cb.isChecked()
        if jntName == "":
            jntName = "default"
        self.cmmCenterJointOnSel(chain=hierVal, name=jntName)

    def guiFollicleMaker(self):
        """ GUI command variant of cmmFollicleMaker.
        """
        object = CMiller_RiggingToolsWin.UI.createFollicle_txt.text()
        uVal = CMiller_RiggingToolsWin.UI.createFollicle_uVal.value()
        vVal = CMiller_RiggingToolsWin.UI.createFollicle_vVal.value()

        self.cmmFollicleMaker(obj=object, uPos=uVal, vPos=vVal)

    def guiFaceCurves(self):
        """ GUI command variant of cmmFaceCurves.
        """
        guiName = CMiller_RiggingToolsWin.UI.faceCurves_txt.text()
        guiVal = CMiller_RiggingToolsWin.UI.faceCurves_val.value()
        foffVal = CMiller_RiggingToolsWin.UI.faceCurvesFallOff_val.value()
        guiCB = CMiller_RiggingToolsWin.UI.faceCurves_cb.isChecked()
        self.cmmFaceCurves(cp=guiVal, foff=foffVal, cb=guiCB, name=guiName)

    def guiBSListSel(self):
        """ Gets a list of blendshapes on selected object and adds to the gui.
        :return: Blendshape nodes list.
        """
        try:
            selMesh = cmds.ls(sl=1)[0]
            BSNodes = cmds.listConnections(cmds.listHistory(selMesh, future=1), type="blendShape")
            if not BSNodes:
                BSNodes = ["**New**"]
            elif len(BSNodes) > 1:
                BSNodes = list(set(BSNodes))

        except:
            BSNodes = ["**New**"]

        self.UI.createBlendShapes_enum.clear()
        self.UI.createBlendShapes_enum.addItems(BSNodes)
        return BSNodes

    def guiCreateBS(self):
        """ GUI command variant of cmmCreateBS.
        """
        num = self.UI.createBlendShapes_sb.value()
        selMesh = cmds.ls(sl=1)[0]

        connectNode = self.UI.createBlendShapes_enum.currentText()
        newNode = self.UI.createBlendShapesNew_txt.text()


        if connectNode=="**New**":
            if not newNode:
                newNode="%s_BS"%selMesh
            self.cmmCreateBS(mesh=selMesh, numShapes=num, newNode=newNode)
        elif newNode:
            self.cmmCreateBS(mesh=selMesh, numShapes=num, newNode=newNode)
        else:
            self.cmmCreateBS(mesh=selMesh, numShapes=num, connectNode=connectNode)

        BSNodes = self.guiBSListSel()




class CMiller_AnimToolsFuncs(object):
    def __init__(self):
        cmds.selectPref(tso=1)

    def matchPreviousPositionAndKey(self):
        """ Match selection to previous frame's world position and rotation.
        :return: None
        """
        curTime = cmds.currentTime(q=1)
        prevFrame = curTime - 1

        selObjs = cmds.ls(sl=1)

        for obj in selObjs:

            try:
                newSpace = cmds.getAttr("%s.spaceSwitch" % obj)
            except:
                cmds.warning("Object has no key on previous frame. Skipping.")
            keyEx = cmds.keyframe(obj, time=(prevFrame, prevFrame), query=1)
            if keyEx:
                cmds.currentTime(prevFrame, u=1)

                ctlPreT = cmds.xform(obj, q=1, ws=1, rp=1)
                ctlPreR = cmds.xform(obj, q=1, ws=1, ro=1)

                print ctlPreR

                cmds.currentTime(curTime, u=1)

                cmds.setAttr("%s.spaceSwitch" % obj, newSpace)

                cmds.xform(obj, ws=1, t=[ctlPreT[0], ctlPreT[1], ctlPreT[2]])
                cmds.xform(obj, ro=[ctlPreR[0], ctlPreR[1], ctlPreR[2]])

                cmds.setKeyframe(obj)

                print("%s matched and keyed." % obj)


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
            # Fitler out Shift, Control, Alt
            if event.key() in [QtCore.Qt.Key_Shift, QtCore.Qt.Key_Control, QtCore.Qt.Key_Alt, QtCore.Qt.Key_CapsLock,
                               QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter]:
                return True
        else:
            # standard event processing
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


class CMiller_RiggingToolsUI(QtGui.QDialog, CMiller_RiggingToolsFuncs):
    def __init__(self, parent=getMayaWindow()):
        """Initialize the class, load the UI file.
        """
        super(CMiller_RiggingToolsUI, self).__init__(parent)
        self.loader = QtUiTools.QUiLoader(self)
        self.UI = self.loader.load(myFile, self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        icons = self.iconListing()
        self.UI.iconList_enum.addItems(icons)

        addFilter(self.UI)

        self.UI.createBlendShapes_enum.addItems(["**New**"])
        # Connect the elements

        self.UI.splitJoints_btn.clicked.connect(self.guiSplitJoint)
        self.UI.createJoints_btn.clicked.connect(self.guiCenterJointOnSel)
        self.UI.doublePad_btn.clicked.connect(self.cmmOffsetPad)
        self.UI.saveIcon_btn.clicked.connect(self.cmmIconSaver)
        self.UI.basicIcon_btn.clicked.connect(self.cmmIconBuilder)
        self.UI.controllerIcon_btn.clicked.connect(self.cmmIconBuilder)
        self.UI.toggleSkin_btn.clicked.connect(self.toggleSkinClusters)
        self.UI.resetSel_btn.clicked.connect(self.resetSelected)
        self.UI.resetAll_btn.clicked.connect(self.resetCTL)
        self.UI.connectCB_btn.clicked.connect(self.connectChannels)
        self.UI.drawLine_btn.clicked.connect(self.cmmDrawLine)
        self.UI.faceCurves_btn.clicked.connect(self.guiFaceCurves)
        self.UI.createFollicle_btn.clicked.connect(self.guiFollicleMaker)
        self.UI.createBlendShapes_btn.clicked.connect(self.guiCreateBS)
        self.UI.ext_launchSkinUtility_btn.clicked.connect(self.skinSaver)
        # self.UI.loadWorld_btn.clicked.connect(self.loadWorldWeights)
        self.UI.createBlendShapesRefresh_btn.clicked.connect(self.guiBSListSel)
        self.UI.wingSpanMaker_btn.clicked.connect(self.wingSpanMaker)
        #self.UI.connectToCog_btn.clicked.connect(self.fbConnectBsToCog)


        # Show the window
        self.UI.show()

    def iconListing(self):
        """ Lists icons in the ICONFILE.
        :return: Icons list (if they exist).
        """
        if os.path.exists(myIconFile):
            with open(myIconFile, 'rb') as file:
                currentData = json.load(file)
                return currentData.keys()
        else:
            return ""

    def skinSaver(self):
        """ Attempts to load the CMiller_skinSaver
        :return: None
        """
        try:
            import CMiller_skinSaver
            reload(CMiller_skinSaver)
            CMiller_skinSaver.run()
        except:
            pass


def run():
    """Run the UI.
    """
    global CMiller_RiggingToolsWin
    try:
        CMiller_RiggingToolsWin.close()
    except:
        pass
    CMiller_RiggingToolsWin = CMiller_RiggingToolsUI()