from py.__.tool.utestconvert import rewrite_utest

class Test_UTestConvert:
    def testall(self):
        assert rewrite_utest("badger badger badger") == (
                          "badger badger badger")

        assert rewrite_utest(
            "self.assertRaises(excClass, callableObj, *args, **kwargs)"
            ) == (
            "raises(excClass, callableObj, *args, **kwargs)"
                          )

        assert rewrite_utest(
            """
            self.failUnlessRaises(TypeError, func, 42, **{'arg1': 23})
            """
            ) == (
            """
            raises(TypeError, func, 42, **{'arg1': 23})
            """
                          )
        assert rewrite_utest(
            """
            self.assertRaises(TypeError,
                              func,
                              mushroom)
            """
            ) == (
            """
            raises(TypeError,
                              func,
                              mushroom)
            """
                          )
        assert rewrite_utest("self.fail()") == "raise AssertionError"
        assert rewrite_utest("self.fail('mushroom, mushroom')") == (
                          "raise AssertionError, 'mushroom, mushroom'")
        assert rewrite_utest("self.assert_(x)") == "assert x"
        assert rewrite_utest("self.failUnless(func(x)) # XXX") == (
                          "assert func(x) # XXX")
        
        assert rewrite_utest(
            """
            self.assert_(1 + f(y)
                         + z) # multiline, keep parentheses
            """
            ) == (
            """
            assert (1 + f(y)
                         + z) # multiline, keep parentheses
            """
                          )

        assert rewrite_utest("self.assert_(0, 'badger badger')") == (
                          "assert 0, 'badger badger'")

        assert rewrite_utest("self.assert_(0, '''badger badger''')") == (
                          "assert 0, '''badger badger'''")

        assert rewrite_utest(
            r"""
            self.assert_(0,
                 'Meet the badger.\n')
            """
            ) == (
            r"""
            assert 0, (
                 'Meet the badger.\n')
            """
                          )
        
        assert rewrite_utest(
            r"""
            self.failIf(0 + 0
                          + len('badger\n')
                          + 0, '''badger badger badger badger
                                 mushroom mushroom
                                 Snake!  Ooh a snake!
                              ''') # multiline, must move the parens
            """
            ) == (
            r"""
            assert not (0 + 0
                          + len('badger\n')
                          + 0), '''badger badger badger badger
                                 mushroom mushroom
                                 Snake!  Ooh a snake!
                              ''' # multiline, must move the parens
            """
                          )

        assert rewrite_utest("self.assertEquals(0, 0)") == (
                          "assert 0 == 0")
        
        assert rewrite_utest(
            r"""
            self.assertEquals(0,
                 'Run away from the snake.\n')
            """
            ) == (
            r"""
            assert 0 == (
                 'Run away from the snake.\n')
            """
                          )

        assert rewrite_utest(
            """
            self.assertEquals(badger + 0
                              + mushroom
                              + snake, 0)
            """
            ) == (
            """
            assert (badger + 0
                              + mushroom
                              + snake) == 0
            """
                          )
                            
        assert rewrite_utest(
            """
            self.assertNotEquals(badger + 0
                              + mushroom
                              + snake,
                              mushroom
                              - badger)
            """
            ) == (
            """
            assert (badger + 0
                              + mushroom
                              + snake) != (
                              mushroom
                              - badger)
            """
                          )

        assert rewrite_utest(
            """
            self.assertEquals(badger(),
                              mushroom()
                              + snake(mushroom)
                              - badger())
            """
            ) == (
            """
            assert badger() == (
                              mushroom()
                              + snake(mushroom)
                              - badger())
            """
                         )
        assert rewrite_utest("self.failIfEqual(0, 0)") == (
                          "assert not 0 == 0")

        assert rewrite_utest("self.failUnlessEqual(0, 0)") == (
                          "assert 0 == 0")

        assert rewrite_utest(
            """
            self.failUnlessEqual(mushroom()
                                 + mushroom()
                                 + mushroom(), '''badger badger badger
                                 badger badger badger badger
                                 badger badger badger badger
                                 ''') # multiline, must move the parens
            """
            ) == (
            """
            assert (mushroom()
                                 + mushroom()
                                 + mushroom()) == '''badger badger badger
                                 badger badger badger badger
                                 badger badger badger badger
                                 ''' # multiline, must move the parens
            """
                          )

                                   
        assert rewrite_utest(
            """
            self.assertEquals('''snake snake snake
                                 snake snake snake''', mushroom)
            """
            ) == (
            """
            assert '''snake snake snake
                                 snake snake snake''' == mushroom
            """
                          )
        
        assert rewrite_utest(
            """
            self.assertEquals(badger(),
                              snake(), 'BAD BADGER')
            """
            ) == (
            """
            assert badger() == (
                              snake()), 'BAD BADGER'
            """
                          )
        
        assert rewrite_utest(
            """
            self.assertNotEquals(badger(),
                              snake()+
                              snake(), 'POISONOUS MUSHROOM!\
                              Ai! I ate a POISONOUS MUSHROOM!!')
            """
            ) == (
            """
            assert badger() != (
                              snake()+
                              snake()), 'POISONOUS MUSHROOM!\
                              Ai! I ate a POISONOUS MUSHROOM!!'
            """
                          )

        assert rewrite_utest(
            """
            self.assertEquals(badger(),
                              snake(), '''BAD BADGER
                              BAD BADGER
                              BAD BADGER'''
                              )
            """
            ) == (
            """
            assert badger() == (
                              snake()), ( '''BAD BADGER
                              BAD BADGER
                              BAD BADGER'''
                              )
            """
                        )

        assert rewrite_utest(
            """
            self.assertEquals('''BAD BADGER
                              BAD BADGER
                              BAD BADGER''', '''BAD BADGER
                              BAD BADGER
                              BAD BADGER''')
            """
            ) == (
            """
            assert '''BAD BADGER
                              BAD BADGER
                              BAD BADGER''' == '''BAD BADGER
                              BAD BADGER
                              BAD BADGER'''
            """
                        )

        assert rewrite_utest(
            """
            self.assertEquals('''GOOD MUSHROOM
                              GOOD MUSHROOM
                              GOOD MUSHROOM''',
                              '''GOOD MUSHROOM
                              GOOD MUSHROOM
                              GOOD MUSHROOM''',
                              ''' FAILURE
                              FAILURE
                              FAILURE''')
            """
            ) == (
            """
            assert '''GOOD MUSHROOM
                              GOOD MUSHROOM
                              GOOD MUSHROOM''' == (
                              '''GOOD MUSHROOM
                              GOOD MUSHROOM
                              GOOD MUSHROOM'''), (
                              ''' FAILURE
                              FAILURE
                              FAILURE''')
            """
                        )

        assert rewrite_utest(
            """
            self.assertAlmostEquals(first, second, 5, 'A Snake!')
            """
            ) == (
            """
            assert round(first - second, 5) == 0, 'A Snake!'
            """
                          )

        assert rewrite_utest(
            """
            self.assertAlmostEquals(first, second, 120)
            """
            ) == (
            """
            assert round(first - second, 120) == 0
            """
                          )

        assert rewrite_utest(
            """
            self.assertAlmostEquals(first, second)
            """
            ) == (
            """
            assert round(first - second, 7) == 0
            """
                          )

        assert rewrite_utest(
            """
            self.assertAlmostEqual(first, second, 5, '''A Snake!
            Ohh A Snake!  A Snake!!
            ''')
            """
            ) == (
            """
            assert round(first - second, 5) == 0, '''A Snake!
            Ohh A Snake!  A Snake!!
            '''
            """
                          )

        assert rewrite_utest(
            """
            self.assertNotAlmostEqual(first, second, 5, 'A Snake!')
            """
            ) == (
            """
            assert round(first - second, 5) != 0, 'A Snake!'
            """
                          )

        assert rewrite_utest(
            """
            self.failIfAlmostEqual(first, second, 5, 'A Snake!')
            """
            ) == (
            """
            assert not round(first - second, 5) == 0, 'A Snake!'
            """
                          )

        assert rewrite_utest(
            """
            self.failIfAlmostEqual(first, second, 5, 6, 7, 'Too Many Args')
            """
            ) == (
            """
            self.failIfAlmostEqual(first, second, 5, 6, 7, 'Too Many Args')
            """
                          )

        assert rewrite_utest(
            """
            self.failUnlessAlmostEquals(first, second, 5, 'A Snake!')
            """
            ) == (
            """
            assert round(first - second, 5) == 0, 'A Snake!'
            """
                          )

        assert rewrite_utest(
            """
              self.assertAlmostEquals(now do something reasonable ..()
            oops, I am inside a comment as a ''' string, and the fname was
            mentioned in passing, leaving us with something that isn't an
            expression ... will this blow up?
            """
            ) == (
            """
              self.assertAlmostEquals(now do something reasonable ..()
            oops, I am inside a comment as a ''' string, and the fname was
            mentioned in passing, leaving us with something that isn't an
            expression ... will this blow up?
            """
                          )
        
        assert rewrite_utest(
            """
        self.failUnless('__builtin__' in modules, "An entry for __builtin__ "
                                                    "is not in sys.modules.")
            """
            ) == (
            """
        assert '__builtin__' in modules, ( "An entry for __builtin__ "
                                                    "is not in sys.modules.")
            """
                           )
        
        # two unittests on the same line separated by a semi-colon is
        # only half-converted.  Just so you know.
        assert rewrite_utest(
            """
            self.assertEquals(0, 0); self.assertEquals(1, 1) #not 2 per line!
            """
            ) == (
            """
            assert 0 == 0; self.assertEquals(1, 1) #not 2 per line!
            """
                           )
            
                              
if __name__ == '__main__':
    unittest.main()


