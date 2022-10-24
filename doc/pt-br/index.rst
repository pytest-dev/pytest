:orphan:

.. _features:

pytest: ajuda você a escrever programas melhores
================================================

.. module:: pytest

O *framework* ``pytest`` torna fácil a tarefa de escrever pequenos, legíveis testes, e consegue escalar para suportar
testes funcionais complexos para aplicações e bibliotecas.


``pytest`` requer: Python 3.7+ ou PyPy3.

**Nome do pacote PyPI**: :pypi:`pytest`


Um exemplo rápido
-----------------

.. code-block:: python

    # conteudo de test_sample.py
    def inc(x):
        return x + 1


    def test_answer():
        assert inc(3) == 5


Para executá-lo:

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
    >       assert inc(3) == 5
    E       assert 4 == 5
    E        +  where 4 = inc(3)

    test_sample.py:6: AssertionError
    ========================= short test summary info ==========================
    FAILED test_sample.py::test_answer - assert 4 == 5
    ============================ 1 failed in 0.12s =============================

Graças a introspecção detalhada de asserções do ``pytest``, somente puras sentenças de ``assert`` são usadas.
Veja :ref:`Começe aqui <getstarted>` para uma indrotução básica de como usar o pytest.


Funcionalidades
---------------

- Informação detalhada sobre sentenças de asserção (não precisa decorar nomes do ``self.assert*``

- Descoberta automática de módulos de testes e funções

- Fixtures modulares para gerenciar recursos de testes pequenos ou parametrizados.

- Capaz de rodar suites de testes escritas usando unittest (incluindo *trial*) e
  nose sem nenhuma mudança extra.

- Python 3.7+ ou PyPy 3

- Arquitetura rica para plugins, com mais de 800+ plugins externos e uma comunidade ativa


Documentação
------------

* :ref:`Comece aqui <get-started>` - instale o pytest e conheça o básico em apenas vinte minutos
* Guias how-to - guias com passo a passo, cobrundo um grande conjunto de casos de uso e necessidades
* Guias de referência - inclui a referência completa para a API do pytest,
  uma lista de plugins e mais
* Explicações - background, discução de tópicos chaves, resposta a perguntas de alto-nível


Bugs/Pedidos
------------

Por favor use o `gerenciador de bugs do Github <https://github.com/pytest-dev/pytest/issues>`_ para submeter bugs ou
pedidos de novas funcionalidades.


Suporte o pytest
----------------

`Open Collective`_ é uma plataforma de financiamento online para comunidades abertas e transparentes.
Ela provê ferramentas para arrecadar dinheiro e compartilhar gastos com trasnparencia total.

Ela é a plataforma recomendada para indivíduos e companhias que queira fazer doações mensais ou imediatas diretamente
para o projeto.

Veja mais detalhes no `pytest collective`_.

.. _Open Collective: https://opencollective.com
.. _pytest collective: https://opencollective.com/pytest


pytest para empresas
--------------------

Disponível como parte da assinatuda Tidelift.

Os mantedores do pytest e milhares de outros pacotes estão trabalhando com a Tidelift para entregar suporte de nível
comercioal e manutenção para as dependencias de código aberto que você usa para construir suas aplicações.
Economize tempo, reduça risco, e melhore a saúde do código, enquanto paga exatamente os mantedores das dependencias que
você usa.

`Saiba mais. <https://tidelift.com/subscription/pkg/pypi-pytest?utm_source=pypi-pytest&utm_medium=referral&utm_campaign=enterprise&utm_term=repo>`_

Segurança
~~~~~~~~~

pytest, até agora, nunca foi associada a uma vulnerabilidade de segurança, mas de qualquer maneira, para reportar
uma vulnerabilidade de segurança, por favor use o `Contato de segurança da Tidelift <https://tidelift.com/security>`_.
A Tidelift irá coordenar o conserto da vulnerabilidade e sua divulgação.
