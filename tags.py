import database as db

_tags = []
_questions = []

def get(question_id):
	"""
	Get a specific tag
	"""
	return get_all()[question_id-1]

def get_all():
	"""
	Get list of all tags
	Returns list in the form of [tag]
	"""

	global _tags
	if not _tags:
		db.cursor.execute('SELECT tag FROM Tags')
		raw_tags = db.cursor.fetchall()
		_tags = [tag[0] for tag in raw_tags]
	return _tags

def get_questions():
	"""
	Gets list of all questions
	"""

	global _questions
	if not _questions:
		db.cursor.execute('SELECT question FROM questions')
		raw_questions = db.cursor.fetchall()
		_questions = [question[0] for question in raw_questions]
	return _questions
