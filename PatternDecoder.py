class PatternDecoder:
    def __init__(self, known_patterns: dict, tolerance: float = 0.5):
        self.known_patterns = known_patterns
        self.tolerance = tolerance

    def decode(self, signal_pattern):
        for ref_pattern, name in self.known_patterns.items():
            if self._matches(ref_pattern, signal_pattern):
                return name
        return None

    def _matches(self, ref_pattern, signal_pattern):
        if len(ref_pattern) != len(signal_pattern):
            return False
        for ref, actual in zip(ref_pattern, signal_pattern):
            if abs(ref - actual) > ref * self.tolerance:
                return False
        return True