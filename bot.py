import requests
import telebot
import random
from API import bot_token, tmdb_key

bot = telebot.TeleBot(bot_token)

GENRES = {
    'Action':    28,
    'Comedy':    35,
    'Horror':    27,
    'Sci-Fi':    878,
    'Romance':   10749,
    'Animation': 16,
}


def get_movie(genre_id, genre_name):
    page = random.randint(1, 5)
    url = 'https://api.themoviedb.org/3/discover/movie'
    params = {
        'api_key':        tmdb_key,
        'with_genres':    genre_id,
        'sort_by':        'popularity.desc',
        'vote_count.gte': 200,
        'language':       'en-US',
        'page':           page,
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        results  = response.json().get('results', [])
    except Exception:
        return None
    if not results:
        return None

    movie    = random.choice(results)
    title    = movie.get('title', 'Unknown')
    overview = movie.get('overview', 'No description available.')
    rating   = movie.get('vote_average', 0)
    votes    = movie.get('vote_count', 0)
    date     = movie.get('release_date', '????')
    year     = date[:4] if date else '????'

    if len(overview) > 300:
        overview = overview[:297] + '...'

    stars = '⭐' * round(rating / 2)
    text = (
        '🎭 Genre: <b>{genre_name}</b>\n\n'
        '🎬 <b>{title}</b>  ({year})\n\n'
        '{stars}  <b>{rating}/10</b>  ({votes} votes)\n\n'
        '📖 {overview}'
    ).format(
        genre_name=genre_name, title=title, year=year,
        stars=stars, rating=round(rating, 1), votes=votes,
        overview=overview
    )
    return text



def send_genre_keyboard(chat_id):
    keyboard = telebot.types.InlineKeyboardMarkup()
    row = []
    for genre_name in GENRES:
        row.append(telebot.types.InlineKeyboardButton(
            genre_name, callback_data='genre-' + genre_name
        ))
        if len(row) == 3:
            keyboard.row(*row)
            row = []
    if row:
        keyboard.row(*row)
    bot.send_message(chat_id, '🎭 Choose a genre:', reply_markup=keyboard)



def send_movie_result(from_id, genre_name):
    bot.send_chat_action(from_id, 'typing')
    result = get_movie(GENRES[genre_name], genre_name)
    if result is None:
        bot.send_message(from_id, '⚠️ Could not fetch a movie. Try again!')
    else:
        bot.send_message(from_id, result, parse_mode='HTML')


@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.from_user.id,
        '🎬 <b>Welcome to MovieBot!</b>\n\n'
        'I pick a random popular movie for any genre you choose.\n\n'
        'Commands:\n'
        '  /movie – pick a genre and get a movie\n'
        '  /help  – show help',
        parse_mode='HTML'
    )

@bot.message_handler(commands=['help'])
def help_command(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.add(telebot.types.InlineKeyboardButton(
        'Data source: TMDB', url='https://www.themoviedb.org'
    ))
    bot.send_message(
        message.from_user.id,
        '🆘 <b>Help</b>\n\n'
        'Use /movie to see genre buttons.\n'
        'Press a genre and get:\n'
        '  • movie title and release year\n'
        '  • rating and number of votes\n'
        '  • short description\n\n'
        'Each press gives a <b>different random movie</b> — try the same genre multiple times!',
        parse_mode='HTML',
        reply_markup=keyboard
    )

@bot.message_handler(commands=['movie'])
def movie_command(message):
    send_genre_keyboard(message.chat.id)

@bot.callback_query_handler(func=lambda call: True)
def iq_callback(query):
    bot.answer_callback_query(query.id)
    if query.data.startswith('genre-'):
        send_movie_result(query.from_user.id, query.data[6:])
    else:
        bot.send_message(query.from_user.id, 'Unexpected error. Try again.')

@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    bot.send_message(message.from_user.id, 'Use /movie to get a movie recommendation 🎬')

bot.polling()
