

**[EN]**  English only
# Timelink data models


`Timelink` uses a dual model to represent historical information.

- A *text-based source-oriented data model* is used to transcribe
  sources with little loss of information.
- A *person-oriented model*, that consolidates biographical data,
  handles inference of networks and reversible record linking

The ``Kleio`` notation (Manfred Thaller) is used for source-oriented
data input.

A relational database structure is used to store person-oriented data
together with original source context.

A special software, *the Kleio translator* processes text transcriptions
of the sources in ``kleio`` notation and generates data for the
the person-oriented database.

This solves the inevitable tension between a source-oriented model
and an analytical model.

The Source Oriented Model
-------------------------

Uses a containment structure of ``source->act->persons`` and ``objects``.

The *source oriented model* uses a number of key terms in a formal way:
``source``, ``act``, ``person``, ``object``, ``function``, ``attribute``
and ``relation``.


- A historical ``source`` contains one or more ``acts``.
- An ``act`` is a description of events in the sources
  (a baptism, a marriage, a sale contact, a rental, ...)
- An ``act`` contains actors (``persons``) and ``objects``
  (things, properties, institutions, ...).
- ``persons`` and ``objects`` appear in ``acts`` with specific ``functions``
  (father in a baptism, owner in a sale contract, house in a rental contract).
- ``Actors`` and ``objects`` are described by ``attributes``
  (name, age, gender, price, area, ...).
- ``Actors`` and ``objects`` are linked by ``relations``. Relations are described
  by a type (kin, economical, professional), and a value
  (brother, lender, apprentice).
- Every ``act``, ``function``, ``attribute`` and ``relation`` has a date
  and a link to the point in the original source where it appeared.

Example of the Kleio notation
-----------------------------
A baptism::

    baptism$17/9/1685/parish church
        n$manuel/m
            father$jose luis
                atr$residence/casal da corujeira
            mother$domingas jorge
            gfather$francisco rodrigues/id=b1685.9.17.gf
                atr$residence/moinhos do paleao
            gmother$maria pereira
                rel$kin/wife/francisco rodrigues/b1685.9.17.gf

This example shows an ``act`` (a baptism) that contains five ``persons``:
child ("n"), father, mother, god father and god mother. Two of the people,
the father and the godfather have the ``attribute`` *residence*, and the god
mother has a *kin* ``relation`` with the godfather.


## The Person Oriented Model


The `Person Oriented Model` represents a biography through 3 domains:

- Functions (the roles of the person in acts)
- Attributes
- Relations

The `Person Oriented Model` is an alternative view on the information recorded
in the sources, in a way that facilitates statistical analysis, network analysis
and prosopographies.

The previous baptism generates information as follows (*italics* show
information inferred by Timelink).


### Entities


TODO



| Id             | Class       | Inside           |
:---------------:|:------------:|:----------------:|
| bapt1685-1700  | source      |       ---        |
| *b1*           | act         | bapt1685-1700    |
| *b1-per1*      | person      | *b1*             |
| b1685.9.17.gf  |  person     | *b1*             |
| *b1-per2*      |  person     | *b1*             |
| *b1-per3*      |  person     | *b1*             |




Note that each *entity* has an unique
identifier: ``id``. Such identifier is necessary to refer unambiguosly
to a ``person``, ``object``, ``act`` or ``source``.

Most ``ids`` are generated
automatically by the *Kleio translator* when processing the source transcripts.
but in some circunstances they need to be explicitly given, when a link
between two entities needs to be recorded in an non ambiguous way, such as
the relation between godmother and godfather in the example above.

### Persons

| Id             | Nome                | Gender |
:---------------:|:------------:|:----------------:|
| *b1-per1*      | manuel              | f      |
| *b1-per2*      | jose luis           | *m*    |
| *b1-per3*      | domingas jorge      | *f*    |
| b1985.9.17.gf	 | francisco rodrigues | *m*    |
| *b1.per5*      | maria pereira       | *f*    |


### Attributes


| Entity          |  Type      | Value              | Date        |
|-----------------|------------|--------------------|-------------|
| *b1-per1i*      | residence  | Casal da Corujeira | *17/9/1685* |
| *b1985.9.17.gf* | residence  | Moinhos do Paleao  | *17/9/1685* |


### Relations


| Origin     | Destination   | Type    |  Value    |  Date          |
|------------|---------------|---------|-----------|----------------|
| *b1-per2*  | *b1.per3*     | *kin*   | *husband* | *17/9/1685*    |
| *b1-per5*  | b1985.9.17.gf | kin     | wife      | *17/9/1685*    |
| *b1-per2*  | *b1-per1*     | *kin*   | *father*  | *17/9/1685*    |

### Functions

Functions of people (father,mother, ...) in acts are a special case
of relations linking people to acts, with the type 'function-in-act'.
The same applies to objects, when they appear in acts.


| Origin        | Destination   | Type             |  Value    |  Date          |
|---------------|---------------|------------------|-----------|----------------|
| b1985.9.17.gf | *b1*          | function-in-act  | gfather   | *17/9/1685*    |
| *b1.per5*     | *b1*          | function-in-act  | gmother   | *17/9/1685*    |


