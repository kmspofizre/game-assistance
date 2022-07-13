import os
import shutil
from news_text_handler import text_handler
from flask import Flask, render_template, redirect, abort, url_for, request
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
from forms.genre_form import GenreForm
from forms.make_moder_form import MakeModerForm
from flask_login import LoginManager, login_required, \
    login_user, current_user, logout_user
import csv
from mail_sender import send_email
from dotenv import load_dotenv
import datetime
import secrets
import schedule
from PIL import Image
import wikipediaapi


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
wiki_wiki = wikipediaapi.Wikipedia('ru')

with open('mails.csv', encoding='utf-8') as mails_file:
    MAILS = list(
        csv.DictReader(
            mails_file,
            delimiter=',',
            quotechar='"'
        )
    )


def separate_mail_domain(mail_address):
    ind = mail_address.find('@')
    mail_domain = mail_address[ind + 1:]
    return mail_domain


def find_mail_site(mail_address):
    mail_domain = separate_mail_domain(mail_address)
    required = list(
        filter(
            lambda x: x['почтовый домен'] == mail_domain,
            MAILS
        )
    )
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


def define_comment_owner(comments):
    return list(map(lambda x: db_sess.query(User).filter(User.id == x.user_id).first().name, comments))


def process_docx_file(docx_file):
    docx1 = docx_file.filename
    docx1 = docx1.rsplit('.', 1)
    if docx1[1].lower() != 'docx':
        return 'docx_error'
    docx_file.save(os.path.join(f'docxs/{docx_file.filename}'))
    markup = text_handler(f'docxs/{docx_file.filename}')
    os.remove(os.path.join(f'docxs/{docx_file.filename}'))
    return markup


def process_news_images(images, s_object, redact=False, previous_name=None, date=None):
    filenames = []
    if not redact:
        dirname = s_object[:10] + str(datetime.date.today())
        try:
            os.mkdir(f'static/img/news/{dirname}')
        except FileExistsError:
            return 'error'
    else:
        dirname = s_object[:10] + str(date)[:10]
        if not previous_name[:10] == s_object[:10]:
            try:
                os.mkdir(f'static/img/news/{dirname}')
            except FileExistsError:
                return 'error'

    for im in images:
        im2 = im.filename
        nm = secrets.token_urlsafe(16)
        if im2.rsplit('.', 1)[1].lower() in ('jpg', 'jpeg'):
            new_name = f'static/img/news/{dirname}/{nm}.jpg'
            filenames.append(f'img/news/{dirname}/{nm}.jpg')
        elif im2.rsplit('.', 1)[1].lower() == 'png':
            new_name = f'static/img/news/{dirname}/{nm}.png'
            filenames.append(f'img/news/{dirname}/{nm}.png')
        else:
            return 'error1'
        im.save(os.path.join(new_name))
        im1 = Image.open(new_name)
        im1 = im1.resize((600, 300))
        im1.save(new_name)

    filenames = ','.join(filenames)
    return filenames


def process_users_images(images):
    filenames = []
    for im in images:
        im2 = im.filename
        nm = secrets.token_urlsafe(16)
        if im2.rsplit('.', 1)[1].lower() in ('jpg', 'jpeg'):
            im2.save(os.path.join(f'static/img/users/{nm}.jpg'))
            filenames.append(f'img/users/{nm}.jpg')
        elif im2.rsplit('.', 1)[1].lower() == 'png':
            im.save(os.path.join(f'static/img/users/{nm}.png'))
            filenames.append(f'img/users/{nm}.png')
        else:
            return 'error1'
    filenames = ','.join(filenames)
    return filenames


