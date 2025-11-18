class PatternDecoder:
    def __init__(self, known_patterns: dict, tolerance: float = 0.5):
        self.known_patterns = known_patterns
        self.tolerance = tolerance

    def clean_pattern(self, pattern, noise_threshold=20000, max_merged_length=300000):
        cleaned = []
        i = 0

        while i < len(pattern):
            p = pattern[i]

            # If not noise → keep it
            if p >= noise_threshold:
                cleaned.append(p)
                i += 1
                continue

            # Now: p is noise pulse (< noise_threshold)
            # Make sure we have previous AND next pulses
            if len(cleaned) == 0 or i + 1 >= len(pattern):
                # Noise with no neighbors → just skip it
                i += 1
                continue

            prev_pulse = cleaned[-1]
            next_pulse = pattern[i + 1]

            merged = prev_pulse + p + next_pulse

            # Check if merged pulse is meaningful
            if merged <= max_merged_length:
                # Accept merge
                cleaned[-1] = merged
                i += 2  # skip next pulse also
            else:
                # Reject noise → do NOT merge, just skip noise pulse
                i += 1
        cleaned = [p for p in cleaned if (p <= max_merged_length or (p >=1000000 and p <= 1300000))]
        #print(f"cleaned: {cleaned}")
        i = 1
        while True:
            if len(cleaned) <2:
                break
            if cleaned[len(cleaned) - i] <60000 or cleaned[len(cleaned) - 1] > 80000:
                cleaned.pop()
            else:
                break
        return cleaned

    def decode(self, signal_pattern):
        #signal_pattern = self.clean_pattern(signal_pattern)
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