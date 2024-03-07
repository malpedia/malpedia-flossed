import binascii
import hashlib

import java.io

from .ApiProxy import ApiProxy


from ghidra.program.util import DefinedDataIterator
from ghidra.app.util import XReferenceUtil
from ghidra.util import MD5Utilities

class GhidraApi(ApiProxy):
    def __init__(self):
        super(GhidraApi, self).__init__()

    def get_filepath(self) -> str:
        filepath = getState().getCurrentProgram().getExecutablePath()
        return filepath[1:]

    def get_md5(self) -> str:
        return MD5Utilities.getMD5Hash(java.io.File(self.get_filepath()))

    def jump_to(self, addr):
        goTo(toAddr(addr))

    def Strings(self):
        # TODO I don't know how to Ghidra with strings :D
        strtype_map = {
            "char": "ascii",
            "ds": "ascii",
            "unicode": "UTF16"
        }
        reformatted_strings = []
        # https://reverseengineering.stackexchange.com/a/26417
        for string in DefinedDataIterator.definedStrings(currentProgram()):
            string_offset = int(str(string.getMinAddress()), 16)
            string_type = str(string.getDataType()).split("[")[0]
            reformatted_tuple = (string_offset, strtype_map.get(string_type, "unknown"), string.getValue())
            print(reformatted_tuple)
            reformatted_strings.append(reformatted_tuple)
        return reformatted_strings
