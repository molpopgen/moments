import os
import unittest
import math
import pathlib

import numpy as np
import moments
from moments.Demes import Demes
import time

import demes


class TestSplits(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        t = time.time() - self.startTime
        print("%s: %.3f seconds" % (self.id(), t))

    def test_two_way_split(self):
        ns0, ns1 = 10, 6
        pop_ids = ["A", "B"]
        fs = moments.Demographics1D.snm([ns0 + ns1], pop_ids=["O"])
        out = Demes._split_fs(fs, 0, pop_ids, [ns0, ns1])
        fs = fs.split(0, ns0, ns1, new_ids=pop_ids)
        self.assertTrue(np.all([x == y for x, y in zip(pop_ids, out.pop_ids)]))
        self.assertTrue(np.all(out.sample_sizes == np.array([ns0, ns1])))
        self.assertTrue(np.allclose(out.data, fs.data))

        rho = [0, 1]
        y = moments.LD.Demographics1D.snm(rho=rho, pop_ids=["O"])
        out = Demes._apply_LD_event(y, ("split", "O", pop_ids), 0, pop_ids)
        y = y.split(0, new_ids=pop_ids)
        self.assertTrue(np.all([x == y for x, y in zip(pop_ids, out.pop_ids)]))
        for s0, s1 in zip(y, out):
            self.assertTrue(np.allclose(s0, s1))

    def test_three_way_split_1(self):
        pop_ids = ["A", "B"]
        child_ids = ["C1", "C2", "C3"]
        child_sizes = [4, 6, 8]
        nsA = 5
        nsB = sum(child_sizes)
        fs = moments.Spectrum(np.ones((nsA + 1, nsB + 1)), pop_ids=pop_ids)
        out = Demes._split_fs(fs, 1, child_ids, child_sizes)
        self.assertTrue(out.Npop == 4)
        self.assertTrue(
            np.all([x == y for x, y in zip(out.sample_sizes, [nsA] + child_sizes)])
        )
        self.assertTrue(
            np.all([x == y for x, y in zip(out.pop_ids, ["A"] + child_ids)])
        )

        rho = [0, 1, 10]
        y = moments.LD.LDstats(
            [np.random.rand(15) for _ in range(len(rho))] + [np.random.rand(3)],
            pop_ids=["A", "B"],
            num_pops=2,
        )
        out = Demes._apply_LD_event(y, ("split", "B", child_ids), 0, ["A"] + child_ids)
        self.assertTrue(out.num_pops == 4)
        self.assertTrue(
            np.all([i == j for i, j in zip(out.pop_ids, ["A"] + child_ids)])
        )

    def test_three_way_split_0(self):
        pop_ids = ["A", "B"]
        child_ids = ["C1", "C2", "C3"]
        child_sizes = [4, 6, 8]
        nsA = sum(child_sizes)
        nsB = 5
        fs = moments.Spectrum(np.ones((nsA + 1, nsB + 1)), pop_ids=pop_ids)
        out = Demes._split_fs(fs, 0, child_ids, child_sizes)
        self.assertTrue(out.Npop == 4)
        self.assertTrue(
            np.all([x == y for x, y in zip(out.sample_sizes, [4, 5, 6, 8])])
        )
        self.assertTrue(
            np.all([x == y for x, y in zip(out.pop_ids, ["C1", "B", "C2", "C3"])])
        )

        rho = [0, 1, 10]
        y = moments.LD.LDstats(
            [np.random.rand(15) for _ in range(len(rho))] + [np.random.rand(3)],
            pop_ids=["A", "B"],
            num_pops=2,
        )
        out = Demes._apply_LD_event(y, ("split", "A", child_ids), 0, ["B"] + child_ids)
        self.assertTrue(out.num_pops == 4)
        self.assertTrue(
            np.all([i == j for i, j in zip(out.pop_ids, ["C1", "B", "C2", "C3"])])
        )


class TestReorder(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        t = time.time() - self.startTime
        print("%s: %.3f seconds" % (self.id(), t))

    def test_reorder_three_pops(self):
        fs = moments.Spectrum(
            np.random.rand(4 * 6 * 8).reshape((4, 6, 8)), pop_ids=["A", "B", "C"]
        )
        y = moments.LD.LDstats(
            [np.random.rand(45)] + [np.random.rand(6)],
            num_pops=3,
            pop_ids=["A", "B", "C"],
        )
        new_orders = [[1, 0, 2], [0, 2, 1], [2, 1, 0], [2, 0, 1]]
        for new_order in new_orders:
            new_ids = [fs.pop_ids[ii] for ii in new_order]
            out = Demes._reorder_fs(fs, new_ids)
            out_ld = Demes._reorder_LD(y, new_ids)
            self.assertTrue(
                np.all(
                    [
                        x == y
                        for x, y in zip((fs.shape[ii] for ii in new_order), out.shape)
                    ]
                )
            )
            self.assertTrue(
                np.all(
                    [
                        x == y
                        for x, y in zip(
                            (fs.pop_ids[ii] for ii in new_order), out.pop_ids
                        )
                    ]
                )
            )
            self.assertTrue(
                np.all(
                    [
                        x == y
                        for x, y in zip(
                            (y.pop_ids[ii] for ii in new_order), out_ld.pop_ids
                        )
                    ]
                )
            )

    def test_reorder_five_pops(self):
        fs = moments.Spectrum(
            np.random.rand(4 * 5 * 6 * 7 * 8).reshape((4, 5, 6, 7, 8)),
            pop_ids=["A", "B", "C", "D", "E"],
        )
        y = moments.LD.LDstats(
            [np.random.rand(210)] + [np.random.rand(15)],
            num_pops=5,
            pop_ids=["A", "B", "C", "D", "E"],
        )
        for new_order_idx in range(10):
            new_order = np.random.permutation([0, 1, 2, 3, 4])
            new_ids = [fs.pop_ids[ii] for ii in new_order]
            out = Demes._reorder_fs(fs, new_ids)
            out_ld = Demes._reorder_LD(y, new_ids)
            self.assertTrue(
                np.all(
                    [
                        x == y
                        for x, y in zip((fs.shape[ii] for ii in new_order), out.shape)
                    ]
                )
            )
            self.assertTrue(
                np.all(
                    [
                        x == y
                        for x, y in zip(
                            (fs.pop_ids[ii] for ii in new_order), out.pop_ids
                        )
                    ]
                )
            )
            self.assertTrue(
                np.all(
                    [
                        x == y
                        for x, y in zip(
                            (y.pop_ids[ii] for ii in new_order), out_ld.pop_ids
                        )
                    ]
                )
            )


class TestAdmix(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        t = time.time() - self.startTime
        print("%s: %.3f seconds" % (self.id(), t))

    def test_two_way_admixture(self):
        fs = moments.Spectrum(np.ones((7, 7, 7)), pop_ids=["A", "B", "C"])
        parents = ["A", "C"]
        proportions = [0.3, 0.7]
        child = "D"
        child_size = 2
        out = Demes._admix_fs(fs, parents, proportions, child, child_size)
        self.assertTrue(
            np.all([x == y for x, y in zip(out.sample_sizes, (4, 6, 4, 2))])
        )
        self.assertTrue(
            np.all([x == y for x, y in zip(out.pop_ids, ("A", "B", "C", "D"))])
        )

        child_size = 6
        out = Demes._admix_fs(fs, parents, proportions, child, child_size)
        self.assertTrue(np.all([x == y for x, y in zip(out.sample_sizes, (6, 6))]))
        self.assertTrue(np.all([x == y for x, y in zip(out.pop_ids, ("B", "D"))]))

        y = moments.LD.LDstats(
            [np.random.rand(45)] + [np.random.rand(6)],
            num_pops=3,
            pop_ids=["A", "B", "C"],
        )
        out = Demes._admix_LD(y, parents, proportions, child, marginalize=False)
        self.assertTrue(
            np.all([x == y for x, y in zip(out.pop_ids, ("A", "B", "C", "D"))])
        )
        out = Demes._admix_LD(y, parents, proportions, child, marginalize=True)
        self.assertTrue(np.all([x == y for x, y in zip(out.pop_ids, ("B", "D"))]))

    def test_three_way_admixture(self):
        fs = moments.Spectrum(np.ones((5, 5, 5)), pop_ids=["A", "B", "C"])
        parents = ["A", "B", "C"]
        proportions = [0.2, 0.3, 0.5]
        child = "D"
        child_size = 2
        out = Demes._admix_fs(fs, parents, proportions, child, child_size)
        self.assertTrue(
            np.all([x == y for x, y in zip(out.sample_sizes, (2, 2, 2, 2))])
        )
        self.assertTrue(
            np.all([x == y for x, y in zip(out.pop_ids, ("A", "B", "C", "D"))])
        )

        child_size = 4
        out = Demes._admix_fs(fs, parents, proportions, child, child_size)
        self.assertTrue(np.all([x == y for x, y in zip(out.sample_sizes, (4,))]))
        self.assertTrue(np.all([x == y for x, y in zip(out.pop_ids, ("D",))]))

        y = moments.LD.LDstats(
            [np.random.rand(45)] + [np.random.rand(6)],
            num_pops=3,
            pop_ids=["A", "B", "C"],
        )
        out = Demes._admix_LD(y, parents, proportions, child, marginalize=False)
        self.assertTrue(
            np.all([x == y for x, y in zip(out.pop_ids, ("A", "B", "C", "D"))])
        )
        out = Demes._admix_LD(y, parents, proportions, child, marginalize=True)
        self.assertTrue(np.all([x == y for x, y in zip(out.pop_ids, ("D",))]))


class TestPulse(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        t = time.time() - self.startTime
        print("%s: %.3f seconds" % (self.id(), t))

    def test_pulse_function(self):
        fs = moments.Demographics2D.snm([20, 10], pop_ids=["A", "B"])
        out = Demes._pulse_fs(fs, "A", "B", 0.2, [10, 10])
        self.assertTrue(out.sample_sizes[0] == 10)
        self.assertTrue(out.sample_sizes[1] == 10)
        fs2 = fs.pulse_migrate(0, 1, 10, 0.2)
        self.assertTrue(np.allclose(fs2.data, out.data))


class CompareOOA(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        t = time.time() - self.startTime
        print("%s: %.3f seconds" % (self.id(), t))

    def test_direct_comparison(self):
        Ne = 7300
        gens = 25
        nuA = 12300 / Ne
        TA = (220e3 - 140e3) / 2 / Ne / gens
        nuB = 2100 / Ne
        TB = (140e3 - 21.2e3) / 2 / Ne / gens
        nuEu0 = 1000 / Ne
        nuEuF = 29725 / Ne
        nuAs0 = 510 / Ne
        nuAsF = 54090 / Ne
        TF = 21.2e3 / 2 / Ne / gens
        mAfB = 2 * Ne * 25e-5
        mAfEu = 2 * Ne * 3e-5
        mAfAs = 2 * Ne * 1.9e-5
        mEuAs = 2 * Ne * 9.6e-5

        ns = [10, 10, 10]

        fs_moments = moments.Demographics3D.out_of_Africa(
            (
                nuA,
                TA,
                nuB,
                TB,
                nuEu0,
                nuEuF,
                nuAs0,
                nuAsF,
                TF,
                mAfB,
                mAfEu,
                mAfAs,
                mEuAs,
            ),
            ns,
        )
        fs_demes = moments.Spectrum.from_demes(
            os.path.join(os.path.dirname(__file__), "test_files/gutenkunst_ooa.yml"),
            ["YRI", "CEU", "CHB"],
            ns,
        )

        self.assertTrue(
            np.all([x == y for x, y in zip(fs_moments.pop_ids, fs_demes.pop_ids)])
        )
        self.assertTrue(np.allclose(fs_demes.data, fs_moments.data))

    def test_direct_comparison_LD(self):
        Ne = 7300
        gens = 25
        nuA = 12300 / Ne
        TA = (220e3 - 140e3) / 2 / Ne / gens
        nuB = 2100 / Ne
        TB = (140e3 - 21.2e3) / 2 / Ne / gens
        nuEu0 = 1000 / Ne
        nuEuF = 29725 / Ne
        nuAs0 = 510 / Ne
        nuAsF = 54090 / Ne
        TF = 21.2e3 / 2 / Ne / gens
        mAfB = 2 * Ne * 25e-5
        mAfEu = 2 * Ne * 3e-5
        mAfAs = 2 * Ne * 1.9e-5
        mEuAs = 2 * Ne * 9.6e-5

        rho = [0, 1, 10]
        theta = 0.001

        y_moments = moments.LD.Demographics3D.out_of_Africa(
            (
                nuA,
                TA,
                nuB,
                TB,
                nuEu0,
                nuEuF,
                nuAs0,
                nuAsF,
                TF,
                mAfB,
                mAfEu,
                mAfAs,
                mEuAs,
            ),
            rho=rho,
            theta=theta,
        )
        y_demes = moments.LD.LDstats.from_demes(
            os.path.join(os.path.dirname(__file__), "test_files/gutenkunst_ooa.yml"),
            ["YRI", "CEU", "CHB"],
            rho=rho,
            theta=theta,
        )

        self.assertTrue(
            np.all([x == y for x, y in zip(y_moments.pop_ids, y_demes.pop_ids)])
        )
        for x, y in zip(y_demes, y_moments):
            self.assertTrue(np.allclose(x, y))


class ComputeFromGraphs(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        t = time.time() - self.startTime
        print("%s: %.3f seconds" % (self.id(), t))

    def test_admixture_with_marginalization(self):
        # admixture scenario where two populations admix, one continues and the other is marginalized
        b = demes.Builder(description="test", time_units="generations")
        b.add_deme("anc", epochs=[dict(start_size=100, end_time=100)])
        b.add_deme(
            "A", epochs=[dict(start_size=100, end_time=0)], ancestors=["anc"],
        )
        b.add_deme(
            "B", epochs=[dict(start_size=100, end_time=50)], ancestors=["anc"],
        )
        b.add_deme(
            "C",
            epochs=[dict(start_size=100, end_time=0)],
            ancestors=["A", "B"],
            proportions=[0.75, 0.25],
            start_time=50,
        )
        g = b.resolve()

        fs = moments.Demographics1D.snm([30])
        fs = fs.split(0, 20, 10)
        fs.integrate([1, 1], 50 / 2 / 100)
        fs = fs.admix(0, 1, 10, 0.75)
        fs.integrate([1, 1], 50 / 2 / 100)
        fs_demes = moments.Demes.SFS(g, sampled_demes=["A", "C"], sample_sizes=[10, 10])
        self.assertTrue(np.allclose(fs.data, fs_demes.data))

        y = moments.LD.Demographics1D.snm()
        y = y.split(0)
        y.integrate([1, 1], 50 / 2 / 100)
        y = y.admix(0, 1, 0.75)
        y = y.marginalize([1])
        y.integrate([1, 1], 50 / 2 / 100)
        y_demes = moments.Demes.LD(g, sampled_demes=["A", "C"])

    def test_migration_end_and_marginalize(self):
        # ghost population with migration that ends before time zero
        b = demes.Builder(description="test", time_units="generations")
        b.add_deme("anc", epochs=[dict(start_size=100, end_time=100)])
        b.add_deme(
            "A", epochs=[dict(start_size=100, end_time=25)], ancestors=["anc"],
        )
        b.add_deme(
            "B", epochs=[dict(start_size=100, end_time=50)], ancestors=["anc"],
        )
        b.add_deme(
            "C", epochs=[dict(start_size=100, end_time=0)], ancestors=["B"],
        )
        b.add_deme(
            "D", epochs=[dict(start_size=100, end_time=0)], ancestors=["B"],
        )
        b.add_migration
        g = b.resolve()

        fs_demes = moments.Demes.SFS(g, sampled_demes=["C", "D"], sample_sizes=[4, 4])
        y_demes = moments.Demes.LD(g, sampled_demes=["C", "D"])
        self.assertTrue(fs_demes.ndim == 2)
        self.assertTrue(np.all([x == y for x, y in zip(fs_demes.pop_ids, ["C", "D"])]))
        self.assertTrue(y_demes.num_pops == 2)
        self.assertTrue(np.all([x == y for x, y in zip(y_demes.pop_ids, ["C", "D"])]))


def moments_ooa(ns):
    fs = moments.Demographics1D.snm([sum(ns)])
    fs.integrate([1.6849315068493151], 0.2191780821917808)
    fs = moments.Manips.split_1D_to_2D(fs, ns[0], ns[1] + ns[2])
    fs.integrate(
        [1.6849315068493151, 0.2876712328767123],
        0.3254794520547945,
        m=[[0, 3.65], [3.65, 0]],
    )
    fs = moments.Manips.split_2D_to_3D_2(fs, ns[1], ns[2])

    def nu_func(t):
        return [
            1.6849315068493151,
            0.136986301369863
            * np.exp(
                np.log(4.071917808219178 / 0.136986301369863) * t / 0.05808219178082192
            ),
            0.06986301369863014
            * np.exp(
                np.log(7.409589041095891 / 0.06986301369863014)
                * t
                / 0.05808219178082192
            ),
        ]

    fs.integrate(
        nu_func,
        0.05808219178082192,
        m=[[0, 0.438, 0.2774], [0.438, 0, 1.4016], [0.2774, 1.4016, 0]],
    )
    return fs


class TestMomentsSFS(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        t = time.time() - self.startTime
        print("%s: %.3f seconds" % (self.id(), t))

    def test_num_lineages(self):
        # simple merge model
        b = demes.Builder(description="test", time_units="generations")
        b.add_deme("anc", epochs=[dict(start_size=100, end_time=100)])
        b.add_deme(
            "pop1", epochs=[dict(start_size=100, end_time=10)], ancestors=["anc"],
        )
        b.add_deme(
            "pop2", epochs=[dict(start_size=100, end_time=10)], ancestors=["anc"],
        )
        b.add_deme(
            "pop3", epochs=[dict(start_size=100, end_time=10)], ancestors=["anc"],
        )
        b.add_deme(
            "pop",
            ancestors=["pop1", "pop2", "pop3"],
            proportions=[0.1, 0.2, 0.7],
            start_time=10,
            epochs=[dict(end_time=0, start_size=100)],
        )
        g = b.resolve()
        sampled_demes = ["pop"]
        demes_demo_events = g.discrete_demographic_events()
        demo_events, demes_present = Demes._get_demographic_events(
            g, demes_demo_events, sampled_demes
        )
        deme_sample_sizes = Demes._get_deme_sample_sizes(
            g, demo_events, sampled_demes, [20], demes_present
        )
        self.assertTrue(deme_sample_sizes[(math.inf, 100)][0] == 60)
        self.assertTrue(
            np.all([deme_sample_sizes[(100, 10)][i] == 20 for i in range(3)])
        )

        # simple admix model
        b = demes.Builder(description="test", time_units="generations")
        b.add_deme("anc", epochs=[dict(start_size=100, end_time=100)])
        b.add_deme(
            "pop1", epochs=[dict(start_size=100, end_time=0)], ancestors=["anc"],
        )
        b.add_deme(
            "pop2", epochs=[dict(start_size=100, end_time=0)], ancestors=["anc"],
        )
        b.add_deme(
            "pop3", epochs=[dict(start_size=100, end_time=0)], ancestors=["anc"],
        )
        b.add_deme(
            "pop",
            ancestors=["pop1", "pop2", "pop3"],
            proportions=[0.1, 0.2, 0.7],
            start_time=10,
            epochs=[dict(start_size=100, end_time=0)],
        )
        g = b.resolve()
        sampled_demes = ["pop"]
        demes_demo_events = g.discrete_demographic_events()
        demo_events, demes_present = Demes._get_demographic_events(
            g, demes_demo_events, sampled_demes
        )
        deme_sample_sizes = Demes._get_deme_sample_sizes(
            g, demo_events, sampled_demes, [20], demes_present, unsampled_n=10
        )
        self.assertTrue(deme_sample_sizes[(math.inf, 100)][0] == 90)
        self.assertTrue(
            np.all([deme_sample_sizes[(100, 10)][i] == 30 for i in range(3)])
        )

    # test basic results against moments implementation
    def test_one_pop(self):
        b = demes.Builder(description="test", time_units="generations")
        b.add_deme("Pop", epochs=[dict(start_size=1000, end_time=0)])
        g = b.resolve()
        fs = Demes.SFS(g, ["Pop"], [20])
        fs_m = moments.Demographics1D.snm([20])
        self.assertTrue(np.allclose(fs.data, fs_m.data))

        b = demes.Builder(description="test", time_units="generations")
        b.add_deme(
            "Pop",
            epochs=[
                dict(start_size=1000, end_time=2000),
                dict(end_time=0, start_size=10000),
            ],
        )
        g = b.resolve()
        fs = Demes.SFS(g, ["Pop"], [20])
        fs_m = moments.Demographics1D.snm([20])
        fs_m.integrate([10], 1)
        self.assertTrue(np.allclose(fs.data, fs_m.data))

    def test_more_than_5_demes(self):
        b = demes.Builder(description="test", time_units="generations")
        b.add_deme("anc", epochs=[dict(start_size=1000, end_time=1000)])
        for i in range(6):
            b.add_deme(
                f"pop{i}",
                epochs=[dict(start_size=1000, end_time=0)],
                ancestors=["anc"],
            )
        g = b.resolve()
        with self.assertRaises(ValueError):
            Demes.SFS(g, ["pop{i}" for i in range(6)], [10 for i in range(6)])

        b = demes.Builder(description="test", time_units="generations")
        b.add_deme("anc", epochs=[dict(start_size=1000, end_time=1000)])
        for i in range(3):
            b.add_deme(
                f"pop{i}",
                epochs=[dict(start_size=1000, end_time=0)],
                ancestors=["anc"],
            )
        g = b.resolve()
        with self.assertRaises(ValueError):
            Demes.SFS(
                g,
                ["pop{i}" for i in range(3)],
                [10 for i in range(3)],
                sample_times=[5, 10, 15],
            )

    def test_one_pop_ancient_samples(self):
        b = demes.Builder(description="test", time_units="generations")
        b.add_deme("Pop", epochs=[dict(start_size=1000, end_time=0)])
        g = b.resolve()
        fs = Demes.SFS(g, ["Pop", "Pop"], [20, 4], sample_times=[0, 100])
        fs_m = moments.Demographics1D.snm([24])
        fs_m = moments.Manips.split_1D_to_2D(fs_m, 20, 4)
        fs_m.integrate([1, 1], 100 / 2 / 1000, frozen=[False, True])
        self.assertTrue(np.allclose(fs.data, fs_m.data))

    def test_simple_merge(self):
        b = demes.Builder(description="test", time_units="generations")
        b.add_deme("Anc", epochs=[dict(start_size=1000, end_time=100)])
        b.add_deme(
            "Source1", epochs=[dict(start_size=2000, end_time=10)], ancestors=["Anc"],
        )
        b.add_deme(
            "Source2", epochs=[dict(start_size=3000, end_time=10)], ancestors=["Anc"],
        )
        b.add_deme(
            "Pop",
            ancestors=["Source1", "Source2"],
            proportions=[0.8, 0.2],
            start_time=10,
            epochs=[dict(start_size=4000, end_time=0)],
        )
        g = b.resolve()
        fs = Demes.SFS(g, ["Pop"], [20])

        fs_m = moments.Demographics1D.snm([40])
        fs_m = moments.Manips.split_1D_to_2D(fs_m, 20, 20)
        fs_m.integrate([2, 3], 90 / 2 / 1000)
        fs_m = moments.Manips.admix_into_new(fs_m, 0, 1, 20, 0.8)
        fs_m.integrate([4], 10 / 2 / 1000)
        self.assertTrue(np.allclose(fs.data, fs_m.data))

    def test_simple_admixture(self):
        b = demes.Builder(description="test", time_units="generations")
        b.add_deme("Anc", epochs=[dict(start_size=1000, end_time=100)])
        b.add_deme(
            "Source1", epochs=[dict(start_size=2000, end_time=0)], ancestors=["Anc"],
        )
        b.add_deme(
            "Source2", epochs=[dict(start_size=3000, end_time=0)], ancestors=["Anc"],
        )
        b.add_deme(
            "Pop",
            ancestors=["Source1", "Source2"],
            proportions=[0.8, 0.2],
            start_time=10,
            epochs=[dict(start_size=4000, end_time=0)],
        )
        g = b.resolve()
        fs = Demes.SFS(g, ["Source1", "Source2", "Pop"], [10, 10, 10])

        fs_m = moments.Demographics1D.snm([40])
        fs_m = moments.Manips.split_1D_to_2D(fs_m, 20, 20)
        fs_m.integrate([2, 3], 90 / 2 / 1000)
        fs_m = moments.Manips.admix_into_new(fs_m, 0, 1, 10, 0.8)
        fs_m.integrate([2, 3, 4], 10 / 2 / 1000)
        self.assertTrue(np.allclose(fs.data, fs_m.data))

    def test_simple_growth_models(self):
        b = demes.Builder(description="test", time_units="generations")
        b.add_deme(
            "Pop",
            epochs=[
                dict(end_time=1000, start_size=1000),
                dict(start_size=500, end_size=5000, end_time=0),
            ],
        )
        g = b.resolve()
        fs = Demes.SFS(g, ["Pop"], [100])

        fs_m = moments.Demographics1D.snm([100])

        def nu_func(t):
            return [0.5 * np.exp(np.log(5000 / 500) * t / 0.5)]

        fs_m.integrate(nu_func, 0.5)
        self.assertTrue(np.allclose(fs.data, fs_m.data))

        # Linear size functions are not currently supported in Demes
        # b = demes.Builder(description="test", time_units="generations")
        # b.add_deme(
        #    "Pop",
        #    epochs=[
        #        dict(end_time=1000, start_size=1000),
        #        dict(
        #            start_size=500, end_size=5000, end_time=0, size_function="linear",
        #        ),
        #    ],
        # )
        # g = b.resolve()
        # fs = Demes.SFS(g, ["Pop"], [100])
        #
        # fs_m = moments.Demographics1D.snm([100])
        #
        # def nu_func(t):
        #    return [0.5 + t / 0.5 * (5 - 0.5)]
        #
        # fs_m.integrate(nu_func, 0.5)
        # self.assertTrue(np.allclose(fs.data, fs_m.data))

    def test_simple_pulse_model(self):
        b = demes.Builder(description="test", time_units="generations")
        b.add_deme("anc", epochs=[dict(start_size=1000, end_time=100)])
        b.add_deme(
            "source", epochs=[dict(start_size=1000, end_time=0)], ancestors=["anc"],
        )
        b.add_deme(
            "dest", epochs=[dict(start_size=1000, end_time=0)], ancestors=["anc"],
        )
        b.add_pulse(source="source", dest="dest", time=10, proportion=0.1)
        g = b.resolve()
        fs = Demes.SFS(g, ["source", "dest"], [20, 20])

        fs_m = moments.Demographics1D.snm([60])
        fs_m = moments.Manips.split_1D_to_2D(fs_m, 40, 20)
        fs_m.integrate([1, 1], 90 / 2 / 1000)
        fs_m = moments.Manips.admix_inplace(fs_m, 0, 1, 20, 0.1)
        fs_m.integrate([1, 1], 10 / 2 / 1000)
        self.assertTrue(np.allclose(fs.data, fs_m.data))

    def test_n_way_split(self):
        b = demes.Builder(description="three-way", time_units="generations")
        b.add_deme("anc", epochs=[dict(start_size=1000, end_time=10)])
        b.add_deme(
            "deme1", epochs=[dict(start_size=1000, end_time=0)], ancestors=["anc"],
        )
        b.add_deme(
            "deme2", epochs=[dict(start_size=1000, end_time=0)], ancestors=["anc"],
        )
        b.add_deme(
            "deme3", epochs=[dict(start_size=1000, end_time=0)], ancestors=["anc"],
        )
        g = b.resolve()
        ns = [10, 15, 20]
        fs = Demes.SFS(g, ["deme1", "deme2", "deme3"], ns)
        self.assertTrue(np.all([fs.sample_sizes[i] == ns[i] for i in range(len(ns))]))

        fs_m1 = moments.Demographics1D.snm([sum(ns)])
        fs_m1 = moments.Manips.split_1D_to_2D(fs_m1, ns[0], ns[1] + ns[2])
        fs_m1 = moments.Manips.split_2D_to_3D_2(fs_m1, ns[1], ns[2])
        fs_m1.integrate([1, 1, 1], 10 / 2 / 1000)

        fs_m2 = moments.Demographics1D.snm([sum(ns)])
        fs_m2 = moments.Manips.split_1D_to_2D(fs_m2, ns[0] + ns[1], ns[2])
        fs_m2 = moments.Manips.split_2D_to_3D_1(fs_m2, ns[0], ns[1])
        fs_m2 = fs_m2.swapaxes(1, 2)
        fs_m2.integrate([1, 1, 1], 10 / 2 / 1000)

        self.assertTrue(np.allclose(fs.data, fs_m1.data))
        self.assertTrue(np.allclose(fs.data, fs_m2.data))

    def test_n_way_admixture(self):
        b = demes.Builder(description="three-way merge", time_units="generations")
        b.add_deme("anc", epochs=[dict(start_size=1000, end_time=100)])
        b.add_deme(
            "source1", epochs=[dict(start_size=1000, end_time=10)], ancestors=["anc"],
        )
        b.add_deme(
            "source2", epochs=[dict(start_size=1000, end_time=10)], ancestors=["anc"],
        )
        b.add_deme(
            "source3", epochs=[dict(start_size=1000, end_time=10)], ancestors=["anc"],
        )
        b.add_deme(
            "merged",
            ancestors=["source1", "source2", "source3"],
            proportions=[0.5, 0.2, 0.3],
            start_time=10,
            epochs=[dict(start_size=1000, end_time=0)],
        )
        g = b.resolve()
        ns = [10]
        fs = Demes.SFS(g, ["merged"], ns)

        fs_m = moments.Demographics1D.snm([30])
        fs_m = moments.Manips.split_1D_to_2D(fs_m, 10, 20)
        fs_m = moments.Manips.split_2D_to_3D_2(fs_m, 10, 10)
        fs_m.integrate([1, 1, 1], 90 / 2 / 1000)
        fs_m = moments.Manips.admix_into_new(fs_m, 0, 1, 10, 0.5 / 0.7)
        fs_m = moments.Manips.admix_into_new(fs_m, 0, 1, 10, 0.3)
        fs_m.integrate([1], 10 / 2 / 1000)

        self.assertTrue(np.allclose(fs_m.data, fs.data))

        b = demes.Builder(description="three-way admix", time_units="generations")
        b.add_deme("anc", epochs=[dict(start_size=1000, end_time=100)])
        b.add_deme(
            "source1", epochs=[dict(start_size=1000, end_time=0)], ancestors=["anc"],
        )
        b.add_deme(
            "source2", epochs=[dict(start_size=1000, end_time=0)], ancestors=["anc"],
        )
        b.add_deme(
            "source3", epochs=[dict(start_size=1000, end_time=0)], ancestors=["anc"],
        )
        b.add_deme(
            "admixed",
            ancestors=["source1", "source2", "source3"],
            proportions=[0.5, 0.2, 0.3],
            start_time=10,
            epochs=[dict(start_size=1000, end_time=0)],
        )
        g = b.resolve()
        ns = [10]
        fs = Demes.SFS(g, ["admixed"], ns)

        fs_m = moments.Demographics1D.snm([30])
        fs_m = moments.Manips.split_1D_to_2D(fs_m, 10, 20)
        fs_m = moments.Manips.split_2D_to_3D_2(fs_m, 10, 10)
        fs_m.integrate([1, 1, 1], 90 / 2 / 1000)
        fs_m = moments.Manips.admix_into_new(fs_m, 0, 1, 10, 0.5 / 0.7)
        fs_m = moments.Manips.admix_into_new(fs_m, 0, 1, 10, 0.3)
        fs_m.integrate([1], 10 / 2 / 1000)

        self.assertTrue(np.allclose(fs_m.data[1:-1], fs.data[1:-1]))

        fs = Demes.SFS(g, ["source1", "admixed"], [10, 10])

        fs_m = moments.Demographics1D.snm([40])
        fs_m = moments.Manips.split_1D_to_2D(fs_m, 20, 20)
        fs_m = moments.Manips.split_2D_to_3D_2(fs_m, 10, 10)
        fs_m.integrate([1, 1, 1], 90 / 2 / 1000)
        fs_m = moments.Manips.admix_into_new(fs_m, 0, 1, 10, 0.5 / 0.7)
        fs_m = moments.Manips.admix_into_new(fs_m, 1, 2, 10, 0.3)
        fs_m.integrate([1, 1], 10 / 2 / 1000)

        fs[0, 0] = fs[-1, -1] = 0
        fs_m[0, 0] = fs_m[-1, -1] = 0
        self.assertTrue(np.allclose(fs_m.data[1:-1], fs.data[1:-1]))


class TestConcurrentEvents(unittest.TestCase):
    def setUp(self):
        self.startTime = time.time()

    def tearDown(self):
        t = time.time() - self.startTime
        print("%s: %.3f seconds" % (self.id(), t))

    def test_branches_at_same_time(self):
        def from_old_style(sample_sizes):
            fs = moments.Demographics1D.snm([4 + sum(sample_sizes)])
            fs = fs.branch(0, sample_sizes[0])
            fs = fs.branch(0, sample_sizes[1])
            fs.integrate([1, 1, 1], 0.5)
            fs = fs.marginalize([0])
            return fs

        b = demes.Builder()
        b.add_deme("x", epochs=[dict(start_size=100)])
        b.add_deme("a", ancestors=["x"], start_time=100, epochs=[dict(start_size=100)])
        b.add_deme("b", ancestors=["x"], start_time=100, epochs=[dict(start_size=100)])
        graph = b.resolve()

        ns = [10, 10]
        fs_demes = moments.Spectrum.from_demes(
            graph, sampled_demes=["a", "b"], sample_sizes=ns
        )

        fs_moments = from_old_style(ns)

        self.assertTrue(np.allclose(fs_demes.data, fs_moments.data))

        b2 = demes.Builder()
        b2.add_deme("x", epochs=[dict(start_size=100)])
        b2.add_deme("a", ancestors=["x"], start_time=100, epochs=[dict(start_size=100)])
        b2.add_deme(
            "b", ancestors=["x"], start_time=99.9999, epochs=[dict(start_size=100)]
        )
        graph2 = b2.resolve()

        fs_demes2 = moments.Spectrum.from_demes(
            graph2, sampled_demes=["a", "b"], sample_sizes=ns
        )

        self.assertTrue(
            np.all([a == b for a, b, in zip(fs_demes.pop_ids, fs_demes2.pop_ids)])
        )
        self.assertTrue(np.allclose(fs_demes.data, fs_demes2.data))
