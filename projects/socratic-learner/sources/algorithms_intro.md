# Fundamental Algorithms: An Introduction

## Section 1: What Is An Algorithm?

### 1.1 Definition

An **algorithm** is a finite sequence of well-defined instructions for solving a class of problems or performing a computation. The word derives from the name of the Persian mathematician Muhammad ibn Musa al-Khwarizmi (c. 780-850 CE).

For a procedure to qualify as an algorithm, it must satisfy five fundamental properties:

1. **Finiteness**: An algorithm must always terminate after a finite number of steps. A procedure that runs forever is not an algorithm.

2. **Definiteness**: Each step of an algorithm must be precisely defined. The actions to be carried out must be rigorously and unambiguously specified for each case.

3. **Input**: An algorithm has zero or more inputs—quantities that are given to it before the algorithm begins, or dynamically as it runs.

4. **Output**: An algorithm has one or more outputs—quantities that have a specified relation to the inputs.

5. **Effectiveness**: An algorithm's operations must be sufficiently basic that they can, in principle, be done exactly and in a finite length of time by a person using pencil and paper.

### 1.2 Algorithms vs. Programs

An algorithm is not the same as a program. An algorithm is an abstract concept—a method or procedure. A program is a concrete implementation of an algorithm in a specific programming language. The same algorithm can be implemented in many different programs.

Consider: The algorithm for finding the greatest common divisor of two numbers existed for over 2000 years before any programming language was invented.

### 1.3 A First Example: Euclid's Algorithm

Euclid's algorithm finds the greatest common divisor (GCD) of two positive integers. It is one of the oldest known algorithms, appearing in Euclid's *Elements* around 300 BCE.

**Problem**: Given two positive integers m and n, find their greatest common divisor—the largest positive integer that divides both m and n without remainder.

