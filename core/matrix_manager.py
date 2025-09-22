# -*- coding: utf-8 -*-
from __future__ import division
import pandas as pd
import csv
import os
import codecs
import numpy as np
import heapq

class Matrix:
    def __init__(self,
                 counts_file="core/transition_counts_matrix.csv",
                 probs_file="core/transition_probabilities_matrix.csv",
                 initial_states=None,
                 epsilon=4.48e-8):
        self.counts_file = counts_file
        self.probs_file = probs_file
        self.epsilon = epsilon

        columns_order = []
        if os.path.exists(counts_file):
            try:
                with codecs.open(counts_file, "r", "utf-8-sig") as f:
                    reader = csv.reader(f)
                    header = next(reader)
                    if len(header) > 1:
                        columns_order = header[1:]
            except Exception:
                columns_order = []

        self.counts_df = self._load_counts(counts_file)

        # header order
        if list(self.counts_df.index):
            state_order = list(self.counts_df.index)
        elif columns_order:
            state_order = list(columns_order)
        else:
            state_order = []

        if initial_states:
            for s in initial_states:
                if s not in state_order:
                    state_order.append(s)
        self.state_order = state_order

        # read & calculate probs_df
        if os.path.exists(probs_file):
            self.probs_df = pd.read_csv(probs_file, index_col=0)
        else:
            self.probs_df = self.counts_to_probs_with_smoothing(self.counts_df, self.epsilon)

        if self.state_order:
            self.counts_df = self.counts_df.reindex(index=self.state_order, columns=self.state_order, fill_value=0).astype("int64")
            self.probs_df  = self.probs_df.reindex(index=self.state_order, columns=self.state_order, fill_value=0.0).astype("float64")
        else:
            self.counts_df = self.counts_df.astype("int64") if not self.counts_df.empty else pd.DataFrame(dtype="int64")
            self.probs_df = self.probs_df.astype("float64") if not self.probs_df.empty else pd.DataFrame(dtype="float64")

        self.last_command = None

    def _load_counts(self, path):
        try:
            df = pd.read_csv(path, index_col=0)
            states = list(df.index)
            return df.reindex(index=states, columns=states, fill_value=0).astype("int64")
        except (IOError, OSError):  
            return pd.DataFrame(dtype="int64")

    def save_matrix(self):
        if self.state_order:
            counts = self.counts_df.reindex(index=self.state_order, columns=self.state_order, fill_value=0)
            probs = self.probs_df.reindex(index=self.state_order, columns=self.state_order, fill_value=0.0)
        else:
            counts = self.counts_df
            probs = self.probs_df

        counts.to_csv(self.counts_file, index=True, encoding="utf-8-sig")
        probs.to_csv(self.probs_file, index=True, encoding="utf-8-sig")

    def counts_to_probs_with_smoothing(self, counts_df, epsilon=None):
        if epsilon is None:
            epsilon = self.epsilon

        if self.state_order:
            counts_df = counts_df.reindex(index=self.state_order, columns=self.state_order, fill_value=0)
        else:
            counts_df = counts_df.copy()

        if counts_df.empty:
            return pd.DataFrame(dtype="float64")

        N = counts_df.shape[1]
        if N == 0:
            return pd.DataFrame(dtype="float64")

        probs = counts_df.astype("float64").copy()

        for s in probs.index:
            row_counts = counts_df.loc[s]
            total = row_counts.sum()

            if total == 0:
                probs.loc[s] = 1.0 / N
                continue

            p = row_counts / total
            n = int((p > 0).sum())

            if n < N:
                p_sm = p.copy()
                nonzero_mask = (p > 0)
                zero_mask = ~nonzero_mask
                p_sm[nonzero_mask] = p_sm[nonzero_mask] * (1.0 - epsilon)
                if (N - n) > 0:
                    p_sm[zero_mask] = epsilon / (N - n)
                probs.loc[s] = p_sm
            else:
                probs.loc[s] = p

        if self.state_order:
            return probs.reindex(index=self.state_order, columns=self.state_order, fill_value=0.0).astype("float64")
        else:
            return probs.astype("float64")

    def update_matrix(self, src, dst, save=False):
        added = False
        for s in [src, dst]:
            if s not in self.state_order:
                self.state_order.append(s)
                added = True

        self.counts_df = self.counts_df.reindex(index=self.state_order, columns=self.state_order, fill_value=0)
        self.probs_df = self.probs_df.reindex(index=self.state_order, columns=self.state_order, fill_value=0.0)

        self.counts_df.loc[src, dst] += 1

        # only update the probs for the src row
        row_counts = self.counts_df.loc[src]
        total = row_counts.sum()
        N = len(self.state_order)
        row_probs = row_counts.astype("float64")

        if total == 0:
            row_probs[:] = 1.0 / N
        else:
            p = row_counts / total
            n = int((p > 0).sum())
            if n < N:
                p_sm = p.copy()
                nonzero_mask = (p > 0)
                zero_mask = ~nonzero_mask
                p_sm[nonzero_mask] = p_sm[nonzero_mask] * (1.0 - self.epsilon)
                if (N - n) > 0:
                    p_sm[zero_mask] = self.epsilon / (N - n)
                row_probs = p_sm
            else:
                row_probs = p

      
        row_probs = row_probs.copy()
        row_probs.name = src

        self.probs_df.loc[src] = row_probs

        if save:
            self.save_matrix()
    
    def find_optimal_pr(self, src, dst, probs_df=None, p_min=1e-9):
        df = probs_df if probs_df is not None else self.probs_df
        if self.state_order:
            df = df.reindex(index=self.state_order, columns=self.state_order, fill_value=0.0)

        # if src/dst not in matrix, return None
        if src not in df.index or dst not in df.columns:
            return None

        # cumulative negative log distance
        dist = {state: np.inf for state in df.index}
        dist[src] = 0.0
        pq = [(0.0, src)]

        # convert probability threshold to maximum allowed cumulative weight
        max_cost = -np.log(p_min) if p_min > 0 else np.inf

        while pq:
            cur_dist, node = heapq.heappop(pq)
            if node == dst:
                return float(np.exp(-cur_dist))  # return probability

            if cur_dist > dist[node]:
                continue
            if cur_dist > max_cost:  # prune paths below probability threshold
                continue

            for nxt in df.columns:
                if nxt is None or (isinstance(nxt, float) and np.isnan(nxt)) or nxt == "":
                    continue
                p = float(df.loc[node, nxt])
                if p <= 0:
                    continue
                weight = -np.log(p)
                new_dist = cur_dist + weight
                if new_dist < dist[nxt]:
                    dist[nxt] = new_dist
                    heapq.heappush(pq, (new_dist, nxt))

        return None



