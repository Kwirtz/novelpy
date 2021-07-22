## from nestauk/narrowing_ai_research/blob/master/narrowing_ai_research/transformers/diversity.py
import numpy as np
import pandas as pd
from scipy.cluster import hierarchy
from scipy.spatial.distance import pdist, squareform
from itertools import combinations
from scipy.stats import entropy


def hh_index(distr):
    """
    Calculate the Hirschmann-Herfindahl index of a distribution
    """
    # Sum of squares
    hh = np.sum([(x / distr.sum()) ** 2 for x in distr])

    return hh


def remove_zero_axis(df):
    """Removes axes where all values are zero"""

    df_r = df.loc[df.sum(axis=1) > 0, df.sum() > 0]
    return df_r


def estimate_balance(data, params):
    """Estimates balance metric
    Args:
        data: df with topic mix
        params: dict including
            div_metric: hh or entropy
            sample: size of sample if we calculate div for a random
                sample
            method: how we allocate topics to papers.
                max allocates each paper to its largest topic;
                binary binarises all topics based on a threshold
            threshold: threshold to consider that a topic is in a paper
                (only relevant when we are using the binary method)
    """
    method = params["method"]
    if method is "binary":
        threshold = params["threshold"]
    div_metric = params["div_metric"]
    sample = params["sample"]
    threshold = params["threshold"]

    if sample != "all":
        selected = np.random.choice(np.arange(0, len(data)), size=sample, replace=False)
        data = data.iloc[selected]

    # If the method is max we allocate each paper t
    # o its top topic and analyse their distributions
    if method is "max":
        distr = data.idxmax(axis=1).value_counts()
        if div_metric == "hh":
            hh = hh_index(distr)
            return 1 - hh
        if div_metric == "entropy":
            ent = entropy(distr)
            return ent

    if method == "binary":
        distr = data.applymap(lambda x: x > threshold).sum()
        if div_metric == "hh":
            hh = hh_index(distr)
            return 1 - hh

        if div_metric == "entropy":
            ent = entropy(distr)
            return ent


def estimate_weitzman(data, params):
    """This function creates a hierarchical tree based on distances between topics
    and calculates diversity (the length in the branches of that tree)
    Args:
        data: df with topic mix
        params:
            distance: is the metric of distance that we use
            sample: if not None, then it will be a random sample of observations
    """
    distance = params["distance"]
    sample = params["sample"]

    if sample != "all":
        selected = np.random.choice(np.arange(0, len(data)), size=sample, replace=False)
        data = data.iloc[selected]

    # Plot distances
    dists = hierarchy.linkage(data.T, metric=distance)

    dend = hierarchy.dendrogram(dists, no_plot=True)

    # This gives the length of each branch at merge
    lengths = [x[1] for x in dend["dcoord"]]

    path_length = np.sum(lengths)

    return path_length


def estimate_rao_stirling(data, params, dist_matrix=False):
    """Calculates the rao-stirling diversity
    #based on population diversities and distances.
    Args:
        data: topic mix for each paper
        params:
            sample: size of sample if we calculate div for a random
                sample
            method: how we allocate topics to papers.
                max allocates each paper to its largest topic;
                binary binarises all topics based on a threshold
            threshold: threshold to consider that a topic is in a paper
                (only relevant when we are using the binary method)
            distance: how to calculate distance between topics
            dist_matrix: whether the distances are calculated in the data
                or externally
                If not False we need to supply a square matrix with
                    inter-topic distances
    """

    sample = params["sample"]
    method = params["method"]
    threshold = params["threshold"]
    distance = params["distance"]

    if sample != "all":
        selected = np.random.choice(np.arange(0, len(data)), size=sample, replace=False)
        data = data.iloc[selected]

    if dist_matrix is False:
        # Calculate distances as a square matrix
        dists = pd.DataFrame(
            squareform(pdist(data.T, metric=distance)),
            columns=data.columns,
            index=data.columns,
        )

        # Create dict with all the distances
        dist_dict = (
            pd.melt(dists.reset_index(drop=False), id_vars="index")
            .set_index(["index", "variable"])
            .to_dict(orient="index")
        )

    else:
        # Takes the distances parametre and calculates

        dist_dict = (
            pd.melt(dist_matrix.reset_index(drop=False), id_vars="index")
            .set_index(["index", "variable"])
            .to_dict(orient="index")
        )

    # Calculate distributions - we create dicts with values to extract scores
    # faster below
    if method == "max":
        distr = data.idxmax(axis=1).value_counts()
        total = np.sum(distr)
        distr_dict = distr.to_dict()
    else:
        distr = data.applymap(lambda x: x > threshold).sum()
        total = np.sum(distr)
        distr_dict = distr.to_dict()

    # Estimate metric
    # Get a list of pairs of topics
    # Note we changed this to distr from topics to
    # avoid errors when a year doesn't contain a topic
    pairs = list(combinations(distr.index, 2))

    # We will store the weighted distances (or weighted proportions!) here
    weighted_dists = []

    # For each pair
    for p in pairs:
        e1 = p[0]
        e2 = p[1]

        # We calculate the distances between elements
        d = dist_dict[(e1, e2)]["value"]

        # We multiply their proportions
        prop_prod = (distr_dict[e1] / total) * (distr_dict[e2] / total)

        # We add to the output list
        weighted_dists.append(d * prop_prod)

    # Return the sum
    return np.sum(weighted_dists)


class Diversity:
    """"""

    def __init__(self, data, meta_info):
        """Initialise class
        Args:
            data: topic mix
            meta_info: any metadata to use in the  name of the variable
        """
        self.data = data
        self.meta_info = meta_info

    def balance(self, params):
        """Estimate balance metric"""
        self.params = params
        self.metric_name = "balance"
        self.metric = estimate_balance(self.data, params)
        self.param_values = "_".join(["balance"] + [str(v) for v in params.values()])

    def weitzman(self, params):
        """Estimate Weitzman metric"""
        self.params = params
        self.metric_name = "weitzman"
        self.metric = estimate_weitzman(remove_zero_axis(self.data), params)
        self.param_values = "_".join(["weitzman"] + [str(v) for v in params.values()])

    def rao_stirling(self, params, dist_matrix=False):
        """Estimate Weitzman metric"""

        # We need to add the distance matrix information.
        if dist_matrix is False:
            self.params = params
            self.params["dist_matrix"] = "internal"
        else:
            self.params = params
            self.params["dist_matrix"] = "external"

        self.metric_name = "rao_stirling"
        self.metric = estimate_rao_stirling(self.data, params, dist_matrix)

        # We don't want to add the threshold parameter if irrelevant
        param_values = "_".join(
            ["rao_stirling"] + [str(v) for v in params.values() if len(str(v)) > 0]
        )
        if dist_matrix is False:
            self.param_values = param_values + "_internal"
        else:
            self.param_values = param_values + "_external"