# Report for Assignment 1

## Project chosen

Name: Pytest

URL: https://github.com/pytest-dev/pytest/tree/main

Number of lines of code and the tool used to count it: 77.686 - lizard
![Screenshot 2024-06-27 at 22 16 31](https://github.com/apanayotova03/pytest/assets/122705116/d227c09a-97b9-4d79-a9f8-93f7f5c58616)

Programming language: Python

## Coverage measurement

### Existing tool

<Inform the name of the existing tool that was executed and how it was executed>

We used tox to run the tests and measured their coverage using coverage.py. The specific commands that were used are:

$ tox
$ coverage html

This allowed us to run all tests in the repository and summarised the coverage of each test in an html file. Here is a screenshot of the results:


The results indicate that the tests have a branch coverage of 38% on the program.

<Show the coverage results provided by the existing tool with a screenshot>
![Screenshot 2024-06-27 at 22 18 22](https://github.com/apanayotova03/pytest/assets/122705116/74aedda1-54a4-4a50-bd9b-8af833493ef8)

### Your own coverage tool

<The following is supposed to be repeated for each group member>
<Group member name> Anastasia
<Function 1 name> create_terminal_writer()
<Show a patch (diff) or a link to a commit made in your forked repository that shows the instrumented code to gather coverage measurements>
![Screenshot 2024-06-27 at 22 19 26](https://github.com/apanayotova03/pytest/assets/122705116/b4933dba-97e4-4337-acc1-1d77c9afb250)

<Provide a screenshot of the coverage results output by the instrumentation>
New branch coverage: 100%
![Screenshot 2024-06-27 at 22 20 47](https://github.com/apanayotova03/pytest/assets/122705116/e2c5a548-2373-4c05-9710-31666b811296)


<Function 2 name> def _strtobool()

<Show a patch (diff) or a link to a commit made in your forked repository that shows the instrumented code to gather coverage measurements>

<Provide a screenshot of the coverage results output by the instrumentation>

New branch coverage: 100%


## Coverage improvement

### Individual tests

<The following is supposed to be repeated for each group member>

<Group member name> Anastasia

<Test 1>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the new/enhanced test>
![Screenshot 2024-06-27 at 22 21 40](https://github.com/apanayotova03/pytest/assets/122705116/9ef88a09-957d-4a18-90cc-b7ae1c855155)


<Provide a screenshot of the old coverage results (the same as you already showed above)>

Previous branch coverage: 50%

![Screenshot 2024-06-27 at 22 22 09](https://github.com/apanayotova03/pytest/assets/122705116/372df057-4d83-4435-abdd-2a5669de463a)


<Provide a screenshot of the new coverage results>

New branch coverage: 100%


<State the coverage improvement with a number and elaborate on why the coverage is improved>

The branch coverage has doubled from 50% to 100%. The reason is because the previous tests did not check every case, for example the case when the colour option was either set to “yes” or “no”. However, the new test checks for all four different cases.


<Test 2>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the new/enhanced test>




<Provide a screenshot of the old coverage results (the same as you already showed above)>
Previous branch coverage: 0%


<Provide a screenshot of the new coverage results>


<State the coverage improvement with a number and elaborate on why the coverage is improved>

The branch coverage has improved from 0% to 100%. In the original test, neither of the branches were covered, possibly due to the fact that the function was not called. However, the new test checks all 3 different branches, creating a branch coverage of 100%.

























<Group member name> Ana Alexandra Cornea 

<Function 1 name> fullwidth() 

<Show a patch (diff) or a link to a commit made in your forked repository that shows the instrumented code to gather coverage measurements>
 


<Provide a screenshot of the coverage results output by the instrumentation>


<Function 2 name>

<Provide the same kind of information provided for Function 1>

## Coverage improvement

### Individual tests

<The following is supposed to be repeated for each group member>

<Group member name> Ana Alexandra Cornea

<Test 1>



<Provide a screenshot of the old coverage results (the same as you already showed above)>

<Provide a screenshot of the new coverage results>

<State the coverage improvement with a number and elaborate on why the coverage is improved>

<Test 2>

<Provide the same kind of information provided for Test 1>













<Show a patch (diff) or a link to a commit made in your forked repository that shows the instrumented code to gather coverage measurements>

<Provide a screenshot of the coverage results output by the instrumentation>

<Provide a screenshot of the new coverage results>

<State the coverage improvement with a number and elaborate on why the coverage is improved>


















<Group member name> Liang Laura Moragues Hincapie

<Function 1 name> get_terminal_width()

<Show a patch (diff) or a link to a commit made in your forked repository that shows the instrumented code to gather coverage measurements>


<Provide a screenshot of the coverage results output by the instrumentation>


<Function 2 name> _highlight

<Provide the same kind of information provided for Function 1>

## Coverage improvement

### Individual tests

<The following is supposed to be repeated for each group member>

<Group member name> Liang Laura Moragues Hincapie

<Test 1>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the new/enhanced test>


<Provide a screenshot of the old coverage results (the same as you already showed above)>

<Provide a screenshot of the new coverage results>


<State the coverage improvement with a number and elaborate on why the coverage is improved>

New branch coverage is 100%

<Test 2>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the new/enhanced test>

<Provide a screenshot of the old coverage results (the same as you already showed above)>

<Provide a screenshot of the new coverage results>

<State the coverage improvement with a number and elaborate on why the coverage is improved>






<Group member name> Anda Gabriela Barbu

<Function 1 name> should_do_markup()

<Show a patch (diff) or a link to a commit made in your forked repository that shows the instrumented code to gather coverage measurements>
The code of the new test after creating a branch array


def test():
    # Branch Id 1
    os.environ["PY_COLORS"] = "1"
    test = should_do_markup(None)
    del os.environ["PY_COLORS"]
    assert test == True


    os.environ["PY_COLORS"] = "0"
    test = should_do_markup(None)
    del os.environ["PY_COLORS"]
    assert test == False


    # Branch Id 3
    os.environ["NO_COLOR"] = "1"
    test = should_do_markup(None)
    del os.environ["NO_COLOR"]
    assert test == False


    # Branch Id 4
    os.environ["FORCE_COLOR"] = "1"
    test = should_do_markup(None)
    del os.environ["FORCE_COLOR"]
    assert test == True


    # Branch Id 5
    test = should_do_markup(None)
    assert test == False


    os.environ["PY_COLORS"] = "1"
if __name__ == "__main__":
    test()




<Provide a screenshot of the coverage results output by the instrumentation>













<Function 2 name>

<Provide the same kind of information provided for Function 1>

## Coverage improvement

### Individual tests

<The following is supposed to be repeated for each group member>

<Group member name>

<Test 1>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the new/enhanced test>

<Provide a screenshot of the old coverage results (the same as you already showed above)>

<Provide a screenshot of the new coverage results>

<State the coverage improvement with a number and elaborate on why the coverage is improved>

<Test 2>

<Show a patch (diff) or a link to a commit made in your forked repository that shows the new/enhanced test>

<Provide a screenshot of the old coverage results (the same as you already showed above)>

<Provide a screenshot of the new coverage results>

<State the coverage improvement with a number and elaborate on why the coverage is improved>



















### Overall

<Provide a screenshot of the old coverage results by running an existing tool (the same as you already showed above)>

<Provide a screenshot of the new coverage results by running the existing tool using all test modifications made by the group>

## Statement of individual contributions

<Write what each group member did>
