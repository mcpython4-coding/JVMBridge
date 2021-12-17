import asyncio
import functools
import os
import typing
import zipfile
from abc import ABC
import aiofiles


class IClassAccessor(ABC):
    async def try_access_class_file(self, cls_name: str) -> typing.Optional[bytes]:
        return await self.try_access_resource(cls_name.replace(".", "/") + ".class")

    async def try_access_resource(self, path: str) -> typing.Optional[bytes]:
        pass


class AccessorDict(IClassAccessor):
    def __init__(self):
        self.items: typing.List[IClassAccessor] = []

    def add_accessor(self, accessor: IClassAccessor):
        self.items.append(accessor)
        return self

    async def try_access_class_file(self, cls_name: str) -> typing.Optional[bytes]:
        for item in self.items:
            data = await item.try_access_class_file(cls_name)
            if data is not None:
                return data

        print(cls_name)

    async def try_access_resource(self, path: str) -> typing.Optional[bytes]:
        for item in self.items:
            data = await item.try_access_resource(path)
            if data is not None:
                return data


class LookupCachedAccessorDict(IClassAccessor):
    def __init__(self):
        self.items: typing.List[IClassAccessor] = []
        self.lookup_cache: typing.Dict[str, IClassAccessor] = {}

    def add_accessor(self, accessor: IClassAccessor):
        self.items.append(accessor)
        return self

    async def try_access_resource(self, path: str) -> typing.Optional[bytes]:
        if path in self.lookup_cache:
            return await self.lookup_cache[path].try_access_resource(path)

        for item in self.items:
            data = await item.try_access_resource(path)
            if data is not None:
                self.lookup_cache[path] = item

                return data

    def clear_lookup_cache(self):
        self.lookup_cache.clear()


class DataCachedAccessorDict(IClassAccessor):
    def __init__(self):
        self.items: typing.List[IClassAccessor] = []
        self.lookup_cache: typing.Dict[str, bytes] = {}

    def add_accessor(self, accessor: IClassAccessor):
        self.items.append(accessor)
        return self

    async def try_access_resource(self, path: str) -> typing.Optional[bytes]:
        if path in self.lookup_cache:
            return self.lookup_cache[path]

        for item in self.items:
            data = await item.try_access_resource(path)
            if data is not None:
                self.lookup_cache[path] = data

                return data

    def clear_data_cache(self):
        self.lookup_cache.clear()


class MemoryFileSource(IClassAccessor):
    def __init__(self):
        self.files = {}
        self.classes = {}

    def provide_class(self, name: str, cls_data: bytes):
        self.classes[name] = cls_data
        self.provide_resource(name.replace(".", "/")+".class", cls_data)
        return self

    def provide_resource(self, path: str, data: bytes):
        self.files[path] = data
        return self

    async def try_access_class_file(self, cls_name: str) -> typing.Optional[bytes]:
        return self.classes[cls_name] if cls_name in self.classes else None

    async def try_access_resource(self, path: str) -> typing.Optional[bytes]:
        return self.files[path] if path in self.files else None


class SingleClassFileSource(IClassAccessor):
    def __init__(self, name: str, file: str | bytes):
        self.name = name

        if isinstance(file, str):
            with open(file, mode="rb") as f:
                file = f.read()

        self.data = file

    async def try_access_class_file(self, cls_name: str) -> typing.Optional[bytes]:
        if cls_name == self.name:
            return self.data

    async def try_access_resource(self, path: str) -> typing.Optional[bytes]:
        if path == self.name.replace(".", "/"):
            return self.data


class DirectoryFileSource(IClassAccessor):
    def __init__(self, directory: str):
        self.directory = directory

    async def try_access_resource(self, path: str) -> typing.Optional[bytes]:
        path = os.path.join(self.directory, path)
        if os.path.exists(path):
            async with aiofiles.open(path, mode="rb") as f:
                return await f.read()


