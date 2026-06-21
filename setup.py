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
    name="autocut-sub",
    install_requires=requirements,
    url="https://github.com/mli/autocut",
    project_urls={
        "source": "https://github.com/mli/autocut",
    },
    license="Apache License 2.0",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    extras_require={
        "all": transcribe_requirements + ["moviepy", "openai", "faster-whisper"],
        "transcribe": transcribe_requirements,
        "merge": ["moviepy"],
        "test": ["parameterized"],
        "openai": transcribe_requirements + ["openai"],
        "faster": transcribe_requirements + ["faster-whisper"],
    },
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "autocut = autocut.main:main",
        ]
    },
)