def process_theme_images(images):
    filenames = []
    for im in images:
        im2 = im.filename
        nm = secrets.token_urlsafe(16)
        if im2.rsplit('.', 1)[1].lower() in ('jpg', 'jpeg'):
            im.save(os.path.join(f'static/img/themes/{nm}.jpg'))
            filenames.append(f'img/themes/{nm}.jpg')
        elif im2.rsplit('.', 1)[1].lower() == 'png':
            im.save(os.path.join(f'static/img/themes/{nm}.png'))
            filenames.append(f'img/themes/{nm}.png')
        else:
            return 'error1'
    filenames = ','.join(filenames)
    return filenames


def datetime_sort():
    list_of_news = []
    for news in db_sess.query(News).all():
        today = datetime.datetime.now()
        delta = today - news.date_of_creation
        id_delta = (news.id, delta)
    list_of_news.sort(key=lambda x: x[1], reverse=True)
    return list_of_news


def append_genres():
    genres = ['RPG', 'Shooter', 'Fighting', 'Souls-like']
    descriptions = ["Компьютерная ролевая игра (англ. Computer Role-Playing Game,"
                    " обозначается аббревиатурой CRPG или RPG) — жанр компьютерных игр,"
                    " основанный на элементах игрового процесса традиционных настольных ролевых игр."
                    " В ролевой игре игрок управляет одним или несколькими персонажами,"
                    " каждый из которых описан набором численных характеристик,"
                    " списком способностей и умений; примерами таких характеристик"
                    " могут быть очки здоровья (англ. hit points, HP), показатели силы,"
                    " ловкости, интеллекта, защиты, уклонения, уровень развития того или иного навыка и т. п.",
                    "Шу́тер (Стрелялка, англ. shooter — «стрелок») — жанр компьютерных игр."
                    " На момент зарождения жанра за рубежом укрепилось слово «шутер», как"
                    " вариант описания игрового процесса и перевод для слова shooter,"
                    " в России и некоторых других странах постсоветского пространства"
                    " жанр изначально был назван как «стрелялка»[1].",
                    "Фáйтинг (от англ. Fighting — бой, драка, поединок, борьба) — жанр компьютерных игр,"
                    " имитирующих рукопашный бой малого числа персонажей в пределах"
                    " ограниченного пространства, называемого ареной (часть игровой вселенной,"
                    " не управляемая участником игры, на которой происходят основные действия игры).",
                    "Soulslike или souls-like (с англ.—«souls-подобные»,"
                    " дословный перевод —«души-подобные»; транслитерация —«соулслайк»),"
                    " также известный как soulsborne (словослияние Souls и Bloodborne)"
                    " — условно выделяемый поджанр компьютерных игр в жанре Action RPG,"
                    " известный высоким уровнем сложности и упором на повествование,"
                    " заложенное в окружающей среде, вдохновленной жанром тёмного фэнтези."
                    " Он берёт своё начало в серии игр Souls, разработанных "
                    "Хидэтакой Миядзаки и студией FromSoftware, темы и механика"
                    " которых напрямую были перенесены во множество других подобных игр."
                    " Альтернативный термин soulsborne представляет собой словослияние"
                    " серии Souls и видеоигры Bloodborne за авторством тех же FromSoftware и Миядзаки."]
    for i in range(len(genres)):
        if not db_sess.query(Genres).filter(Genres.title == genres[i]).all():
            genre = Genres(
                title=genres[i],
                description=descriptions[i]
            )
            db_sess.add(genre)
            db_sess.commit()


def list_of_amount_of_comments():
    list_of_themes = []
    for theme in db_sess.query(Theme).all():
        amount_of_comments = db_sess.query(Comment).filter(Comment.main_theme_id == theme.id)
        list_of_themes.append((theme, len(list(amount_of_comments))))
    return sorted(list_of_themes, key=lambda x: x[1])


def return_list_of_themes_sorted_by_comments(list_of_themes):
    result = []
    lst = []
    for elem in list_of_themes:
        lst.append(elem[0])
    for theme in lst:
        amount_of_comments = list(db_sess.query(Comment).filter(Comment.main_theme_id == theme.id))
        result.append((theme, len(amount_of_comments)))
    return list(sorted(result, key=lambda x: x[1]))


