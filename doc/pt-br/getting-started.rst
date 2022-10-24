.. _get-started:

Comece aqui
===================================

.. _`getstarted`:
.. _`installation`:

Instale o ``pytest``
----------------------------------------

``pytest`` requer: Python 3.7+ or PyPy3.

1. Rode o seguinte comando no seu terminal de comandos:

.. code-block:: bash

    pip install -U pytest

2. Confirme que você instalou a versão correta:

.. code-block:: bash

    $ pytest --version
    pytest 7.1.3

.. _`simpletest`:

Crie seu primeiro teste
----------------------------------------------------------

Crie um novo arquivo chamado ``test_sample.py``, contendo uma função e um teste:

.. code-block:: python

    # conteudo de test_sample.py
    def func(x):
        return x + 1


    def test_answer():
        assert func(3) == 5

O teste

.. code-block:: pytest

    $ pytest
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-7.x.y, pluggy-1.x.y
    rootdir: /home/sweet/project
    collected 1 item

    test_sample.py F                                                     [100%]

    ================================= FAILURES =================================
    _______________________________ test_answer ________________________________

        def test_answer():
    >       assert func(3) == 5
    E       assert 4 == 5
    E        +  where 4 = func(3)

    test_sample.py:6: AssertionError
    ========================= short test summary info ==========================
    FAILED test_sample.py::test_answer - assert 4 == 5
    ============================ 1 failed in 0.12s =============================

O ``[100%]`` se refere ao progresso geral de rodar todos os casos de teste. Depois que ele termina, o pytest mostra um
relatório de falhas pois ``func(3)`` não retorna ``5``.

.. note::

    Você pode usar sentenças ``assert`` para verificar resultados esperados. A :ref:`Introspecçao avançada de asserções <python:assert>` do pytest
    irá inteligentemente reportar valores intermediários da expressão *assert* para que você possa evitar
    usar os vários nomes de :ref:`métodos legados do JUnit <testcase-objects>`.

Rode multiplos testes
----------------------------------------------------------

O ``pytest`` vai rodar todos os arquivos que seguirem o padrão test_*.py ou \*_test.py no diretório atual e em seus
subdiretórios. De maneira mais geral, ele segue as regras padrões de descoberta de testes.

..
   :ref:`regras padrões de descoberta de testes <test discovery>`


Verifique se uma exceção especifica é levantada
--------------------------------------------------------------

Use a expressão auxiliar raises para verificar que algum pedaço de código levanta uma exceção:

..
   :ref:`raises <assertraises>`

.. code-block:: python

    # conteude de test_sysexit.py
    import pytest


    def f():
        raise SystemExit(1)


    def test_mytest():
        with pytest.raises(SystemExit):
            f()

Execute a função de teste com o modo de relatório "quieto" (*quiet*):

.. code-block:: pytest

    $ pytest -q test_sysexit.py
    .                                                                    [100%]
    1 passed in 0.12s

.. note::

    A flag ``-q/--quiet`` é usada para manter a saida desse exemplo e dos próximos pequena.

Agrupe multiplos testes em uma classe
--------------------------------------------------------------

.. regendoc:wipe

Depois de desenvolver multiplos testes, você pode querer agrupá-los em uma classe.
pytest torna fácil o processo de criar uma classe contendo mais de um teste:

.. code-block:: python

    # conteudo of test_class.py
    class TestClass:
        def test_one(self):
            x = "this"
            assert "h" in x

        def test_two(self):
            x = "hello"
            assert hasattr(x, "check")

``pytest`` descobre todos os testes seguindo as Convenções para descoberta de testes Python,
então eé encontra ambas as funlções com o prefixo ``test_``. Não há a necessidade de usar subclasses, mas se certifique
de usar o prefixo ``Test`` nas suas classes, caso contrário a classe vai ser ignorada. Podemos simplesmente rodar o
módulo usando nome do arquivo:

..
   :ref:`Convenções para descoberta de testes Python <test discovery>`

