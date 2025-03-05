from setuptools import setup, find_packages

setup(
    name="stock-market-agents",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "requests>=2.25.0",
        "python-dotenv>=1.0.0",
        "chromadb>=0.4.0"
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-asyncio>=0.20.0"
        ]
    }
)
