from flask import Flask, render_template, redirect
from data import db_session


app = Flask(__name__)


app.config['SECRET_KEY'] = 'nnwllknwthscd'
db_session.global_init("db/content.db")


@app.route('/')
@app.route('/index')
def index():
    return render_template('main_page.html')


@app.route('/register')
def register():
    pass


def main():
    db_session.global_init("db/blogs.db")
    app.run()


if __name__ == '__main__':
    main()

