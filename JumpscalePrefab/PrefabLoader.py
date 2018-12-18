from Jumpscale import j

import sys
import inspect


class PrefabCat():
    pass

JSBASE = j.application.JSBaseClass
class PrefabLoader(JSBASE):

    def __init__(self):
        self.moduleList = {}
        JSBASE.__init__(self)
        self._logger_enable()

    def load(self, executor, prefab, moduleList=None):
        """
        walk over code files & find locations for jumpscale modules

        return as dict

        format

        [$rootlocationname][$locsubname]=(classfile,classname,importItems)

        """

        path = j.sal.fs.getDirName(inspect.getsourcefile(self.__class__))
        path = j.sal.fs.joinPaths(j.sal.fs.getParent(path), "prefab_modules")

        if moduleList is None:
            moduleList = self.moduleList

        self._logger.debug("find prefab modules in %s" % path)

        for cat in j.sal.fs.listDirsInDir(path, recursive=False, dirNameOnly=True, findDirectorySymlinks=True, followSymlinks=True):
            catpath = j.sal.fs.joinPaths(path, cat)
            # print(1)
            # print("prefab.%s = PrefabCat()"%cat)
            exec("prefab.%s = PrefabCat()" % cat)

            if catpath not in sys.path:
                sys.path.append(catpath)

            if not j.sal.fs.exists("%s/__init__.py" % catpath):
                j.sal.fs.writeFile("%s/__init__.py" % catpath, "")

            # print ("CATPATH:%s"%catpath)

            for classfile in j.sal.fs.listFilesInDir(catpath, False, "*.py"):
                # print(classfile)
                basename = j.sal.fs.getBaseName(classfile)
                basename = basename[:-3]

                # print("load prefab module:%s" % classfile)

                if not basename.startswith("Prefab"):
                    continue

                exec("from %s import %s" % (basename, basename))
                # self._logger.debug("import:%s"%basename)
                prefabObject = eval("%s(executor,prefab)" % basename)

                basenameLower = basename.replace("Prefab", "")
                basenameLower = basenameLower.lower()

                exec("prefab.%s.%s = prefabObject" % (cat, basenameLower))
