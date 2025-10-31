from importlib.metadata import version


try:
	__version__ = version('albi0')
except Exception:
	__version__ = None


__all__ = ['__version__']