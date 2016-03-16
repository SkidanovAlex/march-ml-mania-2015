# March machine learning mania 2015 submission
This is my submission for [march ml mania 2016](https://www.kaggle.com/c/march-machine-learning-mania-2016) and [march ml mania 2015](https://www.kaggle.com/c/march-machine-learning-mania-2015).

It is built on top of [Lasagne](https://github.com/benanne/Lasagne/), using a very convenient wrapper [nolearn](https://github.com/dnouri/nolearn/). I configured the virtualenv in 2015 and never updated it, so it potentially depends on rather old versions of Lasagne/nolearn/Theano.

The model only used player data in 2015, in 2016 in addition to it it uses coach stats and some overall team stats. `collect.py` is the script that has all the routines to collect that data from the web.

I use 5 players per team, choosing those that have played the most games in the corresponding season.


The model itself (implemented in `model.py`) is a neural network with two hidden layers.

 * First layer (implemented in `custom_layers.py`) is a partially connected layer, that ensures that features for every player have equal weights going forward to the second layer. First team players are connected to the first half of neurons in the next layer, and second team players are connected to the second half.
 * Second layer is just a dense layer.


For the bracket challenge I prepared two brackets (`bracket.py`), one uses naive approach, where a team with higher probability always advances to the next round. Another uses smarter dynamic programming approach, maximizing the expected score of the bracket. Both brackets for 2015 are in the root of the repo.
