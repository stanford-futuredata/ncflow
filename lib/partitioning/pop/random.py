from .abstract_pop_splitter import AbstractPOPSplitter
import random
import numpy as np

# assign commodities to subproblems at random
class RandomSplitter(AbstractPOPSplitter):
    def __init__(self, num_subproblems):
        super().__init__(num_subproblems)

    def split(self, problem):
        sub_problems = [problem.copy() for _ in range(self._num_subproblems)]
        # num_coms = len(problem.commodity_list)
        max_demand = 100/self._num_subproblems
        for _, (source, target, demand) in problem.commodity_list:
           
            # find out how many times you have to halve demand so its within max 
            b = 0
            while demand/(2**b) > max_demand:
                b += 1         
            num_entity_splits = min(2**b, self._num_subproblems)
            # create list of sps to assign demand to
            assigned_sps_list = np.random.permutation(np.arange(self._num_subproblems))[:num_entity_splits]
            
            # zero our each subproblem's tm entry for this entity, except for assigned sp's who each get a portion
            for sp in range(self._num_subproblems):
                if sp in assigned_sps_list:
                    sub_problems[sp].traffic_matrix.tm[source, target] /= num_entity_splits
                else:
                    sub_problems[sp].traffic_matrix.tm[source, target] = 0
        
        for sub_problem in sub_problems:
            for u, v in sub_problems[-1].G.edges:
                sub_problem.G[u][v]["capacity"] = (
                    sub_problem.G[u][v]["capacity"] / self._num_subproblems
                )
        return sub_problems