def genre_sort(genre):
    list_of_themes = []
    for theme in db_sess.query(Theme).all():
        id_genre = (theme, theme.genre)
        list_of_themes.append(id_genre)
    return list(filter(lambda x: x[1] == genre, list_of_themes))


def create_list_of_news_rating():
    list_of_news = []
    for news in db_sess.query(News).all():
        id_rating = (news.id, news.rating)
        list_of_news.append(id_rating)
    return list_of_news


def return_current_news_rating(tuple_of_id_and_rating):
    news = db_sess.query(News).filter(News.id == tuple_of_id_and_rating[0]).first()
    return news


def update_rating():
    for news in db_sess.query(News).all():
        today = datetime.datetime.now()
        delta = today - news.date_of_creation
        delta = delta.total_seconds() / 3600
        news.rating = delta * news.weight
        db_sess.commit()


schedule.every().hour.do(update_rating)


def process_comment_images(images):
    filenames = []
    for im in images:
        im2 = im.filename
        nm = secrets.token_urlsafe(16)
        if im2.rsplit('.', 1)[1].lower() in ('jpg', 'jpeg'):
            im.save(os.path.join(f'static/img/comments/{nm}.jpg'))
            filenames.append(f'img/comments/{nm}.jpg')
        elif im2.rsplit('.', 1)[1].lower() == 'png':
            im.save(os.path.join(f'static/img/comments/{nm}.png'))
            filenames.append(f'img/comments/{nm}.png')
        else:
            return 'error1'

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


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/')
@app.route('/index')
def index():
    themes_to_show = []
    themes = list_of_amount_of_comments()
    for i in range(5):
        try:
            themes_to_show.append(themes[i][0])
        except IndexError:
            print("IndexError")
            break
    news_to_show = []
    list_of_news = create_list_of_news_rating()
    for i in range(5):
        try:
            news_to_show.append(return_current_news_rating(list_of_news[i]))
        except IndexError:
            break
    images = list(
        map(
            lambda x: make_urls_for_images(x.image.split(','))[0],
            news_to_show
        )
    )
    return render_template(
        'main_page.html',
        title='Game Assistance',
        genres=list(db_sess.query(Genres).all()),
        trads=themes_to_show,
        themes=themes_to_show,
        important_news=news_to_show,
        images=images
    )


@app.route('/registration', methods=["GET", "POST"])
def registration():
    form = UserForm()
    if form.validate_on_submit():
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template(
                "registration.html",
                form=form,
                error="Такой пользователь уже существует"
            )
        if form.password.data != form.repeat_password.data:
            return render_template("registration.html", form=form, error="Пароли не совпадают")
        user = User(
            name=form.name.data,
            email=form.email.data
        )
        delta = datetime.date.today() - form.birthday.data
        if delta < datetime.timedelta(days=365 * 14):
            return render_template("registration.html", form=form, error="Вам должно быть больше 14 лет")
        if form.profile_pic.data:
            profile_pic = process_users_images([form.profile_pic.data])
            if profile_pic == 'error1':
                return render_template("registration.html", form=form, error="Пароли не совпадают")
            user.profile_picture = profile_pic
        token = secrets.token_urlsafe(16)
        user.set_email_code(token)
        user.set_password(form.password.data)

        db_sess.add(user)
        db_sess.commit()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        login_user(user, remember=True)
        if current_user == 1:
            current_user.special_access = 1
        send_confirmation_code(token)
        return redirect('/confirm_mail')
    return render_template(
        'registration.html',
        form=form
    )


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
    return render_template(
        'login.html',
        title='Авторизация',
        form=form
    )


