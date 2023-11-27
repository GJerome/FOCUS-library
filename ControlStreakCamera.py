import socket as sk

class StreakCamera:
    """ This class connect """
    

    def __init__(self,IP,Port,Buffer):
        self.port = sk.socket(sk.AF_INET, sk.SOCK_STREAM)
        self.port.connect((IP, Port))
        self.Buffer=Buffer

    def Sendcommand(self,Cmd):
        self.port.send(Cmd)
    def GetResponse(self,BufferRead):
        rep=self.port.recv(BufferRead)
        return rep
    def __del__(self):
        self.port.close()

     


if __name__ == "__main__":
    print('Main file excecuting code')
