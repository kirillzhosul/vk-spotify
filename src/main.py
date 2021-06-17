# Python VK Spotify integration.
# Author: Kirill Zhosul (@kirillzhosul)

# Importing modules.

# Preinstalled libraries.
import time
import threading
import requests
import os

# VK API.
import vk_api
import vk_api.utils
from vk_api.exceptions import AuthError
from vk_api.longpoll import VkLongPoll, VkEventType

# Spotify API.
import tekore

try:
    # Trying to importing loguru.

    # Importing.
    from loguru import logger  # noqa
except ImportError:
    # If import error.

    # Disabling loguru.
    __loguru_enabled = False
else:
    # If no errors.

    # Enabling loguru.
    __loguru_enabled = True

try:
    # Trying to importing Genius API.

    # Importing.
    import lyricsgenius  # noqa
except ImportError:
    # If import error.

    # Disabling Genius.
    __genius_enabled = False
else:
    # If no errors.

    # Enabling Genius.
    __genius_enabled = True

try:
    # Trying to importing Shazam API.

    # Importing.
    from ShazamAPI import Shazam  # noqa
except ImportError:
    # If import error.

    # Disabling Shazam.
    __shazam_enabled = False
else:
    # If no errors.

    # Enabling Shazam.
    __shazam_enabled = True


def VKontakte_command_information():
    # Information command that returns information.

    # Returning.
    return "Информация:\nSpotify, Genius, Shazam интеграция в VK,\nАвтор: Кирилл Жосул,\nИспользуемые API: Genius API, Spotify API, VKontakte API, Shazam API."

def VKontakte_command_help():
    # Help command that returns help.

    # Response.
    _response = "Команды:\n"
    _response += "!info|i|inormation|инфо - Информация,\n"
    _response += "!help|h|помощь|! - Эта команда,\n"
    _response += "!track|song|current|песня|трек - Выведет трек который играет в данный момент,\n"
    _response += "!next|следующая - Кнопка вперед (Переключить трек),\n"
    _response += "!previous|прошлая- Кнопка назад (Переключить трек),\n"
    _response += "!pause|пауза - Приостановить трек который играет,\n"
    _response += "!resume|продолжить - Продолжить трек который играет,\n"
    _response +=  "!search|s|поиск!п \{ЗАПРОС_ПОИСКА\} - Покажет трек который удалось найти из вашего запроса,\n"
    _response += "!volume|громкость \{ГРОМКОСТЬ(ПУСТО ДЛЯ ПОЛУЧЕНИЯ ЗНАЧЕНИЯ СЕЙЧАС)\} - Поменять громкость на переданную,\n"
    _response += "!lyrics|genius|l|текст \{ЗАПРОС_ПОИСКА\}- Получить текст трека из поиска,\n"
    _response += "!analyse|a|анализ \{ЗАПРОС_ПОИСКА\} - Анализ трека из поиска (Особенности)"

    # Returning.
    return _response    

def VKontakte_command_track():
    # Track command that returns current track.

    # Returning.
    return Spotify_get_current_track(True)

def VKontakte_command_resume():
    # Resume command that resumes song.

    try:
        # Resuming.
        API_Spotify.playback_resume()

        # Returning
        return "Песня продолжена!"
    except Exception:
        return "Произошла ошибки при попытки продолжить песню! (Песня уже идёт?)"

def VKontakte_command_pause():
    # Pause command that pauses song.

    try:
        # Pausing.
        API_Spotify.playback_pause()

        # Returning
        return "Песня остановлена!"
    except Exception:
        return "Произошла ошибки при попытки остановить песню! (Песня уже остановлена?)"

def VKontakte_command_volume(_message):
    # Volume command that set new volume or returns it.
    try:
        # Trying to set or get volume.

        # Getting command arguments.
        _arguments = _message.split(" ")[1:]

        # Global volume.
        global VOLUME

        if len(_arguments) > 0:
            # If any arguments.

            # Getting volume.
            _volume = int(_arguments[0])

            if _volume < 0 or _volume > 100:
                # Overflow error.

                # Returning error.
                return "Громкость должна быть в пределах от 0 до 100%!"

            # Setting volume
            API_Spotify.playback_volume(_volume)

            # Change volume for global variable.
            VOLUME = _volume

            # Returning response.
            return f"Громкость теперь {VOLUME}%"
        else:
            # If no arguments.

            # Return volume.
            return f"Громкость равна {VOLUME}%"
    except Exception:
        # If there is an exception

        # Returning error.
        return f"Произошла ошибка при попытке получать/изменить громкость воспроизведения."

