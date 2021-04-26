import time, vk_api, tekore      
s, v, t = tekore.Spotify(tekore.prompt_for_user_token("2fb5269590f5467ab7235fe43c834b4d", "4226865d2a6a4ce6940ff492e4be6041", "https://nomistic-curve.000webhostapp.com", tekore.scope.every)), vk_api.VkApi(token="23a783f4411d9f0f592372afe383414933ee24945630f3c82db39b58b34e4b70a9463320a897c91c40e99"), None
while True:
    try:
        p, y, a = s.playback(tracks_only=True), "Не слушает Spotify.", []
        if p is not None and p.is_playing:
            [a.append(i.name) for i in p.item.artists]
            y = f"Слушает Spotify. Песня: {p.item.name} от {', '.join(a)}"
        if t != y:
            t, j = y, v.method("status.set", {"text": y})
        time.sleep(3)
    except Exception as e:
        print(e)