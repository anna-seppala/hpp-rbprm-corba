from PythonQt import QtGui, Qt, QtCore
from gepetto.corbaserver import Client
from hpp.corbaserver.rbprm import Client as rbprmClient
from hpp.corbaserver import Client as basicClient
from hpp.corbaserver.affordance import Client as affClient
from hpp.corbaserver.rbprm.rbprmbuilder import Builder
from hpp.corbaserver.rbprm.rbprmfullbody import FullBody
from hpp.corbaserver.rbprm.problem_solver import ProblemSolver
from hpp.gepetto import Viewer

### This class represents one special tab of the new QDockWidget
class _RbprmInterp (QtGui.QWidget):
    def __init__(self, parent, plugin):
        super(_RbprmInterp, self).__init__ (parent)
        self.plugin = plugin
        self.plugin.chooseWithMouse = False
        self.initConfigSet = False
        self.plugin.SO3bounds = [1,0,1,0,1,0]
        self.configs = []
        vbox = QtGui.QVBoxLayout(self)
        robotLabel = QtGui.QLabel("Set up rbprm models:")
        vbox.addWidget(robotLabel)
        vbox.addWidget(self.addWidgetsInHBox([self.bindFunctionToButton("Load full-body model",\
                self.Fullbody), self.bindFunctionToButton("Load limb models", self.Limb)]))
        vbox.addWidget(self.addWidgetsInHBox([self.bindFunctionToButton("Compute contact sequence",\
                self.computeContacts), self.bindFunctionToButton("Panic!",self.addToViewer)]))
        self.slider = QtGui.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(10)
        self.slider.setValue(1)
        self.slider.setTickInterval(1)
        vbox.addWidget(self.slider)

        self.clickTick = QtGui.QCheckBox("Choose with mouse")
        self.slider.valueChanged.connect(self.draw)

        self.clickTick.clicked.connect(self.setChooseWithMouse)
        #TODO: add tree element to show current set init and goal configs?
        self.update ()

    def update(self):
        self.slider.setMaximum(len(self.configs)-1)
        
    def addWidgetsInHBox(self, widgets):
        nameParentW = QtGui.QWidget(self)
        hboxName = QtGui.QHBoxLayout(nameParentW)
        for w in widgets:
            hboxName.addWidget(w)
        return nameParentW

    def bindFunctionToButton (self, buttonLabel, func):
        button = QtGui.QPushButton(self)
        button.text = buttonLabel
        button.connect ('clicked()', func)
        return button

    def Fullbody (self):
        self.fbdialog = _FullBodyDialog()
        if self.fbdialog.exec_():
            name = str(self.fbdialog.Envname.text)
            packageName = str(self.fbdialog.pkgName.text)
            urdfName =  str(self.fbdialog.urdfName.text)
            meshPackageName = str(self.fbdialog.mpkgName.text)
            rootJointType = str(self.fbdialog.rootJoint.currentText)
            urdfSuffix = str(self.fbdialog.urdfSuf.text)
            srdfSuffix = str(self.fbdialog.srdfSuf.text)
            self.plugin.fullbody.loadFullBodyModel (urdfName, rootJointType,\
                    meshPackageName, packageName, urdfSuffix, srdfSuffix)
            self.addToViewer()
        self.update()

    def Limb (self):
        self.limbdialog = _LimbDialog()
        if self.limbdialog.exec_():
            tabs = self.limbdialog.tabs
            self.legIds = []
            for tab in tabs:
                legId = str(tab.legId.text)
                self.legIds.append(legId)
                cType = str(tab.cType.currentText)
                leg = str(tab.leg.text)
                foot = str(tab.foot.text)
                offset = self.str2float(str(tab.offset.text))
                normal = self.str2float(str(tab.normal.text))
                legxlegy = self.str2float(str(tab.legxlegy.text))
                nbSamples = int(tab.nbSamples.value)
                heuristic = str(tab.heur.currentText)
                resolution = float(tab.res.value)
                self.plugin.fullbody.addLimb(legId,leg,foot,offset,normal, legxlegy[0],\
                        legxlegy[1], nbSamples, heuristic, resolution, cType)
        self.update()

    def computeContacts (self):
        q_init = self.plugin.fullbody.getCurrentConfig()
        q_init[0:7] = self.plugin.rbprmPath.q_init[0:7]
        q_goal = self.plugin.fullbody.getCurrentConfig();
        q_goal[0:7] = self.plugin.rbprmPath.q_goal[0:7]
        self.plugin.fullbody.setCurrentConfig (q_init)
        self.q_init = self.plugin.fullbody.generateContacts(q_init, [0,0,1])
        self.plugin.fullbody.setCurrentConfig (q_goal)
        self.q_goal = self.plugin.fullbody.generateContacts(q_goal, [0,0,1])
        self.plugin.fullbody.setStartState(q_init,[])
        self.plugin.fullbody.setEndState(q_goal,self.legIds)
        self.r(q_init)
        self.configs = self.plugin.fullbody.interpolate(0.1, 1, 0)
        self.update()

    def addToViewer (self):
        self.ps = ProblemSolver(self.plugin.fullbody)
        self.r = Viewer(self.ps)

    def str2float (self,text):
        str1 = str(text).replace(" ", "")
        str2 = str1.split(',')
        flist = []
        for s in str2:
            flist.append(float(s))
        return flist
    
    def draw(self, i):
        if len(self.configs) > 0:
            config = self.configs[i]
            self.plugin.fullbody.draw(config, self.r)

    def showConfig(self):
        if str(self.configCombo.currentText) == 'initial':
            q = self.str2float(self.initq.text)
        else:
            q = self.str2float(self.goalq.text)
        if len(q) == self.plugin.basicClient.robot.getConfigSize():
            self.r (q)
        self.update()

    def setChooseWithMouse (self):
        self.plugin.chooseWithMouse = True




