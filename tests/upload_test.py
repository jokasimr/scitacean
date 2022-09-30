# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2022 Scitacean contributors (https://github.com/SciCatProject/scitacean)
# @author Jan-Lukas Wynen

from contextlib import contextmanager
from pathlib import Path
import re
from urllib.parse import urljoin

from pyscicat.client import ScicatCommError
from pyscicat.model import DatasetType, DerivedDataset, Ownable
import pytest
from scitacean import Dataset

from .common.files import make_file


@pytest.fixture
def mock_request(local_url, mock_request):
    mock_request.post(
        urljoin(local_url, "Datasets?"),
        json=lambda request, context: {"pid": request.json()["pid"]},
    )
    mock_request.post(
        re.compile(r"/Datasets/[\da-f\-]+/origdatablocks"), json={"pid": "datablock_id"}
    )
    return mock_request


@pytest.fixture
def ownable():
    return Ownable(ownerGroup="ownerGroup", accessGroups=["group1", "group2"])


@pytest.fixture
def derived_dataset(ownable):
    return DerivedDataset(
        contactEmail="slartibartfast@magrathea.org",
        creationTime="2022-06-14T12:34:56",
        owner="slartibartfast",
        investigator="slartibartfast",
        sourceFolder="UPLOAD",
        type=DatasetType.derived,
        inputDatasets=[],
        usedSoftware=["PySciCat"],
        **ownable.dict(),
    )


@pytest.fixture
def dataset(derived_dataset, fs):
    make_file(fs, path="file.nxs")
    make_file(fs, path="the_log_file.log")
    dset = Dataset.new(derived_dataset)
    dset.add_local_files("file.nxs", "the_log_file.log")
    return dset


class FakeUpload:
    def __init__(self, dataset_id=None):
        self.uploaded = []
        self.reverted = []
        self.dataset_id = dataset_id

    def __call__(self, dataset_id):
        self.dataset_id = dataset_id
        return self

    @property
    def source_dir(self):
        return "/remote/upload"

    def upload_file(self, local, remote):
        self.uploaded.append({"local": local, "remote": remote})

    def revert_upload(self, local, remote):
        item = {"local": local, "remote": remote}
        del self.uploaded[self.uploaded.index(item)]
        self.reverted.append(item)

    @contextmanager
    def connect_for_upload(self, pid):
        yield self


def test_upload_creates_dataset(mock_request, client, dataset):
    finalized = dataset.upload_new_dataset_now(client, uploader=FakeUpload())
    dataset_requests = [
        req
        for req in mock_request.request_history
        if re.search(r"/Datasets([^/]|$)", str(req))
    ]
    assert len(dataset_requests) == 1
    assert dataset_requests[0].json() == finalized.model.dict(exclude_none=True)


def test_upload_uploads_files_to_source_folder(client, dataset):
    uploader = FakeUpload()
    dataset.upload_new_dataset_now(client, uploader=uploader)
    assert sorted(uploader.uploaded, key=lambda d: d["local"]) == [
        {"local": Path("file.nxs"), "remote": Path("/remote/upload/file.nxs")},
        {
            "local": Path("the_log_file.log"),
            "remote": Path("/remote/upload/the_log_file.log"),
        },
    ]


def test_upload_does_not_create_dataset_if_file_upload_fails(
    mock_request, client, dataset
):
    class RaisingUpload(FakeUpload):
        def upload_file(self, *, local, remote):
            raise RuntimeError("Fake upload failure")

        @contextmanager
        def connect_for_upload(self, pid):
            yield self

    with pytest.raises(RuntimeError):
        dataset.upload_new_dataset_now(client, uploader=RaisingUpload())

    assert all("Dataset" not in str(req) for req in mock_request.request_history)


def test_upload_cleans_up_files_if_dataset_ingestion_fails(
    local_url, mock_request, client, dataset
):
    def fail_ingestion(_request, _context):
        raise ScicatCommError("Ingestion failed")

    mock_request.reset()
    mock_request.post(
        urljoin(local_url, "Datasets?"),
        json=fail_ingestion,
    )

    uploader = FakeUpload()
    with pytest.raises(ScicatCommError):
        dataset.upload_new_dataset_now(client, uploader=uploader)

    assert not uploader.uploaded


def test_upload_creates_orig_data_blocks(
    mock_request,
    client,
    dataset,
):
    finalized = dataset.upload_new_dataset_now(client, uploader=FakeUpload())
    datablock_requests = [
        req for req in mock_request.request_history if "datablock" in str(req)
    ]
    assert len(datablock_requests) == 1
    assert f"Datasets/{finalized.pid}" in str(datablock_requests[0])
    assert datablock_requests[0].json() == finalized.datablock.dict(exclude_none=True)


def test_failed_datablock_upload_does_not_revert(mock_request, client, dataset):
    def fail_ingestion(_request, _context):
        raise ScicatCommError("Ingestion failed")

    mock_request.post(re.compile("origdatablocks"), json=fail_ingestion)

    uploader = FakeUpload()
    with pytest.raises(RuntimeError):
        dataset.upload_new_dataset_now(client, uploader=uploader)

    assert uploader.uploaded
    assert not uploader.reverted
