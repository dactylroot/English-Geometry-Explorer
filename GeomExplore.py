#! /usr/bin/env python
""" Use suffix tries to generate English-language analogues of x86-64 
    byteword geometry. Illustrates the way a processor (human)
    parses (reads) instructions (words) from bytecode (alphabet strings).
    
    Using a dictionary of newline-separated words, return the longest string
    of geometrically-overlapping sequences.
    Each sequence may not be distinct (possibly ambiguous word endings.)

    If a dictionary takes too long, try checking for a higher number of
    sequences. This reduces the search space.
"""
"""
    Some example results:
            from test dictionary, [tuvwxyz].* words from "american-english":
            videotapewormwoodwindupswingtiptoeing
            '________'_______'______'______'_____
            _____'_______'_______'______'________

            from dictionary "american-english", 72874 words:
            minamotocrossoverhang
            '_______'________'___
            ____'________'_______
            walleyetheaddress
            _____'__'___'____
            '______'__'______
            wavervetheaddress
            '____'__'___'____
            __'____'__'______
            woodwormwoodwindyupswing
            '_______'_______'___'___
            ____'_______'____'______

            madagascarablesternestores
            ______'_____'_____'_____'_
            ________'_____'_____'_____
            '_________'_____'_____'___

            from dictionary "american-english-insane", 484936 words:
            rethreshelver
            ____'_______'
            ______'______
            '_______'____
            __'_______'__
            coapprenticement
            '___________'___
            __'_____________
            ______'_________
            ________'_______
            __________'_____
            interindividually
            '______________'_
            _____'___________
            _______'_________
            _________'_______
            ___________'_____
            _____________'___
            noncorroborating
            ______________'_
            '_______________
            ___'____________
            ______'_________
            ________'_______
            __________'_____
            ____________'___
"""

import re

# Single-character marker
_MARKER = '\''
#_LEVEL_LIMIT = 25
_nseqs = 2
_wordset = None
#_pretrie = None
_postrie = None

def main():
    desc = \
    parser = argparse.ArgumentParser(
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description=\
     'Using a dictionary of newline-separated words, return \n'\
    +'the longest string of geometrically-overlapping sequences.\n'\
    +'Each sequence is distinct (no ambiguous or overlapping words.)',
                epilog='If a dictionary takes too long, try checking for '\
                      +'a higher number of sequences.')
    parser.add_argument('dict' ,nargs='?',default='american-english',
                                help='the dictionary to analyse')
    parser.add_argument('nseqs',nargs='?',default=2, type=int,
                                help='number of overlapping sequences to find')
    args = parser.parse_args()

    print('building word set and trie')
    get_words(args.dict)
    print('searching sequences')
    leaf = find_longest(args.nseqs)
    print('\n'+walk_results(leaf))

def set_nseqs(n):
    global _nseqs
    _nseqs = n

def get_words(txtfile):

    """ Parse txtfile, return [set,pre,post]

        set      = set of words
        pre,post = pre- and post-fix tries.

        Filter out empty strings, single-character words, and words with
        non-alphabet characters. """

    global _wordset
    global _postrie

    f = open(txtfile,'r')
    _wordset = set([x.lower() for x in set(f.read().split()) \
                             if not re.match('.*[\W,\d]|^.$',x)])

    #print('building suffix trie')
    _postrie = trienode(pre = False)
    _postrie.grow(_wordset)

    # Since this will be recursed through later, take care of it now.
    if len(_wordset) > sys.getrecursionlimit():
        sys.setrecursionlimit(len(_wordset))

def gen_alphabet():
    """ Generator for alphabet characters. """
    for x in list(xrange(ord('a'),ord('z')+1)):
        yield chr(x)

