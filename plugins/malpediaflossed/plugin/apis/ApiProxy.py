class ApiProxy(object):
    
    def __init__(self):
        pass

    def get_filepath(self) -> str:
        """ return the filepath of the input binary """
        raise NotImplementedError

    def get_md5(self) -> str:
        """ return the hexdigest of the MD5 of the input binary """
        raise NotImplementedError

    def jump_to(self, addr) -> None:
        """ Set view to the given address """
        raise NotImplementedError

    def Strings(self):
        """ 
        Return the list of identified strings, each being a tuple with entries:
        (addr, string_type, string)
        e.g.
        (0x1000, "UTF8", "a_string")
        """
        raise NotImplementedError