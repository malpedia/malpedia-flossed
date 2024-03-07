import hashlib
import base64

import cutter

from apis.ApiProxy import ApiProxy


class CutterApi(ApiProxy):
    def __init__(self):
        super(CutterApi, self).__init__()

    def get_filepath(self) -> str:
        return cutter.cmdj("ij")['core']['file']

    def get_md5(self) -> str:
        return cutter.cmdj("itj").get("md5", None)

    def jump_to(self, addr):
        return cutter.cmd(f"s {addr}")
