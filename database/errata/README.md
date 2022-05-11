# Errata

## _Directory with corrections to the original catalog_
## Pasta com correcções à informação do catálogo


Quando se detectam erros na "História administrativa/biográfica/familiar"
(`BiogHist`) ou no Registo Académico - "Âmbito e conteúdo" (`ScopeContet`)
pode ser criado nesta pasta um ficheiro com o texto corrigido (juntando ambos os campos).

Durante o processamento o conteúdo desse ficheiro é usado em vez do conteúdo
do ficheiro original. 

Isso permite corrigir os erros na base de dados de trabalho enquanto o 
ficheiro original não é corrigido e re-exportado.

Cada ficheiro tem como nome o identificador do registo original, que é um
identificador numérico visível no url do registo. Por exemplo: 

    http://pesquisa.auc.uc.pt/details?id=152975

Opcionalmente o nome do ficheiro pode ter o nome do estudante, 
para melhor legibilidade.

O conteúdo é a junção dos dois campos.
As linhas começadas por "#" são ignoradas e podem ser usadas
para comentários.

        # 2021-10-01
        # JRC
        # Correção sintaxe dos campos

        Id: 152975
        Código de referência: PT/AUC/ELU/UC-AUC/B/001-001/R/005128

        Nome        : António Ribeiro
        Data inicial: 1672-10-01
        Data final  : 1679-05-24
        Filiação: Gonçalo Gonçalves
        Naturalidade: Guimarães

        Faculdade: Cânones
        # Matriculas 1673.10.15
        Matrícula(s): 1673.10.15
        1675.10.01
        1675.10.01
        1676.10.14
        1677.10.15
        1678.10.15

        Instituto: 1672.10.01
        # Bacharel 1678.07.18
        Bacharel: 1678.07.18
        # Formatura 1679.05.24
        Formatura: 1679.05.24

Neste exemplo corrige-se a omissão de ":" em alguns campos. 
É uma boa prática manter o texto original das linhas alteradas, precedendo-as de "#".
Outro exemplo, corrigindo um erro no nome da faculdade.

            Id: 147552
            Código de referência: PT/AUC/ELU/UC-AUC/B/001-001/A/007643

            Nome        : António Pereira de Araújo
            Data inicial: 1761-10-29
            Data final  : 1770-05-30
            Filiação: António Alves
            Naturalidade: Sedielos, Penaguião
            # Faculdade: Cânone
            Faculdade: Cânones

            Matrícula(s): 01.10.1764
            01.10.1765
            01.10.1766
            01.10.1767
            01.10.1768

            Instituta: 01.10.1764
            29.10.1761

            Bacharel: 13.06.1769, Atos 103, fl. 51 v.
            Formatura: 30.05.1770, Atos 104, fl. 105 v.

Para melhor clareza e organização esta pasta pode ser organizada em sub-pastas.