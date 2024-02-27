import traceback

import maya.mel as mel
import shutil
import os
import maya.cmds as cmds


def onMayaDroppedPythonFile(*args, **kwargs):
    try:
        currentParent = os.path.abspath(os.path.dirname(__file__))
        scriptFolder = cmds.internalVar(userScriptDir=True)
        ribbonFolder = os.path.join(scriptFolder, "RibbonCreatorTool")
        if not os.path.exists(ribbonFolder):
            os.makedirs(ribbonFolder)
        for file in os.listdir(currentParent):
            filePath = os.path.join(currentParent, file)
            if os.path.isfile(filePath) and "drag" not in file.lower():
                shutil.copy(filePath, ribbonFolder)

        nameExport = 'RG'
        tooltipRibbon = 'Ribbon Creator Tool'
        commandRibbon = "from RibbonCreatorTool import RibbonCreator as rg\n"\
                        "from importlib import reload\n"\
                        "reload(rg)\n"\
                        "rg.show_ui()"

        # Add to current shelf
        topShelf = mel.eval('$nul = $gShelfTopLevel')
        currentShelf = cmds.tabLayout(topShelf, q=1, st=1)
        logoPath = os.path.join(ribbonFolder, "RibbonCreator.png")
        if not os.path.exists(logoPath):
            raise Exception("logo path not found")
        cmds.shelfButton(parent=currentShelf, i=logoPath, c=commandRibbon, imageOverlayLabel=nameExport,
                         annotation=tooltipRibbon)
        cmds.confirmDialog(message=f"Success ! \nYou can see the ribbon tool button in the shelf: \n{currentShelf}",
                           icon="information", title="Success")
    except Exception as e:
        cmds.confirmDialog(message=f"Script failed to install: \n{e}", icon="warning", title="ERROR")
        cmds.warning(traceback.print_exception(e))
