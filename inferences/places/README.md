
**[PT]** Português

---

**[EN]** English


## Toponímia: ficheiros

Lista de ficheiros associados ao tratamento da naturalidade
dos estudantes.

---

## Place names: files

List of files related to the processing of the
place of birth of the students.


__naturalidade_original.csv__

* Lista das expressões usadas na naturalidade
dos estudantes, com número de ocorrências 
e datas extremas.

---

* List of students' expressions used for
place of birth with number of cases, date interval.

__naturalidade_normalizada.csv__

* Acrescenta uma coluna com o topónimo normalizado, 
    substituindo designações em desuso pelas atuais,
    atualizando ortografia e
    uniformizando pontuação, de forma
    a permitir a identificação dos topónimos na atualidade.
    Ver tb _places_normalization.csv_

    ---

* Adds a normalized version of the place name, taking
  into account name changes, modern orthography and
  uniform punctuation in order to facilitate identifying
  the places nowadays.
  

__naturalidade_geo_status.csv__ 

* Estado atual do processo de georeferenciação. Acrescenta
    ao ficheiro anterior:

    * geocoder: fonte de informação geográfica (osm=OpenStreetMaps)
    * id: identificação do topónimo na fonte de informação geográfica
    * address: na forma "local,contexto administrativo, país"
    * city: municipal level name
    * country
    * importance: administrativa ou demográfica, conforme a fonte
    * class: (osm = boundary,place)
    * type: tipo dentro da classe
    * latitude, longitude
    * distance: distância a Coimbra.

    ---

* Current state of geocoding. Adds to previous files:

    * geocoder: information source (osm=OpenStreetMaps)
    * id: identifier in the source
    * address: in the form (place,administrative contexts, country)
    * city: municipal level context
    * country
    * importance: administrative or demographic importance according to the source
    * class: (osm = boundary,place)
    * type: type within the class (place, hamlet)
    * latitude, longitude
    * distance: distance to Coimbra.

__nomes_geograficos.csv__

* Componentes das expressões usadas para naturalidade.
Por exemplo a expressão "Ponta Delgada, S. Miguel, Açores" 
tem três componentes. Esta lista tem mais linhas que 
_naturalidade_original.csv_ mas contém expressões mais
ambíguas e genéricas.

__osm-places.csv__ e __osm_not_found.csv__
* Ficheiros de "cache" de acesso ao serviço _OpenStreetMaps_.

__ine-inspire-clean.csv__
* Lista da topónimos do serviço de GeoNames INSPIRE do Instituto Nacional de Estastística
  com vários processamentos adicionais (ver o [notebook em curso](../../notebooks/911-places-ine-topo.ipynb)):
    * conversão das coordenadas para latitude e longitude
    * uniformização de nomes desdobrando abreviaturas
    * identificação de topónimos repetidos (mesmo nome, menos de 1km de distância)
    * remoção de topónimos fora das fronteiras de Portugal continental
    * adição do contexto administrativo (freguesia,concelho, distrito)
    * adição de um índice de "importância" com base na função administrativa e população em 2011

