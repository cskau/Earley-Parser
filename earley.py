#! /usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Clement Scheelfeldt Skau'
__date__ = '2012/01/15'
__version__ = '2012.01.22'
__status__ = 'Unstable'

''' Earley Parser
An implementation of the Earley Parser as described in [Jurafsky2000].
Top-down parser, using CFG-based production rules.

This code is marked 'unstable' since it is a quick-and-dirty implementation.
If you intend to use this in production, be sure to understand the limitations.

[Jurafsky2000] Jurafsky, Daniel & Martin, James H.:
Speech and Language Processing: An Introduction to Natural Language Processing,
  Computational Linguistics and Speech Recognition
(Prentice Hall Series in Artificial Intelligence)
Prentice Hall (2000)
'''


class State:
  dot = 0
  i, j = 0, 0
  left, right = '', []
  completed_by = []

  def __init__(self, left, right, dot, i, j, completed_by = []):
    self.left = left
    self.right = right
    self.dot = dot
    self.i = i
    self.j = j
    self.completed_by = completed_by
  
  def is_complete(self):
    return not self.dot < len(self.right) 
  
  def __eq__(self, other):
    return (
      self.left == other.left and
      self.right == other.right and
      self.dot == other.dot and
      self.i == other.i and
      self.j == other.j
    )
  
  def __repr__(self):
    return str(self)
  
  def __str__(self):
    return unicode(self).encode('unicode-escape')
  
  def __unicode__(self):
    right = self.right[:]
    right.insert(self.dot, u'.') # •
    cb = u''
    if self.completed_by:
      cb = u', %s' % unicode(self.completed_by)
    t = (self.left, u' '.join(right), self.i, self.j, cb)
    return (u'(%s -> %s, [%i, %i]%s)' % t) # →


class Earley:
  grammar = []
  words = []
  chart = []
  word_pos = {}

  def earley_parse(self, words, grammar):
    self.grammar = grammar
    self.words = words
    self.chart = [[] for i in range(len(self.words) + 1)]
    # Initial dummy state
    self.enqueue(State(u'', [u'S'], 0, 0, 0), 0)
    for i in range(len(self.words) + 1):
      for state in self.chart[i]:
        if not state.is_complete():
          if not self.next_cat_is_pos(state):
            self.predictor(state)
          else:
            self.scanner(state)
        else:
          self.completer(state)
    return self.chart

  def predictor(self, state):
    B = state.right[state.dot]
    j = state.j
    if B in self.grammar:
      for rule in self.grammar[B]:
        self.enqueue(State(B, rule, 0, j, j), j)

  def scanner(self, state):
    B = state.right[state.dot]
    j = state.j
    if j < len(self.words):
      word_i = self.words[j]
      if B in self.parts_of_speech(word_i):
        self.enqueue(State(B, [word_i], 1, j, (j + 1)), (j + 1))

  def completer(self, state):
    B = state.left
    j, k = state.i, state.j
    for old_state in self.chart[j]:
      dot = old_state.dot
      if not old_state.is_complete() and old_state.right[dot] == B:
        i = old_state.i
        A = old_state.left
        cb = old_state.completed_by[:]
        self.enqueue(State(A, old_state.right, (dot + 1), i, k, cb), k, state)

  def enqueue(self, state, chart_entry, completed_by = None):
    if not state in self.chart[chart_entry]:
      self.chart[chart_entry].append(state)
    if not completed_by is None and not completed_by in state.completed_by:
      state.completed_by.append(completed_by)

  # Since this is implicit from the grammar we have to be careful.
  # If the grammar is incomplete, POS part might not be recognized.
  def next_cat_is_pos(self, state):
    next_word = state.right[state.dot]
    # Terminal ?
    if (not next_word in self.grammar and
        not next_word.lower() in self.grammar):
      return False
    # Produces terminal ?
    return not self.grammar[next_word][0][0] in self.grammar

  # This is also not very robust.
  def parts_of_speech(self, word):
    if not self.word_pos:
      for l in self.grammar.keys():
        r = self.grammar[l]
        for alts in r:
          for w in alts:
            if not w in self.grammar:
              if not w in self.word_pos:
                self.word_pos[w.lower()] = []
              self.word_pos[w.lower()].append(l)
    return self.word_pos[word.lower()]


 ################################### Tests ###################################

