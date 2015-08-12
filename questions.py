import math
import time
import logging as log
import sys

import numpy as np

import tags
import database as db
import config
from robot import robot
import interface

# global variables to store constant values retrieved from database by functions
_questions = []
_descriptions = []


def ask(question_id, object_we_play, game, answers, pO, Pi, objects, number_of_objects, answer_data):
	"""
	Asks a question and updates probabilities based on the answer
	"""

	# gets probability that an answer will be yes for each of the 7 possible t-values of question/answer combos
	probabilityD = get_tval()

	# gets the correct question for the given tag
	question_tag = tags.get(question_id)
	questions = tags.get_questions()
	question = questions[question_id - 1]

	# in not simulated game, get answer from user
	if config.args.notsimulated:
		answer = interface.ask(question + " ")

	# in simulated game, get answer from answer bank in database
	else:
		answer = answer_data[game.id-1][object_we_play.id-1][question_id-1]
		print question, answer

	answers.append(answer)

	multipliers = []

	for objectID in range(17): # for all known objects
		# count the number of that object's descriptions that contain the tag used to formulate that question
		T = get_t(objectID+1, question_id, number_of_objects)

		# number of yes answers to this question/object combo
		yes_answers = objects[objectID][question_id-1][0]

		# total number of answers given for this question/object combo
		total_answers = objects[objectID][question_id-1][1]

		# TODO: see if Dr. Nielsen has any suggestions for improving the use of the
		# image models since they reduce the accuracy at the moment

		if answer:
			K = probabilityD[T] + (yes_answers + 1)/(total_answers + 2.0)
			# if Pi is -1 then it means we're skipping the image models for that tag
			if Pi[0][question_id-1] == -1:
				multiplier = K / 2
				multipliers.append(multiplier)
			else:
				multiplier = (K + Pi[objectID][question_id-1]) / 3
				multipliers.append(multiplier)
		else:
			K = (1 - probabilityD[T]) + (total_answers - yes_answers + 1)/(total_answers + 2.0)
			if Pi[0][question_id-1] == -1:
				multiplier = K / 2
			else:
				multiplier = (K + 1 - Pi[objectID][question_id-1]) / 3

		pO[objectID] *= multiplier

	for objectID in range(17,number_of_objects): # TODO: for all new objects/unknown tags for a new object
		# this assigns a probability to unknown objects based on the idea that
		# an object is about as likely as the rest of the objects to have the quality
		# of a certain tag - i.e. many objects are balls, but not many objects are polka dotted
		# TODO: make more sophisticated - some tags are opposites, so if we know an opposite then we
		# can take that into consideration when finding the multiplier
		multiplier = np.mean(multipliers)
		pO[objectID] *= multiplier

	# Normalize the probabilities so that all object probabilities will sum to 1
	pO /= np.sum(pO)

	# Save the questions to each answer and the updated probabilities
	with open("example.txt", "a") as myfile:
		myfile.write(str(question_tag) + " -> " + str(answer)  + " \n")
		myfile.write(str(pO) + "\n")

	return pO, answers


def get_best(game, objects, asked_questions, pO, Pi, start, number_of_objects):
	"""
	Finds the question that best splits our current subset of objects
	"""

	tvals = get_tval()

	# Get top and bottom halves of current subset
	top = (number_of_objects - start - 1)/2 + start + 1
	bottom = number_of_objects - top
	bestDifference = 10
	bestD = 0

	probabilities_yes = []
	probabilities_no = []
	for i in range(number_of_objects):
		probabilities_yes.append(0)
		probabilities_no.append(0)

	# We only consider objects beyond the start index when deciding
	# Objects below the index are still updated when the question is asked and can shift back into play, but decisions are not made based on them while they're below start
	pO_sorted = np.argsort(pO)
	objects_considered = pO_sorted[start:]

	# Look over all tags/potential questions
	for q in range(289):
		yes = 0
		no = 0

		p_for_yes = 0
		p_for_no = 0

		pi_given_yes_times_log = 0
		pi_given_no_times_log = 0

		# Don't reask questions
		if q not in asked_questions:
			# Only look at objects in the correct subset
			for obj in objects_considered:

				T = get_t(obj+1, q+1, number_of_objects) # add 1 to object and question indices to change from 0-16 -> 1-17
				num_yes = objects[obj][q][0]
				length = objects[obj][q][1]
				if Pi[obj][q] == -1:
					probabilities_yes[obj] = pO[obj] * (tvals[T] + (num_yes + 1.0)/(length + 2.0)) / 2
					probabilities_no[obj] = pO[obj] * ((1 - tvals[T]) + (length - num_yes + 1.0)/(length + 2.0)) / 2
				else:
					probabilities_yes[obj] = pO[obj] * (tvals[T] + (num_yes + 1.0)/(length + 2.0) + Pi[obj][q]) / 3
					probabilities_no[obj] = pO[obj] * ((1 - tvals[T]) + (length - num_yes + 1.0)/(length + 2.0) + 1 - Pi[obj][q]) / 3

			# Normalize the probabilities
			probabilities_yes = np.asarray(probabilities_yes)
			probabilities_no = np.asarray(probabilities_no)
			probabilities_yes = probabilities_yes / sum(probabilities_yes)
			probabilities_no = probabilities_no / sum(probabilities_no)

			# Do some fancy math to find out which tag lowers total entropy the most (AKA it gives us the most knowledge)
			for obj in objects_considered:
				num_yes = objects[obj][q][0]
				length = objects[obj][q][1]

				p_for_yes += pO[obj] * num_yes / length
				p_for_no += pO[obj] * (length - num_yes) / length

				yes  += probabilities_yes[obj]
				no += probabilities_no[obj]

				pi_given_yes_times_log += probabilities_yes[obj] * math.log(probabilities_yes[obj], 2)
				pi_given_no_times_log += probabilities_no[obj] * math.log(probabilities_no[obj], 2)

			entropy = -p_for_yes * pi_given_yes_times_log - p_for_no * pi_given_no_times_log
			if entropy < bestDifference:
				bestD = q+1 # add one to change index from 0-16 -> 1-17
				bestDifference = entropy

	return bestD

