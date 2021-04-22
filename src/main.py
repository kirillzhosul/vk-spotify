# Импортация модулей.
import tekore  # Модуль для работы с программным интерфейсом Spotify (WEB API).
import vk_api  # Модуль для работы с VK API.
import threading
import time
import auth


class SpotifyStatus:
    """ Класс для работы с Spotify статусом. """

    def __init__(self, _app_id, _app_secret, _app_redirect_url, _app_scopes, _vk_token):
        """
        Констркуктор класса.
        :param _app_id: Индекс приложения.
        :param _app_secret: Секретный код приложения.
        :param _app_redirect_url: Ссылка из списка разрешенных для перехода.
        """

        # Перевод в переменные объекта.
        self.__application_index = _app_id
        self.__application_secret = _app_secret
        self.__application_redirect_url = _app_redirect_url
        self.__application_scopes = _app_scopes
        self.__vk_token = _vk_token

        # Другие переменные.
        self.__vk_connection = vk_api.VkApi(token=self.__vk_token)
        self.__application_spotify = None
        self.__application_token = None
        self.__update_time = 10

        self.__last_status = -1

    def ask_for_token(self) -> None:
        """
        Получение токена от пользователя.
        :return: None
        """

        # Запрос на авторизацию
        self.__application_token = tekore.prompt_for_user_token(self.__application_index,
                                                                self.__application_secret,
                                                                self.__application_redirect_url,
                                                                self.__application_scopes)

        # Получение приложения.
        self.__application_spotify = tekore.Spotify(self.__application_token)

    def get_current_status(self) -> str:
        """
        Получает статус.
        :return: None
        """

        # Получение трека.
        current_playback = self.__application_spotify.playback(tracks_only=True)

        if current_playback.is_playing:
            # Если он играет.

            # Получение трека.
            current_track = current_playback.item

            artists = []
            for a in current_track.artists:
                artists.append(a.name)

            str = ", ".join(artists)

            # Получение статуса.
            status = f"Слушает Spotify. Песня: {current_track.name} от {str}"

            # Возвращение.
            return status
        else:
            return "Не слущает Spotify в данный момент."

    def set_current_status(self, _status):
        if self.__last_status != _status:
            self.__vk_connection.method("status.set", {
                "text": _status
            })
            self.__last_status = _status

    def run(self) -> None:
        """
        Метод запуска.
        :return: None
        """

        thread = threading.Thread(target=self.update, args=())
        thread.run()

    def update(self):
        while True:

            print("Update called")

            # Получение статуса.
            status = self.get_current_status()

            # Установка статуса.
            self.set_current_status(status)

            time.sleep(self.__update_time)


if __name__ == "__main__":
    # Точка входа.

    # Создание объекта.
    spotify_status = SpotifyStatus(*auth.data)

    # Запрос на токен.
    spotify_status.ask_for_token()

    spotify_status.run()
