import random

class Interval:
    # The notion of closed intervals on floats fundamentally makes no sense
    # Any individual float value is actually a representative of infinitely many real numbers
    # For example, 0.500000000000000000000001, which is in (0.5, 0.6), is represented as 0.5,
    # even though the real number 0.5 is not contained within the interval (0.5, 0.6)
    # To this end, the effects of close_left and close_right are exclusively visual
    close_left: bool
    close_right: bool
    lower: float
    upper: float
    def __init__ (self, lower=0.0, upper=1.0, close_left=False, close_right=False):
        self.lower = lower
        self.upper = upper
        self.close_left = close_left
        self.close_right = close_right
        if self.lower > self.upper:
            raise ArithmeticError(f"lower bound is larger than upper bound ({lower} > {upper})")
    def __repr__ (self):
        left_delim  = '(' if self.close_left  else '['
        right_delim = ')' if self.close_right else ']'
        return f"{left_delim}{self.lower}, {self.upper}{right_delim}"
    def __add__ (self, other: Interval | float | int):
        if isinstance(other, Interval):
            lower = self.lower + other.lower
            upper = self.upper + other.upper
            close_left = self.close_left or other.close_left
            close_right = self.close_right or other.close_right
            return Interval(lower, upper, close_left, close_right)
        elif isinstance(other, float) or isinstance(other, int):
            lower = self.lower + other
            upper = self.upper + other
            close_left = self.close_left
            close_right = self.close_right
            return Interval(lower, upper, close_left, close_right)
        return NotImplemented
    def __sub__ (self, other: Interval | float | int):
        if isinstance(other, Interval):
            lower = self.lower - other.lower
            upper = self.upper - other.upper
            close_left = self.close_left or other.close_left
            close_right = self.close_right or other.close_right
            return Interval(lower, upper, close_left, close_right)
        elif isinstance(other, float) or isinstance(other, int):
            lower = self.lower - other
            upper = self.upper - other
            close_left = self.close_left
            close_right = self.close_right
            return Interval(lower, upper, close_left, close_right)
        return NotImplemented

    def get_random (self, precision: int=-1):
        value = random.uniform(self.lower, self.upper)
        if precision < 0:
            return value
        else:
            return round(value, precision)
    def contains (self, x: float | int):
        return x >= self.lower and x <= self.upper
    def width (self):
        return self.upper - self.lower
    def floor (self, lower: float | int):
        new_lower = self.lower if self.lower > lower else lower
        new_upper = self.upper if self.upper > lower else lower
        return Interval(new_lower, new_upper, self.close_left, self.close_right)
    def ceil (self, upper: float | int):
        new_lower = self.lower if self.lower < upper else upper
        new_upper = self.upper if self.upper < upper else upper
        return Interval(new_lower, new_upper, self.close_left, self.close_right)
    def clamp (self, lower: float | int, upper: float | int):
        return self.floor(lower).ceil(upper)
