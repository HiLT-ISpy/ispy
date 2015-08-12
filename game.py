import time
import logging as log

import objects
import models
import database as db
import config
from robot import robot
import interface

class Game:
	"""
	Main class that handles game logic
	"""

	def playGame(self, number_of_objects):
		"""
		Play the game
		"""

		log.info('Playing game %d', self.id)

		start = time.time()

		# Generate all image probabilities at once since this takes a little while
		if config.args.imagemodels:
			Pi = models.gen_image_probabilities(self, number_of_objects)
		else:
			#we use -1 to say that we'll skip that tag, so this skips all tags for all objects
			Pi = [[-1] * 289] * 17

		# Initialize game stats to empty
		NoOfQuestions = 0
		round_wins = 0
		round_losses = 0
		avg_win = 0
		avg_lose = 0
		question_answers = {}
		questions_asked = {}
		objlist = objects.get_all()
		count = 0

		# quit variable passed to main that tells if user wants to quit
		quit = False

		# For each object in the set
		for i in objlist:
			robot().initGazeCounts()

			if config.args.notsimulated:
				for j in range(len(objlist)):
					print objlist[j].name
				interface.say("Choose an object. Don't tell me! ")
				time.sleep(2.5)
			#TODO: ask if the person is ready???

			result, number_of_questions, answers, askedQuestions = i.playObject(self, Pi, number_of_objects)
			log.info("Game %d, object %d complete, updating stats", self.id, i.id)

			#averages are calculated later (in main) using these sums
			if result == 0: # Loss
				round_losses += 1
				avg_lose += number_of_questions
			else: # Win
				round_wins += 1
				avg_win += number_of_questions
			NoOfQuestions += number_of_questions

			# Save questions and answers for later
			questions_asked[i.id] = askedQuestions
			question_answers[i.id] = answers

			count += 1

			if config.args.notsimulated == True:
				quit = not interface.ask("Do you want to play again?")
				# quit = interface.ask("Would you like to quit this game early? \nThere are %d rounds left. " % (17 - count))
				if quit:
					break

		# Save results
		self._record(round_wins, round_losses, NoOfQuestions, count)

		end = time.time()
		log.info("Game %d complete (Took %ds)", self.id, int(end - start))

		return round_wins, round_losses, NoOfQuestions, avg_win, avg_lose, question_answers, questions_asked, quit

	def _record(self, wins, losses, num_questions, number_of_objects_played):
		"""
		Record data for each game
		"""

		with open("game.txt", "a") as myfile:
			myfile.write("Round " + str(self.id) + ": ")
			myfile.write("Wins=" + str(wins) + ', Losses='+str(losses))
			myfile.write(" Accuracy: " + str(wins/float(number_of_objects_played)) + "\n")
			myfile.write("Average number of questions: " + str(num_questions/float(number_of_objects_played)) + "\n")


	def __init__(self, id):
		self.id = id
