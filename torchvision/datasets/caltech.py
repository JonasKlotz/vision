import os
import os.path
import shutil
from pathlib import Path
from typing import Any, Callable, Optional, Union

from PIL import Image

from .utils import download_and_extract_archive, extract_archive, verify_str_arg
from .vision import VisionDataset


class Caltech101(VisionDataset):
    """`Caltech 101 <https://data.caltech.edu/records/20086>`_ Dataset.

    .. warning::

        This class needs `scipy <https://docs.scipy.org/doc/>`_ to load target files from `.mat` format.

    Args:
        root (str or ``pathlib.Path``): Root directory of dataset where directory
            ``caltech101`` exists or will be saved to if download is set to True.
        target_type (string or list, optional): Type of target to use, ``category`` or
            ``annotation``. Can also be a list to output a tuple with all specified
            target types.  ``category`` represents the target class, and
            ``annotation`` is a list of points from a hand-generated outline.
            Defaults to ``category``.
        transform (callable, optional): A function/transform that takes in a PIL image
            and returns a transformed version. E.g, ``transforms.RandomCrop``
        target_transform (callable, optional): A function/transform that takes in the
            target and transforms it.
        download (bool, optional): If true, downloads the dataset from the internet and
            puts it in root directory. If dataset is already downloaded, it is not
            downloaded again.

            .. warning::

                To download the dataset `gdown <https://github.com/wkentaro/gdown>`_ is required.
    """

    def __init__(
        self,
        root: Union[str, Path],
        target_type: Union[list[str], str] = "category",
        transform: Optional[Callable] = None,
        target_transform: Optional[Callable] = None,
        download: bool = False,
    ) -> None:
        super().__init__(os.path.join(root, "caltech101"), transform=transform, target_transform=target_transform)
        os.makedirs(self.root, exist_ok=True)
        if isinstance(target_type, str):
            target_type = [target_type]
        self.target_type = [verify_str_arg(t, "target_type", ("category", "annotation")) for t in target_type]

        if download:
            self.download()

        if not self._check_integrity():
            raise RuntimeError("Dataset not found or corrupted. You can use download=True to download it")

        self.categories = sorted(os.listdir(os.path.join(self.root, "101_ObjectCategories")))
        self.categories.remove("BACKGROUND_Google")  # this is not a real class

        # For some reason, the category names in "101_ObjectCategories" and
        # "Annotations" do not always match. This is a manual map between the
        # two. Defaults to using same name, since most names are fine.
        name_map = {
            "Faces": "Faces_2",
            "Faces_easy": "Faces_3",
            "Motorbikes": "Motorbikes_16",
            "airplanes": "Airplanes_Side_2",
        }
        self.annotation_categories = list(map(lambda x: name_map[x] if x in name_map else x, self.categories))

        self.index: list[int] = []
        self.y = []
        for i, c in enumerate(self.categories):
            n = len(os.listdir(os.path.join(self.root, "101_ObjectCategories", c)))
            self.index.extend(range(1, n + 1))
            self.y.extend(n * [i])

    def __getitem__(self, index: int) -> tuple[Any, Any]:
        """
        Args:
            index (int): Index

        Returns:
            tuple: (image, target) where the type of target specified by target_type.
        """
        import scipy.io

        img = Image.open(
            os.path.join(
                self.root,
                "101_ObjectCategories",
                self.categories[self.y[index]],
                f"image_{self.index[index]:04d}.jpg",
            )
        )

        target: Any = []
        for t in self.target_type:
            if t == "category":
                target.append(self.y[index])
            elif t == "annotation":
                data = scipy.io.loadmat(
                    os.path.join(
                        self.root,
                        "Annotations",
                        self.annotation_categories[self.y[index]],
                        f"annotation_{self.index[index]:04d}.mat",
                    )
                )
                target.append(data["obj_contour"])
        target = tuple(target) if len(target) > 1 else target[0]

        if self.transform is not None:
            img = self.transform(img)

        if self.target_transform is not None:
            target = self.target_transform(target)

        return img, target

    def _check_integrity(self) -> bool:
        # can be more robust and check hash of files
        return os.path.exists(os.path.join(self.root, "101_ObjectCategories"))

    def __len__(self) -> int:
        return len(self.index)

    def download(self) -> None:
        if self._check_integrity():
            return
        # Download and unzip the single ZIP containing both .tar files
        download_and_extract_archive(
            "https://data.caltech.edu/records/mzrjq-6wc02/files/caltech-101.zip?download=1",
            self.root,
            filename="caltech-101.zip",
            md5="3138e1922a9193bfa496528edbbc45d0",
        )
        archive_folder = os.path.join(self.root, "caltech-101")
        category_archive = os.path.join(archive_folder, "101_ObjectCategories.tar.gz")
        annotation_archive = os.path.join(archive_folder, "Annotations.tar")
        macos_meta = os.path.join(archive_folder, "__MACOSX")

        # Remove macOS metadata folder if it exists
        if os.path.isdir(macos_meta):
            shutil.rmtree(macos_meta)

        # Extract '101_ObjectCategories.tar.gz' into self.root
        extract_archive(category_archive, self.root, remove_finished=True)

        # Extract 'Annotations.tar' into self.root
        extract_archive(annotation_archive, self.root, remove_finished=True)

        # Delete the 'caltech-101' folder (which may now be empty or contain only other hidden files)
        if os.path.isdir(archive_folder):
            shutil.rmtree(archive_folder)

        # Remove the ZIP file itself
        zip_path = os.path.join(self.root, "caltech-101.zip")
        if os.path.isfile(zip_path):
            os.remove(zip_path)

    def extra_repr(self) -> str:
        return "Target type: {target_type}".format(**self.__dict__)


