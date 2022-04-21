from flask import Flask, render_template, redirect
from data import db_session
from forms.user_registration import UserForm


app = Flask(__name__)


app.config['SECRET_KEY'] = 'nnwllknwthscd'
db_session.global_init("db/content.db")


@app.route('/')
@app.route('/index')
def index():
    return render_template('main_page.html', title='Game Helper')


@app.route('/register')
def register():
    reg_form = UserForm()
    return render_template('registration.html', reg_form=reg_form, title='Registration')


@app.route('/news')
def new():
    to_render = """<h3>Заголовок новости.</h3>
<p class="new-text">Текст новости. Текст новости. Текст новости. Текст новости. Текст новости. Текст новости. Текст новости. Текст новости. Текст новости. Текст новости. Текст новости. Текст новости. Текст новости. Текст новости. Текст новости.</p>
<p class="new-text">Текст новости. Текст новости. Текст новости. Текст новости.</p>
<h3>Еще заголовок.</h3>
<p class="new-text"></p>
<p class="new-text"></p>
"""
    return render_template('certain_news.html', text=to_render)


def main():
    db_session.global_init("db/blogs.db")
    app.run()


if __name__ == '__main__':
    main()