import unittest

class Earley_Unittests(unittest.TestCase):

  grammar = {
    'S': [['VP'], ['NP']],
    'VP': [['Verb']],
    'NP': [['Det', 'Nominal'], ['Proper-Noun'], ['Noun']],
    'Nominal': [['Noun'], ['Noun', 'Nominal']],
    'Det': [['that'], ['this'], ['a']],
    'Proper-Noun': [['Batman']],
    'Noun': [['book'], ['flight'], ['banana'], ['meal'], ['factory']],
    'Verb': [['book']],
  }

  def setUp(self):
    self.earley = Earley()

  def test_chart(self):
    words = []
    grammar = {}
    chart = self.earley.earley_parse(words, grammar)
    self.assertEquals(len(chart), 1)
    words = ['A', 'monkey', 'in', 'a', 'banana', 'factory']
    chart = Earley().earley_parse(words, grammar)
    self.assertEquals(len(chart), 7)
    self.assertIn(State(u'', [u'S'], 0, 0, 0), chart[0])
  
  def test_banana(self):
    words = ['Banana']
    grammar = self.grammar
    chart = self.earley.earley_parse(words, grammar)
    self.assertIn(State(u'S', [u'NP'], 0, 0, 0), chart[0])
    self.assertIn(State(u'NP', [u'Noun'], 0, 0, 0), chart[0])
    self.assertIn(State(u'Noun', [u'Banana'], 1, 0, 1), chart[1])
    self.assertIn(State(u'S', [u'NP'], 1, 0, 1), chart[1])
  
  def test_banana_factory(self):
    words = ['A', 'banana', 'factory']
    grammar = self.grammar
    chart = self.earley.earley_parse(words, grammar)
    self.assertIn(State(u'S', [u'NP'], 0, 0, 0), chart[0])
    self.assertIn(State(u'NP', [u'Det', u'Nominal'], 0, 0, 0), chart[0])
    self.assertIn(State(u'Det', [u'A'], 1, 0, 1), chart[1])
    self.assertIn(State(u'Nominal', ['Noun', 'Nominal'], 1, 1, 2), chart[2])
    self.assertIn(State(u'S', [u'NP'], 1, 0, 3), chart[3])


 #################################### main #################################### 

# very naive implementation..
# Convert tree to graphviz-dot digraph format.
def digraph(state, words, rank = []):
  content = u'%s [label="%s"]\n' % (id(state), state.left)
  for s in state.completed_by:
    content += u'%s -> %s\n' % (id(state), id(s))
    content += digraph(s, words)
  if not state.completed_by:
    rank += [state]
  if state.left == u'S':
    for s in rank:
      if s.i < len(words):
        content += u'%s [label="%s"]\n' % (id(words[s.i]), words[s.i])
        content += u'%s -> %s\n' % (id(s), id(words[s.i]))
    content += u'{rank=same;%s}\n' % u' '.join([unicode(id(words[s.i])) for s in rank if s.i < len(words)])
    return u'digraph g {node [shape=plaintext];\n%s}' % content
  return u'%s' % content


if __name__ == u'__main__':
  import sys
  import json
  import codecs

  if '--test' in sys.argv[1:]:
    sys.argv = [ a for a in sys.argv if a != '--test' ]
    suite = unittest.TestLoader().loadTestsFromTestCase(
        Earley_Unittests)
    unittest.TextTestRunner(verbosity=2).run(suite)
    exit(0)
  
  if len(sys.argv) < 3:
    print u'Requires input on the form:'
    print u'earley.py grammar.json "your sentence"'
    exit(1)

  # Assume input is UTF-8, convert to internal Unicode
  grammar_file = codecs.open(sys.argv[1], 'r', 'utf-8')
  words = unicode(sys.argv[2], u'utf-8').split(u' ')
  grammar = json.load(grammar_file)
  
  chart = Earley().earley_parse(words, grammar)

  parsed = [s for s in chart[-1] if s.left == u'S']
  for p in parsed:
    print unicode(digraph(p, words)).encode('utf-8')