.. code-block:: pytest

    $ pytest -q test_class.py
    .F                                                                   [100%]
    ================================= FAILURES =================================
    ____________________________ TestClass.test_two ____________________________

    self = <test_class.TestClass object at 0xdeadbeef0001>

        def test_two(self):
            x = "hello"
    >       assert hasattr(x, "check")
    E       AssertionError: assert False
    E        +  where False = hasattr('hello', 'check')

    test_class.py:8: AssertionError
    ========================= short test summary info ==========================
    FAILED test_class.py::TestClass::test_two - AssertionError: assert False
    1 failed, 1 passed in 0.12s

O primeiro teste passou e o segundo falhou. Você pode facilmente ver os valores intermediários na asserção para ajudar
você a entender a razão da falha.

Agrupar testes em classes traz benefícios pelas seguintes razões:

 * Organização dos testes
 * Compartilhar fixtures apenas para testes de uma classe em particular
 * Aplicar marcadores a nível de classe e tê-los implicitamente aplicados para todos os testes

Uma coisa a manter em mente quando você está agrupando testes dentro de classes é que cada teste tem uma instância
única da classe. Ter cada teste compartilhar uma mesma instância da classe prejudicaria o isolamento do teste e também
encorajaria más práticas de teste.
Isso está detalhado abaixo:

.. regendoc:wipe

.. code-block:: python

    # conteudo de test_class_demo.py
    class TestClassDemoInstance:
        value = 0

        def test_one(self):
            self.value = 1
            assert self.value == 1

        def test_two(self):
            assert self.value == 1


.. code-block:: pytest

    $ pytest -k TestClassDemoInstance -q
    .F                                                                   [100%]
    ================================= FAILURES =================================
    ______________________ TestClassDemoInstance.test_two ______________________

    self = <test_class_demo.TestClassDemoInstance object at 0xdeadbeef0002>

        def test_two(self):
    >       assert self.value == 1
    E       assert 0 == 1
    E        +  where 0 = <test_class_demo.TestClassDemoInstance object at 0xdeadbeef0002>.value

    test_class_demo.py:9: AssertionError
    ========================= short test summary info ==========================
    FAILED test_class_demo.py::TestClassDemoInstance::test_two - assert 0 == 1
    1 failed, 1 passed in 0.12s

Note que os atributes adicionados a nivel de classe são *atributos de classe*, então eles são compartilhados entre os
testes.

Use um diretório temporário para testes funcionáis
--------------------------------------------------------------

O ``pytest`` provê Fixtures e argumentos de função padrões para requisitar recursos arbitrários,
como um diretório temporário único:

..
   :std:doc:`Fixtures e argumentos de função padrões <builtin>`

.. code-block:: python

    # conteudo de test_tmp_path.py
    def test_needsfiles(tmp_path):
        print(tmp_path)
        assert 0

Liste o nome ``tmp_path`` na assinatura da função de teste e o ``pytest`` irá procurar e chamar uma fábrica de fixtures
para criar o recurso antes de executar a chamada da função de teste. Antes do teste rodar, ``pytest`` cria um
diretório temporário que é único para cada invocação/execução daquele teste.

.. code-block:: pytest

    $ pytest -q test_tmp_path.py
    F                                                                    [100%]
    ================================= FAILURES =================================
    _____________________________ test_needsfiles ______________________________

    tmp_path = PosixPath('PYTEST_TMPDIR/test_needsfiles0')

        def test_needsfiles(tmp_path):
            print(tmp_path)
    >       assert 0
    E       assert 0

    test_tmp_path.py:3: AssertionError
    --------------------------- Captured stdout call ---------------------------
    PYTEST_TMPDIR/test_needsfiles0
    ========================= short test summary info ==========================
    FAILED test_tmp_path.py::test_needsfiles - assert 0
    1 failed in 0.12s

Mais informações sobre como manipular diretórios temporários está disponível em
Arquivos e diretórios temporários <tmp_path handling>.

Conheça que tipos de fixtures do pytest <fixtures> estão disponíveis por padrão com o comando:

..
  :ref:`Arquivos e diretórios temporários <tmp_path handling>`
  :ref:`fixtures do pytest <fixtures>`

.. code-block:: bash

    pytest --fixtures   # shows builtin and custom fixtures

Note que esse comando omite fixtures que começam com ``_`` a não ser que a opção ``-v`` seja adicionada ao comando.