def VKontakte_command_previous():
    # Previous command that change track to previous.

    # Playing previous.
    API_Spotify.playback_previous()

    # Returning status.
    return f"Песня переключена на {Spotify_get_current_track(True)}!" 

def VKontakte_command_next():
    # Next command that change track to next.

    # Playing next.
    API_Spotify.playback_next()

    # Returning status.
    return f"Песня переключена на {Spotify_get_current_track(True)}!" 

def VKontakte_command_search(_message):
    # Search command that searces for song.

    try:
        # Getting command arguments.
        _arguments = _message.split(" ")[1:]

        if len(_arguments) < 1:
            # If Invalid arguments (not passed any.)

            # Returning example.
            return "Пример команды !search/s ЗАПРОС_ПОИСКА"

        # Searching tracks indeces.
        founded_tracks, = API_Spotify.search(" ".join(_arguments))
        founded_tracks = founded_tracks.items

        if len(founded_tracks) < 1:
            # If no search result

            # Returning no result text.
            return "Не удалось найти треки из вашего запроса!"

        # Getting just one track.
        founded_track = founded_tracks[0]

        # Playing.
        API_Spotify.playback_start_tracks([founded_track.id])

        # Response.
        return f"Песня переключена на {Spotify_format_track(founded_track)}. {founded_track.album.images[0].url}"
    except Exception:
        # If there is an exception.

        # Returning error.
        return "Произошла ошибки при попытки найти песню!"

def VKontakte_command_analyse(_message):
    # Analyse command that analyse song.

    try:
        # Getting command arguments.
        _arguments = _message.split(" ")[1:]

        if len(_arguments) < 1:
            # If Invalid arguments (not passed any.)

            # Returning example.
            return "Пример команды !analyse/a ЗАПРОС_ПОИСКА"

        # Searching tracks indeces.
        founded_tracks, = API_Spotify.search(" ".join(_arguments))
        founded_tracks = founded_tracks.items

        if len(founded_tracks) < 1:
            # If no search result

            # Returning no result text.
            return "Не удалось найти треки из вашего запроса!"


        # Getting just one track.
        founded_track = founded_tracks[0]

        # Getting track data.
        _track_features = API_Spotify.track_audio_features(founded_track.id)
        _track_analysis = API_Spotify.track_audio_analysis(founded_track.id)

        # Response.
        return f"Анализ трека {Spotify_format_track(founded_track)}: Акустичность: {Spotify_format_feature(_track_features.acousticness)}, \
                \nТанцевальность: {Spotify_format_feature(_track_features.danceability)},\nЭнергичность: {Spotify_format_feature(_track_features.energy)}, \
                \nИнструментальность: {_track_features.instrumentalness},\nЖивучесть: {_track_features.liveness}, \
                \nГромкость: {_track_features.loudness},\nРазговорность: {Spotify_format_feature(_track_features.speechiness)}, \
                \nТемп: {_track_features.tempo},\nВалентность: {Spotify_format_feature(_track_features.valence)},\n"
    except Exception:
        # If there is an exception.

        # Returning error.
        return "Произошла ошибки при попытки анализировать песню!"
  
def VKontakte_command_lyrics(_message):
    # Lyrics command that returns lyrics of the song.

    if not __genius_enabled:
        return "Данная команда отключена!"
    try:
        # Getting command arguments.
        _arguments = _message.split(" ")[1:]

        if len(_arguments) < 1:
            # If Invalid arguments (not passed any.)

            # Returning example.
            return "Пример команды !lyrics/genius ЗАПРОС_ПОИСКА"

        # Searching tracks indeces.
        founded_tracks, = API_Spotify.search(" ".join(_arguments))
        founded_tracks = founded_tracks.items

        if len(founded_tracks) < 1:
            # If no search result

            # Returning no result text.
            return "Не удалось найти треки из вашего запроса (Spotify не имеет данного трека)!"


        # Getting just one track.
        founded_track = founded_tracks[0]

        # Searching song in genius.
        _genius_song = API_Genius.search_song(founded_track.name, Spotify_format_artists([_artist.name for _artist in founded_track.artists]))

        if _genius_song is not None:
            # If there is any song.

            # Getting lyrics.
            _lyrics = _genius_song.lyrics

            # Response.
            return f"Текст песни {Spotify_format_track(founded_track)}: {_lyrics}. {founded_track.album.images[0].url}"

        # Not found error.
        return "Не удалось найти треки из вашего запроса (Genius не имеет данного трека)!"
    except Exception:
        # If there is an exception.

        # Returning error.
        return "Произошла ошибки при попытки получить текст песни!"

