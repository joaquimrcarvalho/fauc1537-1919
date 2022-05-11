# About `Kleio` files

_Kleio_ files are text files with a special notation designed for the transcription of historical sources. 

The notation was created by Manfred Thaller, as part of the _Kleio historical database system_ (http://web.archive.org/web/20130603204750/http://www.hki.uni-koeln.de/kleio/old.website/).

`kleio` notation proved very expressive and efficient, providing a concise way for the transcription of complex historical documents.

The _Timelink-Kleio translator_ implements a subset of the `Kleio` notation designed for the `Timelink` database system. 

_Timelink_ provides a set of data models for handling person-oriented information collected in historical documents. It main advantages are handling time varying personal attributes, representation of interpersonal relations and reversible identification of people in different sources.


This is how a (portuguese) baptism looks like in _Timelink_ `Kleio` notation:

      bap$b1714-2/12/11714/fl.117v./igreja de sao silvestre/manuel lopes serra (padre)

         celebrante$manuel lopes serra
            ls$profissao/padre

         n$francisca/f

            pn$antonio ferreira
               ls$morada/espinheiro
               ls$freguesia/lousa

            mn$leonarda francisca

            pad$joao fernandes ramalheiro
               ls$morada/moita
               ls$freguesia/lousa

            mad$francisca
               ls$ec/solteira

               pmad$joao goncalves
                  ls$morada/espinheiro
                  ls$freguesia/lousa

Text files implementing the Timelink Kleio notation can be translated by
the _Timelink_ `kleio-server` and imported into the _Timelink_ relational database. 

Translation is _intelligent_ in the sense that it operates a _normalization_ of the source information, infering information from the context, and so greatly reducing the overhead of producing normalized data. 