class trienode:
    """ Nodes for prefix and postfix tries. 'exists' flag denotes if complete word terminates with it. """
    def __init__(self, pre = True, exists = True):
        self.branches = {}
        self.exists = exists
        self.pre = pre

    def add_branch(self, char, pre, exists = True):
        self.branches[char] = trienode(pre, exists)

    def grow(self, wordset):
        self.branches.clear()

        if self.pre:
            def sub_set(s,p):
                return set([x[1:] for x in s if x and x[0] == p])
                # re.match('^'+p+'.*',x)
        else:
            def sub_set(s,p):
                return set([x[:-1] for x in s if x and x[-1] == p])

        for letter in gen_alphabet():
            p = sub_set(wordset,letter)
            if p:
                # '' in p means the set contained a word which has been spelled
                self.add_branch(letter,self.pre,'' in p)
                self.branches[letter].grow(p)

    def check(self,word):
        """ If word is reachable from this node, return resulting node. """
        if self.pre:
            def sub_word(chars):
                if re.match('^'+chars+'.*',word):
                    return word[len(chars):]
                else:
                    return None
        else:
            def sub_word(chars):
                if re.match('^.*'+chars+'$',word):
                    return word[:-len(chars)]
                else:
                    return None

        if word == '':
            return self
        for chars in self.branches.keys():
            res =  sub_word(chars)
            if res:
                return self.branches[chars].check(res)
            elif res == '':
                return self.branches[chars]
        return None

    def get_words(self, chars = None):
        """ Return all existing words derived from this node, with prefix chars.
        """
        if not self.branches.keys():
            return ['']

        if self.pre:
            def apre(word,letter):
                return letter + word
        else:
            def apre(word,letter):
                return word + letter

        if chars:
            sub = self.check(chars)
            if sub:
                return [apre(x,chars) for x in sub.get_words()]
            else:
                return []

        # If this node marks an existing word, pass back empty string to parent
        # nodes to rebuild this word separately from any derived compound words
        if self.exists:
            selfwordmarker = ['']
        else:
            selfwordmarker = []

        return  [word for sublist in \
                   [[apre(word,key) for word in self.branches[key].get_words()]\
                   for key in self.branches.keys()]\
                for word in sublist] + selfwordmarker

    def __repr__(self):
        if self.exists:
            xst = 'Is a word.  '
        else:
            xst = 'Non-word. '
        if self.pre:
            cpnd= 'Put at the end to build: '
        else:
            cpnd= 'Put in front to build: '
        return xst+'\n'+cpnd+str(self.branches.keys())

def find_longest(nseqs = None):
    """
        Find the longest string of geometrically overlapping sequences of words.
            words   = a list of lower-case strings
            nseqs   = number of overlapping sequences desired.

        Return [string, markers]

            string  = the string itself
            markers = for each sequence, string of potential start locations

        The following constraints are used for performance:
            No string of length 1 is considered.

        The sequences follows the constraints of assembly language:
            Termination on a given marker (final node, ret)
            TODO: (can build prefix trie)
            No ambiguous (words, instructions) from a given start position

        As well as the following freedom:
            A sequence doesn't have to start at the beginning of the string.

        This is comparable to finding the longest path within a tree.
        The branching function determines how many sequences exist in the
        resulting string.
        For each new node, a search must be done for a word that ends in the
        same characters contained in the (n-1) parent nodes,
        where n is the total number of sequences.

            nseqs = 2:

            minamotocrossoverhang
            '_______'________'___
            ____'________'_______

        Markers mark the start of a node. Their line indicates sequence.
        The above would be represented by a path of 5 nodes.

    """
    if nseqs:
        set_nseqs(nseqs)

    # If nseqs == 1, the function would return all the words of the dict.
    if _nseqs == 1:
        return node(_wordset.pop(),None)

    global COUNT
    def reset_grow(node):
        COUNT = 0
        return grow(node)

    #leaves = [reset_grow(node(word,None)) for word in _wordset]
    #return max(leaves)
    maxleaf = node('',None)
    for word in _wordset:
        # This print statement is best indicator of inf loop or wasting time
        print('checking root: '+word)
        maxleaf = max([maxleaf, grow(node(word,None))])

    return maxleaf

