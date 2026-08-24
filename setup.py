from setuptools import setup, find_packages

setup(
    name="researcher",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn==0.24.0",
        "python-multipart==0.0.6",
        "pdfplumber==0.10.2",
        "python-dotenv==1.0.0",
        "together==0.2.5",
        "sqlalchemy==2.0.23",
        "aiosqlite==0.19.0",
        "langchain>=0.1.0",
        "spacy>=3.7.0",
        "pydantic>=2.5.0"
    ],
) 