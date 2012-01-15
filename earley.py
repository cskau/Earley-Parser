#! /usr/bin/env python
# coding: UTF-8

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
  
  def __repr__(self):
    right = self.right[:]
    right.insert(self.dot, '•')
    if self.completed_by:
      t = (self.left, ' '.join(right), self.i, self.j, self.completed_by)
      return '(%s → %s, [%i, %i], %s)' % t
    t = (self.left, ' '.join(right), self.i, self.j)
    return '(%s → %s, [%i, %i])' % t
  
  def __eq__(self, other):
    return (
      self.left == other.left and
      self.right == other.right and
      self.dot == other.dot and
      self.i == other.i and
      self.j == other.j
    )


class Earley:
  grammar = []
  words = []
  chart = []
  word_pos = {}

  def earley_parse(self, words, grammar):
    self.grammar = grammar
    self.words = words
    self.chart = [[] for i in range(len(self.words) + 1)]
    # dummy state
    self.enqueue(State('', ['S'], 0, 0, 0), 0)
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

  def next_cat_is_pos(self, state):
    word = state.right[state.dot]
    if not word in self.grammar and not word.lower() in self.grammar:
      return False
    return not self.grammar[word][0][0] in self.grammar

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


'''
From Jurafsky, Martin p. 360:
S -> NP VP
S -> Aux NP VP
S -> VP
NP -> Det Nominal
Nominal -> Noun
Nominal -> Noun Nominal
NP -> Proper-Noun
VP -> Verb
VP -> Verb NP
Det -> that | this | a
Noun -> book | flight | ..
Verb -> book | include | prefer
Aux -> does
Prep -> from | to | on
Proper-Noun -> Houston | TWA
Nominal -> Nominal PP
'''

grammar = {
  'S': [['NP', 'VP'], ['Aux', 'NP', 'VP'], ['VP']],
  'NP': [['Det', 'Nominal'], ['Proper-Noun']],
  'Nominal': [['Noun'], ['Noun', 'Nominal'], ['Nominal', 'PP']],
  'VP': [['Verb'], ['Verb', 'NP']],
  'Det': [['that'], ['this'], ['a']],
  'Noun': [['book'], ['flight'], ['meal'], ['money']],
  'Verb': [['book'], ['include'], ['prefer']],
  'Aux': [['does']],
  'Prep': [['from'], ['to'], ['on']],
  'Proper-Noun': [['Houston'], ['TWA']],
}


def digraph(state, words, rank = []):
  content = ''
  for s in state.completed_by:
    content += '%s -> %s\n' % (state.left, s.left)
    content += digraph(s, words)
  if not state.completed_by:
    rank += [(state.left, words[state.i])]
  if state.left == 'S':
    for s in rank:
      content += '%s -> %s\n' % s
    content += '{rank=same;%s}\n' % ' '.join([w for p, w in rank])
    return 'digraph g {node [shape=plaintext];\n%s}' % content
  return '%s' % content

if __name__ == '__main__':
  import sys
  
  words = sys.argv[1].split(' ')
  
  earley = Earley()
  chart = earley.earley_parse(words, grammar)

  parsed = [s for s in chart[-1] if s.left == 'S']
  for p in parsed:
    print digraph(p, words)