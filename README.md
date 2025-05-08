<h1 align="center"> ApiFaceCheck </h1>

<div align="center">

![Badge em Desenvolvimento](http://img.shields.io/static/v1?label=STATUS&message=EM%20DESENVOLVIMENTO&color=GREEN&style=for-the-badge)
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
| RF01 | O sistema deve permitir o **cadastro de uma pessoa física** com os seguintes dados: CPF, nome completo, nome da mãe e imagem facial. |
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


![asd](images/latest.drawio.png)
<p> Arquitetura do Sistema </p>



</div>



## Dificuldades


## Resultados


## Conclusao

