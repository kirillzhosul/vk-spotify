# Importing modules.
from logging import exception
import time
import vk_api
import tekore
import threading
from vk_api.longpoll import VkLongPoll, VkEventType
import vk_api.utils
import lyricsgenius

def get_artists_list(_artists_list):
    # Function that returns string from artists list.

    # Getting artists count.
    _artists_count = len(_artists_list)

    if _artists_count <= 2:
        # Returning default string.
        return ", ".join(_artists_list)
    else:
        # Returning string in style : X, Y + 2 more...
        return ", ".join(_artists_list[:2]) + f" + {_artists_count - 2}.."

def send_message(_api_vkontakte, _peer_index, _message):
    # Function that sends message for vkontakte API.

    try:
        # Sending.
        _api_vkontakte.method("messages.send", {
            "random_id": vk_api.utils.get_random_id(),
            "peer_id": _peer_index,
            "message": _message,
        })
    except Exception as e:
        print(e)

def process_command(_api_vkontakte, _api_spotify, _api_genius, _text):
    # Function that returns response for the command.

    # Response
    _response = None

    # Processing.
    if _text.startswith("!lyrics") or _text.startswith("!genius"):
        # !lyrics command that searches and playing.
        try:
            # Getting command arguments.
            _arguments = _text.split(" ")[1:]

            if len(_arguments) < 1:
                # Invalid arguments (not passed any.)
                _response = "Пример команды !lyrics/genius ЗАПРОС_ПОИСКА"
            else:
                # Searching tracks indeces.
                founded_tracks, = _api_spotify.search(" ".join(_arguments))
                founded_tracks = founded_tracks.items

                if len(founded_tracks) < 1:
                    # If no search result
                    _response = "Не удалось найти треки из вашего запроса (Spotify не имеет данного трека)!"
                else:
                    _song = _api_genius.search_song(founded_tracks[0].name, get_artists_list([_artist.name for _artist in founded_tracks[0].artists]))
                    if _song is not None:
                        # Getting lyrics.
                        _lyrics = _song.lyrics

                        # Response.
                        _response = f"Текст песни {track_format(founded_tracks[0])}: {_lyrics}. {founded_tracks[0].album.images[0].url}"
                    else:
                        # Response.
                        _response = "Не удалось найти треки из вашего запроса (Genius не имеет данного трека)!"
        except Exception as e:
            # Error.
            _response = f"Произошла ошибка: {e}"
    if _text.startswith("!track") or _text.startswith("!song"):
        # !song command that returns current track.

        # Returning status.
        _response = get_track(_api_spotify)
    if _text.startswith("!next"):
        # !next command that plays next track in the playlist.

        # Playing next.
        _api_spotify.playback_next()

        # Returning status.
        _response = f"Песня переключена на {get_track(_api_spotify)}!"
    if _text.startswith("!previous"):
        # !previous command that plays previous track in the playlist.

        # Playing previous.
        _api_spotify.playback_previous()

        # Returning status.
        _response = f"Песня переключена на {get_track(_api_spotify)}!" 
    if _text.startswith("!pause"):
        # !pause command that pause playing.

        # Pausing.
        _api_spotify.playback_pause()

        # Response
        _response = f"Песня остановлена!"
    if _text.startswith("!unpause"):
        # !unpause command that unpause playing.

        # Unpausing.
        _api_spotify.playback_resume()

        # Response
        _response = f"Песня продолжена!"
    if _text.startswith("!search") or _text.startswith("!s"):
        # !search command that searches and playing.
        try:
            # Getting command arguments.
            _arguments = _text.split(" ")[1:]

            if len(_arguments) < 1:
                # Invalid arguments (not passed any.)
                _response = "Пример команды !search/s ЗАПРОС_ПОИСКА"
            else:
                # Searching tracks indeces.
                founded_tracks, = _api_spotify.search(" ".join(_arguments))
                founded_tracks = founded_tracks.items

                if len(founded_tracks) < 1:
                    # If no search result
                    _response = "Не удалось найти треки из вашего запроса!"
                else:
                    # Getting ids list.
                    #founded_tracks_id = [_track.id for _track in founded_tracks]

                    # Playing.
                    _api_spotify.playback_start_tracks([founded_tracks[0].id])

                    # Response.
                    _response = f"Песня переключена на {track_format(founded_tracks[0])}. {founded_tracks[0].album.images[0].url}"
        except Exception as e:
            # Error.
            _response = f"Произошла ошибка: {e}"
    if _text.startswith("!volume"):
        # !volume command that sets the volume.
        try:
            # Getting command arguments.
            _arguments = _text.split(" ")[1:]

            # Global volume?
            global VOLUME

            if len(_arguments) > 0:
                # If any arguments.

                # Getting volume.
                _volume = int(_arguments[0])

                if _volume < 0 or _volume > 100:
                    # Overflow error.
                    _response = "Громкость должна быть от 0 до 100%!"
                else:
                    # Setting volume
                    _api_spotify.playback_volume(_volume)

                    # Change volume for getter.
                    VOLUME = _volume

                    # Response.
                    _response = f"Громкость теперь {VOLUME}%"
            else:
                # If no arguments.

                # Return volume.
                _response = f"Громкость равна {VOLUME}%"
        except Exception as e:
            # Error.
            _response = f"[Spotify] Произошла ошибка: {e}"
    if _text.startswith("!help"):
        # !help command that returns all commands.

        # Response.
        _response = f"Команды:\n!info - Данные о боте,\n!track/song - Получить трек который играет,\n!next - Кнопка вперед,\n!previous " \
                    f"- Кнопка назад,\n!pause - Пауза,\n!unpause - Отпауза, \n!search/s ПОИСК - Включить любой трек из " \
                    f"поиска, \n!volume ГРОМКОСТЬ поменять громкость в процентах, \n!lyrics/genius - Получить текст трека"
    if _text.startswith("!info"):
        # !info command that returns all information about.
        _response = "Информация:\nАвтор кода: Кирилл Жосул, \n Язык кода: Python, \nИспользуемые API: Genius API, Spotify API, VKontakte API,\nИспользуемые модули: vk_api, tekore, lyricsgenius"


        # Response.
    # Returning response
    return _response

