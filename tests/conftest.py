"""Shared test fixtures for book2skill."""

import pytest
from pathlib import Path


@pytest.fixture
def test_book_path():
    return Path(__file__).parent.parent / "test_book.txt"


@pytest.fixture
def sample_cn_text():
    """Sample Chinese book text with clear chapter structure."""
    return """数据分析入门

第一章 概述

这是第一章的内容。数据分析在现代商业中扮演着越来越重要的角色。

1.1 什么是数据分析

数据分析是指用统计方法对数据进行分析的过程。

第二章 工具介绍

Python是数据分析最常用的工具。pandas和numpy是两个核心库。

第三章 案例实战

通过实际案例来学习数据分析的具体应用。
"""


@pytest.fixture
def sample_en_text():
    """Sample English book text."""
    return """Data Science Handbook

Chapter 1: Introduction

Data science is an interdisciplinary field that uses scientific methods.

1.1 What is Data Science

Data science combines statistics, computer science, and domain expertise.

1.2 Tools and Libraries

Python and R are the primary languages for data science.

Chapter 2: Data Preparation

Data preparation is often the most time-consuming part of any data project.

2.1 Cleaning Strategies

Missing values can be handled through deletion or imputation.
"""