### This class represents one special tab of the new QDockWidget
class _RbprmPath (QtGui.QWidget):
    def __init__(self, parent, plugin):
        super(_RbprmPath, self).__init__ (parent)
        self.plugin = plugin
        self.plugin.chooseWithMouse = False
        self.initConfigSet = False
        self.plugin.SO3bounds = [1,0,1,0,1,0]
        self.q_init = [0,0,0,1,0,0,0]
        self.q_goal = [0,0,0,1,0,0,0]
        vbox = QtGui.QVBoxLayout(self)
        robotLabel = QtGui.QLabel("Set up rbprm models:")
        vbox.addWidget(robotLabel)
        vbox.addWidget(self.addWidgetsInHBox([self.bindFunctionToButton("Load ROM robot",\
                self.Robot), self.bindFunctionToButton("Load environment", self.Environment)]))
        filterLabel = QtGui.QLabel("Add filters:")
        vbox.addWidget(filterLabel)
        self.ROMlist = QtGui.QListWidget()
        self.ROMlist.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        filterLabel2 = QtGui.QLabel("Choose ROM:")
        self.ROMfilterList = QtGui.QListWidget()
        filterLabel3 = QtGui.QLabel("Existing filters:")
      #  vbox.addWidget(self.addWidgetsInHBox([filterLabel2,filterLabel3]))
        vbox.addWidget(self.addWidgetsInHBox([self.ROMlist, self.bindFunctionToButton("Add",\
                self.addFilter), self.ROMfilterList]))
        filterLabel = QtGui.QLabel("Add affordance filters:")
        vbox.addWidget(filterLabel)
        self.ROMaffList = QtGui.QListWidget()
        self.ROMaffList.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.ROMaffFilterList = QtGui.QTreeWidget()
        filterLabel4 = QtGui.QLabel("Choose ROM")
        filterLabel5 = QtGui.QLabel("Existing affordance filters:")
        self.affTypeList = QtGui.QListWidget()
        self.affTypeList.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
      #  vbox.addWidget(self.addWidgetsInHBox([filterLabel4,filterLabel5]))
        vbox.addWidget(self.addWidgetsInHBox([self.ROMaffList, self.affTypeList,\
                self.bindFunctionToButton("Add",\
                self.addAffFilter), self.ROMaffFilterList]))
        vbox.addWidget(self.addWidgetsInHBox([self.bindFunctionToButton("Set joint bounds",\
                self.JointBounds), self.bindFunctionToButton("Panic!",self.addToViewer)]))

        self.showTick = QtGui.QCheckBox("Show configuration")
        self.clickTick = QtGui.QCheckBox("Choose with mouse")
        self.configCombo = QtGui.QComboBox()
        self.configCombo.addItem("initial")
        self.configCombo.addItem("goal")
        initLabel = QtGui.QLabel("initial:")
        goalLabel = QtGui.QLabel("goal:")
        self.initq = QtGui.QLineEdit()
        self.goalq = QtGui.QLineEdit()
        vbox.addWidget(self.addWidgetsInHBox([self.clickTick, self.configCombo,\
                self.bindFunctionToButton("Add",self.addConfig),\
                self.bindFunctionToButton("Clear",self.clearConfigs),\
                self.bindFunctionToButton("Reset",self.resetConfigs)]))
        vbox.addWidget(self.addWidgetsInHBox([initLabel, self.initq, goalLabel, self.goalq]))
        self.configTree = QtGui.QTreeWidget()

        self.groupbox = QtGui.QGroupBox()
        self.grid2 = QtGui.QGridLayout(self.groupbox)
        self.grid2.setSpacing(10)
        self.spinx = QtGui.QDoubleSpinBox ()
        self.spiny = QtGui.QDoubleSpinBox ()
        self.spinz = QtGui.QDoubleSpinBox ()
        self.spinx.setRange(-10,10)
        self.spiny.setRange(-10,10)
        self.spinz.setRange(-10,10)
        label1 = QtGui.QLabel("x")
        label2 = QtGui.QLabel("y")
        label3 = QtGui.QLabel("z")
        self.spinx.setSingleStep (0.01)
        self.spiny.setSingleStep (0.01)
        self.spinz.setSingleStep (0.01)
        self.grid2.addWidget (label1,0,0)
        self.grid2.addWidget (self.spinx,0,1)
        self.grid2.addWidget (label2,1,0)
        self.grid2.addWidget (self.spiny,1,1)
        self.grid2.addWidget (label3,2,0)
        self.grid2.addWidget (self.spinz,2,1)

        vbox.addWidget(self.addWidgetsInHBox([self.configTree, self.groupbox]))

        self.clickTick.clicked.connect(self.setChooseWithMouse)
        self.spinx.valueChanged.connect(lambda: self.setConfigPos(self.spinx.value, 0))
        self.spiny.valueChanged.connect(lambda: self.setConfigPos(self.spiny.value, 1))
        self.spinz.valueChanged.connect(lambda: self.setConfigPos(self.spinz.value, 2))

        #TODO: add tree element to show current set init and goal configs?
        self.resetConfigs() # --> calls self.update()
        #self.update ()

    def update(self):
        self.ROMlist.clear()
        self.ROMaffList.clear()
        self.ROMaffFilterList.clear()
        ROMnames = self.plugin.rbprmClient.rbprm.getROMnames ()
        for name in ROMnames:
            self.ROMlist.addItem (name)
            self.ROMaffList.addItem (name)
            afffilters = self.plugin.rbprmClient.rbprm.getAffordanceFilter(name)
            if (len(afffilters) > 0):
                item = QtGui.QTreeWidgetItem()
                item.setText(0,name)
                for affi in afffilters:
                    child = QtGui.QTreeWidgetItem()
                    child.setText(0,affi)
                    item.addChild(child)
                self.ROMaffFilterList.addTopLevelItem(item)
                self.ROMaffFilterList.expandItem(item)
        self.ROMfilterList.clear()
        filters = self.plugin.rbprmClient.rbprm.getFilter ()
        for fi in filters:
            self.ROMfilterList.addItem(fi)
        self.affTypeList.clear()
        affs = self.getAffordanceConfigTypes ()
        for aff in affs:
            self.affTypeList.addItem(aff)
        self.configTree.clear()
        if (self.initConfigSet):
            item = QtGui.QTreeWidgetItem()
            item.setText(0,"initial")
            iq = self.plugin.basicClient.problem.getInitialConfig()    
            child = QtGui.QTreeWidgetItem()
            child.setText(0,str(iq))
            item.addChild(child)
            self.configTree.addTopLevelItem(item)
            self.configTree.expandItem(item)
        gqs = self.plugin.basicClient.problem.getGoalConfigs()
        if (len(gqs) > 0):
            item = QtGui.QTreeWidgetItem()
            item.setText(0,"goal")
            for gq in gqs:
                child = QtGui.QTreeWidgetItem()
                child.setText(0,str(gq))
                item.addChild(child)
            self.configTree.addTopLevelItem(item)
            self.configTree.expandItem(item)
        
    def addWidgetsInHBox(self, widgets):
        nameParentW = QtGui.QWidget(self)
        hboxName = QtGui.QHBoxLayout(nameParentW)
        for w in widgets:
            hboxName.addWidget(w)
        return nameParentW

    def bindFunctionToButton (self, buttonLabel, func):
        button = QtGui.QPushButton(self)
        button.text = buttonLabel
        button.connect ('clicked()', func)
        return button

    def Robot (self):
        self.robotdialog = _RobotDialog()
        if self.robotdialog.exec_():
            name = str(self.robotdialog.Envname.text)
            packageName = str(self.robotdialog.pkgName.text)
            urdfName =  str(self.robotdialog.urdfName.text)
            meshPackageName = str(self.robotdialog.mpkgName.text)
            urdfROMs = str(self.robotdialog.urdfromName.text)
            urdfROMs = urdfROMs.replace(" ", "")
            urdfNameRom = urdfROMs.split(',')
            rootJointType = str(self.robotdialog.rootJoint.currentText)
            urdfSuffix = str(self.robotdialog.urdfSuf.text)
            srdfSuffix = str(self.robotdialog.srdfSuf.text)
            self.plugin.builder.loadModel(urdfName, urdfNameRom, rootJointType, \
                    meshPackageName, packageName, urdfSuffix, srdfSuffix)
            self.addToViewer()
        self.update()

    def Environment (self):
        self.envdialog = _EnvDialog()
        if self.envdialog.exec_():
            name = str(self.envdialog.Envname.text)
            urdfName =  str(self.envdialog.urdfName.text)
            packageName = str(self.envdialog.pkgName.text)
            self.r.loadObstacleModel (packageName, urdfName, name)
        self.update()

    def JointBounds (self):
        self.boundsdialog = _BoundsDialog(self.plugin)
        if self.boundsdialog.exec_():
            name = str(self.boundsdialog.jointList.currentItem().text())
            bounds = [self.boundsdialog.minx.value, self.boundsdialog.maxx.value,\
                    self.boundsdialog.miny.value, self.boundsdialog.maxy.value,\
                    self.boundsdialog.minz.value, self.boundsdialog.maxz.value]
            self.plugin.builder.setJointBounds (name, bounds)
            if self.boundsdialog.tick.isChecked():
                quatbounds = [self.boundsdialog.quatminx.value, self.boundsdialog.quatmaxx.value,\
                    self.boundsdialog.quatminy.value, self.boundsdialog.quatmaxy.value,\
                    self.boundsdialog.quatminz.value, self.boundsdialog.quatmaxz.value]
                self.plugin.builder.boundSO3(quatbounds)
                self.plugin.SO3bounds = quatbounds

    def loadModel (self, name, urdfName, urdfNameroms, rootJointType, meshPackageName,\
            packageName, urdfSuffix, srdfSuffix):
            if(isinstance(urdfNameroms, list)):    
                for urdfNamerom in urdfNameroms:
                    self.plugin.rbprmClient.rbprm.loadRobotRomModel(urdfNamerom, rootJointType,\
                            packageName, urdfNamerom, urdfSuffix, srdfSuffix)
            else:
                self.plugin.rbprmClient.rbprm.loadRobotRomModel(urdfNameroms, rootJointType,\
                        packageName, urdfNameroms, urdfSuffix, srdfSuffix)
            self.plugin.rbprmClient.rbprm.loadRobotCompleteModel(name, rootJointType, packageName,\
                    urdfName, urdfSuffix, srdfSuffix)

    def addFilter (self):
        items = self.ROMlist.selectedItems()
        if (len(items) > 0):
            ROMnames = []
            for item in items:
                ROMnames.append(str(item.text()))
            self.plugin.rbprmClient.rbprm.setFilter(ROMnames)
        self.update()

    def addAffFilter (self):
        items = self.ROMaffList.selectedItems()
        affItems = self.affTypeList.selectedItems()
        if (len(items) > 0 and len (affItems) > 0):
            affNames = []
            for aff in affItems:
                affNames.append(str(aff.text()))
            for item in items:
                self.plugin.rbprmClient.rbprm.setAffordanceFilter(str(item.text()), affNames)
        self.update()

    def getAffordanceConfigTypes (self):
        return self.plugin.affClient.affordance.getAffordanceConfigTypes ()

    def addToViewer (self):
        self.ps = ProblemSolver(self.plugin.builder)
        self.r = Viewer(self.ps)

    def str2float (self, text):
        str1 = str(text).replace(" ", "")
        str2 = str1.split(',')
        flist = []
        for s in str2:
            flist.append(float(s))
        return flist

    def showConfig(self, q):
        if len(q) == self.plugin.basicClient.robot.getConfigSize():
            self.r (q)
        self.update()

    def addConfig (self):
        configSize = self.plugin.basicClient.robot.getConfigSize()
        if str(self.configCombo.currentText) == 'initial':
            conf = self.str2float(str(self.initq.text))
            if len(conf) == configSize:
                self.plugin.basicClient.problem.setInitialConfig(conf)
                self.plugin.builder.setCurrentConfig(conf)
                self.q_init = conf
                self.initConfigSet = True
        else:
            conf = self.str2float(str(self.goalq.text))
            if len(conf) == configSize:
                self.plugin.basicClient.problem.addGoalConfig(conf)
                self.q_goal = conf
        self.update ()

    def clearConfigs (self):
        if str(self.configCombo.currentText) == 'initial':
            configSize = self.plugin.basicClient.robot.getConfigSize()
            conf = [0]*configSize
            self.plugin.basicClient.problem.setInitialConfig(conf)
        else:
            self.plugin.basicClient.problem.resetGoalConfigs()
        self.update()

    def resetConfigs (self):
        initq = "-2, 0, 0.63, 1, 0, 0, 0"
        goalq = "3, 0, 0.63, 1, 0, 0, 0"
        self.initq.setText(initq)
        self.goalq.setText(goalq)
        self.update()

    def qvector2float (self, p):
        conf =  [p.x(), p.y(), p.z()]
        return conf

    def spinConfig (self):
        configSize = self.plugin.basicClient.robot.getConfigSize()
        if str(self.configCombo.currentText) == 'initial':
            conf = self.str2float(self.initq.text)
        else:
            conf = self.str2float(self.goalq.text)
        if len(conf) == configSize:
            self.spinx.setValue(conf[0])
            self.spiny.setValue(conf[1])
            self.spinz.setValue(conf[2])

    def setConfigPos (self, pos, idx):
        configSize = self.plugin.basicClient.robot.getConfigSize()
        if str(self.configCombo.currentText) == 'initial':
            conf = self.str2float(self.initq.text)
        else:
            conf = self.str2float(self.goalq.text)
        # if config input incomplete, assume quat = [1,0,0,0] and other config variables == 0
        if len(conf) != configSize:
            conf = [0]*configSize
            conf[3] = 1
        if type(pos) == list:
            conf[0:len(pos)] = pos
        else:
            conf[idx] = pos
        config = str(conf)
        config = config.replace("[","")
        config = config.replace("]","")
        if str(self.configCombo.currentText) == 'initial':
            self.initq.text = config
        else:
            self.goalq.text = config
        self.showConfig(conf)
        self.spinConfig()
        self.update()

    def setChooseWithMouse (self):
        self.plugin.chooseWithMouse = True

