"""
Testy jednostkowe dla logiki ruletki
"""
import pytest
from game_engine import RouletteEngine


class TestGetColor:
    """Testy metody get_color"""
    
    def test_zero_is_green(self):
        """Test: 0 powinno być zielone"""
        engine = RouletteEngine()
        assert engine.get_color(0) == "green"
    
    def test_red_numbers(self):
        """Test: czerwone numery"""
        engine = RouletteEngine()
        red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
        for num in red_numbers:
            assert engine.get_color(num) == "red"
    
    def test_black_numbers(self):
        """Test: czarne numery"""
        engine = RouletteEngine()
        black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
        for num in black_numbers:
            assert engine.get_color(num) == "black"


class TestSpin:
    """Testy metody spin"""
    
    def test_spin_returns_valid_number(self):
        """Test: spin zwraca liczbę z zakresu 0-36"""
        engine = RouletteEngine()
        for _ in range(50):
            result = engine.spin()
            assert 0 <= result["number"] <= 36
    
    def test_spin_returns_valid_color(self):
        """Test: spin zwraca prawidłowy kolor"""
        engine = RouletteEngine()
        for _ in range(50):
            result = engine.spin()
            assert result["color"] in ["red", "black", "green"]
    
    def test_spin_adds_to_history(self):
        """Test: spin dodaje wynik do historii"""
        engine = RouletteEngine()
        initial_len = len(engine.history)
        engine.spin()
        assert len(engine.history) == initial_len + 1
    
    def test_history_max_length(self):
        """Test: historia ma maksymalnie 10 elementów"""
        engine = RouletteEngine()
        for _ in range(15):
            engine.spin()
        assert len(engine.history) == 10


class TestCalculatePayout:
    """Testy metody calculate_payout"""
    
    def test_number_bet_win(self):
        """Test: wygrana na konkretny numer"""
        engine = RouletteEngine()
        payout = engine.calculate_payout("number", "7", 10.0, 7)
        assert payout == 360.0
    
    def test_number_bet_loss(self):
        """Test: przegrana na konkretny numer"""
        engine = RouletteEngine()
        payout = engine.calculate_payout("number", "7", 10.0, 8)
        assert payout == 0.0
    
    def test_color_red_win(self):
        """Test: wygrana na kolor czerwony"""
        engine = RouletteEngine()
        payout = engine.calculate_payout("color", "red", 10.0, 1)
        assert payout == 20.0
    
    def test_color_black_win(self):
        """Test: wygrana na kolor czarny"""
        engine = RouletteEngine()
        payout = engine.calculate_payout("color", "black", 10.0, 2)
        assert payout == 20.0
    
    def test_color_green_win(self):
        """Test: wygrana na kolor zielony (zero)"""
        engine = RouletteEngine()
        payout = engine.calculate_payout("color", "green", 10.0, 0)
        assert payout == 360.0
    
    def test_parity_even_win(self):
        """Test: wygrana na parzyste"""
        engine = RouletteEngine()
        payout = engine.calculate_payout("parity", "even", 10.0, 2)
        assert payout == 20.0
    
    def test_dozen_first_win(self):
        """Test: wygrana na pierwszy tuzin (1-12)"""
        engine = RouletteEngine()
        payout = engine.calculate_payout("dozen", "1st 12", 10.0, 5)
        assert payout == 30.0

