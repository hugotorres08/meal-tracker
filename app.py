from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import date
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meal_tracker.db'
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)

class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    protein = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    calories = db.Column(db.Float, nullable=False)

class MealLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    food_id = db.Column(db.Integer, db.ForeignKey('food.id'), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    date = db.Column(db.String(10), nullable=False)
    food = db.relationship('Food')

class DailyGoal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.String(10), nullable=False)
    protein_goal = db.Column(db.Float, nullable=False, default=0)
    carbs_goal = db.Column(db.Float, nullable=False, default=0)
    calories_goal = db.Column(db.Float, nullable=False, default=0)

@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users)

@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form['name']
    db.session.add(User(name=name))
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        MealLog.query.filter_by(user_id=user_id).delete()
        DailyGoal.query.filter_by(user_id=user_id).delete()
        db.session.delete(user)
        db.session.commit()
    return redirect(url_for('index'))

@app.route('/user/<int:user_id>')
def user_dashboard(user_id):
    user = User.query.get(user_id)
    foods = Food.query.all()
    today = str(date.today())
    return render_template('dashboard.html', user=user, foods=foods, today=today)

@app.route('/add_food', methods=['POST'])
def add_food():
    name = request.form['name']
    protein = float(request.form['protein'])
    carbs = float(request.form['carbs'])
    calories = float(request.form['calories'])
    db.session.add(Food(name=name, protein=protein, carbs=carbs, calories=calories))
    db.session.commit()
    return redirect(request.referrer)

@app.route('/delete_food/<int:food_id>', methods=['POST'])
def delete_food(food_id):
    food = Food.query.get(food_id)
    if food:
        MealLog.query.filter_by(food_id=food_id).delete()
        db.session.delete(food)
        db.session.commit()
    return redirect(request.referrer)

@app.route('/log_meal/<int:user_id>', methods=['POST'])
def log_meal(user_id):
    food_id = int(request.form['food_id'])
    quantity = float(request.form['quantity'])
    log_date = request.form['date']
    log = MealLog(user_id=user_id, food_id=food_id, quantity=quantity, date=log_date)
    db.session.add(log)
    db.session.commit()
    return redirect(url_for('daily_summary', user_id=user_id, day=log_date))

@app.route('/delete_meal_log/<int:log_id>', methods=['POST'])
def delete_meal_log(log_id):
    log = MealLog.query.get(log_id)
    if log:
        user_id = log.user_id
        day = log.date
        db.session.delete(log)
        db.session.commit()
        return redirect(url_for('daily_summary', user_id=user_id, day=day))
    return redirect(request.referrer)

@app.route('/summary/<int:user_id>/<day>')
def daily_summary(user_id, day):
    logs = MealLog.query.filter_by(user_id=user_id, date=day).all()
    total_protein = sum(log.quantity * log.food.protein for log in logs)
    total_carbs = sum(log.quantity * log.food.carbs for log in logs)
    total_calories = sum(log.quantity * log.food.calories for log in logs)
    goal = DailyGoal.query.filter_by(user_id=user_id, date=day).first()
    if not goal:
        goal = DailyGoal(user_id=user_id, date=day, protein_goal=0, carbs_goal=0, calories_goal=0)
        db.session.add(goal)
        db.session.commit()
    return render_template('daily_summary.html', logs=logs, total_protein=total_protein,
                           total_carbs=total_carbs, total_calories=total_calories, goal=goal, user_id=user_id, day=day)

@app.route('/set_goal/<int:user_id>', methods=['POST'])
def set_goal(user_id):
    today = str(date.today())
    goal = DailyGoal.query.filter_by(user_id=user_id, date=today).first()
    if not goal:
        goal = DailyGoal(user_id=user_id, date=today)
        db.session.add(goal)
    goal.protein_goal = float(request.form['protein_goal'])
    goal.carbs_goal = float(request.form['carbs_goal'])
    goal.calories_goal = float(request.form['calories_goal'])
    db.session.commit()
    return redirect(url_for('daily_summary', user_id=user_id, day=today))

if __name__ == '__main__':
    with app.app_context():
        if not os.path.exists('meal_tracker.db'):
            db.create_all()
    app.run()