@app.route('/news/<news_id>')
def new(news_id):
    news = db_sess.query(News).filter(News.id == news_id).first()
    date_of_publication = news.date_of_creation.strftime("%A %d-%m-%y %H:%M:%S")
    markup = news.news_markup
    images = make_urls_for_images(news.image.split(','))
    if len(images) != 1:
        return render_template('certain_news.html',
                               text=markup,
                               images=images[:3],
                               lenght=len(images[:3]),
                               title=news.title,
                               time=date_of_publication
                               )
    else:
        carousel_maker = images[0]
        return render_template('certain_news.html',
                               text=markup,
                               carousel_maker=carousel_maker,
                               lenght=len(images),
                               title=news.title,
                               time=date_of_publication
                               )


@app.route('/add_news', methods=["GET", "POST"])
@login_required
def add_news():
    news_form = NewsForm()
    if news_form.validate_on_submit():
        img = news_form.pictures.raw_data
        docx_file = news_form.text.data
        news_markup = process_docx_file(docx_file)
        if news_markup == 'docx_error':
            return render_template('add_news.html', title='News', news_form=news_form,
                                   error='Not .docx file uploaded')
        images = process_news_images(img, news_form.title.data)
        if images == 'error':
            return render_template('add_news.html', title='News', news_form=news_form, error='Already exists')
        elif images == 'error1':
            return render_template('add_news.html', title='News', news_form=news_form, error='Unmatched image')
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
        return render_template('page_confirmed.html',
                               title='Page confirmed',
                               welcome=f"src={url_for('static', filename='img/welcome_to_the_family.gif')}"
                               )
    abort(404)


@app.route('/all_news/<news_range>')
def all_news(news_range):
    themes_to_show = []
    themes = list_of_amount_of_comments()
    for i in range(5):
        try:
            themes_to_show.append(themes[i][0])
        except IndexError:
            print("IndexError")
            break
    news_to_show = []
    list_of_news = create_list_of_news_rating()
    for i in range(5):
        try:
            news_to_show.append(return_current_news_rating(list_of_news[i]))
        except IndexError:
            break
    showing_range_left_edge, showing_range_right_edge = map(
        int,
        news_range.split('-')
    )
    news_to_show = list(
        db_sess.query(News).all()
    )[::-1][showing_range_left_edge:showing_range_right_edge]
    images = list(
        map(
            lambda x: make_urls_for_images(x.image.split(','))[0],
            news_to_show
        )
    )
    page = showing_range_right_edge // 10
    left_switch_button_params = {}
    right_switch_button_params = {}
    try:
        showing_range_right_edge > news_to_show[0].id
    except IndexError:
        return redirect('http://51.250.89.77/nothing_yet/news')
    if page == 1 and showing_range_right_edge >= news_to_show[0].id:
        left_switch_button_params['left_dis'] = True
        right_switch_button_params['right_dis'] = True
    elif page == 1:
        left_switch_button_params['left_dis'] = True
        right_switch_button_params['right_dis'] = False
        right_switch_button_params['right_href'] = f"href=http://51.250.89.77/all_news/" \
                                                   f"{showing_range_left_edge + 10}-{showing_range_right_edge + 10}"
    elif showing_range_right_edge >= news_to_show[0].id:
        left_switch_button_params['left_dis'] = False
        right_switch_button_params['right_dis'] = True
        left_switch_button_params['left_href'] = f"href=http://51.250.89.77/all_news/" \
                                                 f"{showing_range_left_edge - 10}-{showing_range_right_edge - 10}"
    else:
        left_switch_button_params['left_dis'] = False
        right_switch_button_params['right_dis'] = False
        right_switch_button_params['right_href'] = f"href=http://51.250.89.77/all_news/" \
                                                   f"{showing_range_left_edge + 10}-{showing_range_right_edge + 10}"
        left_switch_button_params['left_href'] = f"href=http://51.250.89.77/all_news/" \
                                                 f"{showing_range_left_edge - 10}-{showing_range_right_edge - 10}"
    print(news_to_show)
    print(images)
    return render_template('all_news.html',
                           all_news=news_to_show,
                           images=images,
                           current_page=page,
                           genres=list(db_sess.query(Genres).all()),
                           trads=themes_to_show,
                           **right_switch_button_params,
                           **left_switch_button_params
                           )


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
            img = theme_form.image.raw_data
            image = process_theme_images(img)
            if image == 'error1':
                return render_template('add_theme.html', title='Add_theme',
                                       theme_form=theme_form, error='Unmatched image')
            new_theme.image = image
        chosen_genre_id = db_sess.query(Genres).filter(Genres.title == chosen_genre).first()
        new_theme.genre = chosen_genre_id.id
        db_sess.add(new_theme)
        db_sess.commit()
    return render_template('add_theme.html', title='Add_theme', theme_form=theme_form)


