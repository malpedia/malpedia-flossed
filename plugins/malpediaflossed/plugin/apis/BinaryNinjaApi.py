import binascii

from binaryninjaui import DockHandler
from binaryninja.transform import Transform

from .ApiProxy import ApiProxy


# https://github.com/gaasedelen/lighthouse/blob/master/plugins/lighthouse/util/disassembler/binja_api.py#L181
def binja_get_bv_from_dock():
    dh = DockHandler.getActiveDockHandler()
    if not dh:
        return None
    vf = dh.getViewFrame()
    if not vf:
        return None
    vi = vf.getCurrentViewInterface()
    bv = vi.getData()
    return bv


class BinaryNinjaApi(ApiProxy):
    def __init__(self):
        super(BinaryNinjaApi, self).__init__()

    @property
    def bv(self):
        return binja_get_bv_from_dock()

    def get_filepath(self) -> str:
        return self.bv.file.original_filename

    def get_md5(self) -> str:
        bv = self.bv
        return Transform["RawHex"].encode(
            Transform["MD5"].encode(bv.file.raw.read(0, len(bv.file.raw)))
        ).decode()

    def jump_to(self, addr):
        bv = self.bv
        bv.navigate(bv.view, addr)

    def Strings(self):
        bv = self.bv
        # TODO could be harmonized across all APIs
        strtype_map = {
            0: "C",
            1: "UTF16",
            2: "UTF32",
            3: "UTF8"
        }
        reformatted_strings = []
        for item in bv.get_strings():
            reformatted_tuple = (item.start, strtype_map.get(item.type, "unknown"), item.value)
            reformatted_strings.append(reformatted_tuple)
        return reformatted_strings
