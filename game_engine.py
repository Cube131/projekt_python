import random
from collections import deque
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class GameState:
    """
    Klasa danych reprezentujaca stan gry
    """
    status: str
    time_left: int
    last_result: dict = None

class RouletteEngine:
    """
    Klasa zarzadzajaca logiką ruletki
    """
    def __init__(self):
        # Kolejka dwustronna do historii
        self.history: deque = deque(maxlen=10)
        self.red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}

    def get_color(self, number: int) -> str:
        """
        Zwraca kolor dla podanej liczby
        """
        if number == 0:
            return "green"
        return "red" if number in self.red_numbers else "black"

    def spin(self) -> Dict[str, Any]:
        """
        Losuje liczbę całkowitą w zakresie 0-36
        Zwraca slownik z wynikiem losowania i kolorem
        """
        number = random.randint(0, 36)
        color = self.get_color(number)
        
        result = {"number": number, "color": color}
        self.history.appendleft(result)
        return result

    def calculate_payout(self, bet_type: str, bet_value: str, amount: float, result_number: int) -> float:
        """
        Oblicza wygrana na podstawie zakladu i wyniku
        """
        result_color = self.get_color(result_number)
        payout = 0.0

        # Prosta logika wyplat
        if bet_type == "number":
            if int(bet_value) == result_number:
                payout = amount * 36
        elif bet_type == "color":
            if bet_value == result_color:
                multiplier = 36 if bet_value == "green" else 2
                payout = amount * multiplier
        elif bet_type == "parity":
            if result_number != 0:
                is_even = (result_number % 2 == 0)
                if (bet_value == "even" and is_even) or (bet_value == "odd" and not is_even):
                    payout = amount * 2
        elif bet_type == "dozen":
            if result_number != 0:
                if bet_value == "1st 12" and 1 <= result_number <= 12:
                    payout = amount * 3
                elif bet_value == "2nd 12" and 13 <= result_number <= 24:
                    payout = amount * 3
                elif bet_value == "3rd 12" and 25 <= result_number <= 36:
                    payout = amount * 3
        
        return payout