@app.route('/all_themes/<themes_range>')
def all_themes(themes_range):
    themes_to_show = []
    themes = list_of_amount_of_comments()
    for i in range(5):
        try:
            themes_to_show.append(themes[i][0])
        except IndexError:
            print("IndexError")
            break
    news_to_show = []
    list_of_news = create_list_of_news_rating()
    for i in range(5):
        try:
            news_to_show.append(return_current_news_rating(list_of_news[i]))
        except IndexError:
            break
    showing_range_left_edge, showing_range_right_edge = map(int, themes_range.split('-'))
    themes_to_show = []
    themes = list_of_amount_of_comments()
    for i in range(showing_range_left_edge, showing_range_right_edge):
        try:
            themes_to_show.append(themes[i][0])
        except IndexError:
            print("IndexError")
            break
    if not themes_to_show:
        return redirect('http://51.250.89.77/nothing_yet/themes')
    page = showing_range_right_edge // 10
    left_switch_button_params = {}
    right_switch_button_params = {}
    check_theme = len(list(db_sess.query(Theme).all()))
    if check_theme % 10 == 0:
        max_page = check_theme // 10
    else:
        max_page = check_theme // 10 + 1
    if page == max_page == 1:
        left_switch_button_params['left_dis'] = True
        right_switch_button_params['right_dis'] = True
    elif page == 1:
        left_switch_button_params['left_dis'] = True
        right_switch_button_params['right_dis'] = False
        right_switch_button_params['right_href'] = f"href=http://51.250.89.77/all_themes/" \
                                                   f"{showing_range_left_edge + 10}-{showing_range_right_edge + 10}"
    elif max_page == page:
        left_switch_button_params['left_dis'] = False
        right_switch_button_params['right_dis'] = True
        left_switch_button_params['left_href'] = f"href=http://51.250.89.77/all_themes/" \
                                                 f"{showing_range_left_edge - 10}-{showing_range_right_edge - 10}"
    else:
        left_switch_button_params['left_dis'] = False
        right_switch_button_params['right_dis'] = False
        right_switch_button_params['right_href'] = f"href=http://51.250.89.77/all_themes/" \
                                                   f"{showing_range_left_edge + 10}-{showing_range_right_edge + 10}"
        left_switch_button_params['left_href'] = f"href=http://51.250.89.77/all_themes/" \
                                                 f"{showing_range_left_edge - 10}-{showing_range_right_edge - 10}"
    return render_template('themes.html', themes=themes_to_show, title='All themes',
                           current_page=page, **right_switch_button_params, genres=list(db_sess.query(Genres).all()),
                           trads=themes_to_show, **left_switch_button_params)


