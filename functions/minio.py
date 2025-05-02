import boto3
from botocore.config import Config
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import os
from dotenv import load_dotenv

load_dotenv()

def upload_to_minio(bucket_name: str, file_name: str, object_name: str) -> str:
    """
    Faz o upload de um arquivo para o MinIO e retorna a URL do arquivo.

    :param bucket_name: Nome do bucket no MinIO.
    :param file_name: Caminho do arquivo local a ser enviado.
    :param object_name: Nome do arquivo no bucket.
    :return: URL do arquivo enviado.
    """
    # Configuração do cliente S3
    endpoint_url = os.getenv("URL_MINIO")
    s3 = boto3.resource(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=os.getenv("ACCESS_KEY_MINIO"),
        aws_secret_access_key=os.getenv("SECRET_KEY_MINIO"),
        config=Config(signature_version='s3v4'),
        region_name='us-east-1',
    )

    try:
        # Verificar se o bucket existe
        bucket = s3.Bucket(bucket_name)
        if not bucket.creation_date:
            print(f"Bucket '{bucket_name}' não encontrado. Criando...")
            s3.create_bucket(Bucket=bucket_name)
            print(f"Bucket '{bucket_name}' criado com sucesso.")

        # Fazer o upload do arquivo com o Content-Type correto
        bucket.upload_file(
            file_name,
            object_name,
            ExtraArgs={'ContentType': 'image/png'}  # Define o Content-Type como image/png
        )
        print(f"Arquivo '{file_name}' enviado como '{object_name}' para o bucket '{bucket_name}'.")

        # Construir a URL do arquivo
        url = f"{endpoint_url}/{bucket_name}/{object_name}"
        
        return url

    except FileNotFoundError:
        raise FileNotFoundError(f"Erro: O arquivo '{file_name}' não foi encontrado.")
    except NoCredentialsError:
        raise NoCredentialsError("Erro: Credenciais inválidas ou ausentes.")
    except PartialCredentialsError:
        raise PartialCredentialsError("Erro: Credenciais incompletas.")
    except Exception as e:
        raise Exception(f"Erro inesperado: {e}")