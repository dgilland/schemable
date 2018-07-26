Changelog
=========


- Include execption class name in error message returned by ``As``.
- Always return a ``dict`` when parsing from dictionary schemas instead of trying to use the source data's type as an initializer. (**breaking change**)


v0.2.0 (2018-07-25)
-------------------

- Rename ``Collection`` to ``List``. (**breaking change**)
- Rename ``Object`` to ``Dict``. (**breaking change**)
- Allow ``collections.abc.Mapping`` objects to be valid ``Dict`` objects.
- Modify ``Type`` validation so that objects are only compared with ``isinstance``.
- Improve docs.


v0.1.0 (2018-07-24)
-------------------

- First release.
