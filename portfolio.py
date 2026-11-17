"""Compare three portfolios using editable decimal return and risk inputs."""

# Editable inputs: 0.035 means 3.5%. Correlations follow the sleeve order.
SLEEVES = [
    {"name": "Treasury bills", "expected_return": 0.035, "volatility": 0.005,
     "reserve_eligible": True},
    {"name": "Treasury 10-year note", "expected_return": 0.043,
     "volatility": 0.070, "reserve_eligible": True},
    {"name": "Investment-grade bond fund", "expected_return": 0.050,
     "volatility": 0.060, "reserve_eligible": False},
    {"name": "Global equity index fund", "expected_return": 0.080,
     "volatility": 0.160, "reserve_eligible": False},
]
CORRELATIONS = [
    [1.00, 0.10, 0.05, 0.00],
    [0.10, 1.00, 0.80, -0.10],
    [0.05, 0.80, 1.00, 0.25],
    [0.00, -0.10, 0.25, 1.00],
]
OBJECTIVE_RETURN = 0.065
BENCHMARK_ALLOCATIONS = {
    "Investment-grade bond fund": 0.40,
    "Global equity index fund": 0.60,
}

import math
import sys


def validate_inputs(sleeves, correlations):
    """Reject malformed inputs before calculating any portfolios."""
    size = len(sleeves)
    if not size:
        raise ValueError("At least one sleeve is required.")
    if len(correlations) != size or any(len(row) != size for row in correlations):
        raise ValueError("Correlation table must be square and match the sleeves.")
    for i, row in enumerate(correlations):
        for j, value in enumerate(row):
            if not math.isfinite(value) or not -1 <= value <= 1:
                raise ValueError(
                    f"Correlation at row {i + 1}, column {j + 1} must be between -1 and 1."
                )
            if value != correlations[j][i]:
                raise ValueError(
                    f"Correlation table is not symmetric at row {i + 1}, column {j + 1}."
                )
        if row[i] != 1:
            raise ValueError("Each diagonal correlation must equal 1.")
    for sleeve in sleeves:
        if not math.isfinite(sleeve["volatility"]) or sleeve["volatility"] <= 0:
            raise ValueError(f"Volatility for {sleeve['name']} must be positive and finite.")
        if not math.isfinite(sleeve["expected_return"]):
            raise ValueError(f"Expected return for {sleeve['name']} must be finite.")


def build_covariance_matrix(sleeves, correlations):
    """Calculate covariance[i][j] = correlation[i][j] * sigma[i] * sigma[j]."""
    validate_inputs(sleeves, correlations)
    return [
        [correlations[i][j] * left["volatility"] * right["volatility"]
         for j, right in enumerate(sleeves)]
        for i, left in enumerate(sleeves)
    ]


def benchmark_weights(sleeves, allocations):
    """Map benchmark allocations to the input sleeve order."""
    names = {sleeve["name"] for sleeve in sleeves}
    if not set(allocations).issubset(names):
        raise ValueError("Benchmark allocations reference an unknown sleeve.")
    return [allocations.get(sleeve["name"], 0.0) for sleeve in sleeves]


def equal_weights(sleeves):
    return [1.0 / len(sleeves)] * len(sleeves)


def inverse_volatility_weights(sleeves):
    inverse_volatilities = [1.0 / sleeve["volatility"] for sleeve in sleeves]
    total = sum(inverse_volatilities)
    return [value / total for value in inverse_volatilities]


def expected_return(weights, sleeves):
    return sum(weight * sleeve["expected_return"]
               for weight, sleeve in zip(weights, sleeves))


def portfolio_volatility(weights, covariance):
    variance = sum(weights[i] * weights[j] * covariance[i][j]
                   for i in range(len(weights)) for j in range(len(weights)))
    if variance < 0:
        raise ValueError("Portfolio variance is negative; check the correlation inputs.")
    return math.sqrt(variance)


def reserve_eligible_weight(weights, sleeves):
    return sum(weight for weight, sleeve in zip(weights, sleeves)
               if sleeve["reserve_eligible"])


def meets_objective(portfolio_return, objective_return):
    return portfolio_return >= objective_return


