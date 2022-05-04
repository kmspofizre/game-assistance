import os
from news_text_handler import text_handler
from flask import Flask, render_template, redirect, abort, url_for
from werkzeug.utils import secure_filename
from data import db_session
from data.users import User
from data.news import News
from data.themes import Theme
from data.genres import Genres
from data.comments import Comment
from forms.news_form import NewsForm
from forms.login_form import LoginForm
from forms.user_registration import UserForm
from forms.theme_form import ThemeForm
from forms.comment_form import CommentForm
from flask_login import LoginManager, login_required, login_user, current_user
import csv
from mail_sender import send_email
from dotenv import load_dotenv
import datetime
import secrets
from PIL import Image


app = Flask(__name__)
load_dotenv()

ALLOWED_EXTENSIONS = {'jpg', 'png', 'jpeg', 'docx'}
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


def define_comment_owner(comments):
    return list(map(lambda x: db_sess.query(User).filter(User.id == x.user_id).first().name, comments))


def process_docx_file(docx_file):
    docx_file.filename = secure_filename(docx_file.filename)
    docx_file.save(os.path.join(f'docxs/{docx_file.filename}'))
    markup = text_handler(f'docxs/{docx_file.filename}')
    os.remove(os.path.join(f'docxs/{docx_file.filename}'))
    return markup


def process_news_images(images, s_object):
    filenames = []
    dirname = s_object[:10] + str(datetime.date.today())
    os.mkdir(f'static/img/news/{dirname}')
    for im in images:
        nm = secrets.token_urlsafe(16)
        new_name = f'static/img/news/{dirname}/{nm}.jpg'
        im.save(os.path.join(new_name))
        im1 = Image.open(new_name)
        im1 = im1.resize((600, 300))
        im1.save(new_name)
        filenames.append(f'img/news/{dirname}/{nm}.jpg')
    filenames = ','.join(filenames)
    return filenames


def process_users_images(images):
    filenames = []
    for im in images:
        nm = secrets.token_urlsafe(16)
        im.save(os.path.join(f'static/img/users/{nm}.jpg'))
        filenames.append(f'img/users/{nm}.jpg')
    filenames = ','.join(filenames)
    return filenames


def process_theme_images(images):
    filenames = []
    for im in images:
        nm = secrets.token_urlsafe(16)
        im.save(os.path.join(f'static/img/themes/{nm}.jpg'))
        filenames.append(f'img/themes/{nm}.jpg')
    filenames = ','.join(filenames)
    return filenames


def process_comment_images(images):
    filenames = []
    for im in images:
        nm = secrets.token_urlsafe(16)
        im.save(os.path.join(f'static/img/comments/{nm}.jpg'))
        filenames.append(f'img/comments/{nm}.jpg')
    filenames = ','.join(filenames)
    return filenames


def make_url(im):
    if im is not None:
        return f"src={url_for('static', filename=im)}"
    return False


def make_urls_for_images(images):
    urls = list(map(make_url, images))
    return urls


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
        user = User(
            day_of_birth=form.birthday.data,
            name=form.name.data,
            email=form.email.data
        )
        if form.profile_pic.data:
            profile_pic = process_users_images(secure_multiple([form.profile_pic.data]))
            user.profile_picture = profile_pic
        token = secrets.token_urlsafe(16)
        user.set_email_code(token)
        user.set_password(form.password.data)

        db_sess.add(user)
        db_sess.commit()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        login_user(user, remember=True)
        if current_user == 1:
            print('aaaaaaaaaaaaaaa')
            current_user.special_access = 1
        send_confirmation_code(token)
        return redirect('/confirm_mail')
    return render_template('registration.html', form=form)


@app.route('/confirm_mail')
def confirm_mail():
    mail_site = find_mail_site(current_user.email)
    return render_template('confirm_mail.html', title='Mail confirmation', mail_site=mail_site)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
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


@app.route('/news/<news_id>')
def new(news_id):
    news = db_sess.query(News).filter(News.id == news_id).first()
    markup = news.news_markup
    images = make_urls_for_images(news.image.split(','))
    if len(images) != 1:
        return render_template('certain_news.html', text=markup,
                               images=images[:3], lenght=len(images[:3]), title=news.title)
    else:
        carousel_maker = images[0]
        return render_template('certain_news.html', text=markup,
                               carousel_maker=carousel_maker, lenght=len(images), title=news.title)


