import os
from news_text_handler import text_handler
from flask import Flask, render_template, redirect, request, abort, url_for
from werkzeug.utils import secure_filename
from data import db_session
from forms.user_registration import UserForm
from data.users import User
from data.news import News
from forms.news_form import NewsForm
from flask_login import LoginManager, login_required, login_user, current_user
import csv
from mail_sender import send_email
from dotenv import load_dotenv
import datetime
import secrets
from werkzeug.security import generate_password_hash


app = Flask(__name__)
load_dotenv()

ALLOWED_EXTENSIONS = {'jpg', 'png', 'jpeg', 'docx'}  # для проверки расширения файла
app.config['UPLOAD_FOLDER'] = "static/img"
app.config['UPLOAD_NEWS_FOLDER'] = "static/news"
app.config['SECRET_KEY'] = 'nnwllknwthscd'
db_session.global_init("db/content.db")
db_sess = db_session.create_session()
login_manager = LoginManager()
login_manager.init_app(app)


with open('mails.csv', encoding='utf-8') as mails_file:
    MAILS = list(csv.DictReader(mails_file, delimiter=',', quotechar='"'))


def separate_mail_domain(mail_address):
    ind = mail_address.find('@')
    mail_domain = mail_address[ind + 1:]
    return mail_domain


def find_mail_site(mail_address):
    mail_domain = separate_mail_domain(mail_address)
    required = list(filter(lambda x: x['почтовый домен'] == mail_domain, MAILS))
    try:
        return required[0]['адрес для входа в почту']
    except IndexError:
        return ''


def send_confirmation_code(token):
    hash_code = token
    send_email(current_user.email, 'Confirm registration', hash_code, [])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def change_filename(file):
    file.filename = secure_filename(file.filename)
    return file


def secure_multiple(files):
    return list(map(change_filename, files))


def process_docx_file(docx_file):
    docx_file.filename = secure_filename(docx_file.filename)
    docx_file.save(os.path.join(f'docxs/{docx_file.filename}'))
    markup = text_handler(f'docxs/{docx_file.filename}')
    os.remove(os.path.join(f'docxs/{docx_file.filename}'))
    return markup


def process_images(images, news_header):
    filenames = []
    for im in images:
        im.save(os.path.join(f'static/img/news/{im.filename}{news_header[:5]}'))
        filenames.append(f'static/img/news/{im.filename}{news_header[:5]}')
    filenames = ','.join(filenames)
    return filenames


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/')
@app.route('/index')
def index():
    return render_template('main_page.html', title='Game Assistance')


@app.route('/registration', methods=["GET", "POST"])
def registration():
    form = UserForm()
    if form.validate_on_submit():
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template("registration.html", form=form, error="Такой пользователь уже существует")
        if form.password.data != form.repeat_password.data:
            return render_template("registration.html", form=form, error="Пароли не совпадают")
        file = request.files['file']
        user = User(
            day_of_birth=form.birthday.data,
            name=form.name.data,
            email=form.email.data,
        )
        if file and allowed_file(file.filename):
            # filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
            user.profile_picture = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        token = secrets.token_urlsafe(16)
        print(token)
        user.set_email_code(token)
        user.set_password(form.password.data)
        db_sess.add(user)
        db_sess.commit()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        login_user(user, remember=True)
        send_confirmation_code(token)
        return redirect('/confirm_mail')
    return render_template('registration.html', form=form)


@app.route('/confirm_mail')
def confirm_mail():
    mail_site = find_mail_site(current_user.email)
    return render_template('confirm_mail.html', title='Mail confirmation', mail_site=mail_site)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = None # LoginForm() - wtf_форма
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        return render_template('login.html',
                               message="Неправильный логин или пароль",
                               form=form)
    return render_template('login.html', title='Авторизация', form=form)


@app.route('/news')
def new(curr_new):  # через redirect
    to_render = text_handler(curr_new)
    return render_template('certain_news.html', text=to_render)


@app.route('/add_news', methods=["GET", "POST"])
@login_required
def add_news():
    news_form = NewsForm()
    if news_form.validate_on_submit():
        img = news_form.pictures.raw_data
        docx_file = news_form.text.data

        img = secure_multiple(img)
        news_markup = process_docx_file(docx_file)
        images = process_images(img, news_form.title.data)

        news = News(
            title=news_form.title.data,
            image=images,
            date_of_creation=datetime.datetime.now(),
            weight=1,
            news_markup=news_markup
        )
        db_sess.add(news)
        db_sess.commit()
        redirect('/')
    return render_template('add_news.html', title='News', news_form=news_form)


@app.route('/check_email/<user_token>')
@login_required
def check_email(user_token):
    code_check = current_user.check_email_code(user_token)
    if code_check:
        current_user.confirmed = True
        return render_template('page_confirmed.html', title='Page confirmed',
                               welcome=f"src={url_for('static', filename='img/welcome_to_the_family.gif')}")
    abort(404)


def main():
    db_session.global_init("db/blogs.db")
    app.run()


if __name__ == '__main__':
    main()

