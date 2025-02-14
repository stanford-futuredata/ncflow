from .abstract_test import AbstractTest
from ..problems import ToyProblem
from ..partitioning.hard_coded_partitioning import HardCodedPartitioning
from ..algorithms.ncflow.ncflow_edge_per_iter import NCFlowEdgePerIter as NcfEpi


class ToyProblemTest(AbstractTest):
    def __init__(self):
        super().__init__()
        self.problem = ToyProblem()

    @property
    def name(self):
        return "toy"

    def run(self):
        ncf = NcfEpi.new_total_flow(4)
        hc = HardCodedPartitioning(partition_vector=[0, 0, 0, 1, 1, 1])
        ncf.solve(self.problem, hc)

        self.assert_feasibility(ncf)

        self.assert_eq_epsilon(ncf._ncflows[0].r1_obj_val, 31.0)
        self.assert_eq_epsilon(ncf._ncflows[0].intra_obj_vals[0], 5.0)
        self.assert_eq_epsilon(ncf._ncflows[0].intra_obj_vals[1], 7.0)
        self.assert_geq_epsilon(ncf._ncflows[0].r3_obj_val, 31)

        self.assert_geq_epsilon(ncf._ncflows[1].r1_obj_val, 7)
        self.assert_geq_epsilon(ncf._ncflows[1].r3_obj_val, 7)

        self.assert_geq_epsilon(ncf.obj_val, 55)