class _BoundsDialog(QtGui.QDialog):
    def __init__(self, plugin, parent=None):
        super(_BoundsDialog, self).__init__(parent)
        self.plugin = plugin
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(10)
        self.setGeometry(440,418, 450, 450)
        self.setWindowTitle('Input dialog')
        # Create widgets
        label = QtGui.QLabel("Translation bounds for robot joints")
        self.jointList = QtGui.QListWidget()
        self.boundsTree = QtGui.QTreeWidget()
        self.minx = QtGui.QDoubleSpinBox()
        self.minx.setRange(-1000,1000)
        self.maxx = QtGui.QDoubleSpinBox()
        self.maxx.setRange(-1000,1000)
        self.miny = QtGui.QDoubleSpinBox()
        self.miny.setRange(-1000,1000)
        self.maxy = QtGui.QDoubleSpinBox()
        self.maxy.setRange(-1000,1000)
        self.minz = QtGui.QDoubleSpinBox()
        self.minz.setRange(-1000,1000)
        self.maxz = QtGui.QDoubleSpinBox()
        self.maxz.setRange(-1000,1000)
        self.minx.setSingleStep (0.05)
        self.maxx.setSingleStep (0.05)
        self.miny.setSingleStep (0.05)
        self.maxy.setSingleStep (0.05)
        self.minz.setSingleStep (0.05)
        self.maxz.setSingleStep (0.05)
        self.minx.setValue (-2)
        self.maxx.setValue (5)
        self.miny.setValue (-1)
        self.maxy.setValue (1)
        self.minz.setValue (0.3)
        self.maxz.setValue (4)
        text1 = QtGui.QLabel('x translation')
        text2 = QtGui.QLabel('y translation')
        text3 = QtGui.QLabel('z translation')

        self.tick = QtGui.QCheckBox("Set rotation bounds for robot base in rbprm shooter")
        #self.tick.setHidden(True)
        self.tick.setCheckable(True)

        # add widgets to grid
        self.grid.addWidget (label, 0,0)
        self.grid.addWidget (self.jointList, 1,0,1,1)
        self.grid.addWidget (self.boundsTree, 1,1,1,2)
        self.grid.addWidget (text1, 2,0)
        self.grid.addWidget (self.minx, 2,1)
        self.grid.addWidget (self.maxx, 2,2)
        self.grid.addWidget (text2, 3,0)
        self.grid.addWidget (self.miny, 3,1)
        self.grid.addWidget (self.maxy, 3,2)
        self.grid.addWidget (text3, 4,0)
        self.grid.addWidget (self.minz, 4,1)
        self.grid.addWidget (self.maxz, 4,2)
        self.grid.addWidget (self.tick, 5,0,1,2)

        # create grid 2 and its widgets
        self.groupbox = QtGui.QGroupBox()
        self.grid2 = QtGui.QGridLayout(self.groupbox)
        self.grid2.setSpacing(10)
        self.quatminx = QtGui.QDoubleSpinBox()
        self.quatminx.setRange(-1000,1000)
        self.quatmaxx = QtGui.QDoubleSpinBox()
        self.quatmaxx.setRange(-1000,1000)
        self.quatminy = QtGui.QDoubleSpinBox()
        self.quatminy.setRange(-1000,1000)
        self.quatmaxy = QtGui.QDoubleSpinBox()
        self.quatmaxy.setRange(-1000,1000)
        self.quatminz = QtGui.QDoubleSpinBox()
        self.quatminz.setRange(-1000,1000)
        self.quatmaxz = QtGui.QDoubleSpinBox()
        self.quatmaxz.setRange(-1000,1000)
        self.quatminx.setSingleStep (0.05)
        self.quatmaxx.setSingleStep (0.05)
        self.quatminy.setSingleStep (0.05)
        self.quatmaxy.setSingleStep (0.05)
        self.quatminz.setSingleStep (0.05)
        self.quatmaxz.setSingleStep (0.05)
        self.quatminx.setValue (-0.4)
        self.quatmaxx.setValue (0.4)
        self.quatminy.setValue (-3)
        self.quatmaxy.setValue (3)
        self.quatminz.setValue (-3)
        self.quatmaxz.setValue (3)
        text4 = QtGui.QLabel('x rotation')
        text5 = QtGui.QLabel('y rotation')
        text6 = QtGui.QLabel('z rotation')
        self.OKbutton = QtGui.QPushButton("Set bounds")
        self.CANCELbutton = QtGui.QPushButton("Cancel")

        # add widgets to grid2
        self.grid2.addWidget (label, 0,0)
        self.grid2.addWidget (text4, 1,0)
        self.grid2.addWidget (self.quatminx, 1,1)
        self.grid2.addWidget (self.quatmaxx, 1,2)
        self.grid2.addWidget (text5, 2,0)
        self.grid2.addWidget (self.quatminy, 2,1)
        self.grid2.addWidget (self.quatmaxy, 2,2)
        self.grid2.addWidget (text6, 3,0)
        self.grid2.addWidget (self.quatminz, 3,1)
        self.grid2.addWidget (self.quatmaxz, 3,2)

        self.grid.addWidget (self.groupbox,6,0,3,2)
        self.groupbox.setHidden(True)
        self.grid.addWidget (self.CANCELbutton, 9,0,1,1)
        self.grid.addWidget (self.OKbutton, 9,1,1,1)

        # Set dialog layout
        self.setLayout(self.grid)
        # Add button signal to showDetails slot
        #self.jointList.currentItemChanged.connect(lambda: self.hideWidgetCustom(self.jointList.currentItem()))
        self.tick.clicked.connect(lambda: self.hideWidget(self.groupbox, self.tick))
        self.OKbutton.clicked.connect(self.load)
        self.CANCELbutton.clicked.connect(self.cancel)
        self.update()

    # methods
    def update(self):
        self.jointList.clear()
        self.boundsTree.clear()
        joints = self.plugin.basicClient.robot.getJointNames()
        for joint in joints:
            self.jointList.addItem(joint)
            bounds = self.plugin.basicClient.robot.getJointBounds (joint)
            if (bounds[0] < bounds[1]):
                item = QtGui.QTreeWidgetItem()
                item.setText(0,joint)
                child = QtGui.QTreeWidgetItem()
                child.setText(0,str(bounds))
                item.addChild(child)
                self.boundsTree.addTopLevelItem(item)
                self.boundsTree.expandItem(item)
        if (self.plugin.SO3bounds[0] < self.plugin.SO3bounds[1]):
            item = QtGui.QTreeWidgetItem()
            item.setText(0,'So3bounds')
            child = QtGui.QTreeWidgetItem()
            child.setText(0,str(self.plugin.SO3bounds))
            item.addChild(child)
            self.boundsTree.addTopLevelItem(item)
            self.boundsTree.expandItem(item)

    def load (self):
            self.accept()
    def cancel (self):
            self.reject()
    def hideWidget (self,widget, button):
        if button.isChecked():
            widget.setHidden(False)
        else:
            widget.setHidden(True)

    def hideWidgetCustom (self, listItem):
        joint = str(listItem.text())
        if (joint.find ('base_joint') != -1):
            self.tick.setHidden(False)
        else:
            self.tick.setHidden(True)