def vk_handle_command(_message):
    # Function that returns response for the message.

    # Response for returning.
    _response = None

    if _message.startswith("!"):
        # If prefix in the command.

        if _message == "!":
            # Help command.
            _response = VKontakte_command_help()

        # Processing.
        if _response is None:
            # If not help.

            for _command in VKONTAKTE_COMMANDS:
                # For every commands.

                if _message.startswith(_command):
                    # If message starts with.

                    # Executing.
                    _response = VKONTAKTE_COMMANDS[_command](_message)

                    # Breaking loop.
                    break

    # Returning response
    return _response

def VKontakte_send_message(_peer, _text):
    # Function that sends message with the vkontakte API.

    try:
        # Sending.
        API_VKontakte.method("messages.send", {
            "random_id": vk_api.utils.get_random_id(),
            "peer_id": _peer,
            "message": _text,
        })
    except Exception as Error:
        # Error information.
        if __loguru_enabled:
            logger.error(f"Error when sending message with the VKontakte API! Eror information: {Error}")
        else:
            print(f"Error when sending message with the VKontakte API! Eror information: {Error}")

def Spotify_format_artists(_artists_list):
    # Function that returns string with formatted artists list.

    # Getting artists count.
    return ", ".join(_artists_list)

def Spotify_format_feature(_feature_value):
    # Function that formats Spotify feature value.

    if (type(_feature_value) != int and type(_feature_value) != float) or _feature_value < 0 or _feature_value > 1:
        # If not number or not in allowed range
        _error = f"Error when formatting feature with value {_feature_value}"
        if __loguru_enabled:
            logger.warning(_error)
        else:
            print(_error)
        raise ValueError(_error)

    # Returning.
    if _feature_value < 0.4:
        return STRINGS["spotify-feature-value-small"]
    elif _feature_value > 0.4:
        return STRINGS["spotify-feature-value-normal"]
    else:
        return STRINGS["spotify-feature-value-high"]

def Spotify_format_track(_track):
    # Function that formats track to the valid look.
    
    # Gettings artists list.
    _artists = Spotify_format_artists([_artist.name for _artist in _track.artists])

    # Returning.
    return STRINGS["spotify-format-track"].format(_track.name, _artists)

def Spotify_get_current_track(_album_cover=False):
    # Function that returns Spotify current track.

    try:
        # Getting playback.
        _playback = API_Spotify.playback(tracks_only=True)

        # Status for the return.
        _status = None

        if _playback is not None and _playback.is_playing:
            # If there is any track in playing and its playing.
            if _playback.item is not None and _playback.item.artists is not None:
                # If not any error ?.
            
                # Result.
                _status = Spotify_format_track(_playback.item)

                # Album cover if need.
                if _album_cover:
                    # If return cover.
                    if _playback.item.album is not None and len(_playback.item.album.images) > 0:
                        # If not error.
                        _status += f"\n {_playback.item.album.images[0].url}"

        # Returning status.
        return None
    except Exception as Error:
        # Printing exception.
        if __loguru_enabled:
            logger.exception(f"Error when trying to get current track ! Error information: {Error}")
        else:
            print(f"Error when trying to get current track ! Error information: {Error}")

