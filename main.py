from flask import Flask, render_template, redirect
from data import db_session
from forms.user_registration import UserForm
from forms.news_form import NewsForm
from flask_login import LoginManager, login_required
import csv
from mail_sender import send_email
from dotenv import load_dotenv


app = Flask(__name__)
load_dotenv()


app.config['SECRET_KEY'] = 'nnwllknwthscd'
db_session.global_init("db/content.db")
login_manager = LoginManager()
login_manager.init_app(app)


with open('mails.csv', encoding='utf-8') as mails_file:
    mails = csv.DictReader(mails_file, delimiter=',', quotechar='"')
    required = list(filter(lambda x: x['почтовый домен'] == 'mail.ru', mails))
    print(required[0]['адрес для входа в почту'])


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


@app.route('/add_news')
def add_news():
    news_form = NewsForm()
    return render_template('add_news.html', title='News', news_form=news_form)


def post_form():
    email = ''
    if send_email(email, 'Email verification', 'link', []):  # отправляем на нее письмо
        return f'Письмо отправлено успешно на адрес {email}'
    return f'Во время отправки письма на адрес {email} произошла ошибка'


@app.route('/check_email/<hashed_code>')
@login_required
def check_email(hashed_code):
    pass


def main():
    db_session.global_init("db/blogs.db")
    app.run()


if __name__ == '__main__':
    main()

