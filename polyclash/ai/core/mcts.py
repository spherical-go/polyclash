import logging
import math

import numpy as np

EPS = 1e-8

log = logging.getLogger(__name__)


class MCTS:
    """
    This class handles the MCTS tree.
    """

    def __init__(self, game, nnet, args):
        self.game = game
        self.nnet = nnet
        self.args = args
        self.Qsa = {}
        self.Nsa = {}
        self.Ns = {}
        self.Ps = {}
        self.Vs = {}

    def reset(self):
        self.Qsa = {}
        self.Nsa = {}
        self.Ns = {}
        self.Ps = {}
        self.Vs = {}

    def update_network(self, nnet):
        self.nnet = nnet

    def action_prob(self, canonicalBoard, temp=1):
        for i in range(self.args.numMCTSSims):
            self.search(canonicalBoard)

        s = self.game.representation(canonicalBoard)
        counts = [
            self.Nsa[(s, a)] if (s, a) in self.Nsa else 0
            for a in range(self.game.action_size())
        ]

        if temp == 0:
            valids = self.game.valid_moves(canonicalBoard, 1)
            masked_counts = np.array(counts) * valids

            bestAs = np.array(
                np.argwhere(masked_counts == np.max(masked_counts))
            ).flatten()
            bestA = np.random.choice(bestAs)
            probs = [0] * len(counts)
            probs[bestA] = 1
            return probs

        counts = [x ** (1.0 / temp) for x in counts]
        counts_sum = float(sum(counts))

        if counts_sum > 0:
            probs = [x / counts_sum for x in counts]
        else:
            valids = self.game.valid_moves(canonicalBoard, 1)
            valid_sum = np.sum(valids)
            if valid_sum > 0:
                probs = [v / valid_sum for v in valids]
            else:
                log.error("No valid moves available!")
                probs = [1.0 / len(counts)] * len(counts)

        return probs

    _MAX_SEARCH_DEPTH = 64

    def search(self, canonicalBoard, depth=0):
        if depth >= self._MAX_SEARCH_DEPTH:
            return 0

        r = self.game.game_ended(canonicalBoard, 1)
        if r != 0:
            return -r

        s = self.game.representation(canonicalBoard)

        if s not in self.Ps:
            self.Ps[s], v = self.nnet.predict(canonicalBoard)
            valids = self.game.valid_moves(canonicalBoard, 1)
            self.Ps[s] = self.Ps[s] * valids
            sum_Ps_s = np.sum(self.Ps[s])
            if sum_Ps_s > 0:
                self.Ps[s] /= sum_Ps_s
            else:
                log.error("All valid moves were masked, doing a workaround.")
                self.Ps[s] = self.Ps[s] + valids
                self.Ps[s] /= np.sum(self.Ps[s])

            self.Vs[s] = valids
            self.Ns[s] = 0
            return -v

        valids = self.Vs[s]
        cur_best = -float("inf")
        best_act = -1

        for a in range(self.game.action_size()):
            if valids[a]:
                if (s, a) in self.Qsa:
                    u = self.Qsa[(s, a)] + self.args.cpuct * self.Ps[s][a] * math.sqrt(
                        self.Ns[s]
                    ) / (1 + self.Nsa[(s, a)])
                else:
                    u = self.args.cpuct * self.Ps[s][a] * math.sqrt(self.Ns[s] + EPS)

                if u > cur_best:
                    cur_best = u
                    best_act = a

        if best_act == -1:
            return 0
        a = best_act

        next_s, next_player = self.game.next_state(canonicalBoard, 1, a)
        next_s = self.game.canonical_form(next_s, next_player)
        if self.game.representation(next_s) == s:
            return 0

        v = self.search(next_s, depth + 1)

        if (s, a) in self.Qsa:
            self.Qsa[(s, a)] = (self.Nsa[(s, a)] * self.Qsa[(s, a)] + v) / (
                self.Nsa[(s, a)] + 1
            )
            self.Nsa[(s, a)] += 1

        else:
            self.Qsa[(s, a)] = v
            self.Nsa[(s, a)] = 1

        self.Ns[s] += 1
        return -v
