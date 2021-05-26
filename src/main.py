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
    if _text.startswith("!search"):
        # !search command that searches and playing.
        try:
            # Getting command arguments.
            _arguments = _text.split(" ")[1:]

            if len(_arguments) < 1:
                # Invalid arguments (not passed any.)
                _response = "Пример команды !search ЗАПРОС_ПОИСКА"
            else:
                # Searching tracks indeces.
                founded_tracks, = _api_spotify.search(" ".join(_arguments))
                founded_tracks = founded_tracks.items

                if len(founded_tracks) < 1:
                    # If no search result
                    _response = "Не удалось найти треки из вашего запроса!"
                else:
                    # Getting ids list.
                    founded_tracks_id = [_track.id for _track in founded_tracks]

                    # Playing.
                    _api_spotify.playback_start_tracks(founded_tracks_id)

                    # Response.
                    _response = f"Песня переключена на {track_format(founded_tracks[0])}"
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
        _response = f"Команды:\n!track - Получить трек который играет,\n!next - Кнопка вперед,\n!previous " \
                    f"- Кнопка назад,\n!pause - Пауза,\n!unpause - Отпауза, \n!search ПОИСК - Включить любой трек из " \
                    f"поиска, \n!volume ГРОМКОСТЬ поменять громкость в процентах"

    # Returning response
    return _response

def track_format(_track):
    # Function that formats track.

    # Returning.
    return f"{_track.name} от {get_artists_list([_artist.name for _artist in _track.artists])}"

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
                send_message(_api_vkontakte, _event.peer_id, "[Spotify] " + _response)


def get_track(_api_spotify):
    # Function that gets spotify track.

    # Getting playback.
    _playback = _api_spotify.playback(tracks_only=True)

    if _playback is not None and _playback.is_playing and _playback.item.artists is not None:
        # If there is any track in playing.
        
        # Returning result.
        return track_format(_playback.item)

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
SPOTIFY_CLIENT_ID = ""
SPOTIFY_CLIENT_SECRET = ""
SPOTIFY_REDIRECT_URI = ""
VKONTAKTE_TOKEN = ""
SPOTIFY_CLIENT_ID = "2fb5269590f5467ab7235fe43c834b4d"
SPOTIFY_CLIENT_SECRET = "4226865d2a6a4ce6940ff492e4be6041"
SPOTIFY_REDIRECT_URI = "https://nomistic-curve.000webhostapp.com"
VKONTAKTE_TOKEN = "3100a7f90f18a25b3a53af0893da63700f01bceb6fb416c7d299903707474a26416bcc289c8afad18d3be"

# Starting.
start()
