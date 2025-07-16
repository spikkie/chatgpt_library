from setuptools import find_packages, setup

setup(
    name="chatgpt_automation",
    version="0.1.0",
    description="Automate ChatGPT project interaction and file uploads using Playwright.",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "playwright>=1.42.0",
    ],
    python_requires=">=3.8",
)
