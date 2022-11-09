# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen
from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Union

import pyscicat.client
from pyscicat import model

from .dataset import Dataset
from .typing import FileTransfer


class Client:
    """SciCat client to communicate with a backend.

    Clients hold all information needed to communicate with a SciCat instance
    and a filesystem that holds data files. Users of Scitacean should instantiate
    this class but not use it directly. Instead, the corresponding methods of
    ``Dataset`` should be called to download and upload data.

    Use :func:`Client.from_token` or :func:`Client.from_credentials` to initialize
    a client instead of the constructor directly.
    """

    def __init__(
        self,
        *,
        client: ScicatClient,
        file_transfer: Optional[FileTransfer],
    ):
        self._client = client
        self._file_transfer = file_transfer

    @classmethod
    def from_token(
        cls, *, url: str, token: str, file_transfer: Optional[FileTransfer] = None
    ) -> Client:
        """Create a new client and authenticate with a token.

        Parameters
        ----------
        url:
            URL of the SciCat api.
            It should include the suffix `api/vn` where `n` is a number.
        token:
            User token to authenticate with SciCat.

        Returns
        -------
        :
            A new client.
        """
        return Client(
            client=ScicatClient(pyscicat.client.from_token(base_url=url, token=token)),
            file_transfer=file_transfer,
        )

    @classmethod
    def from_credentials(
        cls,
        *,
        url: str,
        username: str,
        password: str,
        file_transfer: Optional[FileTransfer] = None,
    ) -> Client:
        """Create a new client and authenticate with username and password.

        Parameters
        ----------
        url:
            URL of the SciCat api.
            It should include the suffix `api/vn` where `n` is a number.
        username:
            Name of the user.
        password:
            Password of the user.

        Returns
        -------
        :
            A new client.
        """
        return Client(
            client=ScicatClient(
                pyscicat.client.from_credentials(
                    base_url=url, username=username, password=password
                )
            ),
            file_transfer=file_transfer,
        )

    def get_dataset(self, pid: str) -> Dataset:
        return Dataset.from_models(
            dataset_model=self.scicat.get_dataset_model(pid),
            orig_datablock_models=self.scicat.get_orig_datablocks(pid),
        )

    def upload_new_dataset_now(self, dataset: Dataset) -> Dataset:
        dset = dataset.prepare_as_new()
        dset.pid = dset.pid.without_prefix
        with self.file_transfer.connect_for_upload(dset.pid) as con:
            dset.source_folder = con.source_dir
            for file in dset.files:
                file.source_folder = dset.source_folder
                con.upload_file(local=file.local_path, remote=file.remote_access_path)

            models = dset.make_scicat_models()
            try:
                dataset_id = self.scicat.create_dataset_model(models.dataset)
            except pyscicat.client.ScicatCommError:
                for file in dset.files:
                    con.revert_upload(
                        local=file.local_path, remote=file.remote_access_path
                    )
                raise

        dset.pid = dataset_id
        models.datablock.datasetId = dataset_id
        try:
            self.scicat.create_orig_datablock(models.datablock)
        except pyscicat.client.ScicatCommError as exc:
            raise RuntimeError(
                f"Failed to upload original datablocks for SciCat dataset {dset.pid}:"
                f"\n{exc.args}\nThe dataset and data files were successfully uploaded "
                "but are not linked with each other. Please fix the dataset manually!"
            ) from exc

        return dset

    @property
    def scicat(self) -> ScicatClient:
        return self._client

    @property
    def file_transfer(self) -> FileTransfer:
        return self._file_transfer

    def download_file(self, *, remote: Union[str, Path], local: Union[str, Path]):
        if self._file_transfer is None:
            raise RuntimeError(
                f"No file transfer handler specified, cannot download file {remote}"
            )
        with self._file_transfer.connect_for_download() as con:
            con.download_file(remote=remote, local=local)

    def upload_file(
        self, *, dataset_id: str, remote: Union[str, Path], local: Union[str, Path]
    ) -> str:
        if self._file_transfer is None:
            raise RuntimeError(
                f"No file transfer handler specified, cannot upload file {local}"
            )
        with self._file_transfer.connect_for_upload(dataset_id) as con:
            return con.upload_file(remote=remote, local=local)


class ScicatClient:
    def __init__(self, client: pyscicat.client.ScicatClient):
        self._client = client

    def get_dataset_model(
        self, pid: str
    ) -> Union[model.DerivedDataset, model.RawDataset]:
        """Fetch a dataset from SciCat.

        Parameters
        ----------
        pid:
            Unique ID of the dataset. Must include the facility ID.

        Returns
        -------
        :
            A model of the dataset. The type is deduced from the received data.

        Raises
        ------
         pyscicat.client.ScicatCommError
            If the dataset does not exist or communication fails for some other reason.
        """
        if dset_json := self._client.datasets_get_one(pid):
            return (
                model.DerivedDataset(**dset_json)
                if dset_json["type"] == "derived"
                else model.RawDataset(**dset_json)
            )
        raise pyscicat.client.ScicatCommError(f"Unable to retrieve dataset {pid}")

    def get_orig_datablocks(self, pid: str) -> List[model.OrigDatablock]:
        """Fetch all orig datablocks from SciCat for a given dataset.

        Parameters
        ----------
        pid:
            Unique ID of the *dataset*. Must include the facility ID.

        Returns
        -------
        :
            Models of the orig datablocks.

        Raises
        ------
         pyscicat.client.ScicatCommError
            If the datablock does not exist or communication
            fails for some other reason.
        """
        if dblock_json := self._client.datasets_origdatablocks_get_one(pid):
            return [_make_orig_datablock(dblock) for dblock in dblock_json]
        raise pyscicat.client.ScicatCommError(
            f"Unable to retrieve orig datablock for dataset {pid}"
        )

    def create_dataset_model(self, dset: model.Dataset) -> str:
        """Create a new dataset in SciCat.

        The dataset PID must be either

        - ``None``, in which case SciCat assigns an ID.
        - An unused id, in which case SciCat uses it for the new dataset.

        If the ID already exists, creation will fail without
        modification to the database.
        Unless the new dataset is identical to the existing one,
        in which case nothing happens.

        Parameters
        ----------
        dset:
            Model of the dataset to create.

        Returns
        -------
        :
            The PID of the new dataset in the catalogue.

        Raises
        ------
         pyscicat.client.ScicatCommError
            If SciCat refuses the dataset or communication
            fails for some other reason.
        """
        return self._client.datasets_create(dset)["pid"]

    def create_orig_datablock(self, dblock: model.OrigDatablock):
        """Create a new orig datablock in SciCat.

        The datablock PID must be either

        - ``None``, in which case SciCat assigns an ID.
        - An unused id, in which case SciCat uses it for the new datablock.

        If the ID already exists, creation will fail without
        modification to the database.

        Parameters
        ----------
        dblock:
            Model of the orig datablock to create.

        Raises
        ------
         pyscicat.client.ScicatCommError
            If SciCat refuses the datablock or communication
            fails for some other reason.
        """
        self._client.datasets_origdatablock_create(dblock)


def _make_orig_datablock(fields):
    files = [model.DataFile(**file_fields) for file_fields in fields["dataFileList"]]
    return model.OrigDatablock(**{**fields, "dataFileList": files})
