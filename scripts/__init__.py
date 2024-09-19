import os
import sys
import argparse
from copy import copy
from typing import Callable
from collections import OrderedDict
from atexit import register

"""
a makfile style prelude

designate functions as a target with the @target decorator
designate a default target with the @default decorator
note: order matters when declaring targets

@target
  the @target decorator is used to mark a function as a runnable
  build target.

@default
  the @default decorator can be used to mark a function as
  the default invocation behavior.

  if you do not use the default decorator, you can declare a function
  named "default" and designate it with @target and it will become
  the default target.

  otherwise the first declared target will be the default behavior



"""

# import all environment variables
for key, value in os.environ.items():
    globals()[key] = value

def err(*args, **kwargs):
    kwargs['file'] = sys.stderr
    print(*args, **kwargs)

_targets = OrderedDict()
_default = None

def target(target):
    """decorator to specify a function as a target"""
    global _targets
    _targets[target.__name__] = target
    return target

def default(target):
    """decorator to specify a function as the default target"""
    global _targets
    global _default
    if _default is not None:
        err(f"cannot declare multiple @default")
        # skip registered atexit
        os._exit(1)

    _default = target
    return target

# define cli
@register
def _cli():
    global _targets
    global _default

    if not _default:
        _default = lambda *args: err("no targets defined!")
        if len(_targets) > 0:
            _default = next(iter(_targets.values()))

    if 'default' not in _targets:
        _targets['default'] = _default

    parser = argparse.ArgumentParser()
    parser.add_argument('target', type=str, nargs='?', default='default',
        help="target to build (function name defined in invoked script)")
    parser.add_argument('args', type=str, nargs='*',
        help="additional arguments to pass to target")
    args = parser.parse_args()

    target_args = []
    target_kwargs = {}
    for arg in args.args:
        if '=' in arg:
            key, val = arg.split('=')
            target_kwargs[key] = val
        else:
            target_args.append(arg)

    if args.target in _targets:
        target = _targets[args.target]
        if isinstance(target, Callable):
            target(*target_args, **target_kwargs)
        else:
            err(f"error: {args.target} not defined")