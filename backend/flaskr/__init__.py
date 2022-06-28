import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get("page", 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app, resources={r"*": {"origins": "*"}})

    # CORS Headers
    @app.after_request
    def after_request(response):
        response.headers.add(
            "Access-Control-Allow-Headers", "Content-Type,Authorization,true"
        )
        response.headers.add(
            "Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS,PATCH"
        )
        return response

    # Get all available categories
    @app.route('/categories', methods=['GET'])
    def get_all_available_categories():
        # get all the available categories
        categories = Category.query.order_by(Category.id).all()

        # format categories as dict with key/value as category id/type
        formatted_categories = {}
        for category in categories:
            formatted_categories[category.id] = category.type

        # return not found if categories is empty
        if len(formatted_categories) == 0:
            abort(404)

        # else return json object
        response_dict = {
            "success": True,
            "categories": formatted_categories
        }
        return jsonify(response_dict)

    # Get all questions

    @app.route('/questions')
    def get_all_questions():
        # get all the questions
        questions = Question.query.order_by(Question.id).all()
        paginated_formatted_questions = paginate_questions(request, questions)

        # get all categories
        categories = Category.query.order_by(Category.id).all()

        # format categories as dict with key/value as category id/type
        formatted_categories = {}
        for category in categories:
            formatted_categories[category.id] = category.type

        # return 404 if questions is empty or categories is empty
        if len(paginated_formatted_questions) == 0 or len(
                formatted_categories) == 0:
            abort(404)

        # else return json object
        response_dict = {
            "success": True,
            "questions": paginated_formatted_questions,
            "total_questions": len(questions),
            "categories": formatted_categories,
            "current_category": None
        }
        return jsonify(response_dict)

    # Delete a question
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_a_question(question_id):
        try:
            question = Question.query.get(question_id)
            category = Category.query.get(question.category)
            if question is None:
                abort(404)

            question.delete()
            questions = Question.query.order_by(Question.id).all()
            returned_questions = paginate_questions(request, questions)
            response_dict = {
                "success": True,
                "deleted": question_id,
                "questions": returned_questions,
                "total_questions": len(Question.query.all()),
                "current_category": category.type
            }
            return jsonify(response_dict)
        except BaseException:
            abort(422)

    # post a new question
    @app.route('/questions', methods=['POST'])
    def add_a_question():
        new_question = request.get_json()
        try:
            question = Question(
                new_question['question'],
                new_question['answer'],
                new_question['category'],
                new_question['difficulty']
            )
            question.insert()
            response_dict = {
                "success": True,
                "question": question.question,
                "answer": question.answer,
                "difficulty": int(question.difficulty),
                "category": int(question.category)
            }
            return jsonify(response_dict)
        except BaseException:
            abort(422)

    # search a question
    @app.route('/questions/search', methods=['POST'])
    def search_questions():

        try:
            request_str = request.get_json()['searchTerm']
            search_question = '%{}%'.format(request_str)

            questions = Question.query.filter(
                Question.question.ilike(search_question)).all()
            formatted_questions = [question.format() for question in questions]

            response_dict = {
                "success": True,
                "questions": formatted_questions,
                "total_questions": len(formatted_questions),
                "current_category": None
            }
            return jsonify(response_dict)
        except BaseException:
            abort(405)

    # get questions by category

    @app.route('/categories/<int:cat_id>/questions', methods=['GET'])
    def get_qestions_by_category(cat_id):
        try:
            # get all the questions filtered by cat_id
            questions = Question.query.filter_by(
                category=str(cat_id)).order_by(
                Question.id).all()
            formatted_questions = [question.format() for question in questions]

            # get category
            category = Category.query.get(cat_id)

            # else return json object
            response_dict = {
                "success": True,
                "questions": formatted_questions,
                "total_questions": len(questions),
                "current_category": category.type
            }
            return jsonify(response_dict)
        except BaseException:
            abort(404)

    @app.route('/quizzes', methods=['POST'])
    def get_quizzes():

        try:
            # get the category id
            category_id = int(request.get_json()['quiz_category']['id'])
            previous_questions = request.get_json().get(
                'previous_questions')  # previous questions

            if previous_questions is None:
                previous_questions = []
            else:
                previous_questions = request.get_json()["previous_questions"]

            categories = Category.query.all()  # query categories

            # store categories ids for check
            categories_id = []
            for cat in categories:
                categories_id.append(cat.id)

            # if category is not specified -> ALL
            if category_id == 0:
                # get all the questions
                questions = Question.query.order_by(Question.id).all()

                questions_id = []  # store the questions ids for comparison agains previous_questions
                for question in questions:
                    questions_id.append(question.id)

            elif (category_id in categories_id):  # a specific category
                # get all the questions filtered by category id
                questions = Question.query.filter_by(
                    category=str(category_id)).order_by(
                    Question.id).all()

                questions_id = []
                for question in questions:
                    questions_id.append(question.id)
            else:
                abort(400)

            # get random question id from questions_id
            question_id = random.choice(questions_id)

            # let assume the question is not answered
            answered = False
            # while the question is not answered, send the question and mark it
            # answered
            while not answered:
                if question_id in previous_questions:
                    question_id = random.choice(questions_id)
                else:
                    answered = True
                # base case
                if len(questions) == len(previous_questions):
                    return jsonify({"success": True})

            # get a question by id from questions
            def get_question(question_id):
                for question in questions:
                    if question.id == question_id:
                        return question

            question = get_question(question_id)
            question = question.format()

            response_dict = {
                "success": True,
                "question": question
            }

            return jsonify(response_dict)
        except BaseException:
            abort(400)
    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(404)
    def not_found(error):
        return({
            "success": False,
            "message": "resource not found",
            "error": 404
        }), 404

    @app.errorhandler(422)
    def unprocessible(error):
        return({
            "success": False,
            "message": "unprocessable",
            "error": 422
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return({
            "success": False,
            "message": "bad request",
            "error": 400
        }), 400

    @app.errorhandler(405)
    def not_found(error):
        return (jsonify({"success": False, "error": 405,
                         "message": "method not allowed"}), 405)

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': 'internal server error'
        }), 500

    return app
