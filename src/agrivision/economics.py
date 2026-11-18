"""Economic assumptions for turning a yield gain into a decision.

These are ASSUMPTIONS, not data. Verify before presenting and change here only.
"""

# Wheat Minimum Support Price, Rabi Marketing Season 2025-26 (Rs per quintal).
# Verify the current-season value from the official CACP / PIB announcement.
WHEAT_PRICE_RS_PER_QUINTAL = 2425

# Cost of ONE extra irrigation per hectare with a diesel pump set
# (fuel + pump rental + labour). Assumed value; vary it in the dashboard.
IRRIGATION_COST_RS_PER_HA = 2500


def gain_value_rs_per_ha(gain_t_per_ha, price=WHEAT_PRICE_RS_PER_QUINTAL):
    """1 t = 10 quintals."""
    return gain_t_per_ha * 10 * price


def net_benefit_rs_per_ha(gain_t_per_ha, price=WHEAT_PRICE_RS_PER_QUINTAL,
                          cost=IRRIGATION_COST_RS_PER_HA):
    return gain_value_rs_per_ha(gain_t_per_ha, price) - cost


def break_even_gain_t_per_ha(price=WHEAT_PRICE_RS_PER_QUINTAL,
                             cost=IRRIGATION_COST_RS_PER_HA):
    return cost / (10 * price)