def track_format(_track):
    # Function that formats track.
    
    # Returning.
    return f"{_track.name} от {get_artists_list([_artist.name for _artist in _track.artists])}"

def listen_commands(_api_vkontakte, _api_spotify, _api_genius):
    # Function that listen for command in Vkontakte.

    # Getting longpoll server.
    _api_longpoll_vkontakte = VkLongPoll(_api_vkontakte)

    for _event in _api_longpoll_vkontakte.listen():
        # If new event.
        if _event.type == VkEventType.MESSAGE_NEW:
            # If this is new message.

            try:
                # Getting response.
                _response = process_command(_api_vkontakte, _api_spotify, _api_genius, _event.message.lower())

                if _response is not None:
                    # Sending message if response.
                    send_message(_api_vkontakte, _event.peer_id, "[Spotify] " + _response)
            except Exception as e:
                print(e)

def get_track(_api_spotify):
    # Function that gets spotify track.

    # Getting playback.
    _playback = _api_spotify.playback(tracks_only=True)

    if _playback is not None and _playback.is_playing and _playback.item.artists is not None:
        # If there is any track in playing.
        
        # Returning result.
        return track_format(_playback.item) + f"\n {_playback.item.album.images[0].url}"
    # Returning status.
    return "Нет трека"

def get_status(_api_spotify):
    # Function that gets spotify status.

    # Getting playback.
    _playback = _api_spotify.playback(tracks_only=True)

    if _playback is not None and _playback.is_playing and _playback.item is not None and _playback.item.artists is not None:
        # If there is any track in playing.
        
        # Returning result.
        return f"Слушает Spotify. Песня: {track_format(_playback.item)}."

    # Returning status.
    return "Не слушает Spotify."

def auto_update_status(_api_vkontakte, _api_spotify):
    # Function that auto updates status.

    # Status that was before update.
    status_previous = None

    while True:
        # Infinity loop.
        try:
            # Getting new status.
            _new_status = get_status(_api_spotify)

            if status_previous != _new_status:
                # If status changed.

                # Updating status.
                _api_vkontakte.method("status.set", {"text": _new_status})

                # Updating status.
                status_previous = _new_status

            # Sleeping for the timeout.
            time.sleep(UPDATE_TIMEOUT)
        except Exception as e:
            # Printing exception.
            print(f"Exception occurred! Exception info: {e}")

def start():
    # Function that starts all.

    # Spotify API object.
    api_spotify = tekore.Spotify(tekore.prompt_for_user_token(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, tekore.scope.every))
        
    # API VKontakte object.
    api_vkontakte = vk_api.VkApi(token=VKONTAKTE_TOKEN)

    # API Genius object.
    api_genius = lyricsgenius.Genius(GENIUS_TOKEN)

    # Thread for auto update status.
    auto_update_status_thread = threading.Thread(target=auto_update_status, args=(api_vkontakte, api_spotify))

    # Thread for commands.
    listen_commands_thread = threading.Thread(target=listen_commands, args=(api_vkontakte, api_spotify, api_genius))

    # Starting thread.
    auto_update_status_thread.start()
    listen_commands_thread.start()

# Settings.
UPDATE_TIMEOUT = 3
VOLUME = 100
SPOTIFY_CLIENT_ID = ""
SPOTIFY_CLIENT_SECRET = ""
SPOTIFY_REDIRECT_URI = ""
VKONTAKTE_TOKEN = ""
GENIUS_TOKEN = ""

# Starting.
start()