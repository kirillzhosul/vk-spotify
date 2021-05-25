# Importing modules.
import time
import vk_api
import tekore
import threading
from vk_api.longpoll import VkLongPoll, VkEventType
import vk_api.utils


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

    # Sending.
    _api_vkontakte.method("messages.send", {
        "random_id": vk_api.utils.get_random_id(),
        "peer_id": _peer_index,
        "message": _message,
    })


def process_command(_api_vkontakte, _api_spotify, _text):
    # Function that returns response for the command.

    # Response
    _response = None

    # Processing.
    if _text.startswith("!track"):
        # !song command that returns current track.

        # Returning status.
        _response = get_status(_api_spotify)
    if _text.startswith("!next"):
        # !next command that plays next track in the playlist.

        # Playing next.
        _api_spotify.playback_next()

        # Returning status.
        _response = f"[Spotify] Песня переключена на {get_status(_api_spotify)}"
    if _text.startswith("!previous"):
        # !previous command that plays previous track in the playlist.

        # Playing previous.
        _api_spotify.playback_previous()

        # Returning status.
        _response = f"[Spotify] Песня переключена на {get_status(_api_spotify)}"
    if _text.startswith("!pause"):
        # !pause command that pause playing.

        # Pausing.
        _api_spotify.playback_pause()

        # Response
        _response = f"[Spotify] Песня остановлена!"
    if _text.startswith("!unpause"):
        # !unpause command that unpause playing.

        # Unpausing.
        _api_spotify.playback_resume()

        # Response
        _response = f"[Spotify] Песня продолжена!"

    if _text.startswith("!search"):
        # !search command that searches and playing.
        try:
            # Searching.
            founded_track, = _api_spotify.search(_text.split(" ")[1])

            # Getting just one track.
            founded_track = founded_track.items[0]

            # Playing.
            _api_spotify.playback_start_tracks([founded_track.id])

            # Response.
            _response = f"[Spotify] Песня переключена на {founded_track.name} от {get_artists_list([_artist.name for _artist in founded_track.artists])}"
        except Exception as e:
            # Error.
            _response = f"[Spotify] Произошла ошибка: {e}"
    if _text.startswith("!volume"):
        # !volume command that sets the volume.
        try:
            global VOLUME
            if len(_text.split(" ")) > 1:
                _volume = _text.split(" ")[1]
                _volume = int(_volume)
                _api_spotify.playback_volume(_volume)
                VOLUME = _volume
                _response = f"[Spotify] Громкость изменена на {VOLUME}%"
            else:
                _response = f"[Spotify] Громкость стоит на {VOLUME}%"
        except Exception as e:
            # Error.
            _response = f"[Spotify] Произошла ошибка: {e}"

    if _text.startswith("!help"):
        # !help command that returns all commands.

        # Response.
        _response = f"[Spotify] Команды:\n!track - Получить трек который играет,\n!next - Кнопка вперед,\n!previous " \
                    f"- Кнопка назад,\n!pause - Пауза,\n!unpause - Отпауза, \n!search ПОИСК - Включить любой трек из " \
                    f"поиска, \n!volume ГРОМКОСТЬ поменять громкость в процентах"

    # Returning response
    return _response


def listen_commands(_api_vkontakte, _api_spotify):
    # Function that listen for command in Vkontakte.

    # Getting longpoll server.
    _api_longpoll_vkontakte = VkLongPoll(_api_vkontakte)

    for _event in _api_longpoll_vkontakte.listen():
        # If new event.
        if _event.type == VkEventType.MESSAGE_NEW:
            # If this is new message.

            # Getting response.
            _response = process_command(_api_vkontakte, _api_spotify, _event.message.lower())

            if _response is not None:
                # Sending message if response.
                send_message(_api_vkontakte, _event.peer_id, _response)


def get_status(_api_spotify):
    # Function that gets spotify status.

    # Getting playback.
    _playback = _api_spotify.playback(tracks_only=True)

    if _playback is not None and _playback.is_playing:
        # If there is any track in playing.

        # Getting artists.
        _artists = get_artists_list([_artist.name for _artist in _playback.item.artists])

        # Returning result.
        return TEMPLATE_LISTENING.format(_playback.item.name, _artists, "{}")

    # Returning status.
    return TEMPLATE_NOT_LISTEN


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
            print(f"Exception occurred!( Exception info: {e}")


def start():
    # Function that starts all.

    # Spotify API object.
    api_spotify = tekore.Spotify(
        tekore.prompt_for_user_token(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, SPOTIFY_REDIRECT_URI, tekore.scope.every))

    # API VKontakte object.
    api_vkontakte = vk_api.VkApi(token=VKONTAKTE_TOKEN)

    # Thread for auto update status.
    auto_update_status_thread = threading.Thread(target=auto_update_status, args=(api_vkontakte, api_spotify))

    # Thread for commands.
    listen_commands_thread = threading.Thread(target=listen_commands, args=(api_vkontakte, api_spotify))

    # Starting thread.
    auto_update_status_thread.start()
    listen_commands_thread.start()

# Settings.
UPDATE_TIMEOUT = 3
VOLUME = 100
TEMPLATE_NOT_LISTEN = "Не слушает Spotify."
TEMPLATE_LISTENING = "Слушает Spotify. Песня: {} от {}"
SPOTIFY_CLIENT_ID = ""
SPOTIFY_CLIENT_SECRET = ""
SPOTIFY_REDIRECT_URI = ""
VKONTAKTE_TOKEN = ""

# Starting.
start()
