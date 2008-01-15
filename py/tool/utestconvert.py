import re
import sys
import parser

d={}
#  d is the dictionary of unittest changes, keyed to the old name
#  used by unittest.
#  d[old][0] is the new replacement function.
#  d[old][1] is the operator you will substitute, or '' if there is none.
#  d[old][2] is the possible number of arguments to the unittest
#  function.

# Old Unittest Name             new name         operator  # of args
d['assertRaises']           = ('raises',               '', ['Any'])
d['fail']                   = ('raise AssertionError', '', [0,1])
d['assert_']                = ('assert',               '', [1,2])
d['failIf']                 = ('assert not',           '', [1,2])
d['assertEqual']            = ('assert',            ' ==', [2,3])
d['failIfEqual']            = ('assert not',        ' ==', [2,3])
d['assertIn']               = ('assert',            ' in', [2,3])
d['assertNotIn']            = ('assert',            ' not in', [2,3])
d['assertNotEqual']         = ('assert',            ' !=', [2,3])
d['failUnlessEqual']        = ('assert',            ' ==', [2,3])
d['assertAlmostEqual']      = ('assert round',      ' ==', [2,3,4])
d['failIfAlmostEqual']      = ('assert not round',  ' ==', [2,3,4])
d['assertNotAlmostEqual']   = ('assert round',      ' !=', [2,3,4])
d['failUnlessAlmostEquals'] = ('assert round',      ' ==', [2,3,4])

#  the list of synonyms
d['failUnlessRaises']      = d['assertRaises']
d['failUnless']            = d['assert_']
d['assertEquals']          = d['assertEqual']
d['assertNotEquals']       = d['assertNotEqual']
d['assertAlmostEquals']    = d['assertAlmostEqual']
d['assertNotAlmostEquals'] = d['assertNotAlmostEqual']

# set up the regular expressions we will need
leading_spaces = re.compile(r'^(\s*)') # this never fails

pat = ''
for k in d.keys():  # this complicated pattern to match all unittests
    pat += '|' + r'^(\s*)' + 'self.' + k + r'\(' # \tself.whatever(

old_names = re.compile(pat[1:])
linesep='\n'        # nobody will really try to convert files not read
                    # in text mode, will they?


def blocksplitter(fp):
    '''split a file into blocks that are headed by functions to rename'''

    blocklist = []
    blockstring = ''

    for line in fp:
        interesting = old_names.match(line)
        if interesting :
            if blockstring:
                blocklist.append(blockstring)
                blockstring = line # reset the block
        else:
            blockstring += line
            
    blocklist.append(blockstring)
    return blocklist

def rewrite_utest(block):
    '''rewrite every block to use the new utest functions'''

    '''returns the rewritten unittest, unless it ran into problems,
       in which case it just returns the block unchanged.
    '''
    utest = old_names.match(block)

    if not utest:
        return block

    old = utest.group(0).lstrip()[5:-1] # the name we want to replace
    new = d[old][0] # the name of the replacement function
    op  = d[old][1] # the operator you will use , or '' if there is none.
    possible_args = d[old][2]  # a list of the number of arguments the
                               # unittest function could possibly take.
                
    if possible_args == ['Any']: # just rename assertRaises & friends
        return re.sub('self.'+old, new, block)

    message_pos = possible_args[-1]
    # the remaining unittests can have an optional message to print
    # when they fail.  It is always the last argument to the function.

    try:
        indent, argl, trailer = decompose_unittest(old, block)

    except SyntaxError: # but we couldn't parse it!
        return block
    
    argnum = len(argl)
    if argnum not in possible_args:
        # sanity check - this one isn't real either
        return block

    elif argnum == message_pos:
        message = argl[-1]
        argl = argl[:-1]
    else:
        message = None

    if argnum is 0 or (argnum is 1 and argnum is message_pos): #unittest fail()
        string = ''
        if message:
            message = ' ' + message

    elif message_pos is 4:  # assertAlmostEqual & friends
        try:
            pos = argl[2].lstrip()
        except IndexError:
            pos = '7' # default if none is specified
        string = '(%s -%s, %s)%s 0' % (argl[0], argl[1], pos, op )

    else: # assert_, assertEquals and all the rest
        string = ' ' + op.join(argl)

    if message:
        string = string + ',' + message

    return indent + new + string + trailer