class _LimbTab (QtGui.QWidget):
    def __init__(self, parent, plugin):
        super(_LimbTab, self).__init__ (parent)
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(10)
        # Create widgets
        label = QtGui.QLabel("Choose predefined model or provide custom description.")
        self.model = QtGui.QComboBox()
        self.model.editable = False
        text1 = QtGui.QLabel('Choose predefined model')
        text2 = QtGui.QLabel('Limb name')
        self.legId = QtGui.QLineEdit("rfleg")
        self.button = QtGui.QPushButton("Details")
        self.button.setCheckable(True)

        # add widgets to grid
        self.grid.addWidget (label, 0,0)
        self.grid.addWidget (text1, 1,0)
        self.grid.addWidget (self.model, 1,1)
        self.grid.addWidget (text2,2,0,2,1)
        self.grid.addWidget (self.legId, 2,1,2,1)
        self.grid.addWidget (self.button, 4,1,1,1)
        # create grid 2 and its widgets
        self.groupbox = QtGui.QGroupBox()
        self.grid2 = QtGui.QGridLayout(self.groupbox)
        self.grid2.setSpacing(10)
        text3 = QtGui.QLabel('Constraint type')
        self.cType = QtGui.QComboBox()
        self.cType.addItem("_3_DOF")
        text4 = QtGui.QLabel('First joint in URDF file')
        self.leg = QtGui.QLineEdit("rf_haa_joint")
        text5 = QtGui.QLabel('Last joint in URDF file')
        self.foot = QtGui.QLineEdit("rf_foot_joint")
        text6 = QtGui.QLabel('Offset between last joint and contact surface')
        self.offset = QtGui.QLineEdit("0,-0.021,0")
        text7 = QtGui.QLabel('Contact surface direciton for limb in rest pose')
        self.normal = QtGui.QLineEdit("0,1,0")
        text8 = QtGui.QLabel('Rectangular-contact-surface dimensions')
        self.legxlegy = QtGui.QLineEdit("0.02,0.02")
        text9 = QtGui.QLabel('Heuristic')
        self.heur = QtGui.QComboBox()
        self.heur.addItem ("manipulability")
        text10 = QtGui.QLabel ("Octree resolution")
        self.res = QtGui.QDoubleSpinBox()
        self.res.setSingleStep (0.05)
        self.res.setValue (0.1)
        text11 = QtGui.QLabel ("Number of samples")
        self.nbSamples = QtGui.QSpinBox()
        self.nbSamples.setMaximum(30000)
        self.nbSamples.setValue(20000)


        # add widgets to grid2
        self.grid2.addWidget (text3, 0,0)
        self.grid2.addWidget (self.cType, 0,1)
        self.grid2.addWidget (text4, 1,0)
        self.grid2.addWidget (self.leg, 1,1)
        self.grid2.addWidget (text5, 2,0)
        self.grid2.addWidget (self.foot, 2,1)
        self.grid2.addWidget (text6, 3,0)
        self.grid2.addWidget (self.offset, 3,1)
        self.grid2.addWidget (text7, 4,0)
        self.grid2.addWidget (self.normal, 4,1)
        self.grid2.addWidget (text8, 5,0)
        self.grid2.addWidget (self.legxlegy, 5,1)
        self.grid2.addWidget (text9, 6,0)
        self.grid2.addWidget (self.heur, 6,1)
        self.grid2.addWidget (text10, 7,0)
        self.grid2.addWidget (self.res, 7,1)
        self.grid2.addWidget (text11, 8,0)
        self.grid2.addWidget (self.nbSamples, 8,1)
       

        self.grid.addWidget (self.groupbox,5,0,3,2)
        self.groupbox.setHidden(True)

        # Set dialog layout
        self.setLayout(self.grid)
        # Add button signal to showDetails slot
        self.button.clicked.connect(lambda: self.hideWidget(self.groupbox, self.button))

    def hideWidget (self,widget, button):
        if button.isChecked():
            widget.setHidden(False)
        else:
            widget.setHidden(True)