class Caltech256(VisionDataset):
    """`Caltech 256 <https://data.caltech.edu/records/20087>`_ Dataset.

    Args:
        root (str or ``pathlib.Path``): Root directory of dataset where directory
            ``caltech256`` exists or will be saved to if download is set to True.
        transform (callable, optional): A function/transform that takes in a PIL image
            and returns a transformed version. E.g, ``transforms.RandomCrop``
        target_transform (callable, optional): A function/transform that takes in the
            target and transforms it.
        download (bool, optional): If true, downloads the dataset from the internet and
            puts it in root directory. If dataset is already downloaded, it is not
            downloaded again.
    """

    def __init__(
        self,
        root: str,
        transform: Optional[Callable] = None,
        target_transform: Optional[Callable] = None,
        download: bool = False,
    ) -> None:
        super().__init__(os.path.join(root, "caltech256"), transform=transform, target_transform=target_transform)
        os.makedirs(self.root, exist_ok=True)

        if download:
            self.download()

        if not self._check_integrity():
            raise RuntimeError("Dataset not found or corrupted. You can use download=True to download it")

        self.categories = sorted(os.listdir(os.path.join(self.root, "256_ObjectCategories")))
        self.index: list[int] = []
        self.y = []
        for i, c in enumerate(self.categories):
            n = len(
                [
                    item
                    for item in os.listdir(os.path.join(self.root, "256_ObjectCategories", c))
                    if item.endswith(".jpg")
                ]
            )
            self.index.extend(range(1, n + 1))
            self.y.extend(n * [i])

    def __getitem__(self, index: int) -> tuple[Any, Any]:
        """
        Args:
            index (int): Index

        Returns:
            tuple: (image, target) where target is index of the target class.
        """
        img = Image.open(
            os.path.join(
                self.root,
                "256_ObjectCategories",
                self.categories[self.y[index]],
                f"{self.y[index] + 1:03d}_{self.index[index]:04d}.jpg",
            )
        )

        target = self.y[index]

        if self.transform is not None:
            img = self.transform(img)

        if self.target_transform is not None:
            target = self.target_transform(target)

        return img, target

    def _check_integrity(self) -> bool:
        # can be more robust and check hash of files
        return os.path.exists(os.path.join(self.root, "256_ObjectCategories"))

    def __len__(self) -> int:
        return len(self.index)

    def download(self) -> None:
        if self._check_integrity():
            return
        download_and_extract_archive(
            "https://data.caltech.edu/records/nyy15-4j048/files/256_ObjectCategories.tar",
            self.root,
            filename="256_ObjectCategories.tar",
            md5="67b4f42ca05d46448c6bb8ecd2220f6d",
        )