def lowest_risk_mix(sleeves, correlations, objective_return, reserve_minimum):
    """Search every fully invested, long-only mix in 5-percentage-point steps.

    Return a dict of weights and portfolio metrics, or None if infeasible.
    Inputs and results use decimals (0.065 means 6.5%). Ties keep the first mix.
    """
    covariance = build_covariance_matrix(sleeves, correlations)
    if not math.isfinite(objective_return):
        raise ValueError("Objective return must be finite.")
    if not math.isfinite(reserve_minimum) or not 0 <= reserve_minimum <= 1:
        raise ValueError("Reserve minimum must be between 0 and 1.")

    def allocations(remaining, count):
        if count == 1:
            yield [remaining / 20]
        else:
            for units in range(remaining + 1):
                for rest in allocations(remaining - units, count - 1):
                    yield [units / 20] + rest

    best = None
    for weights in allocations(20, len(sleeves)):
        result_return = expected_return(weights, sleeves)
        reserve = reserve_eligible_weight(weights, sleeves)
        # Allow only floating-point rounding at the constraint boundaries.
        if result_return + 1e-12 < objective_return or reserve + 1e-12 < reserve_minimum:
            continue
        volatility = portfolio_volatility(weights, covariance)
        if best is None or volatility < best["volatility"]:
            best = {"weights": weights, "expected_return": result_return,
                    "volatility": volatility, "reserve_eligible_weight": reserve}
    return best


def estimate_from_csv(source, last_36_months=False):
    """Estimate sleeves and correlations from monthly prices, oldest first.

    Accept a path or text file; return (sleeves, correlations). Use simple
    monthly returns, arithmetic means * 12, and sample standard deviations
    * sqrt(12). The optional window selects the last 36 RETURNS (37 prices).
    CSV assets start with reserve eligibility off; callers may edit it.
    Missing, nonpositive, nonfinite, constant, or nonmonthly data are rejected.
    """
    import csv
    import datetime
    import statistics

    if hasattr(source, "read"):
        rows = list(csv.reader(source))
    else:
        with open(source, newline="", encoding="utf-8-sig") as handle:
            rows = list(csv.reader(handle))
    if not rows or len(rows[0]) < 2:
        raise ValueError("CSV needs a date column and at least one ticker column.")
    names = [name.strip() for name in rows[0][1:]]
    if not all(names) or len(set(names)) != len(names):
        raise ValueError("Ticker names must be nonempty and unique.")
    prices = []
    previous_month = None
    for row in rows[1:]:
        if len(row) != len(names) + 1:
            raise ValueError("Each CSV row must contain a date and every ticker price.")
        try:
            date = datetime.date.fromisoformat(row[0].strip())
            values = [float(value) for value in row[1:]]
        except ValueError as error:
            raise ValueError("Use YYYY-MM-DD dates and numeric prices.") from error
        month = date.year * 12 + date.month
        if previous_month is not None and month != previous_month + 1:
            raise ValueError("Prices must be oldest first, one row per consecutive month.")
        if any(not math.isfinite(value) or value <= 0 for value in values):
            raise ValueError("All prices must be positive, finite, and present.")
        previous_month = month
        prices.append(values)
    if len(prices) < 3:
        raise ValueError("At least three monthly price rows are required.")
    returns = [[current[i] / previous[i] - 1 for i in range(len(names))]
               for previous, current in zip(prices, prices[1:])]
    if last_36_months:
        returns = returns[-36:]
    columns = list(zip(*returns))
    sleeves = [{"name": name, "expected_return": statistics.mean(values) * 12,
                "volatility": statistics.stdev(values) * math.sqrt(12),
                "reserve_eligible": False}
               for name, values in zip(names, columns)]
    if any(sleeve["volatility"] == 0 for sleeve in sleeves):
        raise ValueError("Each ticker must have varying monthly returns to estimate correlations.")
    correlations = [[1.0 for _ in names] for _ in names]
    for i in range(len(names)):
        for j in range(i):
            value = max(-1.0, min(1.0, statistics.correlation(columns[i], columns[j])))
            correlations[i][j] = correlations[j][i] = value
    validate_inputs(sleeves, correlations)
    return sleeves, correlations


def main():
    try:
        covariance = build_covariance_matrix(SLEEVES, CORRELATIONS)
        portfolios = [
            ("Benchmark", benchmark_weights(SLEEVES, BENCHMARK_ALLOCATIONS)),
            ("Equal weight", equal_weights(SLEEVES)),
            ("Inverse volatility", inverse_volatility_weights(SLEEVES)),
        ]
        print("Weight order: " + " / ".join(sleeve["name"] for sleeve in SLEEVES))
        print(f"Objective return: {OBJECTIVE_RETURN:.2%}\n")
        for name, weights in portfolios:
            result_return = expected_return(weights, SLEEVES)
            result_volatility = portfolio_volatility(weights, covariance)
            reserve = reserve_eligible_weight(weights, SLEEVES)
            meets = meets_objective(result_return, OBJECTIVE_RETURN)
            print(name)
            print("  Weights: " + " / ".join(f"{weight:.1%}" for weight in weights))
            print(f"  Expected return: {result_return:.2%}")
            print(f"  Volatility: {result_volatility:.2%}")
            print(f"  Reserve-eligible weight: {reserve:.1%}")
            print(f"  Meets objective: {'yes' if meets else 'no'}\n")
    except (ValueError, TypeError) as error:
        print(f"Input error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
