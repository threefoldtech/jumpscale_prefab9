from Jumpscale import j

app = j.tools.prefab._BaseAppClass


class PrefabRust(app):
    NAME = 'rust'

    def install(self, reset=False):
        """
        https://static.rust-lang.org/dist/rust-1.12.0-x86_64-unknown-linux-gnu.tar.gz
        """
        if self.doneGet("install") and not reset:
            return

        version = 'rust-nightly-x86_64-unknown-linux-gnu'
        url = 'https://static.rust-lang.org/dist/{}.tar.gz'.format(version)
        dest = '/tmp/rust.tar.gz'
        self.prefab.core.run('curl -o {} {}'.format(dest, url))
        self.prefab.core.run('tar --overwrite -xf {} -C /tmp/'.format(dest))

        # copy file to correct locations.
        self.prefab.core.run(
            'cd /tmp/{version} && ./install.sh --prefix={DIR_BASE}/apps/rust --destdir=={DIR_BASE}/apps/rust'.format(version=version))

        # was profileDefault
        self.prefab.bash.profileJS.addPath(self.executor.replace('{DIR_BASE}/apps/rust/bin'))
        self.prefab.bash.profileJS.save()

        self.doneSet('install')