def shazam_recognize_from_link(_link):
    # Function that returns recognized song from given link to an mp3 file on web.

    if not __shazam_enabled:
        # If shazam is not enabled.

        # Raising error.
        raise ImportError

    # Debug message.
    if __loguru_enabled:
        logger.debug("Started Shazam recognition!")

    # Getting filename.
    _filename = os.getcwd() + "\\voicemessage.mp3"

    # Downloading file.
    _downloadfile = requests.get(_link)
    open(_filename, 'wb').write(_downloadfile.content)

    # Debug message.
    if __loguru_enabled:
        logger.debug("Downloaded voice message!")

    # Getting shazam API.
    _API_SHAZAM = Shazam(open(_filename, "rb").read())
    _API_SHAZAM_GENERATOR = _API_SHAZAM.recognizeSong()

    # Default response
    _response = None

    for _song in _API_SHAZAM_GENERATOR:
        # For every song in the generator.

        # Getting song (removing offset)
        _song = _song[1]

        if "track" in _song:
            # If there is any track.

            # Getting track.
            _song = _song["track"]

            if "title" and "subtitle" in _song:
                # If there title and subtitle.

                # Getting response,
                _response = STRINGS["shazam-message-founded"].format(_song['title'], _song['subtitle'])

                if "images" in _song and "coverart" in _song["images"]:
                    # Getting image if exists.
                    _response += f"\n{_song['images']['coverart']}"

                # Breaking.
                break

    # Debug message.
    if __loguru_enabled:
        logger.debug(f"End recognition of the song!")

    # Response
    return _response

def shazam_process_message_request(_message_event):
    # Function that process shazam.

    if not __shazam_enabled:
        # If shazam is not enabled.

        # Returning none.
        return None

    if "attachments" in _message_event.attachments and len(_message_event.attachments["attachments"]) > 0:
        # If any attachment.

        # Attachment.
        _attachment = eval(_message_event.attachments["attachments"])[0]

        if _attachment["type"] == "audio_message":
            # If audio message.

            # Recognizing.
            _response = shazam_recognize_from_link(_attachment["audio_message"]["link_mp3"])

            # If no response.
            if _response is None:
                return STRINGS["shazam-message-not-found"]

            # Responding.
            return STRINGS["vkontakte-message-format-shazam"].format(_response)

    # Returning no answer.
    return None

def vk_status_updater():
    # Function that updates status for the VKontakte.

    # Status that was before (For not calling method and not get Captcha).
    _old_status = None

    while True:
        # Infinity loop.

        try:
            # Getting current track..
            _new_status = STRINGS["vkontakte-status-format"].format(Spotify_get_current_track(API_Spotify)) 

            if _new_status != _old_status:
                # If status was changed.

                # Updating status.
                API_VKontakte.method("status.set", {"text": _new_status})

                # Setting old status to the new.
                _old_status = _new_status

            # Sleeping for the timeout.
            time.sleep(VKONTAKTE_STATUS_UPDATE_SPEED)
        except Exception as Error:
            # If error.

            # Printing exception.
            if __loguru_enabled:
                logger.exception(f"Error when trying to update VKontakte status! Error information: {Error}")
            else:
                print(f"Error when trying to update VKontakte status! Error information: {Error}")

def vk_process_messages():
    # Function that listen for command in Vkontakte.

    # Getting longpoll server.
    _API_LONGPOOL_VKONTAKTE = VkLongPoll(API_VKontakte)

    for _message_event in _API_LONGPOOL_VKONTAKTE.listen():
        # For every event.

        if _message_event.type == VkEventType.MESSAGE_NEW:
            # If new message event.

            try:
                # Trying to answer.

                # Getting shazam result.
                _shazam_result = shazam_process_message_request(_message_event)

                if _shazam_result is None:
                    # If shazam not recognized or not voice message.

                    # Getting command text.
                    _command = _message_event.message.lower()

                    # Getting response for the command.
                    _message_response = vk_handle_command(_command)

                    if _message_response is not None and _message_response != "":
                        # If any answer.

                        # Sending message if response is exists.
                        VKontakte_send_message(_message_event.peer_id, STRINGS["vkontakte-message-format"].format(_message_response))
                else:
                    # Responding.
                    VKontakte_send_message(_message_event.peer_id, _shazam_result)
            except Exception as Error:
                # Printing exception.
                logger.exception(f"Error when trying to process VKontakte message! Error information: {Error}")

