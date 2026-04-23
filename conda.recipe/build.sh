#!/bin/bash
# Conda 构建入口脚本
# conda build 会调用这个脚本

{{ PYTHON }} -m pip install . -vv
