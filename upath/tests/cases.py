import pickle
from pathlib import Path
import re
import sys

import pytest
from upath import UPath
from .utils import posixify


class BaseTests:
    def test_cwd(self):
        with pytest.raises(NotImplementedError):
            self.path.cwd()

    def test_home(self):
        with pytest.raises(NotImplementedError):
            self.path.home()

    def test_stat(self):
        stat = self.path.stat()
        assert stat

    def test_chmod(self):
        with pytest.raises(NotImplementedError):
            self.path.joinpath("file1.txt").chmod(777)

    @pytest.mark.parametrize(
        "url, expected", [("file1.txt", True), ("fakefile.txt", False)]
    )
    def test_exists(self, url, expected):
        path = self.path.joinpath(url)
        assert path.exists() == expected

    def test_expanduser(self):
        with pytest.raises(NotImplementedError):
            self.path.expanduser()

    def test_glob(self, pathlib_base):
        mock_glob = list(self.path.glob("**.txt"))
        path_glob = list(pathlib_base.glob("**/*.txt"))

        mock_glob_normalized = sorted(
            [a.relative_to(self.path).path for a in mock_glob]
        )
        path_glob_normalized = sorted(
            [f"/{posixify(a.relative_to(pathlib_base))}" for a in path_glob]
        )

        assert mock_glob_normalized == path_glob_normalized

    def test_group(self):
        with pytest.raises(NotImplementedError):
            self.path.group()

    def test_is_dir(self):
        assert self.path.is_dir()

        path = self.path / "file1.txt"
        assert not path.is_dir()
        assert not (self.path / "not-existing-dir").is_dir()

    def test_is_file(self):
        path = self.path / "file1.txt"
        assert path.is_file()
        assert not self.path.is_file()

        assert not (self.path / "not-existing-file.txt").is_file()

    def test_is_mount(self):
        assert self.path.is_mount() is False

    def test_is_symlink(self):
        assert self.path.is_symlink() is False

    def test_is_socket(self):
        assert self.path.is_socket() is False

    def test_is_fifo(self):
        assert self.path.is_fifo() is False

    def test_is_block_device(self):
        assert self.path.is_block_device() is False

    def test_is_char_device(self):
        assert self.path.is_char_device() is False

    def test_iterdir(self, local_testdir):
        pl_path = Path(local_testdir)

        up_iter = list(self.path.iterdir())
        pl_iter = list(pl_path.iterdir())

        for x in up_iter:
            assert x.name != ""
            assert x.exists()

        assert len(up_iter) == len(pl_iter)
        assert set(p.name for p in pl_iter) == set(u.name for u in up_iter)
        assert next(self.path.parent.iterdir()).exists()

    def test_iterdir2(self, local_testdir):
        pl_path = Path(local_testdir) / "folder1"

        up_iter = list((self.path / "folder1").iterdir())
        pl_iter = list(pl_path.iterdir())

        for x in up_iter:
            assert x.exists()

        assert len(up_iter) == len(pl_iter)
        assert set(p.name for p in pl_iter) == set(u.name for u in up_iter)
        assert next(self.path.parent.iterdir()).exists()

    def test_lchmod(self):
        with pytest.raises(NotImplementedError):
            self.path.lchmod(mode=77)

    def test_lstat(self):
        with pytest.raises(NotImplementedError):
            self.path.lstat()

    def test_mkdir(self):
        new_dir = self.path.joinpath("new_dir")
        new_dir.mkdir()
        assert new_dir.exists()

    def test_open(self):
        pass

    def test_owner(self):
        with pytest.raises(NotImplementedError):
            self.path.owner()

    def test_read_bytes(self, pathlib_base):
        mock = self.path.joinpath("file2.txt")
        pl = pathlib_base.joinpath("file2.txt")
        assert mock.read_bytes() == pl.read_bytes()

    def test_read_text(self, local_testdir):
        upath = self.path.joinpath("file1.txt")
        assert (
            upath.read_text()
            == Path(local_testdir).joinpath("file1.txt").read_text()
        )

    def test_readlink(self):
        with pytest.raises(NotImplementedError):
            self.path.readlink()

    @pytest.mark.xfail
    def test_rename(self):
        # need to implement
        raise False

    def test_replace(self):
        pass

    def test_resolve(self):
        pass

    def test_rglob(self):
        pass

    def test_samefile(self):
        pass

    def test_symlink_to(self):
        pass

    def test_touch_unlink(self):
        path = self.path.joinpath("test_touch.txt")
        path.touch()
        assert path.exists()
        path.unlink()
        assert not path.exists()

        # should raise FileNotFoundError since file is missing
        with pytest.raises(FileNotFoundError):
            path.unlink()

        # file doesn't exists, but missing_ok is True
        path.unlink(missing_ok=True)

    def test_link_to(self):
        pass

    def test_write_bytes(self, pathlib_base):
        fn = "test_write_bytes.txt"
        s = b"hello_world"
        path = self.path.joinpath(fn)
        path.write_bytes(s)
        assert path.read_bytes() == s

    def test_write_text(self, pathlib_base):
        fn = "test_write_text.txt"
        s = "hello_world"
        path = self.path.joinpath(fn)
        path.write_text(s)
        assert path.read_text() == s

    def prepare_file_system(self):
        self.make_top_folder()
        self.make_test_files()

    def make_top_folder(self):
        self.path.mkdir(parents=True, exist_ok=True)

    def make_test_files(self):
        folder1 = self.path.joinpath("folder1")
        folder1.mkdir(exist_ok=True)
        folder1_files = ["file1.txt", "file2.txt"]
        for f in folder1_files:
            p = folder1.joinpath(f)
            p.touch()
            p.write_text(f)

        file1 = self.path.joinpath("file1.txt")
        file1.touch()
        file1.write_text("hello world")
        file2 = self.path.joinpath("file2.txt")
        file2.touch()
        file2.write_bytes(b"hello world")

    def test_fsspec_compat(self):
        fs = self.path.fs
        content = b"a,b,c\n1,2,3\n4,5,6"

        def strip_scheme(path):
            root = "" if sys.platform.startswith("win") else "/"
            return root + re.sub("^[a-z0-9]+:/*", "", str(path))

        upath1 = self.path / "output1.csv"
        p1 = strip_scheme(upath1)
        upath1.write_bytes(content)
        assert fs is upath1.fs
        with fs.open(p1) as f:
            assert f.read() == content
        upath1.unlink()

        # write with fsspec, read with upath
        upath2 = self.path / "output2.csv"
        p2 = strip_scheme(upath2)
        assert fs is upath2.fs
        with fs.open(p2, "wb") as f:
            f.write(content)
        assert upath2.read_bytes() == content
        upath2.unlink()

    def test_pickling(self):
        path = self.path
        pickled_path = pickle.dumps(path)
        recovered_path = pickle.loads(pickled_path)

        assert type(path) == type(recovered_path)
        assert str(path) == str(recovered_path)
        assert path.fs.storage_options == recovered_path.fs.storage_options

    def test_pickling_child_path(self):
        path = (self.path) / "subfolder" / "subsubfolder"
        pickled_path = pickle.dumps(path)
        recovered_path = pickle.loads(pickled_path)

        assert type(path) == type(recovered_path)
        assert str(path) == str(recovered_path)
        assert path._drv == recovered_path._drv
        assert path._root == recovered_path._root
        assert path._parts == recovered_path._parts
        assert path.fs.storage_options == recovered_path.fs.storage_options

    def test_child_path(self):
        path_str = str(self.path).rstrip("/")
        path_a = UPath(f"{path_str}/folder")
        path_b = self.path / "folder"

        assert str(path_a) == str(path_b)
        assert path_a._root == path_b._root
        assert path_a._drv == path_b._drv
        assert path_a._parts == path_b._parts
        assert path_a._url == path_b._url

    def test_copy_path(self):
        path = self.path
        copy_path = UPath(path)

        assert type(path) == type(copy_path)
        assert str(path) == str(copy_path)
        assert path._drv == copy_path._drv
        assert path._root == copy_path._root
        assert path._parts == copy_path._parts
        assert path.fs.storage_options == copy_path.fs.storage_options
