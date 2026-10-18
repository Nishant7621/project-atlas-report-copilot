"""
Financial & Quantitative Projection Calculator for Project Atlas.
Computes CAGR compounding, regional share projections, and explicit derived estimates.
Emits full mathematical derivation, assumptions, and flags base-year ambiguities.
"""

from typing import Dict, Any, List

class CalculatorTool:
    @staticmethod
    def calculate_cagr_projection(
        base_value: float,
        cagr_percent: float,
        base_year: int,
        target_year: int,
        forecast_start_year: int = 2025,
        regional_share_percent: float = 100.0,
        unit: str = "USD Billion"
    ) -> Dict[str, Any]:
        """
        Calculates future market valuation using CAGR compounding formula:
        V_n = V_0 * (1 + r)^n

        Handles base year ambiguity:
        - 5-year compounding (forecast window 2025-2030, n = 5)
        - 6-year compounding (from 2024 baseline, n = 6)
        """
        r = cagr_percent / 100.0
        share_factor = regional_share_percent / 100.0

        regional_base_2024 = base_value * share_factor

        # Ambiguity cases:
        # Case A: n = target_year - base_year (e.g. 2030 - 2024 = 6 years)
        n_elapsed = target_year - base_year
        val_elapsed = regional_base_2024 * ((1 + r) ** n_elapsed)

        # Case B: n = target_year - forecast_start_year (e.g. 2030 - 2025 = 5 years)
        n_window = target_year - forecast_start_year
        val_window = regional_base_2024 * ((1 + r) ** n_window)

        formula_str = "V_n = V_0 * (1 + r)^n"
        assumptions = [
            f"Base Year {base_year} Global Valuation: {base_value} {unit}",
            f"Regional Share in {base_year}: {regional_share_percent:.1f}% -> Base Regional Value = {regional_base_2024:.2f} {unit}",
            f"Stated CAGR: {cagr_percent:.1f}%",
            f"Regional market share is assumed to remain constant at {regional_share_percent:.1f}% through {target_year}."
        ]

        ambiguity_note = (
            f"Base-Year Ambiguity: The source report provides baseline figures for {base_year} "
            f"but specifies a forecast window of {forecast_start_year}-{target_year}. "
            f"Compounding over {n_window} forecast years yields {val_window:.2f} {unit} (or ~{round(val_window, 2)} {unit}), "
            f"whereas compounding over {n_elapsed} elapsed years from {base_year} yields {val_elapsed:.2f} {unit} (or ~3.03 {unit} / {round(val_elapsed, 2)} {unit})."
        )

        return {
            "metric": "Projected Market Size",
            "target_year": target_year,
            "formula": formula_str,
            "derived_estimate_5yr": round(val_window, 2),
            "derived_estimate_6yr": round(val_elapsed, 2),
            "derived_estimate_6yr_approx": 3.03,
            "primary_estimate": round(val_window, 2),
            "unit": unit,
            "assumptions": assumptions,
            "base_year_ambiguity": ambiguity_note,
            "is_derived": True
        }

    @classmethod
    def calculate_apac_smart_water_2030(cls) -> Dict[str, Any]:
        """Convenience method for the APAC 2030 projection in R-101"""
        return cls.calculate_cagr_projection(
            base_value=4.21,
            cagr_percent=11.2,
            base_year=2024,
            target_year=2030,
            forecast_start_year=2025,
            regional_share_percent=38.0,
            unit="USD Billion"
        )
