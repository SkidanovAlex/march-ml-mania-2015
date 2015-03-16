from lasagne import nonlinearities, init
from lasagne.layers import Layer
from lasagne.utils import concatenate
import numpy as np
import theano.tensor as T

ppt = 5

class NCAALayer(Layer):
    def __init__(self, incoming, num_units, W=init.Uniform(),
                 b=init.Constant(0.), nonlinearity=nonlinearities.rectify,
                 **kwargs):
        super(NCAALayer, self).__init__(incoming, **kwargs)
        if nonlinearity is None:
            self.nonlinearity = nonlinearities.identity
        else:
            self.nonlinearity = nonlinearity

        self.num_units = num_units
        assert num_units % 2 == 0

        self.input_shape = incoming.get_output_shape()
        num_inputs = int(np.prod(self.input_shape[1:]))
        assert num_inputs % (2 * ppt) == 0

        self.W = self.create_param(W, (num_inputs / 2 / ppt, num_units / 2))
        self.b = (self.create_param(b, (num_units / 2,))
                  if b is not None else None)

    def get_params(self):
        return [self.W] + self.get_bias_params()

    def get_bias_params(self):
        return [self.b] if self.b is not None else []

    def get_output_shape_for(self, input_shape):
        return (input_shape[0], self.num_units)

    def get_output_for(self, input, *args, **kwargs):
        if input.ndim > 2:
            # if the input has more than two dimensions, flatten it into a
            # batch of feature vectors.
            input = input.flatten(2)

        num_inputs = int(np.prod(self.input_shape[1:]))
        activations = []
        for team in range(2):
            for i, plr in enumerate(range(ppt)):
                feat = num_inputs / 2 / ppt
                mid = feat * i + num_inputs / 2 * team
                if i == 0:
                    activation = T.dot(input[:,mid:mid+feat], self.W)
                else:
                    activation += T.dot(input[:,mid:mid+feat], self.W)
            activations.append(activation)
        if self.b is not None:
            activations[0] = activations[0] + self.b.dimshuffle('x', 0)
            activations[1] = activations[1] + self.b.dimshuffle('x', 0)
        return self.nonlinearity(concatenate(activations, axis=1))