@app.route('/add_news', methods=["GET", "POST"])
@login_required
def add_news():
    news_form = NewsForm()
    if news_form.validate_on_submit():
        img = news_form.pictures.raw_data
        docx_file = news_form.text.data

        img = secure_multiple(img)
        news_markup = process_docx_file(docx_file)
        images = process_news_images(img, news_form.title.data)

        news = News(
            title=news_form.title.data,
            image=images,
            date_of_creation=datetime.datetime.now(),
            weight=1,
            news_markup=news_markup,
            creator=current_user.id
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
        user = db_sess.query(User).filter(User.id == current_user.id).first()
        user.confirmed = 1
        db_sess.commit()
        return render_template('page_confirmed.html', title='Page confirmed',
                               welcome=f"src={url_for('static', filename='img/welcome_to_the_family.gif')}")
    abort(404)


@app.route('/all_news/<news_range>')
def all_news(news_range):
    showing_range_left_edge, showing_range_right_edge = map(int, news_range.split('-'))
    showing_range = list(range(showing_range_left_edge + 1, showing_range_right_edge + 1))
    print(showing_range)
    news_to_show = list(db_sess.query(News).filter(News.id.in_(showing_range)).all())
    images = list(map(lambda x: make_urls_for_images(x.image.split(','))[0], news_to_show))
    page = showing_range_right_edge // 10
    left_switch_button_params = {}
    right_switch_button_params = {}
    print(showing_range_right_edge > news_to_show[-1].id)
    if page == 1 and showing_range_right_edge > news_to_show[-1].id:
        left_switch_button_params['left_dis'] = True
        right_switch_button_params['right_dis'] = True
    elif page == 1:
        left_switch_button_params['left_dis'] = True
        right_switch_button_params['right_dis'] = False
        right_switch_button_params['right_href'] = f"href=http://127.0.0.1:5000/all_news/" \
                                                   f"{showing_range_left_edge + 10}-{showing_range_right_edge + 10}"
    elif showing_range_right_edge > news_to_show[-1].id:
        left_switch_button_params['left_dis'] = False
        right_switch_button_params['right_dis'] = True
        left_switch_button_params['left_href'] = f"href=http://127.0.0.1:5000/all_news/" \
                                                 f"{showing_range_left_edge - 10}-{showing_range_right_edge - 10}"
    else:
        left_switch_button_params['left_dis'] = False
        right_switch_button_params['right_dis'] = False
        right_switch_button_params['right_href'] = f"href=http://127.0.0.1:5000/all_news/" \
                                                   f"{showing_range_left_edge + 10}-{showing_range_right_edge + 10}"
        left_switch_button_params['left_href'] = f"href=http://127.0.0.1:5000/all_news/" \
                                                 f"{showing_range_left_edge - 10}-{showing_range_right_edge - 10}"
    print(news_to_show)
    print(images)
    return render_template('all_news.html', all_news=news_to_show, title='All news',
                           images=images, current_page=page, **right_switch_button_params, **left_switch_button_params)


@app.route('/add_theme', methods=['GET', 'POST'])
def add_theme():
    theme_form = ThemeForm()
    if theme_form.validate_on_submit():
        new_theme = Theme(
            title=theme_form.title.data,
            description=theme_form.description.data,
            content=theme_form.content.data,
            user_id=current_user.id
        )
        chosen_genre = theme_form.genre.data
        if theme_form.image.data:
            img = secure_multiple(theme_form.image.raw_data)
            image = process_theme_images(img)
            new_theme.image = image
        chosen_genre_id = db_sess.query(Genres).filter(Genres.title == chosen_genre).first()
        new_theme.genre = chosen_genre_id.id
        db_sess.add(new_theme)
        db_sess.commit()
    return render_template('add_theme.html', title='Add_theme', theme_form=theme_form)


@app.route('/all_themes/<themes_range>')
def all_themes(themes_range):
    showing_range_left_edge, showing_range_right_edge = map(int, themes_range.split('-'))
    showing_range = list(range(showing_range_left_edge + 1, showing_range_right_edge + 1))
    print(showing_range)
    themes_to_show = list(db_sess.query(Theme).filter(Theme.id.in_(showing_range)).all())
    print(themes_to_show[0])
    page = showing_range_right_edge // 10
    left_switch_button_params = {}
    right_switch_button_params = {}
    print(showing_range_right_edge > themes_to_show[-1].id)
    if page == 1 and showing_range_right_edge > themes_to_show[-1].id:
        left_switch_button_params['left_dis'] = True
        right_switch_button_params['right_dis'] = True
    elif page == 1:
        left_switch_button_params['left_dis'] = True
        right_switch_button_params['right_dis'] = False
        right_switch_button_params['right_href'] = f"href=http://127.0.0.1:5000/all_themes/" \
                                                   f"{showing_range_left_edge + 10}-{showing_range_right_edge + 10}"
    elif showing_range_right_edge > themes_to_show[-1].id:
        left_switch_button_params['left_dis'] = False
        right_switch_button_params['right_dis'] = True
        left_switch_button_params['left_href'] = f"href=http://127.0.0.1:5000/all_themes/" \
                                                 f"{showing_range_left_edge - 10}-{showing_range_right_edge - 10}"
    else:
        left_switch_button_params['left_dis'] = False
        right_switch_button_params['right_dis'] = False
        right_switch_button_params['right_href'] = f"href=http://127.0.0.1:5000/all_themes/" \
                                                   f"{showing_range_left_edge + 10}-{showing_range_right_edge + 10}"
        left_switch_button_params['left_href'] = f"href=http://127.0.0.1:5000/all_themes/" \
                                                 f"{showing_range_left_edge - 10}-{showing_range_right_edge - 10}"
    print(themes_to_show)
    return render_template('themes.html', themes=themes_to_show, title='All themes',
                           current_page=page, **right_switch_button_params, **left_switch_button_params)


@app.route('/themes/<int:theme_id>/<comments_range>', methods=['GET', 'POST'])
def theme(theme_id, comments_range):
    theme_reply = CommentForm()
    if theme_reply.validate_on_submit():
        new_comment = Comment(
            content=theme_reply.comment_text.data,
            date_of_creation=datetime.datetime.now(),
            main_theme_id=theme_id,
            user_id=current_user.id
        )
        theme_image = theme_reply.comment_image.data
        if theme_image.filename != '':
            comment_im = process_comment_images(theme_reply.comment_image.raw_data)
            new_comment.image = comment_im
        db_sess.add(new_comment)
        db_sess.commit()
        return redirect(f'http://127.0.0.1:5000/themes/1/0-10')

    showing_range_left_edge, showing_range_right_edge = map(int, comments_range.split('-'))
    showing_range = list(range(showing_range_left_edge + 1, showing_range_right_edge + 1))
    chosen_theme = db_sess.query(Theme).filter(Theme.id == theme_id).first()
    comments_for_theme = list(db_sess.query(Comment).filter(Comment.main_theme_id == theme_id,
                                                       Comment.id.in_(showing_range)).all())
    theme_image_exists = False
    if chosen_theme.image is not None:
        theme_image_exists = True
    images_to_process = list(map(lambda x: x.image, comments_for_theme))
    images = make_urls_for_images(images_to_process)
    theme_image = make_urls_for_images([chosen_theme.image])[0]
    users = define_comment_owner(comments_for_theme)
    page = showing_range_right_edge // 10
    left_switch_button_params = {}
    right_switch_button_params = {}
    try:
        if page == 1 and showing_range_right_edge > comments_for_theme[-1].id:
            left_switch_button_params['left_dis'] = True
            right_switch_button_params['right_dis'] = True
        elif page == 1:
            left_switch_button_params['left_dis'] = True
            right_switch_button_params['right_dis'] = False
            right_switch_button_params['right_href'] = f"href=http://127.0.0.1:5000/themes/{theme_id}/" \
                                                       f"{showing_range_left_edge + 10}-{showing_range_right_edge + 10}"
        elif showing_range_right_edge > comments_for_theme[-1].id:
            left_switch_button_params['left_dis'] = False
            right_switch_button_params['right_dis'] = True
            left_switch_button_params['left_href'] = f"href=http://127.0.0.1:5000/themes/{theme_id}/" \
                                                     f"{showing_range_left_edge - 10}-{showing_range_right_edge - 10}"
        else:
            left_switch_button_params['left_dis'] = False
            right_switch_button_params['right_dis'] = False
            right_switch_button_params['right_href'] = f"href=http://127.0.0.1:5000/themes/{theme_id}/" \
                                                       f"{showing_range_left_edge + 10}-{showing_range_right_edge + 10}"
            left_switch_button_params['left_href'] = f"href=http://127.0.0.1:5000/themes/{theme_id}/" \
                                                     f"{showing_range_left_edge - 10}-{showing_range_right_edge - 10}"
    except IndexError:
        left_switch_button_params['left_dis'] = True
        right_switch_button_params['right_dis'] = True
    return render_template('certain_theme.html', theme_image_exists=theme_image_exists, images=images,
                           users=users, theme_reply=theme_reply, comments=comments_for_theme,
                           current_page=page, title=chosen_theme.title, theme=chosen_theme,
                           theme_image=theme_image,
                           **right_switch_button_params, **left_switch_button_params)


def main():
    db_session.global_init("db/blogs.db")
    app.run()


if __name__ == '__main__':
    main()