**Algorithm E (Euclid's algorithm)**:

- **E1.** [Find remainder.] Divide m by n and let r be the remainder. (We have 0 ≤ r < n.)
- **E2.** [Is it zero?] If r = 0, the algorithm terminates; n is the answer.
- **E3.** [Reduce.] Set m ← n, n ← r, and go back to step E1.

**Example**: Find gcd(544, 119).

| Step | m | n | r | Action |
|------|-----|-----|-----|--------|
| E1 | 544 | 119 | 68 | 544 = 4×119 + 68 |
| E3 | 119 | 68 | — | Replace m with n, n with r |
| E1 | 119 | 68 | 51 | 119 = 1×68 + 51 |
| E3 | 68 | 51 | — | Replace |
| E1 | 68 | 51 | 17 | 68 = 1×51 + 17 |
| E3 | 51 | 17 | — | Replace |
| E1 | 51 | 17 | 0 | 51 = 3×17 + 0 |
| E2 | — | 17 | 0 | r = 0, so gcd = 17 |

**Verification**: gcd(544, 119) = 17. Indeed, 544 = 17 × 32 and 119 = 17 × 7.

### 1.4 Why Euclid's Algorithm Works

The algorithm relies on a key mathematical property:

**Theorem**: If m = qn + r (where q is the quotient and r is the remainder when m is divided by n), then gcd(m, n) = gcd(n, r).

**Proof**: Any divisor of both m and n must also divide r = m - qn. Conversely, any divisor of both n and r must divide m = qn + r. Therefore, the set of common divisors of (m, n) equals the set of common divisors of (n, r), so their greatest common divisors are equal.

Since r < n at each step, and r ≥ 0, the algorithm must eventually reach r = 0. When r = 0, we have gcd(n, 0) = n, so n is the answer.

### 1.5 Properties Verified

Let us verify that Euclid's algorithm satisfies all five properties:

1. **Finiteness**: The remainder r strictly decreases (since r < n, and n becomes the new r), and r ≥ 0. The sequence of remainders must reach 0 in at most n steps.

2. **Definiteness**: Each step is precisely defined. "Divide m by n" has an unambiguous meaning for positive integers. The comparison r = 0 is definite.

3. **Input**: Two positive integers m and n.

4. **Output**: One positive integer, the gcd of m and n.

5. **Effectiveness**: Division, comparison to zero, and assignment are all operations that can be done by hand.

---

## Section 2: Analyzing Algorithms

### 2.1 Why Analyze?

Analysis tells us how an algorithm behaves as the problem size grows. Two algorithms that both solve a problem correctly may have vastly different performance. Analysis allows us to:

- **Compare** algorithms objectively
- **Predict** behavior on large inputs
- **Identify** bottlenecks and opportunities for improvement

### 2.2 Measuring Performance

We measure algorithm performance in terms of:

- **Time complexity**: How many operations does it perform?
- **Space complexity**: How much memory does it use?

We express these as functions of the input size, typically denoted n.

### 2.3 Big-O Notation

**Definition**: We say f(n) = O(g(n)) if there exist positive constants c and n₀ such that f(n) ≤ c·g(n) for all n ≥ n₀.

In plain language: f(n) is O(g(n)) means f grows no faster than g, ignoring constant factors and small inputs.

**Common complexity classes** (from fastest to slowest growth):

| Notation | Name | Example |
|----------|------|---------|
| O(1) | Constant | Array access by index |
| O(log n) | Logarithmic | Binary search |
| O(n) | Linear | Simple search through a list |
| O(n log n) | Linearithmic | Efficient sorting (mergesort) |
| O(n²) | Quadratic | Simple sorting (bubble sort) |
| O(2ⁿ) | Exponential | Brute-force subset enumeration |

### 2.4 Analysis of Euclid's Algorithm

How many steps does Euclid's algorithm take?

**Theorem (Lamé, 1844)**: The number of steps in Euclid's algorithm never exceeds five times the number of digits in the smaller input.

More precisely, if the algorithm performs k division steps, then the smaller input n must be at least as large as the k-th Fibonacci number.

**Consequence**: Euclid's algorithm is O(log n) where n is the smaller input. This is remarkably efficient—doubling the input size adds only a constant number of steps.

### 2.5 Best, Worst, and Average Case

For many algorithms, performance varies depending on the specific input:

- **Best case**: The minimum operations for any input of size n
- **Worst case**: The maximum operations for any input of size n
- **Average case**: The expected operations over all inputs of size n

For Euclid's algorithm:
- **Best case**: r = 0 on the first step (n divides m), so 1 step
- **Worst case**: Consecutive Fibonacci numbers, approximately 2.078 ln(n) + 1.672 steps
- **Average case**: Approximately 0.843 ln(n) + 1.47 steps

---

## Section 3: Correctness

### 3.1 What Does Correctness Mean?

An algorithm is **correct** if, for every valid input, it:
1. Terminates (doesn't run forever)
2. Produces the correct output

Correctness is not optional. An incorrect algorithm is useless, regardless of how fast it runs.

### 3.2 Proving Correctness

For Euclid's algorithm, we must prove:

1. **Termination**: The algorithm always stops.
2. **Partial correctness**: If it stops, the answer is correct.

**Termination proof**: At each iteration, r < n, and n becomes the new value used for the next remainder. Since n decreases and is always a non-negative integer, it must eventually reach a state where r = 0.

**Partial correctness proof**: We use a **loop invariant**—a property that is true before and after each iteration.

**Loop invariant**: gcd(m, n) = gcd(original m, original n)

- **Initialization**: Before the first iteration, this is trivially true.
- **Maintenance**: If gcd(m, n) = d before an iteration, then after setting m ← n, n ← r, we have gcd(n, r) = gcd(m, n) = d (by the theorem in Section 1.4).
- **Termination**: When r = 0, gcd(m, n) = n. By the invariant, n = gcd(original m, original n).

### 3.3 Defensive Programming

Even correct algorithms can fail in practice due to:

- **Invalid input**: What if m or n is zero? Negative? Not an integer?
- **Overflow**: What if m × n exceeds the maximum integer size?
- **Implementation errors**: Typos, off-by-one mistakes, etc.

Good practice: Verify inputs, test edge cases, and use assertions.

---

## Section 4: Recursion

### 4.1 Definition

A **recursive** algorithm is one that calls itself with a smaller instance of the same problem.

Every recursive algorithm has:
1. **Base case(s)**: Inputs for which the answer is immediate, without recursion
2. **Recursive case(s)**: Inputs that are reduced and the algorithm is called again

### 4.2 Euclid's Algorithm, Recursively

The iterative Euclid's algorithm can be expressed recursively:

```
gcd(m, n):
    if n = 0:
        return m
    else:
        return gcd(n, m mod n)
```

**Base case**: n = 0, return m
**Recursive case**: n > 0, return gcd(n, m mod n)

### 4.3 How Recursion Works

Each recursive call creates a new "frame" with its own variables. The frames stack up until a base case is reached, then unwind as each call returns.

**Example**: gcd(544, 119)

```
gcd(544, 119)
  → gcd(119, 68)    [544 mod 119 = 68]
    → gcd(68, 51)   [119 mod 68 = 51]
      → gcd(51, 17) [68 mod 51 = 17]
        → gcd(17, 0) [51 mod 17 = 0]
          → return 17  [base case]
        → return 17
      → return 17
    → return 17
  → return 17
→ 17
```

### 4.4 Recursion vs. Iteration

Any recursive algorithm can be converted to an iterative one (and vice versa). The choice depends on:

| Factor | Recursion | Iteration |
|--------|-----------|-----------|
| Clarity | Often cleaner for naturally recursive problems | Better for simple loops |
| Efficiency | Overhead from call stack | Generally faster |
| Space | Uses stack space proportional to recursion depth | Constant extra space |
| Risk | Stack overflow on deep recursion | None |

For Euclid's algorithm, both forms are equally clear, but iteration is slightly more efficient.

---

## Section 5: Summary

This section introduced:

1. **Definition of algorithm**: A finite, definite, effective procedure with inputs and outputs
2. **Euclid's algorithm**: An ancient, elegant algorithm for finding the GCD
3. **Analysis**: Measuring time and space complexity using Big-O notation
4. **Correctness**: Proving algorithms work using loop invariants
5. **Recursion**: Algorithms that call themselves on smaller problems

These concepts form the foundation for studying more complex algorithms and data structures.

---

## Exercises

1. Trace Euclid's algorithm for gcd(252, 105). How many steps does it take?

2. What happens if you call Euclid's algorithm with m < n? Does it still work?

3. The **extended Euclidean algorithm** finds integers x and y such that gcd(m, n) = mx + ny. Research and implement it.

4. Prove that for any n > 0, gcd(n, n) = n.

5. What is the time complexity of an algorithm that examines all pairs in a list of n elements?
