from jumpscale import j

base = j.tools.prefab._getBaseClass()

# from JumpscaleLib.sal.disklayout.DiskManager import DiskManager
raise NotImplemented()


class PrefabDiskManager(base,DiskManager):

    def __init__(self,executor, prefab):
        DiskManager.__init__(self)
        base.__init__(self, executor, prefab)

    def _init(self):
        self.set_executor(self.executor)
        self.getDisks()
