Changelog
=========


v0.5.0 (2018-08-17)
-------------------

- Don't load partial data from a nested schema if it was created with ``strict=True`` (e.g. ``Schema({'key': Schema({...}, strict=True)})``).


v0.4.1 (2018-08-14)
-------------------

- Fix previous fix for case where schema results could have ``data`` or ``errors`` with schema classes as keys.
- Ensure that ``Select('key', <iteratee>)`` doesn't call ``<iteratee>`` if ``'key'`` was not found in the source data.


v0.4.0 (2018-08-14)
-------------------

- Fix case where schema object with an ``Optional(key)`` would result in ``SchemaResult.errors[Optional(key)]``. Ensure that ``SchemaResult.errors[key]`` is set instead.
- Ignore ``KeyError`` when using ``Schema({'key': Select('other_key')})`` when ``'other_key'`` isn't present in the source object. Return a missing key error instead.


v0.3.1 (2018-07-31)
-------------------

- If a validate callable raises an exception, use its string representation as the schema error message. Previously, a custom error message stating that the callable should evaluate to true was used when validator returned falsey and when it raised an exception. That message is now only returned when the validator doesn't raise but returns falsey.


v0.3.0 (2018-07-27)
-------------------

- Add schema helpers:

  - ``Select``
  - ``Use``

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
