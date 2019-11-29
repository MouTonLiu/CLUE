# coding=utf-8
# Copyright 2019 The Google Research Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Utility functions for GLUE classification tasks."""

from __future__ import absolute_import
from __future__ import division

from __future__ import print_function

import json
import csv
import os
import six

import tensorflow as tf


def convert_to_unicode(text):
  """Converts `text` to Unicode (if it's not already), assuming utf-8 input."""
  if six.PY3:
    if isinstance(text, str):
      return text
    elif isinstance(text, bytes):
      return text.decode("utf-8", "ignore")
    else:
      raise ValueError("Unsupported string type: %s" % (type(text)))
  elif six.PY2:
    if isinstance(text, str):
      return text.decode("utf-8", "ignore")
    elif isinstance(text, unicode):
      return text
    else:
      raise ValueError("Unsupported string type: %s" % (type(text)))
  else:
    raise ValueError("Not running on Python2 or Python 3?")


class InputExample(object):
  """A single training/test example for simple sequence classification."""

  def __init__(self, guid, text_a, text_b=None, label=None):
    """Constructs a InputExample.
    Args:
      guid: Unique id for the example.
      text_a: string. The untokenized text of the first sequence. For single
        sequence tasks, only this sequence must be specified.
      text_b: (Optional) string. The untokenized text of the second sequence.
        Only must be specified for sequence pair tasks.
      label: (Optional) string. The label of the example. This should be
        specified for train and dev examples, but not for test examples.
    """
    self.guid = guid
    self.text_a = text_a
    self.text_b = text_b
    self.label = label


class PaddingInputExample(object):
  """Fake example so the num input examples is a multiple of the batch size.
  When running eval/predict on the TPU, we need to pad the number of examples
  to be a multiple of the batch size, because the TPU requires a fixed batch
  size. The alternative is to drop the last batch, which is bad because it means
  the entire output data won't be generated.
  We use this class instead of `None` because treating `None` as padding
  battches could cause silent errors.
  """


class DataProcessor(object):
  """Base class for data converters for sequence classification data sets."""

  def get_train_examples(self, data_dir):
    """Gets a collection of `InputExample`s for the train set."""
    raise NotImplementedError()

  def get_dev_examples(self, data_dir):
    """Gets a collection of `InputExample`s for the dev set."""
    raise NotImplementedError()

  def get_test_examples(self, data_dir):
    """Gets a collection of `InputExample`s for prediction."""
    raise NotImplementedError()

  def get_labels(self):
    """Gets the list of labels for this data set."""
    raise NotImplementedError()

  @classmethod
  def _read_tsv(cls, input_file, delimiter="\t", quotechar=None):
    """Reads a tab separated value file."""
    with tf.gfile.Open(input_file, "r") as f:
      reader = csv.reader(f, delimiter=delimiter, quotechar=quotechar)
      lines = []
      for line in reader:
        lines.append(line)
      return lines

  @classmethod
  def _read_txt(cls, input_file):
    """Reads a tab separated value file."""
    with tf.gfile.Open(input_file, "r") as f:
      reader = f.readlines()
      lines = []
      for line in reader:
        lines.append(line.strip().split("_!_"))
      return lines

  @classmethod
  def _read_json(cls, input_file):
    """Reads a tab separated value file."""
    with tf.gfile.Open(input_file, "r") as f:
      reader = f.readlines()
      lines = []
      for line in reader:
        lines.append(json.loads(line.strip()))
      return lines


class XnliProcessor(DataProcessor):
  """Processor for the XNLI data set."""

  def get_train_examples(self, data_dir):
    """See base class."""
    return self._create_examples(
        self._read_json(os.path.join(data_dir, "train.json")), "train")

  def get_dev_examples(self, data_dir):
    """See base class."""
    return self._create_examples(
        self._read_json(os.path.join(data_dir, "dev.json")), "dev")

  def get_test_examples(self, data_dir):
    """See base class."""
    return self._create_examples(
        self._read_json(os.path.join(data_dir, "test.json")), "test")

  def _create_examples(self, lines, set_type):
    """See base class."""
    examples = []
    for (i, line) in enumerate(lines):
      guid = "%s-%s" % (set_type, i)
      text_a = convert_to_unicode(line['premise'])
      text_b = convert_to_unicode(line['hypo'])
      label = convert_to_unicode(line['label']) if set_type != 'test' else 'contradiction'
      examples.append(
          InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label))
    return examples

  def get_labels(self):
    """See base class."""
    return ["contradiction", "entailment", "neutral"]