class _LimbDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(_LimbDialog, self).__init__(parent)
        self.tabWidget = QtGui.QTabWidget()
        self.setGeometry(440,470, 450, 490)
        self.setWindowTitle('Input dialog')
       #  self.tabWidget.addTab(self.tab, "tab")
        self.tabs = [0]*4
        text1 = QtGui.QLabel("Number of limbs")
        self.limbs = QtGui.QSpinBox()
        self.limbs.setValue(4)
        self.limbs.setMaximum(10)
        self.OKbutton = QtGui.QPushButton("Load all limbs")
        self.CANCELbutton = QtGui.QPushButton("Cancel")
        # Set dialog layout
        layout = QtGui.QVBoxLayout()
        layout.addWidget (self.addWidgetsInHBox([text1, self.limbs]))
        layout.addWidget(self.tabWidget)
        layout.addWidget (self.addWidgetsInHBox([self.CANCELbutton, self.OKbutton]))

        self.setLayout(layout)
        self.OKbutton.clicked.connect(self.load)
        self.CANCELbutton.clicked.connect(self.cancel)
        self.limbs.valueChanged.connect(self.update)
        self.update()
    # methods

    def update (self):
        self.tabWidget.clear()
        self.tabs = [0]*self.limbs.value
        for i in range(0,self.limbs.value):
            self.tabs[i] = _LimbTab (self,self)
            self.tabWidget.addTab(self.tabs[i], "limb" + str(i+1) )
            if i == 1:
                self.tabs[i].legId.setText("lhleg")
                self.tabs[i].leg.setText("lh_haa_joint")
                self.tabs[i].foot.setText("lh_foot_joint")
                self.tabs[i].offset.setText("0,0.021,0")
                self.tabs[i].normal.setText("0,-1,0")
            if i == 2:
                self.tabs[i].legId.setText("rhleg")
                self.tabs[i].leg.setText("rh_haa_joint")
                self.tabs[i].foot.setText("rh_foot_joint")
            if i == 3:
                self.tabs[i].legId.setText("lfleg")
                self.tabs[i].leg.setText("lf_haa_joint")
                self.tabs[i].foot.setText("lf_foot_joint")
                self.tabs[i].offset.setText("0,0.021,0")
                self.tabs[i].normal.setText("0,-1,0")

    
    def load (self):
            self.accept()
    def cancel (self):
            self.reject()
    def hideWidget (self,widget, button):
        if button.isChecked():
            widget.setHidden(False)
        else:
            widget.setHidden(True)

    def addWidgetsInHBox(self, widgets):
        nameParentW = QtGui.QWidget(self)
        hboxName = QtGui.QHBoxLayout(nameParentW)
        for w in widgets:
            hboxName.addWidget(w)
        return nameParentW

    def bindFunctionToButton (self, buttonLabel, func):
        button = QtGui.QPushButton(self)
        button.text = buttonLabel
        button.connect ('clicked()', func)
        return button


class _EnvDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super(_EnvDialog, self).__init__(parent)
        self.grid = QtGui.QGridLayout()
        self.grid.setSpacing(10)
        self.setGeometry(440,418, 450, 450)
        self.setWindowTitle('Input dialog')
        # Create widgets
        label = QtGui.QLabel("Choose predefined model or provide custom description.")
        self.model = QtGui.QComboBox()
        self.model.editable = False
        text1 = QtGui.QLabel('Choose predefined model')
        text2 = QtGui.QLabel('Model name')
        self.Envname = QtGui.QLineEdit("planning")
        self.button = QtGui.QPushButton("Details")
        self.button.setCheckable(True)

        # add widgets to grid
        self.grid.addWidget (label, 0,0)
        self.grid.addWidget (text1, 1,0)
        self.grid.addWidget (self.model, 1,1)
        self.grid.addWidget (text2,2,0,2,1)
        self.grid.addWidget (self.Envname, 2,1,2,1)
        self.grid.addWidget (self.button, 4,1,1,1)
        # create grid 2 and its widgets
        self.groupbox = QtGui.QGroupBox()
        self.grid2 = QtGui.QGridLayout(self.groupbox)
        self.grid2.setSpacing(10)
        envText3 = QtGui.QLabel('Package name')
        self.pkgName = QtGui.QLineEdit("hpp-rbprm-corba")
        envText4 = QtGui.QLabel('Mesh package name')
        self.mpkgName = QtGui.QLineEdit()
        envText5 = QtGui.QLabel('URDF filename')
        self.urdfName = QtGui.QLineEdit("darpa")
        envText7 = QtGui.QLabel('URDF suffix')
        self.urdfSuf = QtGui.QLineEdit()
        envText8 = QtGui.QLabel('SRDF suffix')
        self.srdfSuf = QtGui.QLineEdit()

        # add widgets to grid2
        self.grid2.addWidget (label, 0,0)    
        self.grid2.addWidget (envText3, 1,0)
        self.grid2.addWidget (self.pkgName, 1,2)     
        self.grid2.addWidget (envText4, 2,0)
        self.grid2.addWidget (self.mpkgName, 2,2)     
        self.grid2.addWidget (envText5, 3,0)
        self.grid2.addWidget (self.urdfName, 3,2)      
        self.grid2.addWidget (envText7, 5,0)
        self.grid2.addWidget (self.urdfSuf, 5,2)
        self.grid2.addWidget (envText8, 6,0)
        self.grid2.addWidget (self.srdfSuf, 6,2)
       
        self.OKbutton = QtGui.QPushButton("Load")
        self.CANCELbutton = QtGui.QPushButton("Cancel")
        self.grid.addWidget (self.groupbox,5,0,3,2)
        self.groupbox.setHidden(True)
        self.grid.addWidget (self.CANCELbutton, 8,0,1,1)
        self.grid.addWidget (self.OKbutton, 8,1,1,1)

        # Set dialog layout
        self.setLayout(self.grid)
        # Add button signal to showDetails slot
        self.button.clicked.connect(lambda: self.hideWidget(self.groupbox, self.button))
        self.OKbutton.clicked.connect(self.load)
        self.CANCELbutton.clicked.connect(self.cancel)
    # methods
    def load (self):
            self.accept()
    def cancel (self):
            self.reject()
    def hideWidget (self,widget, button):
        if button.isChecked():
            widget.setHidden(False)
        else:
            widget.setHidden(True)
        
