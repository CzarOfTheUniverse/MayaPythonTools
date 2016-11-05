"""
~ Weight Jumper Tool ~ Christopher M. Miller ~ 2016/10/25

Small utility for quickly transferring weights between influences.
Originally used to fix skin weighted to IK instead of Bind joints.
Additionally allows weight transfer via selected vertices.

Written and maintained by Christopher M. Miller



v.1 Initial Release to transfer weight values as command line.

-- To Do --
    1. GUI for easier interaction.

"""



import maya.OpenMaya as om
import maya.OpenMayaAnim as omAnim
from maya import cmds

def weightJumper(skin,jointSource="",jointTarget="",selVerts=False):
    """

    :param skin: The skinCluster to affect.
    :param jointSource: Influence currently holding the weight values.
    :param jointTarget: Influence where the weights will be transferred (added) to.
    :param selVerts: Boolean for transferring entire influence or only affecting selected vertices.
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
    bigOldWeightList = [x + y for x, y in zip(jointSourceWeights, jointDestWeights)]

    for i in xrange(len(jointDestWeights)):
        jointTargetFinalWeights.set(bigOldWeightList[i],i)

    jointSourceNewWeights = om.MDoubleArray(len(jointDestWeights))

    # Set new weights
    skinClusterNode.setWeights(skinPath,finalComponents,myInflArray,jointTargetFinalWeights,False)
    skinClusterNode.setWeights(skinPath,finalComponents,myOtherInflArray,jointSourceNewWeights,False)

    cmds.setAttr("%s.normalizeWeights"%skin,normalVal)