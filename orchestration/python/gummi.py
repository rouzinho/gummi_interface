#!/usr/bin/env python

import rospy
import wx
import sys

from geometry_msgs.msg import Twist
from sensor_msgs.msg import JointState

from antagonist import Antagonist
from direct_drive import DirectDrive

class Gummi:

    def __init__(self):
        self.pi = 3.1416
        self.initVariables()
        self.initJoints()
        self.initPublishers()
        self.initSubscribers()

    def initVariables(self):
        self.jointNames = ("shoulder_roll", "shoulder_pitch", "upperarm_roll", "elbow", "forearm_roll", "wrist")
        self.shoulderRollVel = 0
        self.shoulderPitchVel = 0
        self.upperarmRollVel = 0
        self.elbowVel = 0
        self.forearmRollVel = 0
        self.wristVel = 0
        self.shoulderRollStiff = 0
        self.shoulderPitchStiff = 0
        self.elbowStiff = 0
        self.wristStiff = 0

    def initJoints(self):
        self.shoulderRoll = Antagonist(1, 1, -1, 1, 1, "shoulder_flexor", "shoulder_extensor", "shoulder_roll_encoder", 0, 2*self.pi, -0.2, 1.25)
        self.shoulderPitch = Antagonist(-1, -1, -1, 1, 1, "shoulder_abductor", "shoulder_adductor", "shoulder_pitch_encoder", 0, 2*self.pi, 0, 1.75)
        self.upperarmRoll = DirectDrive("upperarm_roll", self.pi)
        self.elbow = Antagonist(-1, 1, -1, -1, 1, "biceps", "triceps", "elbow_encoder", 0, 2*self.pi, -0.75, 0.85)
        self.forearmRoll = DirectDrive("forearm_roll", 1.75*self.pi)
        self.wrist = Antagonist(-1, -1, -1, -1, 1, "wrist_flexor", "wrist_extensor", "wrist_encoder", 0, 1.75*self.pi, -1.0, 1.0)

    def initPublishers(self):
        self.jointStatePub = rospy.Publisher("/gummi/joint_states", JointState,  queue_size=10) 

    def initSubscribers(self):
        rospy.Subscriber('/gummi/joint_commands', JointState, self.cmdCallback)

    def cmdCallback(self, msg):
        self.shoulderRoll.servoTo(msg.position[0], msg.effort[0])
        self.shoulderPitch.servoTo(msg.position[1], msg.effort[1])
        self.upperarmRoll.servoTo(msg.position[2])
        self.elbow.servoTo(msg.position[3], msg.effort[3])
        self.forearmRoll.servoTo(msg.position[4])
        self.wrist.servoTo(msg.position[5], msg.effort[5])

    def setMaxLoads(self, maxLoadShoulderRoll, maxLoadShoulderPitch, maxLoadElbow, maxloadWrist):
        self.shoulderRoll.setMaxLoad(maxLoadShoulderRoll)
        self.shoulderPitch.setMaxLoad(maxLoadShoulderPitch)
        self.elbow.setMaxLoad(maxLoadElbow)
        self.wrist.setMaxLoad(maxloadWrist)

    def doUpdate(self):
        self.shoulderRoll.servoWith(self.shoulderRollVel, self.shoulderRollStiff)
        self.shoulderPitch.servoWith(self.shoulderPitchVel, self.shoulderPitchStiff)
        self.upperarmRoll.servoWith(self.upperarmRollVel)
        self.elbow.servoWith(self.elbowVel, self.elbowStiff)
        self.forearmRoll.servoWith(self.forearmRollVel)
        self.wrist.servoWith(self.wristVel, self.wristStiff)
        self.publishJointState()

    def publishJointState(self):
        msg = JointState()
        msg.header.stamp = rospy.Time.now()
        msg.name = self.jointNames
        msg.position = self.getJointAngles()
        msg.effort = self.getLoads()
        self.jointStatePub.publish(msg)

    def getJointAngles(self):
        angles = list()
        angles.append(self.shoulderRoll.getJointAngle())
        angles.append(self.shoulderPitch.getJointAngle())
        angles.append(self.upperarmRoll.getJointAngle())
        angles.append(self.elbow.getJointAngle())
        angles.append(self.forearmRoll.getJointAngle())
        angles.append(self.wrist.getJointAngle())
        return angles

    def manualServoWith(self, velocities):
        self.shoulderRollVel = velocities[0]
        self.shoulderPitchVel = velocities[1]
        self.upperarmRollVel = velocities[2]
        self.elbowVel = velocities[3]
        self.forearmRollVel = velocities[4]
        self.wristVel = velocities[5]
        self.doUpdate()

    def manualSetStiffness(self, shoulderRoll, shoulderPitch, elbow, wrist):
        self.shoulderRollStiff = shoulderRoll
        self.shoulderPitchStiff = shoulderPitch
        self.elbowStiff = elbow
        self.wristStiff = wrist

    def getLoads(self):
        loads = list()
        loads.append(self.shoulderRoll.getLoadRatio())
        loads.append(self.shoulderPitch.getLoadRatio())
        loads.append(1234)
        loads.append(self.elbow.getLoadRatio())
        loads.append(1234)
        loads.append(self.wrist.getLoadRatio())
        return loads

    def goRestingPose(self):
        self.shoulderRoll.servoTo(0, self.shoulderRollStiff)
        self.shoulderPitch.servoTo(0, self.shoulderPitchStiff)
        self.upperarmRoll.servoTo(0)
        self.elbow.servoTo(0, self.elbowStiff)
        self.forearmRoll.servoTo(0)
        self.wrist.servoTo(0, self.wristStiff)

    def doGradualStartup(self):
        self.shoulderRoll.moveTo(-1.5, self.shoulderRollStiff)
        rospy.sleep(0.5)
        self.shoulderRoll.moveTo(-1.25, self.shoulderRollStiff)
        rospy.sleep(2)
        self.shoulderPitch.moveTo(0.5, self.shoulderPitchStiff)
        rospy.sleep(2)
        self.upperarmRoll.servoTo(0)
        rospy.sleep(2)
        self.elbow.moveTo(0, self.elbowStiff)
        rospy.sleep(2)
        self.forearmRoll.servoTo(0)
        rospy.sleep(2)
        self.wrist.moveTo(0, self.wristStiff)
        rospy.sleep(2)
        
