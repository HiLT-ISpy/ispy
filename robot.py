import math
import time
import os

import numpy as np
from naoqi import ALModule, ALProxy, ALBroker
import speech_recognition as sr

import config

count = 0
r = None

def connect(address="bobby.local", port=9559, name="r", brokername="broker"):
	global broker
	broker = ALBroker("broker", "0.0.0.0", 0, address, 9559)
	global r
	r = Robot(name, address, 9559)

def robot():
	global r
	return r

def broker():
	global broker
	if not broker:
		broker = ALBroker("broker", "0.0.0.0", 0, "bobby.local", 9559)
	return broker

class Robot(ALModule):
	def __init__( self, strName, address = "bobby.local", port = 9559):
		ALModule.__init__( self, strName )

		# Are these used for anything?
		# self.outfile = None
		# self.outfiles = [None]*(3)
		# self.count = 99999999
		# self.check = False

		# --- audio ---
		self.audio = ALProxy("ALAudioDevice", address, port)
		self.audio.setClientPreferences(self.getName(), 48000, [1,1,1,1], 0, 0)

		# --- speech recognition ---
		self.sr = ALProxy("SoundReceiver", address, port)
		self.asr = ALProxy("ALSpeechRecognition", address, port)
		self.asr.setLanguage("English")

		self.yes_no_vocab = {
			True: ["yes", "ya", "sure", "definitely"],
			False: ["no", "nope", "nah"]
		}

		# TODO: add unknown object names into this somehow
		# also add other names for objects dynamically??????
		self.object_vocab = {
			"digital_clock": ["digital clock", "blue clock", "black alarm clock"],
			"analog_clock": ["analog clock", "black clock", "black alarm clock"],
			"red_soccer_ball": [u"red soccer ball", "red ball"],
			"basketball": ["basketball", "orange ball"],
			"football": ["football"],
			"yellow_book": ["yellow book"],
			"yellow_flashlight": ["yellow flashlight"],
			"blue_soccer_ball": ["blue soccer ball", "blue ball"],
			"apple": ["apple"],
			"black_mug": ["black mug"],
			"blue_book": ["blue book"],
			"blue_flashlight": [u"blue flashlight"],
			"cardboard_box": ["cardboard box"],
			"pepper": ["pepper", "jalapeno"],
			"green_mug": ["green mug"],
			"polka_dot_box": ["polka dot box", "polka dotted box", "spotted box", "brown and white box"],
			"scissors": ["scissors"]
		}

		self.asr.setVocabulary([j for i in self.yes_no_vocab.values() for j in i], False)

		# Custom segmentationation module
		self.segmentation = ALProxy("Segmentation", address, port)

		# --- text to speech ---
		self.tts = ALProxy("ALTextToSpeech", address, port)

		# --- memory ---
		self.mem = ALProxy("ALMemory", address, port)

		# --- robot movement ---
		self.motion = ALProxy("ALMotion", address, port)
		self.pose = ALProxy("ALRobotPosture", address, port)

		self.motion.stiffnessInterpolation("Body", 1.0, 1.0)
		self.pose.goToPosture("Crouch", 0.2)

		# --- face tracking ---
		self.track = ALProxy("ALFaceTracker", address, port)

		self.track.setWholeBodyOn(False)

		# --- gaze analysis ---
		self.gaze = ALProxy("ALGazeAnalysis", address, port)

		# --- camera ---
		self.cam = ALProxy("ALVideoDevice", address, port)

		# --- leds ---
		self.leds = ALProxy("ALLeds", address, port)

		self.colors = {
			"pink": 0x00FF00A2,
			"red": 0x00FF0000,
			"orange": 0x00FF7300,
			"yellow": 0x00FFFB00,
			"green": 0x000DFF00,
			"blue": 0x000D00FF,
			"purple": 0x009D00FF
		}

		# --- sound detection ---
		self.sound = ALProxy("ALSoundDetection", address, port)

		self.sound.setParameter("Sensibility", 0.95)

	def __del__(self):
		print "End Robot Class"


	def say(self, text, block = True):
		"""
		Uses ALTextToSpeech to vocalize the given string.
		If "block" argument is False, makes call asynchronous.
		"""

		if block:
			self.tts.say(text)

		else:
			self.tts.post.say(text)

	def ask(self, question):
		"""
		Has the robot ask a question and returns the answer
		"""

		# use voice recognition to get response? (defaults to using keyboard)
		voice_recognition = False

		# If you're just trying to test voice detection, you can uncomment
		# the following 5 lines. Bobby will guess "yellow flashlight" and will prompt
		# you to correct him by saying "blue flashlight"

		# fake_answers = ["no", "yes", "yes", "yes", "no", "yes", "yes"]
		# global count
		# count += 1
		# print question
		# return fake_answers[count - 1]

		self.say(question)

		if voice_recognition:

			# still needs to be fixed I think, I just uncommented it

			#starts listening for an answer
			self.asr.subscribe("TEST_ASR")
			data = (None, 0)
			while not data[0]:
				if config.args.gaze:
					self.trackGaze()
				data = self.mem.getData("WordRecognized")
			#stops listening after he hears yes or no
			self.asr.unsubscribe("TEST_ASR")

			print data

			for answer in self.yes_no_vocab:
				if data[0] in self.yes_no_vocab[answer]:
					return answer

		# Temporary clause for testing while speech recognition isn't working
		else:
			while True:
				print question
				if config.args.gaze:
					timeout = time.time() + 1.5
					while time.time() < timeout:
						self.trackGaze()
				answer = raw_input().lower()[0]
				if answer == "y":
					return True
				elif answer == "n":
					return False

	def ask_object(self):
		# TODO: fix this so that speech recognition actually works
		# right now it raises a LookupError every time
		# self.sr.start_processing()
		# print "asking object"
		# while True:
		# 	print "check:", self.sr.checking()
		# 	if self.sr.checking():
		# 		break
		# 	time.sleep(.5)
		# data = self.sr.stop_processing()
		# print "converting to a numpy array"
		# data = np.array(data)
		# print "saving as a raw file"
		# data.tofile(open("output.raw", "wb"))
		# #uses sox to convert raw files to wav files
		# print "converting to a wav file"
		# os.system("sox -r 60000 -e signed -b 16 -c 1 output.raw speech.wav")
		# print "converted"
		# r = sr.Recognizer()
		# with sr.WavFile("speech.wav") as source:
		# 	print "listening to wav file"
		# 	speech = r.record(source)
		# try:
		# 	print "gathering possibilities"
		# 	possibilities = r.recognize(speech, True)
		# 	print "possibilities:", possibilities
		# 	for possibility in possibilities:
		# 		for word in self.object_vocab:
		# 			for syn in self.object_vocab[word]:
		# 				if possibility["text"] == unicode(syn):
		# 					# global broker
		# 					# broker.shutdown()
		# 					# exit(0)
		# 					return possibility
		# 	raise LookupError
		# except LookupError:
		# 	# self.say("I couldn't understand what you said. Please go to the computer and type the name of your object.")
		# 	print "Type the name of your object exactly as you see here."
		# 	print self.object_vocab.keys()
		# 	# global broker
		# 	# broker.shutdown()
		# 	# exit(0)
		# 	return raw_input("What object were you thinking of?")
		self.say("What object were you thinking of?")
		print self.object_vocab.keys()
		return raw_input("Type the name of the object as seen above. ")

	def wake(self):
		"""
		Turns stiffnesses on, goes to Crouch position, and lifts head
		"""

		self.motion.stiffnessInterpolation("Body", 1.0, 1.0)
		self.pose.goToPosture("Crouch", 0.2)
		self.turnHead(pitch = math.radians(-10))

	def rest(self):
		"""
		Goes to Crouch position and turns robot stiffnesses off
		"""

		self.motion.rest()

	def turnHead(self, yaw = None, pitch = None, speed = 0.3):
		"""
		Turns robot head to the specified yaw and/or pitch in radians at the given speed.
		Yaw can range from 119.5 deg (left) to -119.5 deg (right) and pitch can range from 38.5 deg (up) to -29.5 deg (down).
		"""

		if not yaw is None:
			self.motion.setAngles("HeadYaw", yaw, speed)
		if not pitch is None:
			self.motion.setAngles("HeadPitch", pitch, speed)

	def colorEyes(self, color, fade_duration = 0.2):
		"""
		Fades eye LEDs to specified color over the given duration.
		"Color" argument should be either in hex format (e.g. 0x0063e6c0) or one of the following
		strings: pink, red, orange, yellow, green, blue, purple
		"""

		if color in self.colors:
			color = colors[color]

		self.leds.fadeRGB("FaceLeds", color, fade_duration)

	def getHeadAngles(self):
		"""
		Returns current robot head angles as a list of yaw, pitch.
		For yaw, from the robot's POV, left is positive and right is negative. For pitch, up is positive and down is negative.
		See http://doc.aldebaran.com/2-1/family/robots/joints_robot.html for info on the range of its yaw and pitch.
		"""

		robot_head_yaw, robot_head_pitch = self.motion.getAngles("Head", False)

		# return adjusted robot head angles
		return [robot_head_yaw, -robot_head_pitch]

	def resetEyes(self):
		"""
		Turns eye LEDs white.
		"""

		self.leds.on("FaceLeds")

	def waitForSound(self, time_limit = 7):
		"""
		Waits until either a sound is detected or until the given time limit expires.
		"""

		self.sound.subscribe("sound_detection_client")

		# give waiting a 7-second time limit
		timeout = time.time() + 7

		# check for new sounds every 0.2 seconds
		while (self.mem.getData("SoundDetected")[0] != 1) and (time.time() < timeout):
			time.sleep(0.2)

		self.sound.unsubscribe("sound_detection_client")

	def trackFace(self):
		"""
		Sets face tracker to just head and starts.
		"""

		# start face tracker
		self.track.setWholeBodyOn(False)
		self.track.startTracker()

	def stopTrackingFace(self):
		"""
		Stops face tracker.
		"""

		self.track.stopTracker()

	def unsubscribeGaze(self):
		"""
		Unsubscribes from gaze analysis module so the robot stops writing gaze data to its memory.
		"""

		self.gaze.unsubscribe("_")

	def initGaze(self, object_yaws):

		# subscribe to gaze analysis module so that robot starts writing gaze data to memory
		self.gaze.subscribe("_")

		# set highest tolerance for determining if people are looking at the robot because those people's IDs are the only ones stored
		self.gaze.setTolerance(1)

		# initialize confidences for each object
		self.gaze_confidences = dict.fromkeys(object_yaws, 0)
		self.angle_error = math.radians(15)

		# start writing gaze data to robot memory
		self.gaze.subscribe("_")

	def updatePersonID(self):
		"""
		Tries to get people IDs from robot memory.
		If none are retrieved, tries again every 0.5 seconds until it gets some.
		Stores the first person ID in the list as self.person_id.
		"""

		# try to get list of IDs of people looking at robot
		people_ids = self.mem.getData("GazeAnalysis/PeopleLookingAtRobot")

		# if robot hasn't gotten any people IDs
		while people_ids is None or len(people_ids) == 0:

			# wait a little bit, then try again
			time.sleep(0.5)
			people_ids = self.mem.getData("GazeAnalysis/PeopleLookingAtRobot")

		self.person_id = people_ids[0]

	def updateRawPersonGaze(self):
		"""
		Stores person's gaze as a list of yaw (left -, right +) and pitch (up pi, down 0) in radians, respectively.
		Bases gaze on both eye and head angles. Does not compensate for variable robot head position.
		"""

		try:
			# retrieve GazeDirection and HeadAngles values
			gaze_dir = self.mem.getData("PeoplePerception/Person/" + str(self.person_id) + "/GazeDirection")
			head_angles =  self.mem.getData("PeoplePerception/Person/" + str(self.person_id) + "/HeadAngles")

			# extract gaze direction and head angles data
			person_eye_yaw = gaze_dir[0]
			person_eye_pitch = gaze_dir[1]

			person_head_yaw = head_angles[0]
			person_head_pitch = head_angles[1]

		# RuntimeError: if gaze data can't be retrieved for that person ID anymore (e.g. if bot entirely loses track of person)
		# IndexError: if gaze direction or head angles are empty lists (e.g. if person's gaze is too steep)
		except (RuntimeError, IndexError):
			self.raw_person_gaze = None
			self.updatePersonID()

		else:
			# combine eye and head gaze values
			self.raw_person_gaze_yaw = -(person_eye_yaw + person_head_yaw) # person's left is (-), person's right is (+)
			self.raw_person_gaze_pitch = person_eye_pitch + person_head_pitch + math.pi / 2 # all the way up is pi, all the way down is 0

			self.raw_person_gaze = [self.raw_person_gaze_yaw, self.raw_person_gaze_pitch]

	def personLookingAtRobot(self):
		"""
		Determines whether the person is looking in the general area of the robot's head.
		Bases this off of the last cached raw gaze values.
		"""

		if self.raw_person_gaze is None:
			return False

		yaw_in_range = abs(self.raw_person_gaze_yaw - 0) < math.radians(15)
		pitch_in_range = abs(self.raw_person_gaze_pitch - math.radians(90)) < math.radians(20)
		return (yaw_in_range and pitch_in_range)

	def pitchSumOverTime(self, duration):
		"""
		Adds pitch value to a sum every time person looks at robot during the given duration.
		Both this sum and the number of times the sum was added to are member variables.
		"""

		timeout = time.time() + duration
		while time.time() < timeout:
			self.updateRawPersonGaze()

			if self.personLookingAtRobot():
				# add current pitch to pitch sum
				self.pitch_sum += self.raw_person_gaze_pitch
				self.pitch_count += 1

	def findPersonPitchAdjustment(self, person_name = "Person", style = "normal"):
		"""
		Stores the adjustment needed to be made to measured gaze pitch values, which it calculates based on the
		difference between 90 deg and an average measurement of the person's gaze when looking at the robot's eyes.
		Robot speaks to get straight-on gaze to measure, then filters measurements with personLookingAtRobot().
		"""

		self.pitch_sum = 0
		self.pitch_count = 0

		self.updatePersonID()

		eye_contact = False

		self.colorEyes("blue")

		# try get person's attention then wait until they look at us (robot)
		self.say("Hey " + person_name + "?", block = False)

		self.updateRawPersonGaze()

		while not self.personLookingAtRobot():
			self.updateRawPersonGaze()
			time.sleep(0.2)
		self.pitchSumOverTime(1)

		# finish talking and add to pitch sum while talking
		self.say("Are you ready to play?", block = False)
		self.pitchSumOverTime(1)

		self.colorEyes("purple")

		control_pitch = self.pitch_sum / self.pitch_count

		# the pitch adjustment we need to make is the difference between (the measured value at 90 degrees) and (90 degrees)
		self.person_pitch_adjustment = control_pitch - math.radians(90)

		print "person_pitch_adjustment:", self.person_pitch_adjustment

		# finish talking
		time.sleep(2)
		self.say("Okay, let's play!")

	def updatePersonGaze(self):
		"""
		Saves person's gaze as a list of yaw (left -, right +) and pitch (up pi, down 0) in radians, respectively.
		Gets gaze from updateRawPersonGaze function, then compensates for variable robot head position and measured pitch inaccuracy.
		"""

		self.updateRawPersonGaze()

		if self.raw_person_gaze is None:
		   self.person_gaze = None

		else:
			robot_head_yaw, robot_head_pitch = self.getHeadAngles()

			# compensate for variable robot head angles
			self.person_gaze_yaw = self.raw_person_gaze_yaw - robot_head_yaw # person's left is (-), person's right is (+)
			self.person_gaze_pitch = self.raw_person_gaze_pitch - robot_head_pitch # all the way up is pi, all the way down is 0

			# compensate for measured pitch inaccuracy
			self.person_gaze_pitch += self.person_pitch_adjustment

			self.person_gaze = [self.person_gaze_yaw, self.person_gaze_pitch]

	def updatePersonLocation(self):
		"""
		Stores person's head location as a list of x, y (right of robot -, left of robot +), and z coordinates
		in meters relative to spot between robot's feet.
		"""

		try:
			self.person_location = self.mem.getData("PeoplePerception/Person/" + str(person_id) + "/PositionInRobotFrame")

		except RuntimeError:
			# print "Couldn't get person's face location"
			self.person_location = None
			self.updatePersonID()

		else:
			self.robot_person_x, self.robot_person_y, self.robot_person_z = self.person_location

	def personLookingAtObjects(self):
		"""
		Returns whether the person is looking lower than the robot's feet.
		"""

		# update and check gaze data
		self.updatePersonGaze()
		if self.person_gaze is None:
			return False

		# update and check location data
		self.updatePersonLocation()
		if self.person_location is None:
			return False

		# threshold angle equals atan of x distance between person + robot divided by person's height
		threshold_angle = math.atan(self.robot_person_x / self.robot_person_z)

		# if person is looking in the area of the objects (gaze pitch < angle to look at robot's feet)
		if self.person_gaze_pitch < threshold_angle:
			return True

		return False

	def updateGazeObjectLocation(self, debug = False):
		"""
		Stores location of gaze relative to spot between robot's feet as a list of x, y, z in meters and yaw, pitch in radians.
		If the person is not looking near the objects, returns None.
		"""

		if not self.personLookingAtObjects():
			self.gaze_object_location = None

		# calculate x distance between robot and object
		person_object_x = self.robot_person_z * math.tan(self.person_gaze_pitch)
		robot_object_x = self.robot_person_x - person_object_x

		# calculate y distance between robot and object (left of robot +, right of robot -)
		person_object_y = person_object_x * math.tan(self.person_gaze_yaw)
		robot_object_y = self.robot_person_y + person_object_y

		# calculate robot head yaw needed to gaze at object
		self.robot_object_yaw = math.atan(robot_object_y / robot_object_x)

		robot_object_z = 0
		self.robot_object_pitch = 0

		if debug:
			print "\tperson gaze:", [math.degrees(angle) for angle in self.person_gaze]
			print "\tperson loc:", self.person_location
			print "\tpers obj x", person_object_x
			print "\tpers obj y", person_object_y

		self.gaze_object_location = [robot_object_x, robot_object_y, robot_object_z, self.robot_object_yaw, self.robot_object_pitch]

	def updateGazeConfidences(self, debug = False):
		"""
		Determines which object(s) the person is gazing at and adds to the count for those objects.
		These counts are stored in dictionary self.confidences as {object angle: confidence, ..., object angle: confidence}.
		"""

		if not self.gaze_object_location is None:

			for object_angle in self.gaze_confidences:

				# if gaze angle is within object_angle_error of the object angle on either side
				if abs(object_angle - self.robot_object_yaw) <= self.angle_error:

					# add 1 to the confidence for that object
					self.gaze_confidences[object_angle] += 1

					if debug:
						print "\t", math.degrees(object_angle),

			if debug:
				print

	def normalizeGazeConfidences(self):
		"""
		Divides the confidence (gaze count) for each object by the sum of all objects' gaze counts,
		so that the confidences sum to 100%.
		"""

		print "Object counts:", [[round(angle, 3), self.gaze_confidences[angle]] for angle in self.gaze_confidences]

		confidence_sum = sum(self.gaze_confidences.values())

		# if we at least got some data
		if confidence_sum != 0:

			for object_angle in self.gaze_confidences:
				self.gaze_confidences[object_angle] /= confidence_sum

	def trackGaze(self):

		self.updateGazeObjectLocation()
		self.updateConfidences()

	def analyzeGaze(self):

		 self.unsubscribeGaze()
		 self.normalizeConfidences()

	def count_objects(self):
		objects = self.segmentation.look_for_objects()
		return objects


#------------------------Main------------------------#

if __name__ == "__main__":

	print "#----------Audio Script----------#"

	connect("bobby.local")
	obj_name = r.ask_object()
	print obj_name

	broker.shutdown()
	exit(0)