COUNT = 0
#outfile = open('dbg','w')
def grow(root, nseqs = None):
    """ Recursively find children for the given tree.
        Return first leaf node from level 'length' or the deepest level. """
    if nseqs:
        set_nseqs(nseqs)

    # Limit is number of additional nodes' characters to restrict suffix to
    # total nodes for a word is _nseqs, but two of these are already supplied
    # by the root node and the node found by this iteration
    lim = min(root.lvl,_nseqs-2)
    current = root
    tail = current.newchars
    for i in xrange(lim):
        current = current.parent
        tail += current.newchars

    global COUNT
    buf = ''.join([' ' for x in xrange(COUNT)])
    COUNT += 1
    #print(buf+ tail + ' , '+str(root.lvl));

    # TODO  Allow multiple words intra-segment.
    #       The same node can represent multiple words in its mrkchars
    # TODO  Disallow alternate words starting at a node
    #       Until fixed, this allows ambiguities between segments.
    # Exclude words already used by next segment
    usedwords = set()
    if current.parent:
        usedwords = current.parent.wordset
    wordpool = set(_postrie.get_words(tail)) - usedwords

    # Empty strings that get through here cause infinite loop
    heads = [x[:-len(tail)] for x in wordpool if len(x)-1 > len(tail)]
    #print('heads: '+ str(heads)); return

    newnodes = [node(newchars,root) for newchars in heads if newchars]
    #print('new nodes: '+str(newnodes)); return newnodes

    leaves = [grow(n) for n in newnodes]
    COUNT += -1
    if leaves:
        return max(leaves)
    else:
        return root

def walk_results(leaf):

    """
        Reconstruct complete string starting at the given leaf node.

        Return [string] + markers, separated by newline characters
        string  = complete string
        markers = list of sequence markers,
                  a list of indices of word positions for each sequence
    """

    def zip_and_line(x):
        return '\n'.join([''.join(y) for y in zip(*x)])

    chars = [[n.newchars] + [n.mrkchars if not (n.lvl+s) % _nseqs \
                        else n.blkchars \
                    for s in xrange(_nseqs)] for n in leaf.walk()]

    return zip_and_line(chars)

def pr(leaf):
    print(walk_results(leaf))

class node:

    """
        node object to keep track of potential strings and sequences.

        Each node has a sequence of letters that form a complete word
        when n parent nodes' letters are appended.

        Sequences can be reconstructed from a tree by choosing a start node,
        then combining node tuples into words until the root is reached.
    """

    def __init__(self,newchars,parent):
        if parent != None:
            self.lvl = 1 + parent.lvl
        else:
            self.lvl = 0
        self.newchars = newchars
        self.blkchars = ''.join(['_' for x in xrange(len(newchars))])
        self.mrkchars = _MARKER+self.blkchars[1:]
        self.parent = parent

        newword = newchars
        current = self
        if self.lvl < _nseqs:
            while current.parent:
                current = current.parent
                newword += current.newchars
        else:
            for x in xrange(1,_nseqs):
                current = current.parent
                newword += current.newchars
        # _next points to node with other words from this sequence
        if (self.lvl - current.lvl) == _nseqs - 1 and current.parent:
            self._next = current.parent
            supset = self._next.wordset
        else:
            self._next = None
            supset = set()
        self.current = current
        self.supset = supset
        self.wordset = set([newword]) | supset

    def walk(self):
        """ Generate sequence from this node to root. """
        current = self
        yield current
        while current.parent:
            current = current.parent
            yield current

    def __repr__(self):
        return 'Node: lvl='+str(self.lvl)+', \''+self.newchars+'\' wordset:'\
                       +str(self.wordset)

    def __lt__(self,other):
        """ Allows use of max() and min() on a list of nodes. """
        return self.lvl < other.lvl

def rebuild_words(node):
    """ Return list of words in sequence starting at given node. """
    wordlist = []
    ncount = 1
    string = node.newchars
    current = node
    while current.parent:
        ncount += 1
        current = current.parent
        string += current.newchars
        if not ncount % _nseqs:
            wordlist.append(string)
            string = ''
    if ncount % _nseqs:
        wordlist.append(string)
    return wordlist

#if __name__ != '__main__':
if False:
    import sys
    n0 = node('',None)
    n1 = node('dress',n0)
    n2 = node('ad',n1)
    n3 = node('he',n2)
    n4 = node('hot',n3)
    n5 = node('no',n4)

    l = [n1,n2,n3,n4,n5]

    get_words('eng05')

if __name__ == '__main__':
    import sys
    import argparse
    main()