class _RobotDialog(_EnvDialog):
    def __init__(self, parent=None):
        super(_RobotDialog, self).__init__(parent)
        #self.grid2.removeWidget(self.envText6)
        #self.grid2.removeWidget(self.urdfromName)
        text = QtGui.QLabel('Root-joint type')
        self.rootJoint = QtGui.QComboBox()
        self.rootJoint.addItem("freeflyer")
        self.rootJoint.addItem("planar")
        self.rootJoint.addItem("anchor")
        self.grid.addWidget(text,3,0,1,1)
        self.grid.addWidget(self.rootJoint,3,1,2,1)
        self.envText6 = QtGui.QLabel('URDF ROM names, separated by commas')
        self.urdfromName = QtGui.QLineEdit("hyq_rhleg_rom, hyq_lfleg_rom, hyq_rfleg_rom, hyq_lhleg_rom")
        self.grid2.addWidget (self.envText6, 4,0)
        self.grid2.addWidget (self.urdfromName, 4,2)
        self.Envname.setText("hyq_trunk_large")
        self.urdfName.setText("hyq_trunk_large")
        self.pkgName.setText("hpp-rbprm-corba")
        self.mpkgName.setText("hpp-rbprm-corba")

class _FullBodyDialog (_RobotDialog):
     def __init__(self, parent=None):
        super(_FullBodyDialog, self).__init__(parent)
        self.Envname.setText("hyq")
        self.urdfName.setText("hyq")
        self.pkgName.setText("hyq_description")
        self.mpkgName.setText("hyq_description")
        self.envText6.setHidden(True)
        self.urdfromName.setHidden(True)

class _QColorButton(QtGui.QPushButton):
    #colorChanged = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(_QColorButton, self).__init__(*args, **kwargs)
        self._color = [0.7450980392156863, 1.0, 0.3333333333333333, 1]
        self.setMaximumWidth(32)
        self.pressed.connect(self.onColorPicker)

    def setColor(self, color):
        if color != self._color:
            self._color = color
     #       self.colorChanged.emit()

        if self._color:
            self.setStyleSheet("background-color: %s;" % self._color)
        else:
            self.setStyleSheet("")

    def color(self):
        return self._color

    def onColorPicker(self):
        dlg = QtGui.QColorDialog(self)
        if self._color:
            dlg.setCurrentColor(QtGui.QColor(self._color))

        if dlg.exec_():
            self.setColor(dlg.currentColor().name())

    #def mousePressEvent(self, e):
    #    if e.button() == Qt.RightButton:
    #        self.setColor(None)

    #    return super(_QColorButton, self).mousePressEvent(e)
