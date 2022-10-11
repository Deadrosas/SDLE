from time import time
from datetime import datetime
class Post:
    def __init__(self, user, content):
        self.timestamp = time()
        self.content = content
        self.user = user

    def setID(self, id):
        self.id = id
    
    def __str__(self):
        return "------------------------------------\n"+"@%s"%(self.user)+":\n"+"\t%s"%(self.content)+"\n\t\t"+datetime.utcfromtimestamp(self.timestamp).strftime('%Y-%m-%d %H:%M:%S')+"\n"

