from hpp.corbaserver.rbprm.rbprmbuilder import Builder
from hpp.corbaserver.rbprm.rbprmfullbody import FullBody
from hpp.gepetto import Viewer

import ground_crouch_hyq_path as tp

packageName = "hyq_description"
meshPackageName = "hyq_description"
rootJointType = "freeflyer"
##
#  Information to retrieve urdf and srdf files.
urdfName = "hyq"
urdfSuffix = ""
srdfSuffix = ""

fullBody = FullBody ()
 
fullBody.loadFullBodyModel(urdfName, rootJointType, meshPackageName, packageName, urdfSuffix, srdfSuffix)

from hpp.corbaserver.rbprm.problem_solver import ProblemSolver

nbSamples = 20000

ps = tp.ProblemSolver( fullBody )
r = tp.Viewer (ps)

rootName = 'base_joint_xyz'

#~ AFTER loading obstacles
cType = "_3_DOF"
rLegId = 'rfleg'
rLeg = 'rf_haa_joint'
rfoot = 'rf_foot_joint'
rLegOffset = [0.,0,0.]
rLegNormal = [0,1,0]
rLegx = 0.02; rLegy = 0.02
fullBody.addLimb(rLegId,rLeg,rfoot,rLegOffset,rLegNormal, rLegx, rLegy, nbSamples, "forward", 0.1,cType)

lLegId = 'lhleg'
lLeg = 'lh_haa_joint'
lfoot = 'lh_foot_joint'
lLegOffset = [0,0,0]
lLegNormal = [0,1,0]
lLegx = 0.02; lLegy = 0.02
fullBody.addLimb(lLegId,lLeg,lfoot,lLegOffset,rLegNormal, lLegx, lLegy, nbSamples, "backward", 0.05,cType)

rarmId = 'rhleg'
rarm = 'rh_haa_joint'
rHand = 'rh_foot_joint'
rArmOffset = [0.,0,-0.]
rArmNormal = [0,1,0]
rArmx = 0.02; rArmy = 0.02
fullBody.addLimb(rarmId,rarm,rHand,rArmOffset,rArmNormal, rArmx, rArmy, nbSamples, "backward", 0.05,cType)

larmId = 'lfleg'
larm = 'lf_haa_joint'
lHand = 'lf_foot_joint'
lArmOffset = [0.,0,-0.]
lArmNormal = [0,1,0]
lArmx = 0.02; lArmy = 0.02
fullBody.addLimb(larmId,larm,lHand,lArmOffset,lArmNormal, lArmx, lArmy, nbSamples, "forward", 0.05,cType)

q_0 = fullBody.getCurrentConfig(); 
q_init = fullBody.getCurrentConfig(); q_init[0:7] = tp.q_init[0:7]
q_goal = fullBody.getCurrentConfig(); q_goal[0:7] = tp.q_goal[0:7]


fullBody.setCurrentConfig (q_init)
q_init = fullBody.generateContacts(q_init, [0,0,1])
q_0 = fullBody.getCurrentConfig(); 

fullBody.setCurrentConfig (q_goal)
q_goal = fullBody.generateContacts(q_goal, [0,0,1])

fullBody.setStartState(q_init,[])
fullBody.setEndState(q_goal,[rLegId,lLegId,rarmId,larmId])

r(q_init)

configs = fullBody.interpolate(0.1)

r.loadObstacleModel ('hpp-rbprm-corba', "groundcrouch", "contact")
#~ fullBody.exportAll(r, configs, 'obstacle_hyq_robust_10');
i = 0;
r (configs[i]); i=i+1; i-1

q0 = configs[2]
q0 = fullBody.generateContacts(q0, [0,0,1])
r(q0)
c = fullBody.getContactSamplesIds("rfleg",q_init, [0,0,1])
r(fullBody.getSample("rfleg",int(c[i]))); i = i+1

