"""
Linear Congruential Generator (LCG)
From: Knuth's "The Art of Computer Programming"

The LCG generates pseudo-random numbers using:
    X(n+1) = (a * X(n) + c) mod m

Key insight: The choice of a, c, m determines the period and quality.
"""

class LCG:
    """Linear Congruential Generator - classic PRNG algorithm"""
    
    def __init__(self, seed: int = 42, 
                 a: int = 1103515245,  # multiplier
                 c: int = 12345,       # increment
                 m: int = 2**31):      # modulus
        self.state = seed
        self.a = a
        self.c = c
        self.m = m
    
    def next(self) -> int:
        """Generate next pseudo-random number"""
        self.state = (self.a * self.state + self.c) % self.m
        return self.state
    
    def random(self) -> float:
        """Generate float in [0, 1)"""
        return self.next() / self.m
    
    def randint(self, low: int, high: int) -> int:
        """Generate integer in [low, high]"""
        return low + (self.next() % (high - low + 1))


def demo():
    rng = LCG(seed=12345)
    
    print("First 10 random numbers:")
    for i in range(10):
        print(f"  {i+1}: {rng.random():.6f}")
    
    print("\n10 dice rolls:")
    rng2 = LCG(seed=42)
    rolls = [rng2.randint(1, 6) for _ in range(10)]
    print(f"  {rolls}")


if __name__ == "__main__":
    demo()
