from setuptools import setup, find_packages

requirements = [
    "ffmpeg-python",
    "numpy",
    "opencc-python-reimplemented",
    "srt",
]

transcribe_requirements = [
    "openai-whisper",
    "pydub",
    "torchaudio",
    "tqdm",
]


setup(
    name="autocut",
    install_requires=requirements,
    python_requires=">=3.9",
    url="https://github.com/LYK-love/autocut",
    project_urls={
        "source": "https://github.com/LYK-love/autocut",
        "documentation": "https://github.com/LYK-love/autocut/tree/main/docs",
    },
    license="Apache License 2.0",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    extras_require={
        "all": transcribe_requirements
        + ["moviepy", "openai", "faster-whisper", "funasr", "qwen-asr"],
        "transcribe": transcribe_requirements,
        "merge": ["moviepy"],
        "test": ["parameterized", "pytest"],
        "openai": transcribe_requirements + ["openai"],
        "faster": transcribe_requirements + ["faster-whisper"],
        "sensevoice": transcribe_requirements + ["funasr"],
        "qwen3-asr": transcribe_requirements + ["qwen-asr"],
    },
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "autocut = autocut.main:main",
            "autocut-resolve = autocut.resolve:main",
            "autocut-harness = autocut.harness:main",
        ]
    },
)