@app.route('/themes_by_genre/<int:genre_id>/<themes_range>')
def themes_sorted_by_genre(genre_id, themes_range):
    themes_to_show = []
    themes = list_of_amount_of_comments()
    for i in range(5):
        try:
            themes_to_show.append(themes[i][0])
        except IndexError:
            print("IndexError")
            break
    news_to_show = []
    list_of_news = create_list_of_news_rating()
    for i in range(5):
        try:
            news_to_show.append(return_current_news_rating(list_of_news[i]))
        except IndexError:
            break
    showing_range_left_edge, showing_range_right_edge = map(int, themes_range.split('-'))
    themes_to_show = []
    list_of_themes = return_list_of_themes_sorted_by_comments(genre_sort(genre_id))
    print(list_of_themes)
    for elem in list_of_themes:
        themes_to_show.append(elem[0])
    if not themes_to_show:
        return redirect('http://51.250.89.77/nothing_yet/themes')
    page = showing_range_right_edge // 10
    left_switch_button_params = {}
    right_switch_button_params = {}
    check_theme = len(list(db_sess.query(Theme).all()))
    if check_theme % 10 == 0:
        max_page = check_theme // 10
    else:
        max_page = check_theme // 10 + 1
    if page == max_page == 1:
        left_switch_button_params['left_dis'] = True
        right_switch_button_params['right_dis'] = True
    elif page == 1:
        left_switch_button_params['left_dis'] = True
        right_switch_button_params['right_dis'] = False
        right_switch_button_params['right_href'] = f"href=http://51.250.89.77/all_themes/" \
                                                   f"{showing_range_left_edge + 10}-{showing_range_right_edge + 10}"
    elif max_page == page:
        left_switch_button_params['left_dis'] = False
        right_switch_button_params['right_dis'] = True
        left_switch_button_params['left_href'] = f"href=http://51.250.89.77/all_themes/" \
                                                 f"{showing_range_left_edge - 10}-{showing_range_right_edge - 10}"
    else:
        left_switch_button_params['left_dis'] = False
        right_switch_button_params['right_dis'] = False
        right_switch_button_params['right_href'] = f"href=http://51.250.89.77/all_themes/" \
                                                   f"{showing_range_left_edge + 10}-{showing_range_right_edge + 10}"
        left_switch_button_params['left_href'] = f"href=http://51.250.89.77/all_themes/" \
                                                 f"{showing_range_left_edge - 10}-{showing_range_right_edge - 10}"
    return render_template('themes.html', themes=themes_to_show, title='All themes',
                           genres=list(db_sess.query(Genres).all()),
                           trads=themes_to_show,
                           current_page=page, **right_switch_button_params, **left_switch_button_params)


@app.route('/themes/<int:theme_id>/<comments_range>', methods=['GET', 'POST'])
def theme(theme_id, comments_range):
    themes_to_show = []
    themes = list_of_amount_of_comments()
    for i in range(5):
        try:
            themes_to_show.append(themes[i][0])
        except IndexError:
            print("IndexError")
            break
    news_to_show = []
    list_of_news = create_list_of_news_rating()
    for i in range(5):
        try:
            news_to_show.append(return_current_news_rating(list_of_news[i]))
        except IndexError:
            break
    theme_reply = CommentForm()
    if theme_reply.validate_on_submit():
        new_comment = Comment(
            content=theme_reply.comment_text.data,
            date_of_creation=datetime.datetime.now().strftime("%d-%m-%y %H:%M"),
            main_theme_id=theme_id,
            user_id=current_user.id
        )
        theme_image = theme_reply.comment_image.data
        if theme_image.filename != '':
            comment_im = process_comment_images(theme_reply.comment_image.raw_data)
            if comment_im == 'error1':
                return redirect(f'http://51.250.89.77/themes/1/0-10')
            new_comment.image = comment_im
        db_sess.add(new_comment)
        db_sess.commit()
        return redirect(f'http://51.250.89.77/themes/1/0-10')

    showing_range_left_edge, showing_range_right_edge = map(int, comments_range.split('-'))
    chosen_theme = db_sess.query(Theme).filter(Theme.id == theme_id).first()
    date_of_publication = chosen_theme.date_of_creation.strftime("%A %d-%m-%y %H:%M:%S")
    comments_for_theme = list(
        db_sess.query(Comment).all()
    )[::-1][showing_range_left_edge:showing_range_right_edge]
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
        if page == 1 and showing_range_right_edge >= comments_for_theme[0].id:
            left_switch_button_params['left_dis'] = True
            right_switch_button_params['right_dis'] = True
        elif page == 1:
            left_switch_button_params['left_dis'] = True
            right_switch_button_params['right_dis'] = False
            right_switch_button_params['right_href'] = f"href=http://51.250.89.77/themes/{theme_id}/" \
                                                       f"{showing_range_left_edge + 10}-{showing_range_right_edge + 10}"
        elif showing_range_right_edge >= comments_for_theme[0].id:
            left_switch_button_params['left_dis'] = False
            right_switch_button_params['right_dis'] = True
            left_switch_button_params['left_href'] = f"href=http://51.250.89.77/themes/{theme_id}/" \
                                                     f"{showing_range_left_edge - 10}-{showing_range_right_edge - 10}"
        else:
            left_switch_button_params['left_dis'] = False
            right_switch_button_params['right_dis'] = False
            right_switch_button_params['right_href'] = f"href=http://51.250.89.77/themes/{theme_id}/" \
                                                       f"{showing_range_left_edge + 10}-{showing_range_right_edge + 10}"
            left_switch_button_params['left_href'] = f"href=http://51.250.89.77/themes/{theme_id}/" \
                                                     f"{showing_range_left_edge - 10}-{showing_range_right_edge - 10}"
    except IndexError:
        left_switch_button_params['left_dis'] = True
        right_switch_button_params['right_dis'] = True
    return render_template('certain_theme.html', theme_image_exists=theme_image_exists, images=images,
                           users=users, theme_reply=theme_reply, comments=comments_for_theme,
                           current_page=page, title=chosen_theme.title, theme=chosen_theme,
                           theme_image=theme_image, time=date_of_publication, genres=list(db_sess.query(Genres).all()),
                           trads=themes_to_show,
                           **right_switch_button_params, **left_switch_button_params)


