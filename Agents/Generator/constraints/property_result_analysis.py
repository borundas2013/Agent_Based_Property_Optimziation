from pathlib import Path

import pandas as pd
from chemical_validity import ChemicalValidityCheck
from property_check.property_checker import PropertyChecker


class PropertyResultAnalyzer:
    """
    Class-based interface for all result-analysis utilities:
    - Chemical validity statistics
    - Group validity statistics
    - Reactivity statistics

    All higher-level analyses are conditioned on chemical validity first.
    """

    def __init__(self, allow_disconnected: bool = False):
        self.allow_disconnected = allow_disconnected
        self.chem_checker = ChemicalValidityCheck(
            allow_disconnected=allow_disconnected
        )
        self.property_checker = PropertyChecker()

    # ----------------------
    # Shared helper methods
    # ----------------------
    @staticmethod
    def _load_csv(path: str | Path) -> tuple[Path, pd.DataFrame | None]:
        """
        Reusable helper to load a CSV file with basic validation.
        Returns (resolved_path, dataframe_or_None).
        """
        csv_path = Path(path)

        if not csv_path.exists():
            print(f"Path does not exist: {csv_path}")
            return csv_path, None

        if not csv_path.is_file():
            print(f"Path is not a file: {csv_path}")
            return csv_path, None

        if csv_path.suffix.lower() != ".csv":
            print(f"Not a CSV file: {csv_path}")
            return csv_path, None

        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            print(f"Error reading CSV {csv_path}: {e}")
            return csv_path, None

        return csv_path, df

    @staticmethod
    def _extract_in_parentheses(value):
        """
        Simple helper to extract the content between the first '('
        and the last ')' in a string, e.g. 'vinyl(C=C)' -> 'C=C'.
        If no such pair exists, returns the original value.
        """
        if not isinstance(value, str):
            return value
        start = value.find("(")
        end = value.rfind(")")
        if start != -1 and end != -1 and end > start + 1:
            return value[start + 1 : end].strip()
        return value


    def check_property_alignment(
        self,
        path: str | Path,
        smiles_col_1: str = "SMILES1",
        smiles_col_2: str = "SMILES2",
        tg_target_col: str = "target_tg",
        er_target_col: str = "target_er",
    ) -> None:
       
        base = Path(path)

        if base.is_dir():
            csv_files = sorted(
                p for p in base.rglob("*.csv") if p.name.endswith("evaluation.csv")
            )
            if not csv_files:
                print(f"No evaluation CSV files found under {base} for property alignment check")
                return
        else:
            csv_files = [base]

        property_stats: list[dict] = []
        property_details: list[dict] = []

        for csv_path in csv_files:
            resolved_path, df = self._load_csv(csv_path)
            if df is None:
                continue

            if smiles_col_1 not in df.columns or smiles_col_2 not in df.columns:
                print(
                    f"[{resolved_path}] Missing SMILES columns '{smiles_col_1}'/'{smiles_col_2}'. "
                    f"Available columns: {list(df.columns)}"
                )
                continue

            if tg_target_col not in df.columns or er_target_col not in df.columns:
                print(
                    f"[{resolved_path}] Missing target columns '{tg_target_col}'/'{er_target_col}'. "
                    f"Available columns: {list(df.columns)}"
                )
                continue

            total_rows = len(df)
            tg_series = pd.to_numeric(df[tg_target_col], errors="coerce")
            er_series = pd.to_numeric(df[er_target_col], errors="coerce")

            target_mask = tg_series.notna() & er_series.notna()
            df_targets = df.loc[target_mask]
            rows_with_targets = int(target_mask.sum())

            rows_valid_chem = 0
            dtg_vals: list[float] = []
            der_vals: list[float] = []

            tol_tg = float(getattr(self.property_checker, "tol_tg", 0.0))
            tol_er = float(getattr(self.property_checker, "tol_er", 0.0))

            for row_idx, row in df_targets.iterrows():
                smiles1 = row[smiles_col_1]
                smiles2 = row[smiles_col_2]

                valid, fixed_1, fixed_2 = self.chem_checker.check_chemical_validity(
                    smiles1, smiles2
                )
                if not valid:
                    continue

                rows_valid_chem += 1
                tg_target = float(tg_series.loc[row_idx])
                er_target = float(er_series.loc[row_idx])

                best_result = None
                best_score = None

                # Sweep ratio_1 from 0.1 → 0.9 (step 0.1); ratio_2 = 1 - ratio_1
                for i in range(1, 10):
                    ratio_1 = i / 10.0
                    ratio_2 = 1.0 - ratio_1

                    try:
                        result = self.property_checker(
                            monomer_1=fixed_1,
                            monomer_2=fixed_2,
                            tg_target=tg_target,
                            er_target=er_target,
                            ratio_1=ratio_1,
                            ratio_2=ratio_2,
                        )
                    except Exception:
                        # Skip this ratio setting if model fails
                        continue

                    dtg = float(result.get("dtg"))
                    der = float(result.get("der"))

                    # Prefer dtg/der close to or below tolerances
                    over_tg = max(dtg - tol_tg, 0.0)
                    over_er = max(der - tol_er, 0.0)
                    penalty = over_tg + over_er

                    # Tie‑break by overall absolute error dtg + der
                    tie_break = dtg + der
                    score_tuple = (penalty, tie_break)

                    if (best_score is None) or (score_tuple < best_score):
                        best_score = score_tuple
                        # Record the best result and ratios used
                        best_result = {
                            **result,
                            "ratio_1": ratio_1,
                            "ratio_2": ratio_2,
                        }

                # If no ratio combination succeeded, skip this row
                if best_result is None:
                    continue

                best_dtg = float(best_result.get("dtg"))
                best_der = float(best_result.get("der"))
                dtg_vals.append(best_dtg)
                der_vals.append(best_der)

                property_details.append(
                    {
                        "file": str(resolved_path),
                        "row_index": int(row_idx),
                        smiles_col_1: fixed_1,
                        smiles_col_2: fixed_2,
                        **best_result,
                    }
                )

            mean_dtg = float(pd.Series(dtg_vals).mean()) if dtg_vals else None
            mean_der = float(pd.Series(der_vals).mean()) if der_vals else None

            print("====== Property alignment summary (per file) ======")
            print(f"File: {resolved_path}")
            print(f"Total rows: {total_rows}")
            print(f"Rows with targets (non-null): {rows_with_targets}")
            print(f"Rows valid chemistry (among target rows): {rows_valid_chem}")
            print(f"Mean |Tg_hat - Tg_target| (dtg): {mean_dtg}")
            print(f"Mean |Er_hat - Er_target| (der): {mean_der}")
            print("===============================================")

            property_stats.append(
                {
                    "file": str(resolved_path),
                    "property_rows_with_targets": rows_with_targets,
                    "property_rows_valid_chem": rows_valid_chem,
                    "property_mean_dtg": mean_dtg,
                    "property_mean_der": mean_der,
                }
            )

        # Export/update aggregated per-file stats (same pattern as other analyzers)
        stats_base = base if base.is_dir() else base.parent
        stats_path = stats_base / "chemical_validity_statistics_fixed.csv"
        property_df = pd.DataFrame(property_stats)

        if not property_df.empty:
            if stats_path.exists():
                try:
                    stats_df = pd.read_csv(stats_path)
                except Exception as e:
                    print(f"Error reading statistics file {stats_path}: {e}")
                else:
                    stats_df = stats_df.set_index("file")
                    prop_idx = property_df.set_index("file")

                    for file_key, row in prop_idx.iterrows():
                        if file_key in stats_df.index:
                            for col, val in row.items():
                                stats_df.at[file_key, col] = val
                        else:
                            stats_df.loc[file_key] = row

                    stats_df.reset_index().to_csv(stats_path, index=False)
                    print(f"Property alignment statistics updated at: {stats_path}")
            else:
                property_df.to_csv(stats_path, index=False)
                print(f"Statistics file created with property alignment data at: {stats_path}")

        # Export per-row details for deeper analysis/debugging
        details_df = pd.DataFrame(property_details)
        if not details_df.empty:
            details_path = stats_base / "property_alignment_details.csv"
            details_df.to_csv(details_path, index=False)
            print(f"Property alignment row-level details written at: {details_path}")


if __name__ == "__main__":
    directory = "RLHF_TSMP/src/Evaluations/Output/SFT/DeepSeek"

    analyzer = PropertyResultAnalyzer()
    analyzer.check_property_alignment(directory)

    directory = "RLHF_TSMP/src/Evaluations/Output/SFT/Llama32"

    analyzer = PropertyResultAnalyzer()
    analyzer.check_property_alignment(directory)

    directory = "RLHF_TSMP/src/Evaluations/Output/SFT/GPTOSS"

    analyzer = PropertyResultAnalyzer()
    analyzer.check_property_alignment(directory)
   