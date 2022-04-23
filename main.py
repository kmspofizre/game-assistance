import os
# from news_text_handler import text_handler  не работает
from flask import Flask, render_template, redirect, request
from werkzeug.utils import secure_filename
from data import db_session
from forms.user_registration import UserForm
from data.users import User
from data.news import News
from forms.news_form import NewsForm
from flask_login import LoginManager, login_required
import csv
from mail_sender import send_email
from dotenv import load_dotenv


app = Flask(__name__)
load_dotenv()

ALLOWED_EXTENSIONS = {'jpg', 'png', 'jpeg', 'docx'}  # для проверки расширения файла
app.config['UPLOAD_FOLDER'] = "static\img"
app.config['UPLOAD_NEWS_FOLDER'] = "static/news"
app.config['SECRET_KEY'] = 'nnwllknwthscd'
db_session.global_init("db/content.db")
login_manager = LoginManager()
login_manager.init_app(app)


with open('mails.csv', encoding='utf-8') as mails_file:
    mails = csv.DictReader(mails_file, delimiter=',', quotechar='"')
    required = list(filter(lambda x: x['почтовый домен'] == 'mail.ru', mails))
    print(required[0]['адрес для входа в почту'])


def allowed_file(filename):  # для проверки расширения файла
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
@app.route('/index')
def index():
    return render_template('main_page.html', title='Game Helper')


@app.route('/registration', methods=["GET", "POST"])
def registration():
    form = UserForm()
    if request.method == "POST":
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template("registration.html", form=form, error="Такой пользователь уже существует")
        if form.password.data != form.repeat_password.data:
            return render_template("registration.html", form=form, error="пароль")
        print("qwe")
        file = request.files['file']
        print("123")
        user = User(
            age=form.birthday.data,
            name=form.name.data,
            email=form.email.data,

        )
        if file and allowed_file(file.filename):
            print("hello")
            filename = secure_filename(file.filename)
            print("hello2")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print("hello3")
            user.profile_picture = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            print("hello4")
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        return redirect("/")
    return render_template('registration.html', form=form)


#@app.route('/news')
#def new(curr_new):  # через redirect
    #to_render = text_handler(curr_new)
    #return render_template('certain_news.html', text=to_render)


@app.route('/add_news', methods=["GET", "POST"])
def add_news():
    news_form = NewsForm()
    if request.method == "POST":
        db_sess = db_session.create_session()
        img = request.files['news_img']
        file = request.files['docx_file']
        if db_sess.query(News).filter(News.title == news_form.title.data):
            return render_template("add_news.html", form=news_form, error="Новость с таким заголовком уже сущесвует")
        if file.filename == '':
            return render_template("add_news.html", form=news_form, error="Отсутствует .docx file")
        news = News(
            title=news_form.title.data,
            revelance=news_form.importance.data
        )
        if file and img and allowed_file(file.filename) and allowed_file(img.filename):
            docx_filename = secure_filename(file.filename)
            img_filename = secure_filename(img.filename)
            file.save(os.path.join(app.config['UPLOAD_NEWS_FOLDER'], docx_filename))
            img.save(os.path.join(app.config['UPLOAD_FOLDER'], img_filename))
            news.image = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)
            news.news_markup = os.path.join(app.config['UPLOAD_NEWS_FOLDER'], docx_filename)
        db_sess.add(news)
        db_sess.commit()
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

