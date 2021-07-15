---
title: A Nested Page
description: An example of a nested page
---

# A Nested Page

This is an example of a page that doesn't have a permalink defined, and
is not included in the table of contents (`_data/toc.yml`). This means
that it will render based on it's path. Since it's in `docs/example-page.md`,
the url will be `docs/example-page/`.

## Link to a subfolder

Now let's say we want to link to a subfolder, specifically with this
setup:

```
docs/
  example-page.md  (-- we are here
  subfolder/
     example-page.md  (-- we want to link here
```

You can provide the relative path to the file, like `subfolder/example-page.md`
and Jekyll will handle parsing it. For example:

 - [here is that link](subfolder/example-page)
 
And {% include doc.html name="here" path="subfolder/example-page" %} is the same link, 
but generated with the include statement:

```
{% raw %}{% include doc.html name="here" path="subfolder/example-page" %}{% endraw %}
```