# class TnewsProcessor(DataProcessor):
#     """Processor for the MRPC data set (GLUE version)."""
#
#     def get_train_examples(self, data_dir):
#         """See base class."""
#         return self._create_examples(
#             self._read_txt(os.path.join(data_dir, "toutiao_category_train.txt")), "train")
#
#     def get_dev_examples(self, data_dir):
#         """See base class."""
#         return self._create_examples(
#             self._read_txt(os.path.join(data_dir, "toutiao_category_dev.txt")), "dev")
#
#     def get_test_examples(self, data_dir):
#         """See base class."""
#         return self._create_examples(
#             self._read_txt(os.path.join(data_dir, "toutiao_category_test.txt")), "test")
#
#     def get_labels(self):
#         """See base class."""
#         labels = []
#         for i in range(17):
#             if i == 5 or i == 11:
#                 continue
#             labels.append(str(100 + i))
#         return labels
#
#     def _create_examples(self, lines, set_type):
#         """Creates examples for the training and dev sets."""
#         examples = []
#         for (i, line) in enumerate(lines):
#             if i == 0:
#                 continue
#             guid = "%s-%s" % (set_type, i)
#             text_a = convert_to_unicode(line[3])
#             text_b = None
#             label = convert_to_unicode(line[1])
#             examples.append(
#                 InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label))
#         return examples


class TnewsProcessor(DataProcessor):
  """Processor for the MRPC data set (GLUE version)."""

  def get_train_examples(self, data_dir):
    """See base class."""
    return self._create_examples(
        self._read_json(os.path.join(data_dir, "train.json")), "train")

  def get_dev_examples(self, data_dir):
    """See base class."""
    return self._create_examples(
        self._read_json(os.path.join(data_dir, "dev.json")), "dev")

  def get_test_examples(self, data_dir):
    """See base class."""
    return self._create_examples(
        self._read_json(os.path.join(data_dir, "test.json")), "test")

  def get_labels(self):
    """See base class."""
    labels = []
    for i in range(17):
      if i == 5 or i == 11:
        continue
      labels.append(str(100 + i))
    return labels

  def _create_examples(self, lines, set_type):
    """Creates examples for the training and dev sets."""
    examples = []
    for (i, line) in enumerate(lines):
      guid = "%s-%s" % (set_type, i)
      text_a = convert_to_unicode(line['sentence'])
      text_b = None
      label = convert_to_unicode(line['label']) if set_type != 'test' else None
      examples.append(
          InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label))
    return examples


# class iFLYTEKDataProcessor(DataProcessor):
#     """Processor for the iFLYTEKData data set (GLUE version)."""
#
#     def get_train_examples(self, data_dir):
#         """See base class."""
#         return self._create_examples(
#             self._read_txt(os.path.join(data_dir, "train.txt")), "train")
#
#     def get_dev_examples(self, data_dir):
#         """See base class."""
#         return self._create_examples(
#             self._read_txt(os.path.join(data_dir, "dev.txt")), "dev")
#
#     def get_test_examples(self, data_dir):
#         """See base class."""
#         return self._create_examples(
#             self._read_txt(os.path.join(data_dir, "test.txt")), "test")
#
#     def get_labels(self):
#         """See base class."""
#         labels = []
#         for i in range(119):
#             labels.append(str(i))
#         return labels
#
#     def _create_examples(self, lines, set_type):
#         """Creates examples for the training and dev sets."""
#         examples = []
#         for (i, line) in enumerate(lines):
#             if i == 0:
#                 continue
#             guid = "%s-%s" % (set_type, i)
#             text_a = convert_to_unicode(line[1])
#             text_b = None
#             label = convert_to_unicode(line[0])
#             examples.append(
#                 InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label))
#         return examples


