from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = 'pocketsmart-dev-key'
DB = Path(__file__).with_name('pocketsmart.db')

def db():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c

def init_db():
    c=db(); c.execute('CREATE TABLE IF NOT EXISTS expenses(id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT, amount REAL, note TEXT)'); c.commit(); c.close()

def categories():
    return ['Food','Travel','Shopping','Education','Bills','Entertainment','Other']

def recommendations(total, budget):
    if budget <= 0: return ['Set a monthly budget to start tracking your spending.']
    ratio = total / budget
    if ratio >= 1: return ['You are over budget. Review non-essential spending first.', 'Try setting category-wise limits for the next month.']
    if ratio >= .8: return ['You are close to your budget limit. Reduce optional spending.', 'Keep a small emergency buffer for unexpected expenses.']
    return ['Your spending is within the budget.', 'Consider saving the remaining amount instead of increasing discretionary spending.']

@app.route('/')
def home():
    c=db(); rows=c.execute('SELECT * FROM expenses ORDER BY id DESC').fetchall(); c.close()
    total=sum(r['amount'] for r in rows); budget=float(session.get('budget', 0) or 0)
    return render_template('index.html', rows=rows, total=total, budget=budget, remaining=budget-total, recommendations=recommendations(total,budget), categories=categories())

@app.post('/budget')
def budget():
    try: session['budget']=float(request.form['budget'])
    except ValueError: flash('Enter a valid budget.')
    return redirect(url_for('home'))

@app.post('/expense')
def expense():
    try: amount=float(request.form['amount'])
    except ValueError: flash('Enter a valid amount.'); return redirect(url_for('home'))
    c=db(); c.execute('INSERT INTO expenses(category,amount,note) VALUES(?,?,?)',(request.form['category'],amount,request.form.get('note',''))); c.commit(); c.close()
    return redirect(url_for('home'))

@app.post('/delete/<int:eid>')
def delete(eid):
    c=db(); c.execute('DELETE FROM expenses WHERE id=?',(eid,)); c.commit(); c.close(); return redirect(url_for('home'))

@app.route('/planner')
def planner():
    return render_template('planner.html')

@app.post('/recommend')
def recommend():
    kind=request.form.get('kind','General'); amount=float(request.form.get('amount') or 0); people=int(request.form.get('people') or 1)
    base={'Party':1500,'Home':5000,'Jewelry':10000,'General':2000}.get(kind,2000)
    estimate=base*people if kind=='Party' else base
    if amount and amount < estimate: tips=f'For {kind}, keep the plan simple and compare prices before buying.'
    else: tips=f'Your amount can support a {kind} plan around the entered budget.'
    return render_template('recommend.html',kind=kind,amount=amount,estimate=estimate,tips=tips)

if __name__=='__main__':
    init_db(); app.run(debug=True)