def copy_into_answers():
	"""
	QuestionAnswers holds just the answer set data
	Copies the pure data into a table that will be appended to throughout gameplay
	"""

	log.info('Copying into answers')
	db.cursor.execute('SELECT tag, answer, object from QuestionAnswers')
	question_answers = db.cursor.fetchall()

	for q_a in question_answers:
		db.cursor.execute('SELECT id from Tags where tag = %s', (q_a[0],))
		qid = db.cursor.fetchone()[0]
		db.cursor.execute('INSERT INTO answers (qid, oid, answer) VALUES (%s, %s, %s)', (qid, q_a[2], q_a[1]))

	db.connection.commit()

def build_pqd(number_of_objects):
	"""
	Pqd is the probability that an the answer will be yes to a keyword asked about an object where the keyword shows up X number of times in the descriptions
	Summed over all objects where a keyword shows up X number of times
	"""

	log.info('Building Pqd')
	probabilityD = [0,0,0,0,0,0,0]
	denominator = [0,0,0,0,0,0,0]

	all_tags = tags.get_all()

	for objectID in range(1, number_of_objects + 1):
		log.info("	Object %d", objectID)
		for tag in range(0, 289):

			# T is a based on a tag and an object description. T is how many times a tag is used in an object's description. It can be 0-6
			db.cursor.execute('SELECT * FROM Descriptions WHERE description like "%' + all_tags[tag] + '%" AND objectID = ' + str(objectID))
			T = len(db.cursor.fetchall())

			# count is the number of times someone answered yes to a tag/object pair
			db.cursor.execute('SELECT * FROM QuestionAnswers WHERE tag = "' + all_tags[tag] + '" AND object = ' + str(objectID) + ' AND answer = TRUE')
			count = len(db.cursor.fetchall())

			# D is the total number of times a tag/object pair has been asked (yes's and no's)
			db.cursor.execute('SELECT * FROM QuestionAnswers WHERE tag = "' + all_tags[tag] + '" AND object = ' + str(objectID))
			D = len(db.cursor.fetchall())

			# For the T value based on th specific tag/object pair, update the probability of all tag/object pairs with the same T value
			probabilityD[T] += count
			denominator[T] += D

	for freq in range(0,7):
		# This puts the sum of the yes answers and the total answers into the row that corresponds with the T value
		db.cursor.execute('INSERT INTO Pqd (t_value, yes_answers, total_answers) VALUES (%s, %s, %s)', (freq, probabilityD[freq], denominator[freq]))
		db.connection.commit()


def get_subset_split(pO, number_of_objects):
	"""
	When probabilities ordered least to greatest, returns index of largest difference between probabilities
	System asks questions to try to split subset in half each time, so the split should move closer to the max probability each time
	"""

	pO_sorted = np.sort(pO)
	pO_args_sorted = np.argsort(pO)

	max_diff = 0
	max_diff_index = 0

	for x in range(pO_sorted.size-1):
	    if pO_sorted[x+1] - pO_sorted[x] > max_diff:
			max_diff = pO_sorted[x+1] - pO_sorted[x]
	 		max_diff_index = x

	return max_diff_index


def get_tval():
	"""
	Gets the proportion of yes answers to all answers for each of the 7 possible T-values.
	This probability/proportion is used to predict the person's answer based on the T-value for that question/object combo.
	"""

	db.cursor.execute('SELECT yes_answers/total_answers FROM Pqd')

	raw_tvals = db.cursor.fetchall()

	tvals = [float(tval[0]) for tval in raw_tvals]

	return tvals


def get_t(object_id, question_id, number_of_objects):
	"""
	Returns the number of an object's descriptions that contain a specific tag
	"""

	global _descriptions

	if not _descriptions:
		_descriptions = [{} for _ in range(number_of_objects)]
		all_tags = tags.get_all()
		db.cursor.execute('SELECT description, objectID, descNum FROM Descriptions')
		for row in db.cursor.fetchall():
			for tag in all_tags:
				if tag in row[0]:
					if not tag in _descriptions[row[1]-1]:
						_descriptions[row[1]-1][tag] = 1
					else:
						_descriptions[row[1]-1][tag] += 1

	tag = tags.get(question_id)
	object_id = int(object_id)
	o = _descriptions[object_id-1]
	if not tag in o:
		return 0
	return o[tag]
