<h1 align="center"> VisionApp - API </h1>

<div align="center">

![Badge em Desenvolvimento](http://img.shields.io/static/v1?label=STATUS&message=FINALIZADO&color=GREEN&style=for-the-badge)
![Static Badge](https://img.shields.io/badge/python-gray?style=for-the-badge&logo=python&logoColor=yellow)
![Static Badge](https://img.shields.io/badge/minio-purple?style=for-the-badge&logo=minio&logoColor=white)
![Static Badge](https://img.shields.io/badge/postgresql-blue?style=for-the-badge&logo=postgresql&logoColor=white)
![Static Badge](https://img.shields.io/badge/docker-blue?style=for-the-badge&logo=docker&logoColor=white)
![Static Badge](https://img.shields.io/badge/firebase-red?style=for-the-badge&logo=firebase&logoColor=yellow)

  
</div>

## Sumário

* [Integrantes](#integrantes)
* [Descrição](#descrição)
* [Requisitos](#requisitos)
* [Tecnologias](#tecnologias)
* [Fluxo do Software](#fluxo-do-software)
* [Dificuldades](#dificuldades)
* [Resultados](#resultados)
* [Como_Usar](#como_usar)
* [Conclusao](#conclusao)




## Integrantes

- Anderson do Vale - [and3510](https://github.com/and3510) 
- Beatriz Barreto - [whosbea](https://github.com/whosbea)
- Cristovam Paulo - [cristovam10000](https://github.com/cristovam10000)
- Gustavo do Vale - [gustavodovale](https://github.com/gustavodovale)
- Lucas Cesar

## Descrição

Este projeto consiste em uma API desenvolvida com FastAPI para reconhecimento facial, armazenamento de informações biométricas e gerenciamento de registros criminais. A API utiliza tecnologias modernas para garantir alta performance, precisão e segurança no processamento de dados sensíveis.


## Requisitos

### Requisitos Funcionais (RF)

| Código | Requisito |
|--------|-----------|
| RF01 | O sistema deve permitir o **cadastro de criminosos** com os seguintes dados: CPF, nome completo, nome da mãe e imagem facial. |
| RF02 | O sistema deve permitir a **extração automática da face** a partir da imagem enviada. |
| RF03 | O sistema deve **gerar e armazenar um vetor de 128 dimensões** representando a face da pessoa. |
| RF04 | O sistema deve permitir o **registro de ficha criminal** apenas se o CPF já estiver cadastrado como pessoa física. |
| RF05 | O sistema deve permitir o **reconhecimento facial** por similaridade com vetores já cadastrados. |
| RF06 | O sistema deve aplicar **algoritmo de ajuste de iluminação** caso a imagem tenha baixa ou alta luminosidade. |
| RF07 | O sistema deve permitir a **consulta de informações por CPF**, retornando se há ficha criminal e se está foragido. |
| RF08 | O sistema deve permitir o envio de imagem por requisição (POST) para verificar a presença de um rosto válido. |
| RF09 | O sistema deve realizar **autenticação de usuários via Firebase**. |
| RF10 | O sistema deve gerar um **token JWT** com validade temporária após autenticação via Firebase. |
| RF11 | O sistema deve segmentar as informações em dois bancos: **usuarios** e **pessoas procuradas por crimes**. |


### Requisitos Não Funcionais (RNF)

| Código | Requisito |
|--------|-----------|
| RNF01 | O sistema deve ser desenvolvido em **Python**, utilizando **FastAPI** como framework principal. |
| RNF02 | O banco de dados utilizado deve ser o **PostgreSQL** com suporte à extensão `vector` para armazenar vetores. |
| RNF03 | O sistema deve usar **OpenCV, Dlib e face_recognition** para manipulação e vetorização facial. |
| RNF04 | Todas as comunicações entre cliente e servidor devem ocorrer via **HTTPS**. |
| RNF05 | O sistema deve seguir os princípios de **segurança de dados**, evitando exposição de informações sensíveis. |
| RNF06 | O sistema deve garantir **alta disponibilidade e escalabilidade**, podendo operar em ambientes com múltiplas requisições simultâneas. |
| RNF07 | O tempo médio de resposta para reconhecimento facial deve ser inferior a **3 segundos**. |
| RNF08 | A API deve seguir boas práticas REST, com respostas em **formato JSON**. |
| RNF09 | O sistema deve estar preparado para lidar com **falhas de rede, imagem inválida ou ausência de rosto**. |

## Tecnologias

- Python
- JWT
- Firebase
- Docker
- Postgresql
- Minio


### Bibliotecas principais
FastAPI – Framework rápido e moderno para construção de APIs com Python.

OpenCV – Leitura e pré-processamento de imagens.

dlib – Detecção facial por retângulo delimitador.

face_recognition – Geração de vetores faciais (descritores de 128 dimensões).

SQLAlchemy – ORM para integração com banco de dados relacional.

FireAuth - Para Autentição com FireBase

## Fluxo do Software

<div align="center"> 


![Imagem do Diagrama da Arquitetura do Sistema](images/latest.drawio.png)
<p> Arquitetura do Sistema </p>

</div>

De acordo com diagrama da imagem, a autenticação é realizada via Firebase, garantindo o acesso seguro dos usuários por meio de tokens JWT. A API desenvolvida com FastAPI gerencia o recebimento de fotos, CPF e a autenticação, realizando o reconhecimento facial e a consulta de informações em bancos PostgreSQL e no serviço de armazenamento MinIO. O sistema permite identificar usuários ou suspeitos a partir da análise facial, cruzando dados com os cadastros existentes. Por fim, os resultados são retornados à aplicação móvel, completando o fluxo de verificação e resposta.




## Dificuldades

### Configuração

Em diversos momentos, ocorreram erros do tipo *Internal Server Error 500*, causados pelo envio de dados incorretos ao banco de dados. Também enfrentamos problemas relacionados à privacidade ao utilizar o MinIO. Para mitigar esse risco, optamos por tornar o repositório de imagens privado. Assim, para acessar uma imagem via URL, utilizamos o CPF como chave de verificação. Caso exista uma imagem associada ao mesmo CPF, é gerado um link temporário com validade de 6 minutos.

Além disso, foi necessário modificar repetidamente as colunas das tabelas, devido a mudanças nos requisitos ao longo do desenvolvimento. Isso evidenciou a ausência de um planejamento adequado na fase inicial da modelagem do banco de dados.

### Reconhecimento Facial

Embora tivéssemos acesso a diversas fotos de rostos, a maioria não atendia aos critérios mínimos de qualidade estabelecidos: o rosto precisava estar centralizado, sem obstruções e bem iluminado. Como resultado, apenas 48 imagens foram consideradas adequadas e armazenadas no banco para uso no reconhecimento facial.




## Resultados

<div align="center"> 

![Imagem da Interface do FastApi](images/interface_FastApi.png)
<p> Interface do FastApi para realização de Requisições </p>

</div>

A imagem apresenta a documentação da API desenvolvida com FastAPI, onde estão listadas as principais requisições que a aplicação móvel pode realizar. Entre elas, destaca-se o endpoint /auth/firebase, responsável pela autenticação via Firebase, e o ´/buscar-similaridade-foto´, que permite o envio de uma imagem para análise de similaridade facial. Além disso, o endpoint /buscar-ficha-criminal/{cpf} possibilita a consulta da ficha criminal a partir do CPF, enquanto o /usuario/perfil recupera os dados do perfil do usuário autenticado. Todas as rotas exigem autenticação, garantindo segurança nas interações entre o app e o servidor.


### Reconhecimento Facial

#### **Table I**

**Taxa de Sucesso e Tempo Médio por Requisição – Homens**

| Intervalo  | Taxa de Sucesso | Tempo Médio (s) |
| ---------- | --------------- | --------------- |
| 1 segundo  | 97,33%          | 1,570           |
| 2 segundos | 97,33%          | 1,718           |
| 5 segundos | 97,33%          | 1,760           |

---

#### **Table II**

**Taxa de Sucesso e Tempo Médio por Requisição – Mulheres**

| Intervalo  | Taxa de Sucesso | Tempo Médio (s) |
| ---------- | --------------- | --------------- |
| 1 segundo  | 98,61%          | 1,688           |
| 2 segundos | 98,61%          | 1,927           |
| 5 segundos | 98,61%          | 1,968           |

---

#### **Table III**

**Classificações de Similaridade – Homens (%)**

| Tom de Pele | Intervalo | Confiante | Ambíguo | Nenhuma Similaridade Forte |
| ----------- | --------- | --------- | ------- | -------------------------- |
| Brancos     | 1 s       | 75,25     | 23,38   | 1,38                       |
|             | 2 s       | 73,13     | 25,50   | 1,38                       |
|             | 5 s       | 75,00     | 24,25   | 0,75                       |
| Pardos      | 1 s       | 75,00     | 23,63   | 1,38                       |
|             | 2 s       | 73,00     | 25,63   | 1,38                       |
|             | 5 s       | 75,25     | 23,38   | 1,38                       |
| Negros      | 1 s       | 48,50     | 44,75   | 6,75                       |
|             | 2 s       | 49,38     | 43,88   | 6,75                       |
|             | 5 s       | 47,25     | 46,00   | 6,75                       |

---

#### **Table IV**

**Classificações de Similaridade – Mulheres (%)**

| Tom de Pele | Intervalo | Confiante | Ambíguo | Nenhuma Similaridade Forte |
| ----------- | --------- | --------- | ------- | -------------------------- |
| Brancos     | 1 s       | 46,75     | 51,88   | 1,38                       |
|             | 2 s       | 46,75     | 51,88   | 1,38                       |
|             | 5 s       | 46,25     | 52,38   | 1,38                       |
| Pardos      | 1 s       | 45,13     | 53,88   | 1,00                       |
|             | 2 s       | 45,13     | 53,88   | 1,00                       |
|             | 5 s       | 45,13     | 53,88   | 1,00                       |
| Negros      | 1 s       | 42,38     | 55,63   | 1,99                       |
|             | 2 s       | 42,38     | 55,63   | 1,99                       |
|             | 5 s       | 42,38     | 55,63   | 1,99                       |

---

#### **Table V**

**Matriz de Confusão Geral**

| Categoria                | Homens | Mulheres | Total |
| ------------------------ | ------ | -------- | ----- |
| Verdadeiro Positivo (VP) | 450    | 329      | 779   |
| Falso Negativo (FN)      | 198    | 319      | 517   |
| Verdadeiro Negativo (VN) | 129    | 93       | 222   |
| Falso Positivo (FP)      | 0      | 0        | 0     |

---

#### **Table VI**

**Resultados do Teste com Gêmeos**

| Classificação              | Gêmeo A | Gêmeo B |
| -------------------------- | ------- | ------- |
| Confiante                  | 3       | 0       |
| Ambíguo                    | 9       | 12      |
| Nenhuma Similaridade Forte | 0       | 0       |



## Conclusao