@app.route('/add_genre', methods=['GET', 'POST'])
def add_genre():
    genre_form = GenreForm()
    if genre_form.validate_on_submit():
        wiki_page = wiki_wiki.page(genre_form.title.data)
        if wiki_page.exists():
            if not db_sess.query(Genres).filter(Genres.title == genre_form.title.data).first():
                new_genre = Genres(
                    title=genre_form.title.data,
                    description=wiki_page.summary
                )
                db_sess.add(new_genre)
                db_sess.commit()
                return redirect('/')
            else:
                return render_template('add_genre.html', title='Add genre',
                                       genre_form=genre_form, genre_error='This genre already exists')
        else:
            return render_template('add_genre.html', title='Add genre',
                                   genre_form=genre_form, genre_error='There is no Wiki page for this genre')
    return render_template('add_genre.html', title='Add genre', genre_form=genre_form)


@app.route('/make_moder', methods=['GET', 'POST'])
def make_moder():
    add_moder_form = MakeModerForm()
    if add_moder_form.validate_on_submit():
        user = db_sess.query(User).filter(User.email == add_moder_form.email.data).first()
        if user:
            user.special_access = True
            db_sess.commit()
            return redirect('/')
        else:
            return render_template('make_moder.html', title='Add moder',
                                   mod_error='User with such email doesnt exist', add_moder_form=add_moder_form)
    return render_template('make_moder.html', title='Add moder', error='', add_moder_form=add_moder_form)


@app.route('/delete_news/<int:news_id>')
def delete_news(news_id):
    chosen_news = db_sess.query(News).filter(News.id == news_id).first()
    print(chosen_news.date_of_creation)
    shutil.rmtree(f"static/img/news/{chosen_news.title}{str(chosen_news.date_of_creation)[:10]}", ignore_errors=True)
    db_sess.delete(chosen_news)
    db_sess.commit()
    return redirect('/all_news/0-10')


@app.route('/delete_theme/<int:theme_id>')
def delete_theme(theme_id):
    chosen_theme = db_sess.query(Theme).filter(Theme.id == theme_id).first()
    os.remove(f"static/{chosen_theme.image}")
    for elem in list(db_sess.query(Comment).filter(Comment.main_theme_id == chosen_theme.id)):
        im_path = elem.image
        os.remove(f"static/img/comments/{im_path}")
        db_sess.delete(elem)
        db_sess.commit()
    db_sess.delete(chosen_theme)
    db_sess.commit()
    return redirect('/all_themes/0-10')