### This class represents one special tab of the new QDockWidget
class _AffCreator (QtGui.QWidget):
    def __init__(self, parent, plugin):
        super(_AffCreator, self).__init__ (parent)
        self.plugin = plugin
        vbox1 = QtGui.QVBoxLayout(self)
        # vbox1.setGeometry(QtCore.QRect(1000,1000,1000,1000))
        # vbox1.setSpacing(20)
        gridW = QtGui.QWidget()#(self)
        grid = QtGui.QGridLayout(gridW)
        
        #hbox1.setSpacing (0) #no effect
        #box.setMargin(0)
        #self.affMargin.setAlignment(Qt.Qt.AlignLeft)
        
        # Affordance Types
        self.affordanceTypes = QtGui.QComboBox(self)
        self.affordanceTypes.editable = False
        self.affordanceTypes.setMaximumWidth(100)
        affTypeLabel = QtGui.QLabel("Affordance Type:")
        affTypeLabel.setMaximumWidth(200)

        grid.addWidget(self.addWidgetsInHBox( [affTypeLabel,
            self.affordanceTypes]), 0,0)

        # Affordance Creation by Name
        self.affMargin = QtGui.QDoubleSpinBox() 
        self.affMargin.setValue (0.03)
        self.affMargin.setMaximumWidth(100)
        marginLabel = QtGui.QLabel("Normal Margin:")
        marginLabel.setMaximumWidth(200)
        grid.addWidget(self.addWidgetsInHBox([marginLabel, self.affMargin]), 1,0)
        self.affNTriMargin = QtGui.QDoubleSpinBox()
        self.affNTriMargin.setValue (0.03)
        self.affNTriMargin.setMaximumWidth(100)
        nTMarginLabel = QtGui.QLabel("Neighbour-Triangle Margin:")
        nTMarginLabel.setMaximumWidth(200)
        grid.addWidget(self.addWidgetsInHBox([nTMarginLabel, self.affNTriMargin]), 0,1)
        self.affMinArea = QtGui.QDoubleSpinBox()
        self.affMinArea.setValue (0.05)
        self.affMinArea.setMaximumWidth(100)
        areaLabel = QtGui.QLabel("Minimum Area:")
        areaLabel.setMaximumWidth(200)
        grid.addWidget(self.addWidgetsInHBox([areaLabel, self.affMinArea]), 1,1)
        
        vbox1.addWidget(gridW)

        # Add Affordance Configuration
        vbox1.addWidget(self.bindFunctionToButton("Edit", self.setAffConfig))
        # Affordance Analysis Button
        self.affAnalysisObjects = QtGui.QComboBox(self)
        self.affAnalysisObjects.editable = False
        self.affAnalysisOptions = QtGui.QComboBox(self)
        self.affAnalysisOptions.editable = False
       
        self.colour = [0.7450980392156863, 1.0, 0.3333333333333333, 1]
        self.affColour = QtGui.QAction('Font bg Color', self)
        self.affColour.triggered.connect(self.colour_picker)

        vbox1.addWidget(self.addWidgetsInHBox( [
            QtGui.QLabel("Object:"), self.affAnalysisObjects,
            QtGui.QLabel("Affordance type:"), self.affAnalysisOptions]))

        self.colourButton = self.bindFunctionToButton("Choose Colour", self.colour_picker)
        vbox1.addWidget(self.colourButton)
      #  self.colorButton = _QColorButton("Choose colour")
      #  vbox1.addWidget(self.colorButton)
        vbox1.addWidget(self.bindFunctionToButton("Find Affordances", self.affordanceAnalysis))

        self.deleteObjects = QtGui.QComboBox(self)
        self.deleteObjects.editable = False
        self.deleteAffs = QtGui.QComboBox(self)
        self.deleteAffs.editable = False
        vbox1.addWidget(self.addWidgetsInHBox( [
            QtGui.QLabel("Object:"), self.deleteObjects,
            QtGui.QLabel("Affordance type:"), self.deleteAffs]))
        vbox1.addWidget(self.bindFunctionToButton("Delete Affordances", self.deleteAffordancesByType))
        self.groupbox = QtGui.QGroupBox()
        self.grid2 = QtGui.QGridLayout(self.groupbox)
        optimiserLabel = QtGui.QLabel("Choose Path Optimisers:")
        self.optimiserList = QtGui.QListWidget()
        self.chosenOptimiserList = QtGui.QListWidget()
        shooterLabel = QtGui.QLabel("Choose Configuration Shooter:")
        self.shooters = QtGui.QComboBox()
        validationLabel = QtGui.QLabel("Choose Path Validation method:")
        self.validations = QtGui.QComboBox()
        toleranceLabel = QtGui.QLabel("Validation tolerance:")
        self.validationTolerance = QtGui.QDoubleSpinBox()
        self.validationTolerance.setSingleStep (0.01)
        self.validationTolerance.setValue(0.05)
        self.validate = self.bindFunctionToButton("Validate settings", self.validateSettings)
        self.clearOptimisers = self.bindFunctionToButton("Clear path optimisers", self.clearOptimisers)
        self.grid2.addWidget(optimiserLabel, 0,0)
        self.grid2.addWidget(self.optimiserList, 1,0)
        self.grid2.addWidget(self.chosenOptimiserList, 1,1)
        self.grid2.addWidget(shooterLabel, 2,0)
        self.grid2.addWidget(self.shooters, 2,1)
        self.grid2.addWidget(validationLabel, 3,0)
        self.grid2.addWidget(self.validations, 3,1)
        self.grid2.addWidget(toleranceLabel, 4,0)
        self.grid2.addWidget(self.validationTolerance, 4,1)
        self.grid2.addWidget(self.validate, 5,1)
        self.grid2.addWidget(self.clearOptimisers, 5,0)
        vbox1.addWidget(self.groupbox)
        vbox1.addWidget(self.bindFunctionToButton("Solve", self.solve))
        self.update()

    def update(self):
        self.affordanceTypes.clear()
        self.affAnalysisOptions.clear()
        affordances = self.getAffordanceConfigTypes()
        for aff in affordances:
            self.affordanceTypes.addItem (aff)
            self.affAnalysisOptions.addItem (aff)
        self.affAnalysisOptions.addItem ("All types")
        self.affAnalysisObjects.clear ()
        self.deleteObjects.clear ()
        objects = self.plugin.basicClient.obstacle.getObstacleNames(False,True)
        for obj in objects:
            self.affAnalysisObjects.addItem (obj)
            self.deleteObjects.addItem (obj)
        self.affAnalysisObjects.addItem ("All objects")
        self.deleteObjects.addItem ("All objects")
        self.deleteAffs.clear ()
        affordances = self.getAffordanceTypes()
        for aff in affordances:
            self.deleteAffs.addItem (aff)
        self.deleteAffs.addItem ("All types")
        opts = self.plugin.basicClient.problem.getAvailable("PathOptimizer")
        vals = self.plugin.basicClient.problem.getAvailable("PathValidation")
        shs = self.plugin.basicClient.problem.getAvailable("ConfigurationShooter")
        self.optimiserList.clear()
        self.chosenOptimiserList.clear()
        self.validations.clear()
        self.shooters.clear()
        for opt in opts:
            self.optimiserList.addItem(opt)
        for val in vals:
            self.validations.addItem(val)
        for sh in shs:
            self.shooters.addItem(sh)

    def addWidgetsInHBox(self, widgets):
        nameParentW = QtGui.QWidget(self)
        hboxName = QtGui.QHBoxLayout(nameParentW)
        for w in widgets:
            hboxName.addWidget(w)
        return nameParentW

    def addWidgetsInVBox(self, widgets):
        nameParentW = QtGui.QWidget(self)
        vboxName = QtGui.QVBoxLayout(nameParentW)
        for w in widgets:
            vboxName.addWidget(w)
        return nameParentW

    def bindFunctionToButton (self, buttonLabel, func):
        button = QtGui.QPushButton(self)
        button.text = buttonLabel
        button.connect ('clicked()', func)
        return button

    def colour_picker (self):
        colour = QtGui.QColorDialog.getColor()
        self.colour = [colour.redF(), colour.greenF(), colour.blueF(), colour.alphaF()]
        self.colourButton.setStyleSheet("background-color: %s;" % self.colour)

    def addMesh (self):
        filename = QtGui.QFileDialog.getOpenFileName (self, "Choose a mesh")
        self.plugin.client.gui.addMesh(str(self.nodeName.text), str(filename))
        self.refreshBodyTree()

    def addBox (self):
        self.plugin.client.gui.addBox(str(self.nodeName.text), 1, 1, 1, self.colour)
        self.refreshBodyTree()

    def createGroup (self):
        self.plugin.client.gui.createGroup(str(self.nodeName.text))
        self.groupNodes.addItem(self.nodeName.text)
        self.refreshBodyTree()

    def addToGroup (self):
        self.plugin.client.gui.addToGroup(str(self.nodeName.text), str(self.groupNodes.currentText))
        self.refreshBodyTree()

    def setAffConfig (self):
        config = [self.affMargin.value, self.affNTriMargin.value, self.affMinArea.value]
        self.plugin.affClient.affordance.setAffordanceConfig (str(self.affordanceTypes.currentText), config)

    def affordanceAnalysis (self):
        objectname = str(self.affAnalysisObjects.currentText)
        affType = str(self.affAnalysisOptions.currentText)
        if objectname == "All objects":
            objectname = ""
            self.plugin.affClient.affordance.analyseAll ()
        else:
            self.plugin.affClient.affordance.analyseObject (objectname)
        if affType == "All types":
            affordances = self.getAffordanceTypes ()
            for aff in affordances:
                 self.visualiseAffordances(aff, self.colour, objectname)
        else:
            self.visualiseAffordances(affType, self.colour, objectname)
        self.update ()

    def getAffordancePoints (self, affordanceType):
        return self.plugin.affClient.affordance.getAffordancePoints (affordanceType)

    def visualiseAllAffordances (self, affType, colour):
        if len(colour) < 4 : # if the colour is only rgb we suppose alpha = 1 
          colour = colour + [1]
        self.deleteNode (str (affType), True)
        objs = self.getAffordancePoints (affType)
        refs = self.getAffRefObstacles (affType)
        self.plugin.client.gui.createGroup (str (affType))
        # TODO: add to groupNodes / refresh Body tree?
        for aff in objs:
          count = 0
          for tri in aff:
            self.plugin.client.gui.addTriangleFace (str (affType) + '-' + \
                 str (refs[objs.index (aff)]) + '.' + \
                 str (objs.index (aff)) + '.' + str(count), \
                 tri[0], tri[1], tri[2], [colour[0], colour[1], colour[2], colour[3]])
            self.plugin.client.gui.addToGroup (str (affType) + '-' + \
                 str (refs[objs.index (aff)]) + '.' + \
                 str (objs.index (aff)) + '.' + str(count), str (affType))
            count += 1
        scenes = self.plugin.client.gui.getSceneList() #TODO: add check to see whether scenes is empty
        groupNodes = self.plugin.client.gui.getGroupNodeList("hpp-gui")
        self.plugin.client.gui.addToGroup (str (affType), "hpp-gui")
        # By default, oldest node is displayed in front. Removing and re-adding
        # object from scene assure that the new triangles are displayed on top     
        for groupNode in groupNodes :
            self.plugin.client.gui.removeFromGroup(groupNode, "hpp-gui")
            self.plugin.client.gui.addToGroup(groupNode, "hpp-gui")

    def visualiseAffordances (self, affType, colour, obstacleName=""):
        if len(colour) < 4 : # if the colour is only rgb we suppose alpha = 1 
          colour = colour + [1]
        if obstacleName == "":
          return self.visualiseAllAffordances (affType, colour)
        else:
          self.deleteAffordancesByTypeFromViewer (affType, obstacleName)
          nodes = self.plugin.client.gui.getNodeList ()
          if affType not in nodes: self.plugin.client.gui.createGroup (str (affType))
          objs = self.getAffordancePoints (affType)
          refs = self.getAffRefObstacles (affType)
          for aff in objs:
            if refs[objs.index (aff)] == obstacleName:
              count = 0
              for tri in aff:
                name = str (affType) + '-' + \
                str (refs[objs.index (aff)]) + '.' + \
         str (objs.index (aff)) + '.' + str(count)
                self.plugin.client.gui.addTriangleFace (name, \
                    tri[0], tri[1], tri[2], [colour[0], colour[1], colour[2], colour[3]])
                self.plugin.client.gui.addToGroup (name, str (affType))
                count += 1
          scenes = self.plugin.client.gui.getSceneList() #TODO: add check to see whether scenes is empty
          groupNodes = self.plugin.client.gui.getGroupNodeList('hpp-gui')
          self.plugin.client.gui.addToGroup (str (affType), 'hpp-gui')
          # By default, oldest node is displayed in front. Removing and re-adding i
          # object from scene assure that the new triangles are displayed on top     
          for groupNode in groupNodes :
              self.plugin.client.gui.removeFromGroup(groupNode,'hpp-gui')
              self.plugin.client.gui.addToGroup(groupNode,'hpp-gui')

    def deleteNode (self, nodeName, all):
        return self.plugin.client.gui.deleteNode (nodeName, all)

    def getAffordanceTypes (self):
        return self.plugin.affClient.affordance.getAffordanceTypes ()

    def getAffordanceConfigTypes (self):
        return self.plugin.affClient.affordance.getAffordanceConfigTypes ()

    def getAffRefObstacles (self, affType):
        return self.plugin.affClient.affordance.getAffRefObstacles (affType)

    def deleteAffordances (self, obstacleName=""):
        self.deleteAffordancesFromViewer (obstacleName)
        return self.plugin.affClient.affordance.deleteAffordances (obstacleName)

    def deleteAffordancesFromViewer (self, obstacleName=""):
        affs = self.getAffordanceTypes ()
        if obstacleName == "":
            for aff in affs:
                self.deleteNode (aff, True)
        else:
           import re
           for aff in affs:
             refs = self.getAffRefObstacles (aff)
             count = 0
             while count < len(refs):
               if refs[count] == obstacleName:
                 toDelete = aff + '-' + refs[count]
                 nodes = self.plugin.client.gui.getGroupNodeList(aff)
                 for node in nodes:
                   splt = re.split ('\.', node)
                   if splt[0] == toDelete:
                     self.deleteNode (node, True)
               count += 1

    def deleteAffordancesByType (self):
        objectname = str(self.deleteObjects.currentText)
        affType = str(self.deleteAffs.currentText)
        if objectname == "All objects":
            objectname = ""
        if affType == "All types":
            affType == ""
            self.plugin.affClient.affordance.deleteAffordances(objectname)
        else:
            self.deleteAffordancesByTypeFromViewer (affType, objectname)
            self.plugin.affClient.affordance.deleteAffordancesByType (affType, objectname)
        self.update ()

    def deleteAffordancesByTypeFromViewer (self, affordanceType, obstacleName=""):
        if obstacleName == "":
          self.deleteNode (affordanceType, True)
        else:
           import re
           affs = self.getAffordanceTypes ()
           for aff in affs:
             if aff == affordanceType:
               refs = self.getAffRefObstacles (aff)
               count = 0
               while count < len(refs):
                 if refs[count] == obstacleName:
                   toDelete = aff + '-' + refs[count]
                   nodes = self.plugin.client.gui.getNodeList()
                   for node in nodes:
                     splt = re.split ('\.', node)
                     if splt[0] == toDelete:
                       self.deleteNode (node, True)
                 count += 1


    ## See gepetto::gui::MainWindow::requestRefresh for more information
    def refreshBodyTree(self):
        self.plugin.main.requestRefresh()

    def validateSettings (self):
        self.plugin.basicClient.problem.addPathOptimizer (str(self.optimiserList.currentItem().text()))
        self.plugin.basicClient.problem.selectConFigurationShooter (str(self.shooters.currentText))
        self.plugin.basicClient.problem.selectPathValidation (str(self.validations.currentText),\
                float(self.validationTolerance.value))

    def clearOptimisers (self):
        self.plugin.basicClient.problem.clearPathOptimizers()
        self.update()

    def solve (self):
        self.plugin.basicClient.problem.solve()
        self.update()

