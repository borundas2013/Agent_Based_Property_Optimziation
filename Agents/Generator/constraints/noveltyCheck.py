from __future__ import annotations

from typing import Iterable, List, Set, Tuple

import os
import sys

from rdkit import Chem

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, "..", "..")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from Utils import load_smiles_data


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
data_path = os.path.join(project_root, "RLHF_TSMP", "data", "unique_smiles_Er.csv")


class NoveltyCheck:
    """
    Novelty checking for two-monomer pairs.

    - Training data is loaded as ordered pairs (monomer_1, monomer_2).
    - For pairwise novelty, both (m1, m2) and (m2, m1) are treated as the
      same training example (reverse pair counts as seen).
    - We also track the set of *individual* monomers for per-monomer novelty.
    """

    def __init__(self) -> None:
        self._train_pairs: Set[Tuple[str, str]] = set()
        self._train_monomers: Set[str] = set()
        self._build_training_sets(get_training_pairs())

    def _build_training_sets(self, pairs: Iterable[Tuple[str, str]]) -> None:
        """
        Build:
        - a set of ordered training pairs (including reverse pairs)
        - a set of individual monomers appearing anywhere in training.
        """
        for s1, s2 in pairs:
            # Store both directions so that (A, B) and (B, A) are treated
            # as the same known pair for novelty purposes.
            self._train_pairs.add((s1, s2))
            self._train_pairs.add((s2, s1))

            self._train_monomers.add(s1)
            self._train_monomers.add(s2)

    # ---- Monomer-level novelty -------------------------------------------------

    def is_monomer_novel(self, smiles: str) -> bool:
        """
        Check novelty for a single monomer against the training monomer set.
        Only valid SMILES are considered; invalid/empty SMILES are treated
        as not novel (return False).
        """
        if smiles is None:
            return False
        s = str(smiles).strip()
        if not s:
            return False

        # Validate SMILES before novelty check
        mol = Chem.MolFromSmiles(s)
        if mol is None:
            return False

        return s not in self._train_monomers

    def pair_monomer_novelty(self, smiles1: str, smiles2: str) -> Tuple[bool, bool]:
        """
        Returns (novel1, novel2) for the two monomers individually.
        """
        return (self.is_monomer_novel(smiles1), self.is_monomer_novel(smiles2))

    # ---- Pair-level novelty ----------------------------------------------------

    def check_pair_novelty(self, smiles1: str, smiles2: str) -> float:
        """
        Pairwise novelty:

        - A query pair (s1, s2) is considered non-novel if either
          (s1, s2) or (s2, s1) appears in the training set.
        - Otherwise, it is considered novel.

        Returns
        -------
        1.0  → pair is novel (neither orientation seen in training)
        0.0  → pair is not novel (seen in training, in either order)
        -1.0 → one or both SMILES are missing/empty
        """
        if smiles1 is None or smiles2 is None:
            return -1.0

        s1 = str(smiles1).strip()
        s2 = str(smiles2).strip()
        if not s1 or not s2:
            return -1.0

        # Validate both SMILES before pairwise novelty check
        mol1 = Chem.MolFromSmiles(s1)
        mol2 = Chem.MolFromSmiles(s2)
        if mol1 is None or mol2 is None:
            return -1.0

        if (s1, s2) in self._train_pairs or (s2, s1) in self._train_pairs:
            return 0.0
        return 1.0

    def check_monomer_novelty_scores(self, smiles1: str, smiles2: str) -> Tuple[float, float]:
        """
        Check novelty scores for each monomer separately.

        Returns
        -------
        (score1, score2)
        where each score is:
        - 1.0 → monomer not seen in training monomer set
        - 0.0 → monomer seen in training monomer set
        - -1.0 → empty / None
        """
        def _score(s: str) -> float:
            # if s is None:
            #     return -1.0
            # s_clean = str(s).strip()
            # if not s_clean:
            #     return -1.0

            # mol = Chem.MolFromSmiles(s_clean)
            # if mol is None:
            #     return -1.0

            return 1.0 if s not in self._train_monomers else 0.0

        return _score(smiles1), _score(smiles2)


def get_training_pairs() -> List[Tuple[str, str]]:
    smiles1_list, smiles2_list = load_smiles_data(data_path)
    return [(smiles1, smiles2) for smiles1, smiles2 in zip(smiles1_list, smiles2_list)]


if __name__ == "__main__":
    smiles_lists = get_training_pairs()
    print(len(smiles_lists))
    test_smiles1 = smiles_lists[0][0]+"aaa"
    test_smiles2 = smiles_lists[0][1]+"CCCC"

    novelty_check = NoveltyCheck()
    print("Pair novelty score:", novelty_check.check_pair_novelty(test_smiles1, test_smiles2))
    print(
        "Monomer novelty scores:",
        novelty_check.check_monomer_novelty_scores(test_smiles1, test_smiles2),
    )