# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from setuptools import setup, find_packages

setup(
    name="horton_helpers",
    version="0.0.0a1",  # Alpha Release
    description="Microsoft Azure IoT Hub Device SDK E2E FX helpers",
    license="MIT License",
    url="https://github.com/Azure/iot-sdks-e2e-fx",
    author="Microsoft Corporation",
    author_email="opensource@microsoft.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT Software License",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
    install_requires=[],
    python_requires=">=3.6, <4",
)