@app.route('/delete_comment/<int:theme_id>/<int:comment_id>')
def delete_comment(theme_id, comment_id):
    chosen_comment = db_sess.query(Comment).filter(Comment.id == comment_id).first()
    db_sess.delete(chosen_comment)
    db_sess.commit()
    return redirect(f'/themes/{theme_id}/0-10')


@app.route('/edit_news/<int:news_id>', methods=['GET', 'POST'])
def edit_news(news_id):
    chosen_news = db_sess.query(News).filter(News.id == news_id).first()
    news_form = NewsForm()
    if request.method == 'GET':
        if chosen_news:
            news_form.title.data = chosen_news.title
        else:
            abort(404)
    if news_form.validate_on_submit():
        if chosen_news:
            img = news_form.pictures.raw_data
            docx_file = news_form.text.data
            news_markup = process_docx_file(docx_file)
            images = process_news_images(img, news_form.title.data, redact=True, previous_name=chosen_news.title,
                                         date=chosen_news.date_of_creation)
            if images == 'error1':
                return render_template('add_news.html', title='News', news_form=news_form, error='Unmatched image')
            chosen_news.title = news_form.title.data
            chosen_news.image = images
            chosen_news.news_markup = news_markup
            db_sess.commit()
            return redirect('/all_news/0-10')
        else:
            abort(404)
    return render_template('add_news.html', title='Edit news', news_form=news_form)


@app.route('/edit_theme/<int:theme_id>', methods=['GET', 'POST'])
def edit_theme(theme_id):
    chosen_theme = db_sess.query(Theme).filter(Theme.id == theme_id).first()
    theme_form = ThemeForm()
    if request.method == 'GET':
        if chosen_theme:
            theme_form.title.data = chosen_theme.title
            theme_form.description.data = chosen_theme.description
            theme_form.content.data = chosen_theme.content
        else:
            abort(404)
    if theme_form.validate_on_submit():
        if chosen_theme:
            chosen_theme.title = theme_form.title.data
            chosen_theme.description = theme_form.description.data
            chosen_theme.content = theme_form.content.data
            chosen_genre = theme_form.genre.data
            if theme_form.image.data:
                img = theme_form.image.raw_data
                image = process_theme_images(img)
                if image == 'error1':
                    return render_template('add_theme.html', title='Edit theme',
                                           theme_form=theme_form, error='Unmatched image')
                chosen_theme.image = image
            chosen_genre_id = db_sess.query(Genres).filter(Genres.title == chosen_genre).first()
            chosen_theme.genre = chosen_genre_id.id
            db_sess.commit()
        else:
            abort(404)
        return redirect('/all_themes/0-10')
    return render_template('add_theme.html', title='Edit theme', theme_form=theme_form)


@app.route('/glossary')
def glossary():
    themes_to_show = []
    themes = list_of_amount_of_comments()
    for i in range(5):
        try:
            themes_to_show.append(themes[i][0])
        except IndexError:
            print("IndexError")
            break
    news_to_show = []
    list_of_news = create_list_of_news_rating()
    for i in range(5):
        try:
            news_to_show.append(return_current_news_rating(list_of_news[i]))
        except IndexError:
            break
    genres = db_sess.query(Genres).all()
    return render_template('glossary.html', genres=genres, genres_mp=list(db_sess.query(Genres).all()),
                           trads=themes_to_show)


@app.route('/nothing_yet/<type_n>')
def nothing_yet(type_n):
    return render_template('nothing_yet.html', title='Nothing yet', type_n=type_n)


def main():
    db_session.global_init("db/blogs.db")
    append_genres()
    app.run(host="0.0.0.0")


if __name__ == '__main__':
    main()
