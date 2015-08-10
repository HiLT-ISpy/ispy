import os
import time
import logging as log

import numpy as np

import questions
import tags
import database as db
import config
from robot import robot, Robot, broker, connect
from naoqi import ALBroker
import interface

_objects = []
_answers = []

class Object:

	def playObject(self, game, Pi, number_of_objects):
		"""
		Play this object
		"""

		log.info('Playing object %d in game %d', self.id, game.id)
		objects = self.gen_init_prob(number_of_objects)

		folder =  os.getcwd()
		answer_data = get_all_answers(number_of_objects)
		NoOfQuestions = 0

		# at the very beginning of a round, each object has an equal chance of getting picked
		pO = np.array([1/float(number_of_objects)] * number_of_objects)

		askedQuestions = []
		answers = []
		split = 0

		difference_threshold = 0.15

		# while the best guess is less than 15% probability away from the 2nd-best guess and we've asked fewer than 15 questions
		while np.sort(pO)[pO.size - 1] - np.sort(pO)[pO.size - 2] < difference_threshold and len(askedQuestions) < 15:
			# Find best question (aka gives most info)
			best_question = questions.get_best(game, objects, askedQuestions, pO, Pi, split, number_of_objects)
			# Save under questions already asked
			askedQuestions.append(best_question)
			# Ask question and update probabilies based on the answer
			pO, answers = questions.ask(best_question, self, game, answers, pO, Pi, objects, number_of_objects, answer_data)
			if config.args.robot:
				robot().analyzeGaze()

			# Split the current subset into two more subsets
			split = questions.get_subset_split(pO, number_of_objects)
		log.info('Finished asking %d questions', len(askedQuestions))

		# Get most likely object
		minimum=np.max(pO)
		itemindexes = [i for i,x in enumerate(pO) if x==minimum]
		objects = np.asarray([[obj] for obj in get_all()])
		guess = objects[itemindexes][0][0]

		# Guess object (Compare what the system thinks is most likely to object currenly in play)
		result = self._guess_object(guess)

		# Save results
		self._record_results(game, answers, askedQuestions, guess, result, number_of_objects)

		return result, len(askedQuestions), answers, askedQuestions


	def gen_init_prob(self, number_of_objects):
		"""
		Fetches the proportions of yes answers
		Returns a list containing sub-lists, each corresponding to an object
		Each sub-list contains 289 tuples, one per question
		Each tuple is in the form of (yes_answers, total_answers)
		"""

		objects = []
		for i in range(number_of_objects):
			objects.append([])

		db.cursor.execute('SELECT qid, oid, SUM(answer), COUNT(*) FROM answers GROUP BY oid, qid')
		for row in db.cursor.fetchall():
			objects[int(row[1])-1].append((int(row[2]), int(row[3])))

		return objects


	def _record_results(self, game, game_answers, game_questions, guess, result, number_of_objects):
		"""
		Puts results into the DB as well as writing them to file for examination
		"""
		# TODO: make sure this can be used for new objects and when playing with the human's choice of object

		log.info('Recording object results to the database')
		for i in range(0, len(game_questions)):
			T = questions.get_t(self.id, game_questions[i], number_of_objects)
			if game_answers[i] == True:
				db.cursor.execute("SELECT yes_answers FROM Pqd where t_value = %s", (T,))
				yes_count = db.cursor.fetchone()[0]
				#print yes_count, 'yes'
				db.cursor.execute("UPDATE Pqd SET yes_answers = %s WHERE t_value = %s", (yes_count + 1, T))

			db.cursor.execute("SELECT total_answers FROM Pqd where t_value = %s", (T,))
			total_count = db.cursor.fetchone()[0]
			#print total_count
			db.cursor.execute("UPDATE Pqd SET total_answers = %s WHERE t_value = %s", (total_count + 1, T))

			db.cursor.execute("INSERT INTO answers (oid, qid, answer) VALUES (%s, %s, %s)", (str(self.id), game_questions[i], game_answers[i]))

			db.connection.commit()

		if result == 0:
			result = 'lose'
		else:
			result = 'win'

		# TODO: clean up all the text files because this is kind of ridiculous
		with open("game.txt", "a") as myfile:
			myfile.write(str(game.id)+','+ str(self.id) +','+ str(guess.name)+"," + str(self.name) + "," + str(len(game_questions)) + "," + result  +  "\n")
		myfile.close()

		with open("answers.txt", "a") as answerfile:
			answerfile.write("\n" + str(game.id) + " " + str(self.id) + " " + result + "\n")
			for i in range(0, len(game_questions)):
				answerfile.write(tags.get(game_questions[i]) + " -> " + str(game_answers[i]) + "\n")
		answerfile.close()


	def _guess_object(self, guess):
		"""
		Compare the object that the system thinks is most likely to the object currently in play
		"""

		if config.args.notsimulated:
			self.id, self.name = get_actual(guess)
		if self.id == guess.id:
			log.info('Win [Guess: %s | Actual: %s]', guess.name, self.name)
			return 1
		else:
			log.info('Lose [Guess: %s | Actual: %s]', guess.name, self.name)
			return 0

	def __init__(self, id, name):
		# assigns an ID as a placeholder because we can't read the person's mind
		# in order to assign an id for the purposes of initialization
		# however, the id picked here does end up getting used if the computer
		# generates the objects/answers
		self.id = id
		self.name = name


def get(object_id):
	"""
	Get a specific object based on id
	"""

	return get_all()[object_id-1]

def get_all():
	"""
	Returns a list of all objects
	"""

	# TODO: make sure new objects have already been written into the database
	global _objects
	if not _objects:
		db.cursor.execute('SELECT DISTINCT(observation_id), name FROM NameInfo')
		for obj in db.cursor.fetchall():
			_objects.append(Object(obj[0], obj[1]))
	return _objects

def get_actual(guess):
	"""
	Returns the object the human player was thinking of
	"""

	global _objects
	answer = interface.ask("My guess is %s. Was I right? " % guess.name)

	if answer:
		obj_name = guess.name
		obj_id = guess.id
	else:
		if robot():
			obj_name = robot().ask_object()

		else:
			print "\nObject names:\n"
			for j in range(len(_objects)):
				print _objects[j].name
			obj_name = raw_input("\nWhat was your object? Remember to type it exactly as you saw above. ")
		while True:
			check = False
			for i in range(len(_objects)):
				if _objects[i].name == obj_name:
					check = True
					obj_id = _objects[i].id
					break
			if check == True:
				break
			obj_name = raw_input("It seems as though you mistyped. Please try typing the name of your object again. ")

	return obj_id, obj_name

def get_all_answers(number_of_objects):
	"""
	Returns a list of sublists pertaining to each game
	For each game's sublist there is a sublist for each object
	Each object's sublist contains the answers for all 289 possible questions about the object
	"""

	global _answers
	if not _answers:
		_answers = []

		db.cursor.execute('SELECT answer FROM reference_answers')
		questionanswers = db.cursor.fetchall()

		answercnt = 0

		for gamecnt in range(30):
			_answers.append([])
			for objcnt in range(17):
				_answers[gamecnt].append([])
				for tagcnt in range(289):
					answer = int(questionanswers[answercnt][0])
					_answers[gamecnt][objcnt].append(answer)
					answercnt += 1

		# total_length = 0
		# for i in range(30):
		# 	for j in range(number_of_objects):
		# 		total_length += len(_answers[i][j])

	return _answers