class iFLYTEKDataProcessor(DataProcessor):
  """Processor for the iFLYTEKData data set (GLUE version)."""

  def get_train_examples(self, data_dir):
    """See base class."""
    return self._create_examples(
        self._read_json(os.path.join(data_dir, "train.json")), "train")

  def get_dev_examples(self, data_dir):
    """See base class."""
    return self._create_examples(
        self._read_json(os.path.join(data_dir, "dev.json")), "dev")

  def get_test_examples(self, data_dir):
    """See base class."""
    return self._create_examples(
        self._read_json(os.path.join(data_dir, "test.json")), "test")

  def get_labels(self):
    """See base class."""
    labels = []
    for i in range(119):
      labels.append(str(i))
    return labels

  def _create_examples(self, lines, set_type):
    """Creates examples for the training and dev sets."""
    examples = []
    for (i, line) in enumerate(lines):
      guid = "%s-%s" % (set_type, i)
      text_a = convert_to_unicode(line['sentence'])
      text_b = None
      label = convert_to_unicode(line['label']) if set_type != 'test' else None
      examples.append(
          InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label))
    return examples


class AFQMCProcessor(DataProcessor):
  """Processor for the internal data set. sentence pair classification"""

  def get_train_examples(self, data_dir):
    """See base class."""
    return self._create_examples(
        self._read_json(os.path.join(data_dir, "train.json")), "train")

  def get_dev_examples(self, data_dir):
    """See base class."""
    return self._create_examples(
        self._read_json(os.path.join(data_dir, "dev.json")), "dev")

  def get_test_examples(self, data_dir):
    """See base class."""
    return self._create_examples(
        self._read_json(os.path.join(data_dir, "test.json")), "test")

  def get_labels(self):
    """See base class."""
    return ["0", "1"]

  def _create_examples(self, lines, set_type):
    """Creates examples for the training and dev sets."""
    examples = []
    for (i, line) in enumerate(lines):
      guid = "%s-%s" % (set_type, i)
      text_a = convert_to_unicode(line['sentence1'])
      text_b = convert_to_unicode(line['sentence2'])
      label = convert_to_unicode(line['label']) if set_type != 'test' else '0'
      examples.append(
          InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label))
    return examples


# class CslProcessor(DataProcessor):
#     """Processor for the CSL data set."""
#
#     def get_train_examples(self, data_dir):
#         """See base class."""
#         return self._create_examples(
#             self._read_tsv(os.path.join(data_dir, "train.tsv")), "train")
#
#     def get_dev_examples(self, data_dir):
#         """See base class."""
#         return self._create_examples(
#             self._read_tsv(os.path.join(data_dir, "dev.tsv")), "dev")
#
#     def get_test_examples(self, data_dir):
#         """See base class."""
#         return self._create_examples(
#             self._read_tsv(os.path.join(data_dir, "test.tsv")), "test")
#
#     def _create_examples(self, lines, set_type):
#         """Creates examples for the training and dev sets."""
#         examples = []
#         seq_length=FLAGS.max_seq_length
#         for (i, line) in enumerate(lines):
#             if i == 0:
#                 continue
#             guid = "%s-%s" % (set_type, i)
#             abst = convert_to_unicode(line[0])
#             keyword = convert_to_unicode(line[1])
#             label = convert_to_unicode(line[2])
#             if (len(abst) + len(keyword)) >  seq_length:
#                 abst = abst[:seq_length - len(keyword)]
#             examples.append(
#                 InputExample(guid=guid, text_a=abst, text_b=keyword, label=label))
#         return examples
#
#     def get_labels(self):
#         """See base class."""
#         return ["0", "1"]


