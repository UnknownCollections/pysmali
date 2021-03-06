from typing import TypeVar, Union, Iterator, Iterable

T = TypeVar('T', covariant=True)

_default = object()


class Peekable(Iterator[T]):
    _it: Iterator[T]
    _top_item: T

    def __init__(self, it: Union[Iterable[T], Iterator[T]]):
        if isinstance(it, Iterator):
            self._it = it
        elif isinstance(it, Iterable):
            self._it = iter(it)
        else:
            raise TypeError
        self._top_item = self._safe_next()

    def _safe_next(self) -> T:
        try:
            return next(self._it)
        except StopIteration:
            return _default

    def __next__(self) -> T:
        next_value = self._top_item
        if next_value == _default:
            raise StopIteration

        self._top_item = self._safe_next()

        return next_value

    def peek(self, default: T = _default) -> T:
        if self._top_item == _default:
            if default != _default:
                return default
            raise StopIteration
        return self._top_item

    @property
    def empty(self) -> bool:
        return self._top_item == _default

    def __bool__(self) -> bool:
        return self._top_item != _default
