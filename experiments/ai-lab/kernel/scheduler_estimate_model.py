#!/usr/bin/env python3
"""AI-assisted independent fork: arithmetic model, not a kernel runtime test."""
def estimate(count, priority, base, minimum, maximum):
    adjusted = count - count * priority // 120
    return max(minimum, min(adjusted * base, maximum))

def main():
    checks = 0
    for base, minimum, maximum in ((1000, 100, 5000), (500, 100, 2500),
                                  (2000, 500, 20000)):
        for count in (0, 1, 2, 3, 4, 16, 128, 1024, 2147483647):
            previous = maximum
            for priority in range(121):
                result = estimate(count, priority, base, minimum, maximum)
                assert minimum <= result <= maximum
                assert result <= previous
                previous = result
                checks += 1
            assert estimate(count, 120, base, minimum, maximum) == minimum
        for priority in range(121):
            values = [estimate(n, priority, base, minimum, maximum)
                      for n in range(129)]
            assert values == sorted(values)
        assert estimate(4, 10, base, minimum, maximum) > minimum
    print(f"Arithmetic model PASS: {checks} count/priority/mode cases")

if __name__ == "__main__":
    main()
