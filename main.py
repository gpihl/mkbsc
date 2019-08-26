#!/usr/bin/env python3

from mkbsc import MultiplayerGame, iterate_until_isomorphic, \
                  export, to_string, from_string, to_file, from_file

#states
L = ["start", "hole", "no hole", "win", "lose"]

#initial state
L0 = "start"

#action alphabet
Sigma = (("G", "P", "D"), ("G", "P", "D"))

#action labeled transitions
Delta = [
    ("start", ("G", "G"), "hole"), 
    ("start", ("G", "G"), "no hole"),
    ("hole", ("D", "D"), "hole"), 
    ("hole", ("P", "P"), "win"),
    ("hole", ("P", "D"), "lose"),
    ("hole", ("D", "P"), "lose"),
    ("no hole", ("D", "D"), "hole"),
    ("no hole", ("D", "P"), "lose"),
    ("no hole", ("P", "D"), "lose"),
    ("hole", ("P", "P"), "lose"),
]
#observation partitioning
Obs = [
    [["start"], ["hole", "no hole"], ["win"], ["lose"]],
    [["start"], ["hole"], ["no hole"], ["win"], ["lose"]]
]

#G is a Multiplayer Game-object, and so are GK and GK0
G = MultiplayerGame.create(L, L0, Sigma, Delta, Obs)
GK = G.KBSC()
G2K = GK.KBSC()

# We set epistemic to e-tree to generate e-trees as a representation of the knowledge in the game graph 
export(G2K, "G2K", epistemic = "e-tree", file = "eps")


#print(test)
#to_file(GK, "GK")