class Plugin(QtGui.QDockWidget):
    """
    This plugin interacts with PythonWidget C++ class.
    """
    def __init__ (self, mainWindow, flags = None):
        if flags is None:
            super(Plugin, self).__init__ ("Affordance plugin", mainWindow)
        else:
            super(Plugin, self).__init__ ("Affordance plugin", mainWindow, flags)
        self.client = Client ()
        self.rbprmClient = rbprmClient ()
        self.builder = Builder ()
        self.fullbody = FullBody ()
        self.basicClient  = basicClient ()
        self.affClient = affClient ()
        #action = self.addAction("Affo")
        #action.setShortcut(QtGui.QKeySequence("Shift+Alt+A"))
        #self.mainWindow.actionExit.setShortcut('Ctrl+Alt+A')
        #self.mainWindow.actionExit.setStatusTip(_('Open affordance plugin'))
        #self.mainWindow.connect(self.mainWindow.actionExit, QtCore.SIGNAL('triggered()'), QtCore.SLOT('close()'))
        # Initialize the widget
        self.tabWidget = QtGui.QTabWidget() #(self)
        self.setWidget (self.tabWidget)
        self.rbprmPath = _RbprmPath (self,self)
        self.tabWidget.addTab (self.rbprmPath, "Rbprm Path")
        self.affCreator = _AffCreator(self, self)
        self.tabWidget.addTab (self.affCreator, "Affordance Creator")
        self.rbprmInterp = _RbprmInterp (self,self)
        self.tabWidget.addTab (self.rbprmInterp, "Rbprm Interp")
        self.main = mainWindow
        mainSize = self.main.size
        self.tabWidget.setMaximumSize(mainSize.height(), int(float(mainSize.width())*0.9))
        mainWindow.connect('refresh()', self.refresh)
        self.chooseWithMouse = False
        self.tabWidget.connect(self.tabWidget, QtCore.SIGNAL("currentChanged(int)"), self.updateSelected)
    ### If present, this function is called when a new OSG Widget is created.
    def osgWidget(self, osgWindow):
        osgWindow.connect('selected(QString,QVector3D)', self.selected)

    def resetConnection(self):
        self.client = Client()
        self.rbprmClient = rbprmClient ()
        self.basicClient = basicClient ()
        self.affClient = affClient ()

    def updateSelected(self):
        currentWidget=self.tabWidget.currentWidget()
        currentWidget.update()

    def refresh(self):
        self.affCreator.update()
        self.rbprmPath.update()
        self.rbprmInterp.update()

    def selected(self, name, posInWorldFrame):
        if (self.chooseWithMouse):
            QtGui.QMessageBox.information(self, "Selected object", name + " " + str(posInWorldFrame))
            self.rbprmPath.setConfigPos(self.rbprmPath.qvector2float (posInWorldFrame), -1)