def main():
    # Function that starts all.

    # Authorizing APIs.
    try:
        # Trying to auth.

        # Global APIs.
        global API_Spotify, API_VKontakte

        # Spotify auth.
        API_Spotify = tekore.Spotify(tekore.prompt_for_user_token(__AUTH_SPOTIFY_CLIENT_ID, __AUTH_SPOTIFY_CLIENT_SECRET, __AUTH_SPOTIFY_REDIRECT_URI, tekore.scope.every))

        # Vkontakte auth.
        API_VKontakte = vk_api.VkApi(token=__AUTH_VKONTAKTE_TOKEN)

        if __genius_enabled:
            # If genius is enabled.

            # Global API.
            global API_Genius

            # Genius auth.
            API_Genius = lyricsgenius.Genius(__AUTH_GENIUS_TOKEN)
    except Exception as Error:
        # If there exception.

        # Error message.
        if __loguru_enabled:
            logger.error(f"Error when authorizing the APIs! Error information: {Error}")
        else:
            print(f"Error when authorizing the APIs! Error information: {Error}")

        # Raising error.
        raise AuthError

    # Launching threads.
    threading.Thread(target=vk_status_updater, args=()).start()
    threading.Thread(target=vk_process_messages, args=()).start()

    # Success message.
    if __loguru_enabled:
        logger.success("Launched main() function!")
    else:
        print("Launched main() function!")

# Uncomment this blocks to disable support of some functions.
#__genius_enabled = False
#__shazam_enabled = False
#__loguru_enabled = False

# Every VKONTAKTE_STATUS_UPDATE_SPEED will be called update of the status (VK).
VKONTAKTE_STATUS_UPDATE_SPEED = 3

# Default volume for the spotify (Will be set when launching as spotify don't has method to get current volume).
VOLUME = 100

# Authorizations values.

# Spotify auth.
__AUTH_SPOTIFY_CLIENT_ID = ""
__AUTH_SPOTIFY_CLIENT_SECRET = ""
__AUTH_SPOTIFY_REDIRECT_URI = ""

# Vkontakte auth (user token).
__AUTH_VKONTAKTE_TOKEN = ""

# Genius token (Left blank if genius is disabled.
__AUTH_GENIUS_TOKEN = None

# APIs objects.
API_Spotify = None
API_VKontakte = None
API_Genius = None

# Commands for the VK.
VKONTAKTE_COMMANDS = {
    "!help": VKontakte_command_help, "!h": VKontakte_command_help, "!помошь": VKontakte_command_help,
    "!info": VKontakte_command_information, "!i": VKontakte_command_information, "!information": VKontakte_command_information, "!инфо": VKontakte_command_information, "!информация": VKontakte_command_information,
    "!lyrics": VKontakte_command_lyrics, "!l": VKontakte_command_lyrics, "!текст": VKontakte_command_lyrics, "!genius": VKontakte_command_lyrics,
    "!search": VKontakte_command_search, "!s": VKontakte_command_search, "!поиск": VKontakte_command_search, "!п": VKontakte_command_search,
    "!next": VKontakte_command_next, "!следующая": VKontakte_command_next,
    "!previous": VKontakte_command_previous, "!прошлая": VKontakte_command_previous,
    "!pause": VKontakte_command_pause, "!пауза": VKontakte_command_pause,
    "!resume": VKontakte_command_resume, "!продолжить": VKontakte_command_resume,
    "!analyse": VKontakte_command_analyse, "!анализ": VKontakte_command_analyse,
    "!volume": VKontakte_command_volume, "!громкость": VKontakte_command_volume,
    "!track": VKontakte_command_track, "!song": VKontakte_command_track, "!current": VKontakte_command_track, "!песня": VKontakte_command_track, "!трек": VKontakte_command_track
}

# Strings used for answering / other.
STRINGS = {
    "vkontakte-status-format": "Слушает Spotify. Трек: {}.",
    "vkontakte-message-format": "[Spotify Integration]\n{}",
    "vkontakte-message-format-shazam": "[Shazam Integration]\n{}",
    "spotify-format-track": "{} от {}",
    "spotify-feature-value-small": "Малая",
    "spotify-feature-value-normal": "Средняя",
    "spotify-feature-value-high": "Высокая",
    "shazam-message-not-found": "По вашему запросу не удалось ничего найти.",
    "shazam-message-founded": "Это {} от {}?"
}

# Starting.
if __name__ == "__main__":
    # Entry point.

    # Calling entry point functions.
    main()