# class InewsProcessor(DataProcessor):
#   """Processor for the MRPC data set (GLUE version)."""
#
#   def get_train_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_txt(os.path.join(data_dir, "train.txt")), "train")
#
#   def get_dev_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_txt(os.path.join(data_dir, "dev.txt")), "dev")
#
#   def get_test_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_txt(os.path.join(data_dir, "test.txt")), "test")
#
#   def get_labels(self):
#     """See base class."""
#     labels = ["0", "1", "2"]
#     return labels
#
#   def _create_examples(self, lines, set_type):
#     """Creates examples for the training and dev sets."""
#     examples = []
#     for (i, line) in enumerate(lines):
#       if i == 0:
#         continue
#       guid = "%s-%s" % (set_type, i)
#       text_a = convert_to_unicode(line[2])
#       text_b = convert_to_unicode(line[3])
#       label = convert_to_unicode(line[0]) if set_type != "test" else '0'
#       examples.append(
#           InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label))
#     return examples
#
#
# class THUCNewsProcessor(DataProcessor):
#   """Processor for the THUCNews data set (GLUE version)."""
#
#   def get_train_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_txt(os.path.join(data_dir, "train.txt")), "train")
#
#   def get_dev_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_txt(os.path.join(data_dir, "dev.txt")), "dev")
#
#   def get_test_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_txt(os.path.join(data_dir, "test.txt")), "test")
#
#   def get_labels(self):
#     """See base class."""
#     labels = []
#     for i in range(14):
#       labels.append(str(i))
#     return labels
#
#   def _create_examples(self, lines, set_type):
#     """Creates examples for the training and dev sets."""
#     examples = []
#     for (i, line) in enumerate(lines):
#       if i == 0 or len(line) < 3:
#         continue
#       guid = "%s-%s" % (set_type, i)
#       text_a = convert_to_unicode(line[3])
#       text_b = None
#       label = convert_to_unicode(line[0])
#       examples.append(
#           InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label))
#     return examples
#
# class LCQMCProcessor(DataProcessor):
#   """Processor for the internal data set. sentence pair classification"""
#
#   def __init__(self):
#     self.language = "zh"
#
#   def get_train_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "train.txt")), "train")
#     # dev_0827.tsv
#
#   def get_dev_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "dev.txt")), "dev")
#
#   def get_test_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "test.txt")), "test")
#
#   def get_labels(self):
#     """See base class."""
#     return ["0", "1"]
#     # return ["-1","0", "1"]
#
#   def _create_examples(self, lines, set_type):
#     """Creates examples for the training and dev sets."""
#     examples = []
#     print("length of lines:", len(lines))
#     for (i, line) in enumerate(lines):
#       # print('#i:',i,line)
#       if i == 0:
#         continue
#       guid = "%s-%s" % (set_type, i)
#       try:
#         label = convert_to_unicode(line[2])
#         text_a = convert_to_unicode(line[0])
#         text_b = convert_to_unicode(line[1])
#         examples.append(
#             InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label))
#       except Exception:
#         print('###error.i:', i, line)
#     return examples
#
#
# class JDCOMMENTProcessor(DataProcessor):
#   """Processor for the internal data set. sentence pair classification"""
#
#   def __init__(self):
#     self.language = "zh"
#
#   def get_train_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "jd_train.csv"), ",", "\""), "train")
#     # dev_0827.tsv
#
#   def get_dev_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "jd_dev.csv"), ",", "\""), "dev")
#
#   def get_test_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "jd_test.csv"), ",", "\""), "test")
#
#   def get_labels(self):
#     """See base class."""
#     return ["1", "2", "3", "4", "5"]
#     # return ["-1","0", "1"]
#
#   def _create_examples(self, lines, set_type):
#     """Creates examples for the training and dev sets."""
#     examples = []
#     print("length of lines:", len(lines))
#     for (i, line) in enumerate(lines):
#       # print('#i:',i,line)
#       if i == 0:
#         continue
#       guid = "%s-%s" % (set_type, i)
#       try:
#         label = convert_to_unicode(line[0])
#         text_a = convert_to_unicode(line[1])
#         text_b = convert_to_unicode(line[2])
#         examples.append(
#             InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label))
#       except Exception:
#         print('###error.i:', i, line)
#     return examples
#
#
# class BQProcessor(DataProcessor):
#   """Processor for the internal data set. sentence pair classification"""
#
#   def __init__(self):
#     self.language = "zh"
#
#   def get_train_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "train.txt")), "train")
#     # dev_0827.tsv
#
#   def get_dev_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "dev.txt")), "dev")
#
#   def get_test_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "test.txt")), "test")
#
#   def get_labels(self):
#     """See base class."""
#     return ["0", "1"]
#     # return ["-1","0", "1"]
#
#   def _create_examples(self, lines, set_type):
#     """Creates examples for the training and dev sets."""
#     examples = []
#     print("length of lines:", len(lines))
#     for (i, line) in enumerate(lines):
#       # print('#i:',i,line)
#       if i == 0:
#         continue
#       guid = "%s-%s" % (set_type, i)
#       try:
#         label = convert_to_unicode(line[2])
#         text_a = convert_to_unicode(line[0])
#         text_b = convert_to_unicode(line[1])
#         examples.append(
#             InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label))
#       except Exception:
#         print('###error.i:', i, line)
#     return examples
#
#
# class MnliProcessor(DataProcessor):
#   """Processor for the MultiNLI data set (GLUE version)."""
#
#   def get_train_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "train.tsv")), "train")
#
#   def get_dev_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "dev_matched.tsv")),
#         "dev_matched")
#
#   def get_test_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "test_matched.tsv")), "test")
#
#   def get_labels(self):
#     """See base class."""
#     return ["contradiction", "entailment", "neutral"]
#
#   def _create_examples(self, lines, set_type):
#     """Creates examples for the training and dev sets."""
#     examples = []
#     for (i, line) in enumerate(lines):
#       if i == 0:
#         continue
#       guid = "%s-%s" % (set_type, convert_to_unicode(line[0]))
#       text_a = convert_to_unicode(line[8])
#       text_b = convert_to_unicode(line[9])
#       if set_type == "test":
#         label = "contradiction"
#       else:
#         label = convert_to_unicode(line[-1])
#       examples.append(
#           InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label))
#     return examples
#
#
# class MrpcProcessor(DataProcessor):
#   """Processor for the MRPC data set (GLUE version)."""
#
#   def get_train_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "train.tsv")), "train")
#
#   def get_dev_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "dev.tsv")), "dev")
#
#   def get_test_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "test.tsv")), "test")
#
#   def get_labels(self):
#     """See base class."""
#     return ["0", "1"]
#
#   def _create_examples(self, lines, set_type):
#     """Creates examples for the training and dev sets."""
#     examples = []
#     for (i, line) in enumerate(lines):
#       if i == 0:
#         continue
#       guid = "%s-%s" % (set_type, i)
#       text_a = convert_to_unicode(line[3])
#       text_b = convert_to_unicode(line[4])
#       if set_type == "test":
#         label = "0"
#       else:
#         label = convert_to_unicode(line[0])
#       examples.append(
#           InputExample(guid=guid, text_a=text_a, text_b=text_b, label=label))
#     return examples
#
#
# class ColaProcessor(DataProcessor):
#   """Processor for the CoLA data set (GLUE version)."""
#
#   def get_train_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "train.tsv")), "train")
#
#   def get_dev_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "dev.tsv")), "dev")
#
#   def get_test_examples(self, data_dir):
#     """See base class."""
#     return self._create_examples(
#         self._read_tsv(os.path.join(data_dir, "test.tsv")), "test")
#
#   def get_labels(self):
#     """See base class."""
#     return ["0", "1"]
#
#   def _create_examples(self, lines, set_type):
#     """Creates examples for the training and dev sets."""
#     examples = []
#     for (i, line) in enumerate(lines):
#       # Only the test set has a header
#       if set_type == "test" and i == 0:
#         continue
#       guid = "%s-%s" % (set_type, i)
#       if set_type == "test":
#         text_a = convert_to_unicode(line[1])
#         label = "0"
#       else:
#         text_a = convert_to_unicode(line[3])
#         label = convert_to_unicode(line[1])
#       examples.append(
#           InputExample(guid=guid, text_a=text_a, text_b=None, label=label))
#     return examples