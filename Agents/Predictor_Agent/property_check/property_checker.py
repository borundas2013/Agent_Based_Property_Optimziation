# property_alignment_reward.py
# Smoothed property-alignment reward using pretrained Tg/Er predictors.
# - Tg model predicts Tg directly
# - Er model predicts log1p(Er); we invert with expm1
#
# Reward is smooth & bounded:
#   r_Tg = exp(-|Tg_hat - Tg_target| / sigma_Tg)
#   r_Er = exp(-|Er_hat - Er_target| / sigma_Er)
#   reward = w_Tg * r_Tg + w_Er * r_Er
#
# sigma_* should be set to your validation MAE (good default).

import os
import sys
import joblib
import numpy as np

# Setup import paths (same as data_processor.py)

# Reuse your existing utilities & feature extraction
from Generator.constraints.Utils.Util import is_valid_smiles, mol
from Predictor_Agent.property_check.data_processor import extract_molecular_features
from Predictor_Agent.property_check.model_io import load_models
import sklearn
print(sklearn.__version__)



class PropertyChecker:
    """
    Property alignment reward based on pretrained Tg/Er predictors.

    Score per property:
      if |pred-target| <= tol -> 1
      else -> exp(-( |pred-target| - tol ) / sigma)

    Final reward:
      w_tg * score_tg + w_er * score_er   (clipped to [0,1])

    sigma meaning (simple):
      - how fast reward drops after leaving the tolerance band
      - good default: sigma = validation MAE of your predictor
    """

    def __init__(self):
        # Get absolute paths relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
        print(project_root)
        print(current_dir)
        
        tg_model_path = os.path.join(project_root, "Agents", "Predictor_Agent", "property_check", "models", "tg_hgb_with_G.pkl")
        er_model_path = os.path.join(project_root, "Agents", "Predictor_Agent", "property_check", "models", "er_hgb_log1p_with_G.pkl")
        
        if not os.path.exists(tg_model_path):
            raise FileNotFoundError(f"Tg model not found: {tg_model_path}")
        if not os.path.exists(er_model_path):
            raise FileNotFoundError(f"Er model not found: {er_model_path}")

        self.tg_model, self.er_model = load_models(tg_model_path, er_model_path)

        self.fp_bits = 1024
        self.use_symmetric = True

        self.tol_tg = 10
        self.tol_er = 5
        self.sigma_tg = 13.75
        self.sigma_er = 9.44
        if self.sigma_tg <= 0 or self.sigma_er <= 0:
            raise ValueError("sigma_tg and sigma_er must be > 0")
       
       

    def predict(self, smi1: str, smi2: str, ratio1: float = 0.5, ratio2: float = 0.5):
        """
        Returns:
          tg_hat (float), er_hat (float in original scale)
        """
        X = extract_molecular_features(
            [smi1], [smi2],
            ratio1_list=[float(ratio1)],
            ratio2_list=[float(ratio2)],
            fp_bits=self.fp_bits,
            use_symmetric=self.use_symmetric,
        )

        tg_hat = float(self.tg_model.predict(X)[0])

        # er model trained on log1p(Er)
        er_hat_log = float(self.er_model.predict(X)[0])
        er_hat = float(np.expm1(er_hat_log))

        return tg_hat, er_hat

    @staticmethod
    def _band_then_decay(err: float, tol: float, sigma: float) -> float:
        """
        1.0 inside tolerance band, exponential decay outside.
        """
        if err <= tol:
            return 1.0
        return float(np.exp(-(err - tol) / sigma))

    def __call__(
        self,
        monomer_1: str,
        monomer_2: str,
        tg_target: float,
        er_target: float,
        ratio_1: float = 0.1,
        ratio_2: float = 0.9,
        return_debug: bool = False,
    ):

        # 2) predict
        tg_hat, er_hat = self.predict(monomer_1, monomer_2, ratio_1, ratio_2)
        tg_hat = float(round(tg_hat, 2))
        er_hat = float(round(er_hat, 2))

        # # 3) optional noise (start with 0.0)
        # if self.noise_tg > 0:
        #     tg_hat += float(np.random.normal(0.0, self.noise_tg))
        # if self.noise_er > 0:
        #     er_hat += float(np.random.normal(0.0, self.noise_er))

        # 4) compute errors
        tg_target = float(tg_target)
        er_target = float(er_target)
        dtg = float(round(abs(tg_hat - tg_target), 2))
        der = float(round(abs(er_hat - er_target), 2))
       
        return {
            "tg_target": tg_target,
            "er_target": er_target,
            "predicted_tg": tg_hat,
            "predicted_er": er_hat,
            "dtg": dtg,
            "der": der,
            "tol_tg": self.tol_tg,
            "tol_er": self.tol_er,
        }

      


# -------------------------
# Example usage
# -------------------------
if __name__ == "__main__":
    property_checker = PropertyChecker()

    # Example polymer pair (replace with real generated monomers)
    mon1 = "CC(C)(c2ccc(OC(=O)C(=C)C)cc2)c4ccc(OC(=O)C(=C)C)cc4"
    mon2 = "CC(NC(=O)C(=C)C)COCC(C)OCC(C)OCC(C)OCC(C)OCC(C)OCC(C)NC(=O)C(=C)C"

    # Example targets
    tg_target = 100.0
    er_target = 28.0

    score_details = property_checker(
        monomer_1=mon1,
        monomer_2=mon2,
        tg_target=tg_target,
        er_target=er_target,
        ratio_1=0.4,
        ratio_2=0.6,
        
    )

   
    print("Debug:")
    for k, v in score_details.items():
        print(f"  {k}: {v}")