def decompose_unittest(old, block):
    '''decompose the block into its component parts'''

    ''' returns indent, arglist, trailer 
        indent -- the indentation
        arglist -- the arguments to the unittest function
        trailer -- any extra junk after the closing paren, such as #commment
    '''
 
    indent = re.match(r'(\s*)', block).group()
    pat = re.search('self.' + old + r'\(', block)

    args, trailer = get_expr(block[pat.end():], ')')
    arglist = break_args(args, [])

    if arglist == ['']: # there weren't any
        return indent, [], trailer

    for i in range(len(arglist)):
        try:
            parser.expr(arglist[i].lstrip('\t '))
        except SyntaxError:
            if i == 0:
                arglist[i] = '(' + arglist[i] + ')'
            else:
                arglist[i] = ' (' + arglist[i] + ')'

    return indent, arglist, trailer

def break_args(args, arglist):
    '''recursively break a string into a list of arguments'''
    try:
        first, rest = get_expr(args, ',')
        if not rest:
            return arglist + [first]
        else:
            return [first] + break_args(rest, arglist)
    except SyntaxError:
        return arglist + [args]

def get_expr(s, char):
    '''split a string into an expression, and the rest of the string'''

    pos=[]
    for i in range(len(s)):
        if s[i] == char:
            pos.append(i)
    if pos == []:
        raise SyntaxError # we didn't find the expected char.  Ick.
     
    for p in pos:
        # make the python parser do the hard work of deciding which comma
        # splits the string into two expressions
        try:
            parser.expr('(' + s[:p] + ')')
            return s[:p], s[p+1:]
        except SyntaxError: # It's not an expression yet
            pass
    raise SyntaxError       # We never found anything that worked.

if __name__ == '__main__':

    import sys
    import py

    usage = "usage: %prog [-s [filename ...] | [-i | -c filename ...]]"
    optparser = py.compat.optparse.OptionParser(usage)

    def select_output (option, opt, value, optparser, **kw):
        if hasattr(optparser, 'output'):
            optparser.error(
                'Cannot combine -s -i and -c options. Use one only.')
        else:
            optparser.output = kw['output']

    optparser.add_option("-s", "--stdout", action="callback",
                         callback=select_output,
                         callback_kwargs={'output':'stdout'},
                         help="send your output to stdout")

    optparser.add_option("-i", "--inplace", action="callback",
                         callback=select_output,
                         callback_kwargs={'output':'inplace'},
                         help="overwrite files in place")

    optparser.add_option("-c", "--copy", action="callback",
                         callback=select_output,
                         callback_kwargs={'output':'copy'},
                         help="copy files ... fn.py --> fn_cp.py")

    options, args = optparser.parse_args()

    output = getattr(optparser, 'output', 'stdout')

    if output in ['inplace', 'copy'] and not args:
        optparser.error(
                '-i and -c option  require at least one filename')

    if not args:
        s = ''
        for block in blocksplitter(sys.stdin):
            s += rewrite_utest(block)
        sys.stdout.write(s)

    else:
        for infilename in args: # no error checking to see if we can open, etc.
            infile = file(infilename)
            s = ''
            for block in blocksplitter(infile):
                s += rewrite_utest(block)
            if output == 'inplace':
                outfile = file(infilename, 'w+')
            elif output == 'copy': # yes, just go clobber any existing .cp
                outfile = file (infilename[:-3]+ '_cp.py', 'w+')
            else:
                outfile = sys.stdout

            outfile.write(s)

    
