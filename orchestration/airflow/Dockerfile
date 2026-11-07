
FROM apache/airflow:3.3.2

USER airflow

RUN pip install --no-cache-dir \
    --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-3.3.2/constraints-3.13.txt" \
    "requests>=2.32,<3" \
    "python-dotenv>=1.0,<2" \
    "pandas>=2.2,<4" \
    "pyarrow==25.0.1" \
    "boto3>=1.35,<2"

WORKDIR /opt/airflow
