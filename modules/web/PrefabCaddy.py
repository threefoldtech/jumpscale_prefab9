from js9 import j


app = j.tools.prefab._getBaseAppClass()


class PrefabCaddy(app):
    NAME = "caddy"
    default_plugins = ['git', 'jwt', 'login', 'webdav', 'restic', 'cgi',
                       'hugo', 'minify', 'search', 'filter', 'ratelimit']

    def _init(self):
        self.BUILDDIR_ = self.replace("$BUILDDIR/caddy")

    def reset(self):
        self.stop()
        app.reset(self)
        self._init()
        self.prefab.core.dir_remove(self.BUILDDIR_)
        self.prefab.core.dir_remove("$BINDIR/caddy")

    def build(self, reset=False, plugins=None):
        """
        Get/Build the binaries of caddy itself.
        :param reset: boolean to reset the build process
        :param plugins: list of plugins names to be installed
        :return:
        """
        if not self.core.isUbuntu:
            raise j.exceptions.RuntimeError("only ubuntu supported")

        if self.doneGet('build') and reset is False:
            return

        self.prefab.system.base.install()
        golang = self.prefab.runtimes.golang
        golang.install()

        # build caddy from source using our caddyman
        self.prefab.tools.git.pullRepo("https://github.com/incubaid/caddyman", dest="/tmp/caddyman")
        self.prefab.core.execute_bash("cd /tmp/caddyman && chmod u+x caddyman.sh")
        if not plugins:
            plugins = self.default_plugins
        cmd = "/tmp/caddyman/caddyman.sh install {plugins}".format(plugins=" ".join(plugins))
        self.prefab.core.execute_bash(cmd)
        self.doneSet('build')

    def install(self, plugins=None, reset=False, configpath="{{CFGDIR}}/caddy.cfg"):
        """
        will build if required & then install binary on right location
        """

        if not self.doneGet('build'):
            self.build(plugins=plugins)

        if self.doneGet('install') and reset is False and self.isInstalled():
            return

        self.prefab.core.file_copy('/opt/go_proj/bin/caddy', '$BINDIR/caddy')
        self.prefab.bash.profileDefault.addPath(self.prefab.core.dir_paths['BINDIR'])
        self.prefab.bash.profileDefault.save()

        configpath = self.replace(configpath)

        if not self.prefab.core.exists(configpath):
            # default configuration, can overwrite
            self.configure(configpath=configpath)

        fw = not self.prefab.core.run("ufw status 2> /dev/null", die=False)[0]

        port = self.getTCPPort(configpath=configpath)

        # Do if not  "ufw status 2> /dev/null" didn't run properly
        if fw:
            self.prefab.security.ufw.allowIncoming(port)

        if self.prefab.system.process.tcpport_check(port, ""):
            raise RuntimeError(
                "port %s is occupied, cannot install caddy" % port)

        self.doneSet('install')

    def reload(self, configpath="{{CFGDIR}}/caddy.cfg"):
        configpath = self.replace(configpath)
        for item in self.prefab.system.process.info_get():
            if item["process"] == "caddy":
                pid = item["pid"]
                self.prefab.core.run("kill -s USR1 %s" % pid)
                return True
        return False

    def configure(self, ssl=False, wwwrootdir="{{DATADIR}}/www/", configpath="{{CFGDIR}}/caddy.cfg",
                  logdir="{{LOGDIR}}/caddy/log", email='info@greenitglobe.com', port=8000):
        """
        @param caddyconfigfile
            template args available DATADIR, LOGDIR, WWWROOTDIR, PORT, TMPDIR, EMAIL ... (using mustasche)
        """

        C = """
        #tcpport:{{PORT}}
        :{{PORT}}
        gzip
        log {{LOGDIR}}/access.log
        errors {
            * {{LOGDIR}}/errors.log
        }
        root {{WWWROOTDIR}}
        """

        configpath = self.replace(configpath)

        args = {}
        args["WWWROOTDIR"] = self.replace(wwwrootdir).rstrip("/")
        args["LOGDIR"] = self.replace(logdir).rstrip("/")
        args["PORT"] = str(port)
        args["EMAIL"] = email
        args["CONFIGPATH"] = configpath

        C = self.replace(C, args)

        self.prefab.core.dir_ensure(args["LOGDIR"])
        self.prefab.core.dir_ensure(args["WWWROOTDIR"])

        self.prefab.core.file_write(configpath, C)

    def getTCPPort(self, configpath="{{CFGDIR}}/caddy.cfg"):
        configpath = self.replace(configpath)
        C = self.prefab.core.file_read(configpath)
        for line in C.split("\n"):
            if "#tcpport:" in line:
                return line.split(":")[1].strip()
        raise RuntimeError(
            "Can not find tcpport arg in config file, needs to be '#tcpport:'")

    def start(self, configpath="{{CFGDIR}}/caddy.cfg", agree=True, expect="done."):
        """
        @expect is to see if we can find this string in output of caddy starting
        """

        configpath = self.replace(configpath)

        if not j.sal.fs.exists(configpath, followlinks=True):
            raise RuntimeError(
                "could not find caddyconfigfile:%s" % configpath)

        tcpport = int(self.getTCPPort(configpath=configpath))

        # TODO: *1 reload does not work yet
        # if self.reload(configpath=configpath) == True:
        #     self.logger.info("caddy already started, will reload")
        #     return

        self.stop()  # will also kill

        cmd = self.prefab.bash.cmdGetPath("caddy")
        if agree:
            agree = " -agree"

        cmd = 'ulimit -n 8192; %s -conf=%s %s' % (cmd, configpath, agree)
        # wait 10 seconds for caddy to generate ssl certificate before returning error
        self.prefab.system.processmanager.get().ensure("caddy", cmd, wait=10, expect=expect)

    def stop(self):
        self.prefab.system.processmanager.get().stop("caddy")