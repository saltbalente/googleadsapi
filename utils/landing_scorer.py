class LandingScorer:
    def __init__(self, conversions, conversion_rate, cpc_efficiency, ctr):
        self.conversions = conversions
        self.conversion_rate = conversion_rate
        self.cpc_efficiency = cpc_efficiency
        self.ctr = ctr

    def normalize(self, value, min_value, max_value):
        """Normalize a metric to a scale of 0 to 1."""
        if max_value - min_value == 0:
            return 0
        return (value - min_value) / (max_value - min_value)

    def calculate_weighted_score(self):
        """Calculate the weighted score based on the defined metrics."""
        normalized_conversions = self.normalize(self.conversions, 0, 100)  # Example range
        normalized_conversion_rate = self.normalize(self.conversion_rate, 0, 100)  # Example range
        normalized_cpc_efficiency = self.normalize(self.cpc_efficiency, 0, 100)  # Example range
        normalized_ctr = self.normalize(self.ctr, 0, 100)  # Example range

        weighted_score = (
            (normalized_conversions * 0.35) +
            (normalized_conversion_rate * 0.25) +
            (normalized_cpc_efficiency * 0.20) +
            (normalized_ctr * 0.20)
        )
        return weighted_score

    def performance_level(self):
        """Determine performance level based on the weighted score."""
        score = self.calculate_weighted_score()
        if score >= 0.8:
            return "Excellent"
        elif score >= 0.6:
            return "Good"
        elif score >= 0.4:
            return "Average"
        else:
            return "Poor"