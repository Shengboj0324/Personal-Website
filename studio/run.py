"""Entry point: blender -b -P studio/run.py -- <slug> [preview|views|hero|bake|all]"""
import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
slug = args[0]
mode = args[1] if len(args) > 1 else 'preview'
module = importlib.import_module('islands.' + slug.replace('-', '_'))
module.build(mode)
