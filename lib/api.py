from collections import namedtuple

import requests

TorrentStatus = namedtuple("TorrentStatus", [
    "active_time",  # type:int
    "all_time_download",  # type:int
    "all_time_upload",  # type:int
    "download_rate",  # type:int
    "finished_time",  # type:int
    "has_metadata",  # type:bool
    "paused",  # type:bool
    "peers",  # type:int
    "peers_total",  # type:int
    "progress",  # type:float
    "seeders",  # type:int
    "seeders_total",  # type:int
    "seeding_time",  # type:int
    "state",  # type:int
    "total",  # type:int
    "total_done",  # type:int
    "total_wanted",  # type:int
    "total_wanted_done",  # type:int
    "upload_rate",  # type:int
])

Torrent = namedtuple("Torrent", [
    "info_hash",  # type:str
    "name",  # type:str
    "size",  # type:int
    "status",  # type:TorrentStatus
])

FileStatus = namedtuple("FileStatus", [
    "total",  # type:int
    "total_done",  # type:int
    "buffering_progress",  # type:float
    "priority",  # type:int
    "progress",  # type:float
    "state",  # type:int
])

File = namedtuple("File", [
    "id",  # type:int
    "length",  # type:int
    "name",  # type:str
    "path",  # type:str
    "status",  # type:FileStatus
])


def from_dict(data, clazz, **converters):
    if data is None:
        return None
    # data = dict(data)
    for k, converter in converters.items():
        data[k] = converter(data.get(k))
    return clazz(**data)


class TorrestError(Exception):
    pass


class Torrest(object):
    def __init__(self, host, port):
        self._base_url = "http://{}:{}".format(host, port)
        self._session = requests.Session()

    def add_magnet(self, magnet):
        self._get("/add/magnet", params={"uri": magnet})

    def add_torrent(self, path):
        with open(path, "rb") as f:
            self._post("/add/torrent", files={"torrent": f})

    def torrents(self, status=True):
        """
        :type status: bool
        :rtype: typing.List[Torrent]
        """
        for t in self._get("/torrents", params={"status": self._bool_str(status)}).json():
            yield from_dict(t, Torrent, status=lambda v: from_dict(v, TorrentStatus))

    def pause_torrent(self, info_hash):
        self._get("/torrents/{}/pause".format(info_hash))

    def resume_torrent(self, info_hash):
        self._get("/torrents/{}/resume".format(info_hash))

    def download_torrent(self, info_hash):
        self._get("/torrents/{}/download".format(info_hash))

    def stop_torrent(self, info_hash):
        self._get("/torrents/{}/stop".format(info_hash))

    def remove_torrent(self, info_hash, delete=True):
        self._get("/torrents/{}/remove".format(info_hash), params={"delete": self._bool_str(delete)})

    def torrent_status(self, info_hash):
        """
        :type info_hash: str
        :rtype: TorrentStatus
        """
        return from_dict(self._get("/torrents/{}/status".format(info_hash)).json(), TorrentStatus)

    def files(self, info_hash, status=True):
        """
        :type info_hash: str
        :type status: bool
        :rtype: typing.List[File]
        """
        for f in self._get("/torrents/{}/files".format(info_hash), params={"status": self._bool_str(status)}).json():
            yield from_dict(f, File, status=lambda v: from_dict(v, FileStatus))

    def file_status(self, info_hash, file_id):
        """
        :type info_hash: str
        :type file_id: int
        :rtype: FileStatus
        """
        return from_dict(self._get("/torrents/{}/files/{}/status".format(info_hash, file_id)).json(), FileStatus)

    def download_file(self, info_hash, file_id, buffer=False):
        self._get("/torrents/{}/files/{}/download".format(info_hash, file_id),
                  params={"buffer": self._bool_str(buffer)})

    def stop_file(self, info_hash, file_id):
        self._get("/torrents/{}/files/{}/stop".format(info_hash, file_id))

    def serve_url(self, info_hash, file_id):
        return "{}/torrents/{}/files/{}/serve".format(self._base_url, info_hash, file_id)

    @staticmethod
    def _bool_str(value):
        return "true" if value else "false"

    def _post(self, url, **kwargs):
        return self._request("post", url, **kwargs)

    def _get(self, url, **kwargs):
        return self._request("get", url, **kwargs)

    def _request(self, method, url, validate=True, **kwargs):
        r = self._session.request(method, self._base_url + url, **kwargs)
        if validate and r.status_code >= 400:
            error = r.json()["error"]
            raise TorrestError(error)
        return r