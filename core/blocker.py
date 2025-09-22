### DF: blocker.py
from core.matrix_manager import Matrix

class Blocker:
    def __init__(self, counts_file="transition_counts_matrix.csv", probs_file="transition_probabilities_matrix.csv"):
        self.matrix = Matrix(counts_file, probs_file)

    def check_and_update(self, current_command):
        result = {"block": False, "payoff": 0.0, "Pr_Actual": None, "Pr_Max": None}
        dst = current_command

        if self.matrix.last_command is None:
            self.matrix.last_command = dst
            return result

        src = self.matrix.last_command

        probs_before_update = self.matrix.probs_df.copy()

        if src in probs_before_update.index and dst in probs_before_update.columns:
            Pr_Actual = float(probs_before_update.loc[src, dst])
        else:
            Pr_Actual = None

        Pr_Max_raw = self.matrix.find_optimal_pr(src, dst, probs_before_update)
        Pr_Max = float(Pr_Max_raw) if Pr_Max_raw is not None else None

        payoff = self.calc_payoff(Pr_Actual, Pr_Max)

        result.update({
            "Pr_Actual": Pr_Actual,
            "Pr_Max": Pr_Max,
            "payoff": payoff,
            "block": payoff > 0.5
        })

        self.matrix.update_matrix(src, dst)
        self.matrix.last_command = dst

        return result


    def calc_payoff(self, Pr_Actual, Pr_Max):
        if Pr_Actual is None or Pr_Max is None:
            return 0.0
        if Pr_Max <= 0:
            return 0.0
        return Pr_Actual / Pr_Max