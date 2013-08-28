import json
import pstats

class myStats(pstats.Stats):
    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
    
    def  __init__(self, ps):
        pstats.Stats.__init__(self)
        self.__dict__ = ps.__dict__ 

ps = pstats.Stats('/home/openstack/profile_data/proxy.profile')
ms = myStats(ps)
print ms.toJSON()
