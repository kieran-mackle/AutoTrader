---
title: Quiz
description: How to add interactive quizzes to your site.
---

# Quizzes

As of version 0.0.12, docsy-jekyll has support for basic quizzes! These are
intended to help educate your users about the content of your documentation.
For a quiz, you can add a new file to the folder `_data/quizzes`, and write a 
questions file based on the format shown in `_data/quizzes/example-quiz.yml`.
Here is a simple example of a multiple choice question (which can also serve as 
True/False):

```yaml
title: This is the Quiz Title
randomized: false
questions:

 - type: "multiple-choice"
   question: "True or False, Pittsburgh is West of Philadelphia"
   items:
    - choice: True
      correct: true
    - choice: False
      correct: false
   followup: | 
      The answer is True! Pittsburgh is 304.9 miles West of 
      Philadelphia, or approximately a car ride of 
      4 hours and 52 minutes. Buckle up!
```

The quiz is rendered with a "Show Answer" button below each question, and when
the user clicks it, any questions that are flagged with `correct: true` will be 
bolded, and if a followup section is included, it will be displayed.
See the live example at the end of this page.

## Options

#### Title

If you include a title, it will be rendered at the top of the quiz. This is
optional - you can leave it out and add it before the include on the page.

#### Random

If you want your questions to be presented randomly, just add randomized: true
to the data.


## Example Quiz

If I want to include the quiz located at `_data/quizzes/example-quiz.yml`, I 
can do so like this:

```
{% raw %}{% include quiz.html file='example-quiz' %}{% endraw %}
```

The rendered quiz is shown here:


{% include quiz.html file='example-quiz' %}
