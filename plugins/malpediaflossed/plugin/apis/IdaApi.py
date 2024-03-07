import idc
import idautils
import ida_nalt

from .ApiProxy import ApiProxy

class IdaApi(ApiProxy):
    
    def __init__(self):
        pass

    def get_filepath(self) -> str:
        return ida_nalt.get_input_file_path()

    def get_md5(self) -> str:
        return idautils.GetInputFileMD5().hex()

    def jump_to(self, addr):
        idc.jumpto(addr)

    def Strings(self):
        # TODO there are some more types, add PASCAL-type strings
        strtype_map = {
            0: "C",
            1: "C32",
            2: "C16",
            33554433: "UTF16LE"
        }
        reformatted_strings = []
        for item in idautils.Strings():
            reformatted_tuple = (item.ea, strtype_map.get(item.strtype, "unknown"), str(item))
            reformatted_strings.append(reformatted_tuple)
        return reformatted_strings