class CachedFilelistDirectorySource(IClassAccessor):
    """
    Caches the file list in the directory
    Gives some boost when accessing a lot of files per second

    Use do_lookup() when you want to update the index
    """

    def __init__(self, directory: str):
        self.directory = directory
        self.cache = set()
        self.do_lookup()

    async def try_access_resource(self, path: str) -> typing.Optional[bytes]:
        path = os.path.join(self.directory, path)
        if path in self.cache:
            async with aiofiles.open(path, mode="rb") as f:
                return await f.read()

    def do_lookup(self):
        self.cache.clear()
        for root, _, files in os.walk(self.directory):
            self.cache |= {os.path.join(root, file) for file in files}


class CachedDataDirectorySource(IClassAccessor):
    """
    Should be even faster than CachedFilelistDirectorySource, but stores the data in memory,
    so it consumes more of it.

    Use clean() to clear the internal cache

    You may use the keyword arguments to disable caching for your request or go around the cache.
    WARNING: access times will go up if you do this!
    """

    def __init__(self, directory: str):
        self.directory = directory
        self.data_cache = {}

    async def try_access_class_file(self, cls_name: str, write_to_cache=True, read_from_cache=None) -> typing.Optional[bytes]:
        return await self.try_access_resource(cls_name.replace(".", "/") + ".class", write_to_cache, read_from_cache)

    async def try_access_resource(self, path: str, write_to_cache=True, read_from_cache=None) -> typing.Optional[bytes]:
        if read_from_cache is None:
            read_from_cache = write_to_cache

        if path in self.data_cache and read_from_cache:
            return self.data_cache[path]

        path = os.path.join(self.directory, path)
        if os.path.exists(path):
            async with aiofiles.open(path, mode="rb") as f:
                data = await f.read()

                if write_to_cache:
                    self.data_cache[path] = data

                return data

    def clean(self):
        self.data_cache.clear()


class ArchiveFileSource(IClassAccessor):
    def __init__(self, file: str):
        self.file = file
        self.data_file = zipfile.ZipFile(file)

        self.access_lock = asyncio.Lock()

    async def try_access_resource(self, path: str) -> typing.Optional[bytes]:
        await self.access_lock.acquire()
        try:
            return self.data_file.read(path)
        except KeyError:
            pass
        finally:
            self.access_lock.release()


class CachedNamelistArchiveSource(IClassAccessor):
    def __init__(self, file: str):
        self.file = file
        self.data_file = zipfile.ZipFile(file)
        self.namelist = self.data_file.namelist()

        self.access_lock = asyncio.Lock()

    async def try_access_resource(self, path: str) -> typing.Optional[bytes]:
        if path not in self.namelist: return

        await self.access_lock.acquire()
        data = self.data_file.read(path)
        self.access_lock.release()

        return data


class CachedDataArchiveSource(IClassAccessor):
    def __init__(self, file: str):
        self.file = file
        self.data_file = zipfile.ZipFile(file)
        self.cache = {}

        self.access_lock = asyncio.Lock()

    async def try_access_class_file(self, cls_name: str, write_to_cache=True, read_from_cache=None) -> typing.Optional[bytes]:
        return await self.try_access_resource(cls_name.replace(".", "/") + ".class", write_to_cache, read_from_cache)

    async def try_access_resource(self, path: str, write_to_cache=True, read_from_cache=None) -> typing.Optional[bytes]:
        if read_from_cache is None:
            read_from_cache = write_to_cache

        if path in self.cache and read_from_cache:
            return self.cache[path]

        await self.access_lock.acquire()
        data = self.data_file.read(path)
        self.access_lock.release()

        if write_to_cache:
            self.cache[path] = data

        return data


def decide_simple(file: str) -> IClassAccessor:
    if os.path.isfile(file):
        if not zipfile.is_zipfile(file): raise IOError("file is not an archive!")
        return ArchiveFileSource(file)

    elif os.path.isdir(file):
        return DirectoryFileSource(file)

    raise IOError("path is not a file or directory!")

