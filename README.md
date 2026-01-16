Aplikacja to prosta symulacja ruletki znanej z kasyna. Zawiera panel administratora,
w którym możemy wykonywać operacje CRUD - ustawianie funduszy kont graczy oraz podgląd historii losowań.

Aby uruchomić aplikację należy stworzyć środowisko wirtualne i pobrać biblioteki
z pliku requirements.txt

Następnie w kosnoli w głównym katalogu aplikacji należy wpisac: uvicorn main:app --reload

Aby uruchomić testy należy wpisać w konsoli (będąc w głównym katlaogu): pytest tests/test_game_engine.py

W aplikacji automatycznie tworzony jest administrator - login: admin, hasło: admin
W dołączonej bazie danych jes też dwóch użytkowników - user1 i user2, hasła to 123
