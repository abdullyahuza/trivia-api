import os
from dotenv import load_dotenv
import unittest
import json
from flask_sqlalchemy import SQLAlchemy

from flaskr import create_app
from models import setup_db, Question, Category
load_dotenv()

DB_DIALECT=os.getenv("DB_DIALECT")
DB_USERNAME = os.getenv("DB_USERNAME")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SERVER = os.getenv("DB_SERVER")
DB_NAME = os.getenv("TEST_DB_NAME")
DB_PORT=os.getenv("DB_PORT")


class TriviaTestCase(unittest.TestCase):
    """This class represents the trivia test case"""

    def setUp(self):
        """Define test variables and initialize app."""
        self.app = create_app()
        self.client = self.app.test_client

        # database setup
        self.database_name = DB_NAME
        self.database_path = f"{DB_DIALECT}://{DB_USERNAME}:{DB_PASSWORD}@{DB_SERVER}:{DB_PORT}/{DB_NAME}"

        setup_db(self.app, self.database_path)
        self.new_question = {
              "question": "What is my name",
              "answer": "Abdull Yahuza",
              "difficulty": 1,
              "category": 3
        }
        self.search_question = {
            "searchTerm": "What is my name"
        }
        self.category_test = 3
        self.quiz_data = {
            "previous_questions": [],
            "quiz_category": {
                "id": 1,
                "type": "Science"
            }
        }
        self.bad_quiz_data = {
            "previous_questions": [],
            "quiz_category": {
                "id": None
            }
        }
        # binds the app to the current context
        with self.app.app_context():
            self.db = SQLAlchemy()
            self.db.init_app(self.app)
            # create all tables
            self.db.create_all()
            
    
    def tearDown(self):
        """Executed after reach test"""
        pass

    """
    TODO
    Write at least one test for each test for successful operation and for expected errors.
    """
    def test_get_all_available_categories(self):
        response = self.client().get('/categories')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(len(data["categories"]))

    def test_405_get_all_available_categories(self):
        response = self.client().put('/categories')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["error"], 405)
        self.assertEqual(data["message"], "method not allowed")

    def test_get_all_questions(self):
        response = self.client().get('/questions')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(len(data["questions"]))
        self.assertTrue(len(data["categories"]))
        self.assertTrue(data["total_questions"])

    # def test_delete_a_question(self):
    #     questions = Question.query.all()
    #     last_question = questions[len(questions)-1]
        
    #     response = self.client().delete(f"/questions/{last_question.id}")
    #     data = json.loads(response.data)

    #     question = Question.query.filter(Question.id == last_question.id).one_or_none()

    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(data["success"], True)
    #     self.assertEqual(data["deleted"], last_question.id)

    def test_422_if_question_does_not_exist(self):
        response = self.client().delete("questions/5555")
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "unprocessable")

    def test_add_new_question(self):
        response = self.client().post("/questions", json=self.new_question)
        data = json.loads(response.data)

        questions = Question.query.all()
        last_question = questions[len(questions)-1]

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertEqual(data["question"], self.new_question['question'])
        self.assertEqual(data["answer"], self.new_question['answer'])
        self.assertEqual(data["difficulty"], self.new_question['difficulty'])
        self.assertEqual(data["category"], self.new_question['category'])

    def test_405_if_add_question_not_allowed(self):
        response = self.client().post("/questions/45", json=self.new_question)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "method not allowed")

    def test_404_sent_requesting_beyond_valid_page(self):
        response = self.client().get("/questions?page=1000")
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data["success"], False)
        self.assertEqual(data["message"], "resource not found")

    def test_search_questions(self):
        response = self.client().post("/questions/search", json=self.search_question)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)

    def test_405_search_questions(self):
        response = self.client().put("/questions/search", json=self.search_question)
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 405)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "method not allowed")

    def test_get_questions_by_category(self):
        response = self.client().get(f'/categories/{self.category_test}/questions')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data["success"], True)
        self.assertTrue(len(data["questions"]))
        self.assertEqual(data["current_category"], Category.query.get(self.category_test).type)

    def test_404_questions_category(self):
        response = self.client().get('/categories/00000/questions')
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "resource not found")

    def  test_get_quizzes(self):
        response = self.client().post('/quizzes', json=self.quiz_data)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['success'], True)

    def  test_405_get_quizzes(self):
        response = self.client().delete('/quizzes', json=self.quiz_data)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "method not allowed")

    def test_play_quiz_400(self):
        response = self.client().post('/quizzes', json=self.bad_quiz_data)
        data = json.loads(response.data)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['success'], False)
        self.assertEqual(data['message'], "bad request")

        
# Make the tests conveniently executable
if __name__ == "__main__":
    unittest.main()