# Copyright (c) 2017 NVIDIA Corporation
"""Data Layer Classes"""
from __future__ import absolute_import, division, print_function
from __future__ import unicode_literals
from six.moves import range

import abc
import six
import tensorflow as tf
import copy
from open_seq2seq.utils.utils import check_params


@six.add_metaclass(abc.ABCMeta)
class DataLayer:
  """Abstract class from which all data layers must inherit.
  """
  @staticmethod
  def get_required_params():
    """Static method with description of required parameters.

      Returns:
        dict:
            Dictionary containing all the parameters that **have to** be
            included into the ``params`` parameter of the
            class :meth:`__init__` method.
    """
    return {
      'mode': ['train', 'eval', 'infer'],
    }

  @staticmethod
  def get_optional_params():
    """Static method with description of optional parameters.

      Returns:
        dict:
            Dictionary containing all the parameters that **can** be
            included into the ``params`` parameter of the
            class :meth:`__init__` method.
    """
    return {
      'batch_size': int,
      'shuffle': bool,
      'dtype': [tf.float32, tf.float16],
    }

  @abc.abstractmethod
  def __init__(self, params, model, num_workers, worker_id):
    """Data layer constructor.
    The TensorFlow graph should not be created here, but rather in the
    :meth:`self.build_graph() <build_graph>` method.

    Args:
      params (dict): parameters describing the data layer.
          All supported parameters are listed in :meth:`get_required_params`,
          :meth:`get_optional_params` functions.
      model (instance of a class derived from :class:`Model<models.model.Model>`):
          parent model that created this data layer.
          Could be None if no model access is required for the use case.
      num_workers (int): number of Horovod processes or number of GPUs
          if Horovod is not used.
      worker_id (int): Horovod process id or GPU id if Horovod is not used.

    Config parameters:

    * **shuffle** (bool) --- whether to shuffle dataset after an epoch.
      Typically will be True for train and False for inference and evaluation.
    * **dtype** --- data dtype. Could be either ``tf.float16`` or ``tf.float32``.
    """
    check_params(params, self.get_required_params(), self.get_optional_params())
    self._params = copy.deepcopy(params)
    self._model = model

    if 'dtype' not in self._params:
      if self._model:
        self._params['dtype'] = self._model.get_tf_dtype()
      else:
        self._params['dtype'] = tf.float32

    if 'shuffle' not in params:
      if self._params['mode'] == 'train':
        self._params['shuffle'] = True
      else:
        self._params['shuffle'] = False

    if self._params['mode'] != 'train' and self._params['shuffle']:
      raise ValueError("Shuffle should not be performed in eval or infer modes")

    # should be used for correct evaluation on multiple GPUs
    self._num_workers = num_workers
    self._worker_id = worker_id

  @property
  def params(self):
    """Parameters used to construct the data layer (dictionary)."""
    return self._params

  @abc.abstractmethod
  def build_graph(self):
    """Here all TensorFlow graph construction should happen."""
    pass

  @property
  @abc.abstractmethod
  def iterator(self):
    """``tf.data.Dataset`` iterator.
    Should be created by :meth:`self.build_graph()<build_graph>`.
    """
    pass

  @property
  @abc.abstractmethod
  def input_tensors(self):
    """Dictionary containing input tensors.
    This dictionary has to define the following keys: `source_tensors`,
    which should contain all tensors describing the input object (i.e. tensors
    that are passed to the encoder, e.g. input sequence and input length). And
    when ``self.params['mode'] != "infer"`` data layer should also define
    `target_tensors` which is the list of all tensors related to the
    corresponding target object (i.e. tensors taht are passed to the decoder and
    loss, e.g. target sequence and target length). Note that all tensors have
    to be created inside :meth:`self.build_graph()<build_graph>` method.
    """
    pass

  def get_size_in_samples(self):
    """Should return the dataset size in samples.
    That is, the number of objects in the dataset. This method is used to
    calculate a valid epoch size. If this method is not defined, you will need
    to make sure that your dataset for evaluation is created only for
    one epoch. You will also not be able to use ``num_epochs`` parameter in the
    base config.

    Returns:
      int: dataset size in samples.
    """
    return None
