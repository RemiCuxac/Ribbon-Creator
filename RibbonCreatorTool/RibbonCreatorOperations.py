import math
from enum import Enum
from typing import Union, List, Tuple, Optional

import maya.cmds as cmds


class KnotType(Enum):
    main = "mainKnot"
    roll = "rollKnot"

    def __str__(self):
        return str(self.value)


class MethodName(Enum):
    posi = "pointOnSurfaceInfo"
    uvPin = "uvPin"

    def __str__(self):
        return str(self.value)


class RibbonOperations:
    selection: list = []  # selected joints
    align: bool = False
    ribbon: str = ""
    ribbonList: list = []
    length: float = 10
    smooth: int = 3
    distances: list = []
    jntRadius: float = 1
    grpRibbon: str = ""
    grpLoc: str = ""
    grpJnt: str = ""
    grpDeform: str = ""

    makeNurbNode: str = ""
    mainKnotNode: str = ""
    rollKnotNode: str = ""
    pinchKnotNode: str = ""
    blendShapeNode: str = ""
    mainIsoPos: tuple = tuple()
    rollIsoPos: tuple = tuple()
    forwardVector: list = []
    upVector: list = []
    orient: list = []

    # networkNode: str = ""
    controlJointsMain: list = []
    controlJointsAll: list = []

    previs_step: bool = False

    @classmethod
    def init_params(cls):
        cls.ribbon: str = ""
        cls.ribbonList: list = []
        cls.length: float = 10
        cls.smooth: int = 3
        cls.distances: list = []
        cls.jntRadius: float = 1
        cls.grpRibbon: str = ""
        cls.grpLoc: str = ""
        cls.grpJnt: str = ""
        cls.grpDeform: str = ""

        cls.makeNurbNode: str = ""
        cls.mainKnotNode: str = ""
        cls.rollKnotNode: str = ""
        cls.pinchKnotNode: str = ""
        cls.blendShapeNode: str = ""
        cls.mainIsoPos: tuple = tuple()
        cls.rollIsoPos: tuple = tuple()
        cls.forwardVector: list = []
        cls.upVector: list = []
        cls.orient: list = []

        # cls.networkNode: str = ""
        cls.controlJointsMain: list = []
        cls.controlJointsAll: list = []
        cls.previs_step: bool = False

    # --------------------------------------------------------
    # ---------------------- GET THINGS ----------------------
    # --------------------------------------------------------
    @classmethod
    def get_selection(cls, pType: Optional[str] = None, pExcludeControlJoints: bool = False) -> List[str]:
        """
        :return: A list containing selected objects
        """
        selection = cmds.ls(selection=True, type=pType) if pType else cmds.ls(selection=True)
        if pExcludeControlJoints:
            if cls.controlJointsAll:
                for jnt in cls.controlJointsAll:
                    if jnt in selection:
                        selection.remove(jnt)
        return selection

    @staticmethod
    def get_distance_node(pObj1: str, pObj2: str) -> str:
        """
        :return: the name of the distance node connected between pObj1 and pObj2
        """
        connections1 = cmds.listConnections(f"{pObj1}.worldMatrix[0]", destination=True, source=False)
        connections2 = cmds.listConnections(f"{pObj2}.worldMatrix[0]", destination=True, source=False)
        if connections1 and connections2:
            commonNodes = list(set(connections1) & set(connections2))  # get items that are both in the two lists
            for node in commonNodes:
                if cmds.objectType(node) == "distanceBetween":
                    return node
        return ""

    @staticmethod
    def get_length_from_list(pDistances: Optional[List[float]] = None) -> float:
        """
        :param pDistances: a list like [3,5] or [4,4,3]
        :return: the sum of each item of the list
        """
        if pDistances is None:
            pDistances = [10]
        return sum(pDistances)

    @staticmethod
    def get_make_nurb_node(pNurbShape: str) -> Union[str, None]:
        """
        :return: the modifier that defines parameters of the nurb plane.
        """
        connections = cmds.listHistory(pNurbShape)
        for c in connections:
            if cmds.objectType(c) == "makeNurbPlane":
                return c
        return None

    @staticmethod
    def get_skin_node(pNurbShape: str) -> Union[str, None]:
        """
        :return: the modifier that defines parameters of the nurb plane.
        """
        connections = cmds.listHistory(pNurbShape)
        for c in connections:
            if cmds.objectType(c) == "skinCluster":
                return c
        return None

    @staticmethod
    def get_shape(pTransform: Union[List[str], str]) -> str:
        """
        :param pTransform: the transform of the shape, or the shape.
        :return: the first shape that is under pTransform.
        """
        if isinstance(pTransform, list):
            pTransform = pTransform[0]
        if cmds.objectType(pTransform, isType="transform"):
            return cmds.listRelatives(pTransform, shapes=True)[0]
        elif cmds.objectType(pTransform, isType="shape"):
            return pTransform
        return ""

    @staticmethod
    def get_knot(pShape: str, pKnotName: KnotType) -> str:
        """
        :return: the modifier
        """
        history = cmds.listHistory(pShape, allConnections=True)
        for a in history:
            if cmds.objectType(a) == "insertKnotSurface":
                if pKnotName in a:
                    return a
        return ""

    @staticmethod
    def get_orientation_from_normalized_vector(pForwardNormVect: list, pUpNormVect: list) -> List[int]:
        orientVect = [0, 0, 0]
        if pForwardNormVect == [1, 0, 0] and pUpNormVect == [0, 1, 0]:
            orientVect = [0, 0, 0]
        if pForwardNormVect == [1, 0, 0] and pUpNormVect == [0, 0, 1]:
            orientVect = [-90, 0, 0]
        if pForwardNormVect == [0, 1, 0] and pUpNormVect == [1, 0, 0]:
            orientVect = [0, 180, -90]
        if pForwardNormVect == [0, 1, 0] and pUpNormVect == [0, 0, 1]:
            orientVect = [0, -90, -90]
        if pForwardNormVect == [0, 0, 1] and pUpNormVect == [1, 0, 0]:
            orientVect = [90, 0, 90]
        if pForwardNormVect == [0, 0, 1] and pUpNormVect == [0, 1, 0]:
            orientVect = [90, 90, 90]
        return orientVect

    @classmethod
    def get_sorted_loc(cls) -> list:
        myDict = {}
        if cls.mainKnotNode:
            outMainKnot = sorted(cmds.listConnections(f"{cls.mainKnotNode}.message", destination=True, source=False))
            for i in range(len(cmds.getAttr(f"{cls.mainKnotNode}.parameter")[0])):
                node = outMainKnot[i + 1]
                param = cmds.getAttr(f"{cls.mainKnotNode}.parameter[{i}]")
                myDict[node] = param
        else:
            outMainKnot = sorted(cmds.listRelatives(f"{cls.ribbon}_grp_loc_main", children=True))
        myDict[outMainKnot[0]] = 0
        myDict[outMainKnot[-1]] = 1

        if cls.rollKnotNode:
            outRollKnot = sorted(cmds.listConnections(f"{cls.rollKnotNode}.message", destination=True, source=False))
            for i in range(len(cmds.getAttr(f"{cls.rollKnotNode}.parameter")[0])):
                node = outRollKnot[i]
                param = cmds.getAttr(f"{cls.rollKnotNode}.parameter[{i}]")
                myDict[node] = param

        return sorted(myDict, key=myDict.get)

    @staticmethod
    def get_or_create_node(pName, pType):
        pass

    @classmethod
    def check_ribbon(cls, pName: str = None, pCheckAll: bool = False) -> bool:
        sel = cmds.ls(pName, f"{pName}_setup") if pName else cmds.ls(cls.ribbon, f"{cls.ribbon}_setup")
        if pCheckAll:
            return True if len(sel) == 2 else False  # checks for all the setup
        else:
            return True if sel else False  # check if pName is already used in one of the two components.

    # ------------------------------------------------------------
    # ---------------------- GENERATE DATAS ----------------------
    # ------------------------------------------------------------
    @staticmethod
    def generate_new_name(pName: str) -> str:
        if pName[-1].isdigit():
            number = int(pName[-1])
            pName = pName[:-1]
        else:
            number = 1
        name = f"{pName}{str(number)}"
        if cmds.ls(f"{name}*"):
            while cmds.ls(f"{name}*"):
                number += 1
                name = f"{pName}{str(number)}"
        return name

    @classmethod
    def generate_distance_list(cls, pSelection: List[str] = None,
                               pLength: float = None,
                               pMainJointCount: int = None) -> List[float]:
        """
        :param pSelection: something like : [jnt_1, jnt_2, jnt_3]
        :param pLength: Optional, used if pSelection is None
        :param pMainJointCount: Optional, used if pSelection is None
        :return: something like [4, 3]
        """
        if pSelection:
            distancesList = []
            for obj in pSelection[:-1]:
                startObj = obj
                endObj = pSelection[pSelection.index(obj) + 1]
                distNode = cls.get_distance_node(startObj, endObj)
                if not distNode:
                    distNode = cls.create_distance_node(startObj, endObj)
                distance = cmds.getAttr(f"{distNode}.distance")
                distancesList.append(distance)
            cmds.select(pSelection)
            return distancesList
        else:
            return [pLength / pMainJointCount for _ in range(pMainJointCount)]

    @staticmethod
    def generate_iso_pos_main(pDistancesList: List[float]) -> Tuple[float, ...]:
        """
        :param pDistancesList: something like [4,3] or [4,4,3]
        :return: the isoparm values between 0 and 1 (excluded). For pDistancesList = [4,4], returns tuple(0.5)
        """
        mainIso = 0
        isoPos = []
        fullLength = 0
        for a in pDistancesList:
            fullLength += a
        for d in list(pDistancesList):
            partLength = d
            mainIso += partLength / fullLength
            isoPos.append(mainIso)
        return tuple(isoPos[:-1])

    @staticmethod
    def generate_iso_pos_full(pIsoPos: Tuple[float]) -> Tuple[float]:
        if pIsoPos:
            if (pIsoPos[0] != 0) and (pIsoPos[-1] != 1):
                fullIsoPos = (0,) + pIsoPos + (1,)
            else:
                fullIsoPos = pIsoPos
        else:
            fullIsoPos = (0, 1)
        return fullIsoPos

    @classmethod
    def generate_iso_pos_roll(cls, pRollCount: int, pIsoPosMain: Tuple[float]) -> Tuple[float, ...]:
        """
        :param pRollCount: the number of roll joint desired per between two main bones.
        :param pIsoPosMain: something like [0.25, 0.75] because main joint is at 0.5...
        :return: the isoparm values between 0 and 1 (excluded). For pDistancesList = [4,4], returns tuple(0.5)
        """
        # result_list = [((input_list[i]+value) / (number+1)) for i, value in enumerate(input_list[1:])]
        # basic result : tuple([b / (bonesCount + 1) for b in range(1, bonesCount + 1)])
        fullIsoPosMain = cls.generate_iso_pos_full(pIsoPosMain)
        result_list = []
        for i, value in enumerate(fullIsoPosMain[1:]):
            incr = 0
            for j in range(1, pRollCount + 1):
                incr += (value - fullIsoPosMain[i]) / (pRollCount + 1)
                sub = fullIsoPosMain[i] + incr
                result_list.append(sub)
        return tuple(result_list)

    @classmethod
    def store_vectors(cls, pForwardVector: list, pUpVector: list) -> None:
        cls.forwardVector = pForwardVector
        cls.upVector = pUpVector
        cls.orient = cls.get_orientation_from_normalized_vector(pForwardVector, pUpVector)

    # -----------------------------------------------------------
    # ---------------------- CREATE THINGS ----------------------
    # -----------------------------------------------------------
    @staticmethod
    def create_distance_node(pObj1: str, pObj2: str) -> str:
        """
        :return: a distance node created between pObj1 and pObj2, which calculate the distance between those 2 objects.
        """
        distNode = cmds.createNode("distanceBetween")
        cmds.connectAttr(f"{pObj1}.worldMatrix[0]", f"{distNode}.inMatrix1")
        cmds.connectAttr(f"{pObj2}.worldMatrix[0]", f"{distNode}.inMatrix2")
        return distNode

    @staticmethod
    def create_nurb(pName: str, pLength: float, pSmoothDeformation: int) -> Tuple[str, str]:
        ribbon, makeNurbNode = cmds.nurbsPlane(name=pName, pivot=[pLength / 2, 0, 0], axis=[0, 0, 1], width=pLength,
                                               lengthRatio=0.1,
                                               degree=pSmoothDeformation, u=1, v=1, constructionHistory=True)
        return ribbon, makeNurbNode

    @classmethod
    def create_deformer(cls, pMainIsoPos, pRollIsoPos, pDeformerType: str, pPinch: bool) -> Tuple[str, str]:
        # TODO: get knotsDeform from pNurbShape and copy them to the new deformNurb below, instead of using pIsoPos ?
        blendShapeName = f"{cls.ribbon}_deformers"
        cls.blendShapeNode = cmds.ls(blendShapeName, type="blendShape")
        if not cls.blendShapeNode:
            cls.blendShapeNode = cmds.blendShape(cls.ribbon, name=blendShapeName, frontOfChain=True)

        grpName = f"{cls.ribbon}_grp_deform"
        cls.grpDeform = cmds.ls(grpName)
        if not cls.grpDeform:
            cls.grpDeform = cmds.group(name=grpName, empty=True)
            cmds.parent(cls.grpDeform, cls.grpRibbon)
            cmds.hide(cls.grpDeform)

        bsCount = cmds.blendShape(cls.blendShapeNode, query=True, weight=1)
        targetIndex = len(bsCount) if bsCount else 0
        deformNurb, knotDeform = cls.create_nurb(f"{cls.ribbon}_{pDeformerType.capitalize()}", cls.length, cls.smooth)
        cls.add_knots(deformNurb, pMainIsoPos, KnotType.main, pPinch)
        cls.add_knots(deformNurb, pRollIsoPos, KnotType.roll, pPinch)
        deformNurbShape = cls.get_shape(deformNurb)
        cmds.blendShape(cls.blendShapeNode, edit=True, target=(cls.ribbon, targetIndex, deformNurbShape, 1),
                        weight=(targetIndex, 1))
        deform, handle = cmds.nonLinear(deformNurbShape, type=pDeformerType)
        newHandleName = f"{cls.ribbon}_{pDeformerType.capitalize()}_handle"
        cmds.rename(handle, newHandleName)
        handle = newHandleName
        cmds.rotate(0, 0, 90, handle)
        cmds.parent(deformNurb, cls.grpDeform)
        cmds.parent(handle, cls.grpDeform)

        # customize a little bit of modifiers
        node = cmds.listConnections(f"{newHandleName}.specifiedManipLocation", destination=False, source=True)[0]
        if "bend" in newHandleName.lower():
            cmds.setAttr(f"{newHandleName}.translate", 0, 0, 0)
            cmds.setAttr(f"{node}.lowBound", -10)
            cmds.setAttr(f"{node}.highBound", 10)
        elif "sine" in newHandleName.lower():
            cmds.setAttr(f"{node}.dropoff", 1)
        # TODO: create a network node that connects main parameters to the node.
        return deform, handle

    @staticmethod
    def add_knots(pShape: str, pIsoPos: tuple, pKnotName: KnotType, pPinch=False) -> Optional[str]:
        """
        Creates a modifier "insertKnotSurface" on the nurb pShape, and add pIsoPos as divisions of the modifier.
        It renames the modifier to be deleted if the function is executed more than once.
        :return: the name of the modifier
        """
        # Delete previous modifier :
        history = cmds.listHistory(pShape, allConnections=True)
        for a in history:
            if cmds.objectType(a) == "insertKnotSurface":
                if (str(KnotType.roll) in a) or (str(pKnotName) in a):
                    cmds.delete(a)  # because there is no way to remove parameters on the know modifier.
        if len(pIsoPos) > 0:
            nbKnots = 3 if pKnotName == KnotType.main and pPinch else 1
            knotDeform = cmds.insertKnotSurface(pShape, constructionHistory=True, parameter=pIsoPos,
                                                numberOfKnots=nbKnots, direction=1, replaceOriginal=True)[-1]
            newName = cmds.rename(knotDeform, pKnotName)
            return newName
        return None

    @classmethod
    def update_follicles(cls, pIsoPos: Tuple[float], pKnotNode: str, pType: KnotType,
                         pMethod: MethodName = MethodName.uvPin) -> None:
        if pType == KnotType.main:
            pIsoPos = cls.generate_iso_pos_full(pIsoPos)
        typeName = str(pType).lower().split("knot")[0]
        grpName = f"{cls.ribbon}_grp_loc_{typeName}"
        if cmds.ls(grpName):
            cmds.delete(grpName)

        grpLoc = cmds.group(name=grpName, empty=True)
        cmds.parent(grpLoc, cls.grpLoc)
        for i, v in enumerate(pIsoPos):
            loc = cmds.spaceLocator(name=f"loc_foll_{cls.ribbon}_{typeName}_{i:02d}", absolute=True)
            locTrs = loc[0]
            locShape = cmds.listRelatives(locTrs, shapes=True)[0]
            cmds.parent(loc, grpLoc)
            jointLoc = cmds.joint(name=f"jnt_skin_{cls.ribbon}_{typeName}_{i:02d}", orientation=cls.orient,
                                  radius=cls.jntRadius)  # it automatically parents itself to the loc previously created
            ctrlExtra = cmds.circle(name=f"ctrl_extra_{cls.ribbon}_{typeName}_{i:02d}", center=[0, 0, 0],
                                    normal=cls.forwardVector, constructionHistory=False)[0]
            # rotate the ctrl
            ctrlMatrix = cmds.matrixUtil(r=map(math.radians, cls.orient))
            cmds.setAttr(f"{ctrlExtra}.offsetParentMatrix", ctrlMatrix, type="matrix")

            cmds.parent(jointLoc, ctrlExtra)
            cmds.parent(ctrlExtra, locTrs)

            dm = cmds.createNode("decomposeMatrix")
            cmds.setAttr(f"{dm}.isHistoricallyInteresting", 0)
            cfsi = cmds.createNode("curveFromSurfaceIso")
            cmds.setAttr(f"{cfsi}.isHistoricallyInteresting", 0)
            ci = cmds.createNode("curveInfo")
            cmds.setAttr(f"{ci}.isHistoricallyInteresting", 0)

            if pMethod == MethodName.uvPin:
                uvPin = cmds.createNode("uvPin")
                cmds.setAttr(f"{uvPin}.isHistoricallyInteresting", 0)
                if 0 < v < 1:
                    index = i - 1 if pType == KnotType.main else i
                    cmds.connectAttr(f"{pKnotNode}.parameter[{index}]", f"{uvPin}.coordinate[0].coordinateU")
                    cmds.connectAttr(f"{pKnotNode}.parameter[{index}]", f"{cfsi}.isoparmValue")
                else:
                    cmds.setAttr(f"{uvPin}.coordinate[0].coordinateU", v)
                    cmds.setAttr(f"{cfsi}.isoparmValue", v)

                cmds.connectAttr(f"{cls.ribbon}.worldSpace[0]", f"{uvPin}.deformedGeometry")
                cmds.connectAttr(f"{uvPin}.outputMatrix[0]", f"{dm}.inputMatrix")
                cmds.setAttr(f"{uvPin}.normalAxis", 2)  # Z axis
                cmds.setAttr(f"{uvPin}.tangentAxis", 0)  # X axis
                cmds.setAttr(f"{uvPin}.coordinate[0].coordinateV", 0.5)

            elif pMethod == MethodName.posi:
                posi = cmds.createNode("pointOnSurfaceInfo")
                cmds.setAttr(f"{posi}.isHistoricallyInteresting", 0)
                fbfm = cmds.createNode("fourByFourMatrix")
                cmds.setAttr(f"{fbfm}.isHistoricallyInteresting", 0)
                if 0 < v < 1:
                    index = i - 1 if pType == KnotType.main else i
                    cmds.connectAttr(f"{pKnotNode}.parameter[{index}]", f"{posi}.parameterU")
                    cmds.connectAttr(f"{pKnotNode}.parameter[{index}]", f"{cfsi}.isoparmValue")
                else:
                    cmds.setAttr(f"{posi}.parameterU", v)
                    cmds.setAttr(f"{cfsi}.isoparmValue", v)
                cmds.connectAttr(f"{cls.ribbon}.worldSpace[0]", f"{posi}.inputSurface")
                cmds.connectAttr(f"{posi}.positionX", f"{fbfm}.in30")
                cmds.connectAttr(f"{posi}.positionY", f"{fbfm}.in31")
                cmds.connectAttr(f"{posi}.positionZ", f"{fbfm}.in32")
                cmds.connectAttr(f"{posi}.normalizedNormalX", f"{fbfm}.in20")
                cmds.connectAttr(f"{posi}.normalizedNormalY", f"{fbfm}.in21")
                cmds.connectAttr(f"{posi}.normalizedNormalZ", f"{fbfm}.in22")
                cmds.connectAttr(f"{posi}.normalizedTangentUX", f"{fbfm}.in00")
                cmds.connectAttr(f"{posi}.normalizedTangentUY", f"{fbfm}.in01")
                cmds.connectAttr(f"{posi}.normalizedTangentUZ", f"{fbfm}.in02")
                cmds.connectAttr(f"{posi}.normalizedTangentVX", f"{fbfm}.in10")
                cmds.connectAttr(f"{posi}.normalizedTangentVY", f"{fbfm}.in11")
                cmds.connectAttr(f"{posi}.normalizedTangentVZ", f"{fbfm}.in12")
                cmds.setAttr(f"{posi}.parameterV", 0.5)
                cmds.connectAttr(f"{fbfm}.output", f"{dm}.inputMatrix")

            cmds.connectAttr(f"{dm}.outputRotate", f"{locTrs}.rotate")
            cmds.connectAttr(f"{dm}.outputTranslate", f"{locTrs}.translate")

            cmds.connectAttr(f"{cls.ribbon}.worldSpace[0]", f"{cfsi}.inputSurface")
            cmds.connectAttr(f"{cfsi}.outputCurve", f"{ci}.inputCurve")

            md1 = cmds.createNode("multiplyDivide")
            cmds.setAttr(f"{md1}.isHistoricallyInteresting", 0)
            cmds.connectAttr(f"{ci}.arcLength", f"{md1}.input1X")
            cmds.connectAttr(f"{cls.makeNurbNode}.width", f"{md1}.input2X")
            cmds.setAttr(f"{md1}.operation", 2)
            md2 = cmds.createNode("multiplyDivide")
            cmds.setAttr(f"{md2}.isHistoricallyInteresting", 0)
            cmds.connectAttr(f"{md1}.outputX", f"{md2}.input1X")
            cmds.setAttr(f"{md2}.input2X", 10)
            cmds.connectAttr(f"{md2}.outputX", f"{locTrs}.scaleX")
            cmds.connectAttr(f"{md2}.outputX", f"{locTrs}.scaleY")
            cmds.connectAttr(f"{md2}.outputX", f"{locTrs}.scaleZ")

            cmds.setAttr(f"{cfsi}.isoparmDirection", 1)
            cmds.setAttr(f"{locShape}.visibility", False)

            # setup message connection from knot to locators
            if pKnotNode:
                cmds.connectAttr(f"{pKnotNode}.message", f"{locTrs}.creator")

            cmds.setAttr(f"{jointLoc}.overrideEnabled", True)
            cmds.setAttr(f"{jointLoc}.overrideColor", 18)  # CYAN

    @classmethod
    def update_control_joint(cls, pCreateControlJoints: bool, pIsChain: bool, pSkinChain: bool):
        if cls.previs_step:
            grpName = f"{cls.ribbon}_grp_control"
            if cmds.ls(grpName):
                cmds.delete(grpName)
            if pCreateControlJoints:
                jntGrp = cmds.group(name=grpName, empty=True)
                cmds.parent(jntGrp, cls.grpJnt)

                cls.controlJointsMain.clear()
                cls.controlJointsAll.clear()

                locators = cls.get_sorted_loc()
                indexMain = 0
                indexRoll = 0
                prevMain = jntGrp
                for i, loc in enumerate(locators):
                    if "main" in loc and i != 0:
                        indexMain += 1
                        indexRoll = 0
                    translate = cmds.xform(loc, query=True, translation=True, worldSpace=True)
                    if i == 0:
                        rotate = cls.orient
                    else:
                        rotate = cmds.xform(loc, query=True, rotation=True, worldSpace=True)
                    jnt = cmds.joint(name=f"jnt_ctrl_{cls.ribbon}_{indexMain:02d}_{indexRoll:02d}", orientation=rotate,
                                     position=translate, radius=cls.jntRadius + 0.5)
                    cmds.setAttr(f"{jnt}.overrideEnabled", True)
                    cmds.setAttr(f"{jnt}.overrideColor", 17)  # YELLOW
                    if prevMain not in cmds.listRelatives(jnt, parent=True):
                        cmds.parent(jnt, prevMain)
                    if "main" in loc:
                        if pIsChain:
                            prevMain = jnt
                        cls.controlJointsMain.append(jnt)
                    cls.controlJointsAll.append(jnt)
                    indexRoll += 1
                    if not pIsChain:
                        if cmds.listRelatives(jnt, parent=True) != [jntGrp]:
                            cmds.parent(jnt, jntGrp)
                if pSkinChain:
                    cls.update_skin()
                else:
                    cls.unbind_skin(cls.ribbon)
                return cls.controlJointsMain

    @classmethod
    def update_skin(cls) -> Union[str, None]:
        if cls.ribbon:
            if cls.controlJointsMain:
                # method1 : unbind and re-bind all
                # cls.unbind_skin(cls.ribbon)
                # skin = cmds.skinCluster(cls.controlJointsAll, cls.ribbon, maximumInfluences=3)[0]

                # method2: find skin, add new joints, update dagPose
                skin = cls.get_skin_node(cls.ribbon)
                if not skin:
                    skin = cmds.skinCluster(cls.controlJointsAll, cls.ribbon, maximumInfluences=3)[0]
                else:
                    dp = cmds.dagPose(cls.controlJointsAll[0], query=True,
                                      bindPose=True)  # maybe there is a better way to get the dagPose
                    # cmds.delete(dp)
                    # cmds.dagPose(cls.controlJointsAll, save=True, bindPose=True)
                    # cmds.bindSkin(cls.controlJointsAll, enable=False)  # deactivate skin to allow moving joints
                    for jnt in cls.controlJointsAll:
                        try:
                            cmds.skinCluster(skin, edit=True, addInfluence=jnt)
                            cmds.dagPose(jnt, name=dp, addToPose=True)
                        except RuntimeError:
                            pass

                jntDataPos = [(jnt, cmds.xform(jnt, query=True, worldSpace=True, translation=True)[0]) for jnt in
                              cls.controlJointsAll]
                nurbCVs = cmds.ls(f'{cls.ribbon}.cv[:][:]', flatten=True)  # Get all cvs from curve
                jointIndex = 0
                for cv in nurbCVs:
                    xPosU = cmds.xform(cv, worldSpace=True, query=True, translation=True)[
                        0]  # We extract tX to determine if control vertex are before or after the position of the joint
                    jnt, jntPos = jntDataPos[jointIndex]
                    nextJnt, nextJntPos = jntDataPos[jointIndex + 1]
                    if xPosU + 0.001 < nextJntPos:
                        jntToSkin = jnt
                    else:
                        jntToSkin = nextJnt
                        if jointIndex + 1 < len(jntDataPos) - 1:
                            jointIndex += 1
                    cmds.skinPercent(skin, cv, transformValue=[(jntToSkin, 1)])

                # uSpans = cmds.getAttr(cls.ribbon + ".spansU")
                # vSpans = cmds.getAttr(cls.ribbon + ".spansV")
                # degree = cmds.getAttr(cls.ribbon + ".degreeU")
                # uCount = uSpans + degree
                # vCount = vSpans + degree

                cmds.setAttr(f"{skin}.skinningMethod", 1)  # set to dual quaternion to reduce stretching
                # cmds.bindSkin(cls.controlJointsAll, enable=True)

                return skin
            return None
        return None

    @classmethod
    def update_main_iso(cls, pMainJointCount: int, pRollJointCount: int,
                        pCreateControlJoints: bool, pCreateChain: bool, pSkinChain: bool) -> None:

        cls.distances = cls.generate_distance_list(cls.selection, cls.length, pMainJointCount)
        cls.mainIsoPos = cls.generate_iso_pos_main(cls.distances)
        cls.mainKnotNode = cls.add_knots(cls.ribbon, cls.mainIsoPos, KnotType.main, pCreateChain)
        cls.update_follicles(cls.mainIsoPos, cls.mainKnotNode, KnotType.main)
        cls.update_roll_iso(pRollJointCount, pCreateChain, pCreateControlJoints, pSkinChain)

    @classmethod
    def update_roll_iso(cls, pRollJointCount: int, pIsChain: bool,
                        pCreateControlJoints: bool,
                        pSkinChain: bool) -> None:
        cls.rollIsoPos = cls.generate_iso_pos_roll(pRollJointCount, cls.mainIsoPos)
        cls.rollKnotNode = cls.add_knots(cls.ribbon, cls.rollIsoPos, KnotType.roll)
        cls.update_follicles(cls.rollIsoPos, cls.rollKnotNode, KnotType.roll)
        cls.controlJointsMain = cls.update_control_joint(pCreateControlJoints, pIsChain, pSkinChain)
        cls.end_step(False, True)

    @classmethod
    def update_length(cls, pLength: float) -> None:
        skin = cls.get_skin_node(cls.ribbon)

        if skin:
            cmds.setAttr(f"{skin}.envelope", 0)

        cls.length = pLength
        for ribbon in cls.ribbonList:
            makeNurbNode = cls.get_make_nurb_node(ribbon)
            cmds.setAttr(f"{makeNurbNode}.width", cls.length)
            cmds.setAttr(f"{makeNurbNode}.pivot", cls.length / 2, 0, 0)
        if cls.controlJointsAll:
            locators = cls.get_sorted_loc()
            for i, (loc, jnt) in enumerate(zip(locators, cls.controlJointsAll)):
                matrix = cmds.xform(loc, query=True, translation=True, worldSpace=True)
                cmds.xform(jnt, translation=matrix, worldSpace=True)
                invMatrix = cmds.getAttr(f"{jnt}.worldInverseMatrix")
                cmds.setAttr(f"{skin}.bindPreMatrix[{i}]", invMatrix, type="matrix")

        if skin:
            cmds.setAttr(f"{skin}.envelope", 1)

        cls.end_step(False, True)

    @classmethod
    def unbind_skin(cls, pShape):
        skin = cls.get_skin_node(pShape)
        if skin:
            cmds.skinCluster(skin, edit=True, unbind=True)

    @classmethod
    def match_selected(cls, pSelection: list) -> None:
        for source, target in zip(cls.controlJointsMain, pSelection):
            cmds.matchTransform(source, target)

    @classmethod
    def reset_control_joints_transform(cls) -> None:
        if cls.controlJointsMain and cls.distances:
            distIter = 0
            for jnt, dist in zip(cls.controlJointsMain, cls.distances):
                cmds.xform(jnt, worldSpace=True, translation=[distIter, 0, 0])
                cmds.xform(jnt, worldSpace=True, rotation=[0, 0, 0])
                distIter += dist

    @classmethod
    def restore_selection(cls):
        if cls.selection:
            if cls.align:
                cls.match_selected(cls.selection)
            cmds.select(cls.selection)
        else:
            cmds.select(clear=True)

    @classmethod
    def delete_history(cls) -> None:
        cmds.bakePartialHistory(cls.ribbon, prePostDeformers=True)

    @classmethod
    def delete_ribbon(cls, pRibbonName: str) -> None:
        cmds.delete(cls.grpRibbon)
        cmds.delete(f"{pRibbonName}")
        cls.previs_step = False

    @classmethod
    def previs_ribbon(cls,
                      pName: str,
                      pForwardVector: list,
                      pUpVector: list,
                      pLength: float,
                      pMainJointCount: int,
                      pRollJointCount: int,
                      pCreateControlJoints: bool,
                      pSkinChain: bool,
                      pCreateChain: bool,
                      pShowPopup: bool = True) -> str:
        cls.init_params()
        cls.selection = cls.get_selection("joint", True)
        cls.previs_step = True
        cls.store_vectors(pForwardVector, pUpVector)
        cls.length = pLength
        cls.ribbon, cls.makeNurbNode = cls.create_nurb(pName, pLength, cls.smooth)
        cls.ribbonList.append(cls.ribbon)
        cls.grpRibbon = cmds.group(name=f"{cls.ribbon}_setup", empty=True)
        cls.grpLoc = cmds.group(name=f"{cls.ribbon}_grp_loc", empty=True, parent=cls.grpRibbon)
        cls.grpJnt = cmds.group(name=f"{cls.ribbon}_grp_jnt", empty=True, parent=cls.grpRibbon)
        cls.update_main_iso(pMainJointCount, pRollJointCount, pCreateControlJoints,
                            pCreateChain, pSkinChain)
        message = cls.end_step(pShowPopup, True)
        return message

    @classmethod
    def build_ribbon(cls, *args, **kwargs) -> str:
        if cls.previs_step is False:
            cls.previs_ribbon(*args, pShowPopup=False)

        # build deformers
        for param, value in kwargs.items():
            if param.lower() in ["sine", "twist", "flare", "bend"] and value:
                cls.create_deformer(cls.mainIsoPos, cls.rollIsoPos, param, kwargs["pCreateChain"])

        message = cls.end_step(True, False)
        return message

    @classmethod
    def end_step(cls, pShowPopup: bool, pPreBuildStep: bool = "") -> Optional[str]:
        cls.restore_selection()
        if pShowPopup:
            if pPreBuildStep:
                message = "You can now adjust parameters and click 'Build' when it looks good."
            else:
                message = "\N{Party Popper} Enjoy ! \N{Party Popper}"
            return message
